"""Tax, BHXH, and TNCN calculator API routes.

Deterministic endpoints use pure Python calculations.
Chat endpoint uses LLM to extract params, then calculates deterministically.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends

from src.api.models import (
    BHXHCalcRequest,
    BHXHCalcResponse,
    CalculatorChatRequest,
    CalculatorChatResponse,
    TaxCalcRequest,
    TaxCalcResponse,
    TNCNCalcRequest,
    TNCNCalcResponse,
)
from src.auth.dependencies import get_current_user
from src.core.gate import require_feature
from src.calculator.extractor import extract_business_params
from src.calculator.tax_rules import (
    calculate_bhxh,
    calculate_ho_kinh_doanh,
    calculate_tncn,
)
from src.db.models.user import User

router = APIRouter(prefix="/api/calculator", tags=["calculator"])


def _fmt_vnd(amount: int) -> str:
    return f"{amount:,.0f}đ"


@router.post("/tax", response_model=TaxCalcResponse)
async def calc_tax(
    req: TaxCalcRequest,
    _current_user: Annotated[User, Depends(require_feature("calculator"))],
) -> TaxCalcResponse:
    result = calculate_ho_kinh_doanh(req.doanh_thu_thang, req.loai_hinh)
    return TaxCalcResponse(**asdict(result))


@router.post("/bhxh", response_model=BHXHCalcResponse)
async def calc_bhxh(
    req: BHXHCalcRequest,
    _current_user: Annotated[User, Depends(require_feature("calculator"))],
) -> BHXHCalcResponse:
    result = calculate_bhxh(req.luong_dong_bhxh, req.so_nhan_vien, req.region)
    return BHXHCalcResponse(
        luong_dong_bhxh=result.luong_dong_bhxh,
        luong_dong_bhxh_cap=result.luong_dong_bhxh_cap,
        so_nhan_vien=result.so_nhan_vien,
        region=result.region,
        min_wage=result.min_wage,
        lines=[asdict(l) for l in result.lines],
        total_employee=result.total_employee,
        total_employer=result.total_employer,
        total_monthly=result.total_monthly,
        total_company_monthly=result.total_company_monthly,
    )


@router.post("/tncn", response_model=TNCNCalcResponse)
async def calc_tncn(
    req: TNCNCalcRequest,
    _current_user: Annotated[User, Depends(require_feature("calculator"))],
) -> TNCNCalcResponse:
    result = calculate_tncn(req.thu_nhap, req.giam_tru_gia_canh, req.so_nguoi_phu_thuoc)
    return TNCNCalcResponse(**asdict(result))


@router.post("/chat", response_model=CalculatorChatResponse)
async def calc_chat(
    req: CalculatorChatRequest,
    _current_user: Annotated[User, Depends(require_feature("calculator"))],
) -> CalculatorChatResponse:
    """Neuro-symbolic: LLM extracts params → Python calculates → format response."""
    params = await extract_business_params(req.question)

    results: list[str] = []
    tax_result = None
    bhxh_result = None
    tncn_result = None

    calc_type = params.calculation_type or "all"

    # Tax (ho kinh doanh)
    if params.doanh_thu and params.loai_hinh and calc_type in ("tax", "all"):
        r = calculate_ho_kinh_doanh(params.doanh_thu, params.loai_hinh)
        tax_result = TaxCalcResponse(**asdict(r))
        results.append(
            f"**Thuế hộ kinh doanh ({r.loai_hinh}):**\n"
            f"- Doanh thu: {_fmt_vnd(r.doanh_thu)}\n"
            f"- Thuế GTGT ({r.vat_rate*100:.0f}%): {_fmt_vnd(r.vat_amount)}\n"
            f"- Thuế TNCN ({r.tncn_rate*100:.1f}%): {_fmt_vnd(r.tncn_amount)}\n"
            f"- **Tổng thuế: {_fmt_vnd(r.total_tax)}** "
            f"(tỷ lệ thực: {r.effective_rate*100:.1f}%)"
        )

    # BHXH
    if params.luong_dong_bhxh and calc_type in ("bhxh", "all"):
        r = calculate_bhxh(
            params.luong_dong_bhxh,
            params.so_nhan_vien or 1,
            params.region or "vung_1",
        )
        bhxh_result = BHXHCalcResponse(
            luong_dong_bhxh=r.luong_dong_bhxh,
            luong_dong_bhxh_cap=r.luong_dong_bhxh_cap,
            so_nhan_vien=r.so_nhan_vien,
            region=r.region,
            min_wage=r.min_wage,
            lines=[asdict(l) for l in r.lines],
            total_employee=r.total_employee,
            total_employer=r.total_employer,
            total_monthly=r.total_monthly,
            total_company_monthly=r.total_company_monthly,
        )
        lines_detail = "\n".join(
            f"  - {l.label}: NLĐ {l.rate_employee*100:.1f}% = {_fmt_vnd(l.amount_employee)}, "
            f"DN {l.rate_employer*100:.1f}% = {_fmt_vnd(l.amount_employer)}"
            for l in r.lines
        )
        results.append(
            f"**BHXH/BHYT/BHTN** (lương đóng: {_fmt_vnd(r.luong_dong_bhxh_cap)}):\n"
            f"{lines_detail}\n"
            f"- Tổng NLĐ đóng: {_fmt_vnd(r.total_employee)}/tháng\n"
            f"- Tổng DN đóng: {_fmt_vnd(r.total_employer)}/tháng\n"
            f"- **Tổng: {_fmt_vnd(r.total_monthly)}/người/tháng**"
        )
        if r.so_nhan_vien > 1:
            results.append(
                f"- Toàn công ty ({r.so_nhan_vien} NV): "
                f"**{_fmt_vnd(r.total_company_monthly)}/tháng**"
            )

    # TNCN
    if params.thu_nhap and calc_type in ("tncn", "all"):
        r = calculate_tncn(
            params.thu_nhap,
            giam_tru_gia_canh=True,
            so_nguoi_phu_thuoc=params.so_nguoi_phu_thuoc or 0,
        )
        tncn_result = TNCNCalcResponse(**asdict(r))
        results.append(
            f"**Thuế TNCN (tiền lương):**\n"
            f"- Thu nhập: {_fmt_vnd(r.thu_nhap)}\n"
            f"- Giảm trừ bản thân: {_fmt_vnd(r.giam_tru_ban_than)}\n"
            f"- Giảm trừ {r.so_nguoi_phu_thuoc} người phụ thuộc: "
            f"{_fmt_vnd(r.giam_tru_phu_thuoc)}\n"
            f"- Thu nhập chịu thuế: {_fmt_vnd(r.thu_nhap_chiu_thue)}\n"
            f"- **Thuế TNCN: {_fmt_vnd(r.total_tax)}** "
            f"(tỷ lệ thực: {r.effective_rate*100:.1f}%)"
        )

    if not results:
        summary = (
            "Tôi chưa xác định được đủ thông tin để tính toán. "
            "Vui lòng cung cấp:\n"
            "- **Thuế HKD**: doanh thu, loại hình (dịch vụ/thương mại/sản xuất)\n"
            "- **BHXH**: mức lương đóng BHXH, số nhân viên\n"
            "- **Thuế TNCN**: thu nhập, số người phụ thuộc"
        )
    else:
        summary = "\n\n".join(results)

    return CalculatorChatResponse(
        summary=summary,
        tax=tax_result,
        bhxh=bhxh_result,
        tncn=tncn_result,
    )

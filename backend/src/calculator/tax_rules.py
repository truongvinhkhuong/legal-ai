"""Deterministic tax, BHXH, and TNCN calculation engine.

All calculations are pure Python — NEVER use LLM for math.
Constants are reused from compliance_rules where available.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from src.contracts.compliance_rules import BHXH_RATES, MIN_WAGE_2024


# ---------------------------------------------------------------------------
# Ho kinh doanh tax rates — Luat Thue GTGT, Luat Thue TNCN
# ---------------------------------------------------------------------------

HO_KINH_DOANH_RATES: dict[str, dict[str, float]] = {
    "dich_vu": {"vat": 0.05, "tncn": 0.02},
    "thuong_mai": {"vat": 0.01, "tncn": 0.005},
    "san_xuat": {"vat": 0.03, "tncn": 0.015},
    "cho_thue_tai_san": {"vat": 0.05, "tncn": 0.05},
    "hoat_dong_khac": {"vat": 0.02, "tncn": 0.01},
}

# TNCN progressive brackets — Luat Thue TNCN, Dieu 22
# (upper_limit, rate) — upper_limit is monthly taxable income in VND
TNCN_BRACKETS: list[tuple[int, float]] = [
    (5_000_000, 0.05),
    (10_000_000, 0.10),
    (18_000_000, 0.15),
    (32_000_000, 0.20),
    (52_000_000, 0.25),
    (80_000_000, 0.30),
    (999_999_999_999, 0.35),
]

# Giam tru gia canh — Nghi quyet 954/2020/UBTVQH14
GIAM_TRU_BAN_THAN = 11_000_000  # 11 trieu/thang
GIAM_TRU_PHU_THUOC = 4_400_000  # 4.4 trieu/nguoi/thang

# BHXH salary cap — 20 lan luong co so (2024: 2,340,000 x 20 = 46,800,000)
LUONG_CO_SO_2024 = 2_340_000
BHXH_SALARY_CAP = LUONG_CO_SO_2024 * 20  # 46,800,000

# Deadline rules
DEADLINE_RULES = {
    "bhxh": {"day": 20, "description": "Nộp BHXH, BHYT, BHTN tháng trước"},
    "vat_monthly": {"day": 20, "description": "Nộp tờ khai & thuế GTGT tháng trước"},
    "vat_quarterly": {"day": 30, "description": "Nộp tờ khai & thuế GTGT quý trước"},
    "tncn_monthly": {"day": 20, "description": "Nộp thuế TNCN khấu trừ tháng trước"},
    "tncn_quyet_toan": {
        "month": 3, "day": 31,
        "description": "Quyết toán thuế TNCN năm trước",
    },
}


# ---------------------------------------------------------------------------
# Result data classes
# ---------------------------------------------------------------------------

@dataclass
class TaxBreakdown:
    doanh_thu: int
    loai_hinh: str
    vat_rate: float
    vat_amount: int
    tncn_rate: float
    tncn_amount: int
    total_tax: int
    effective_rate: float  # tong thue / doanh thu


@dataclass
class BHXHLine:
    label: str
    rate_employee: float
    rate_employer: float
    amount_employee: int
    amount_employer: int


@dataclass
class BHXHBreakdown:
    luong_dong_bhxh: int
    luong_dong_bhxh_cap: int  # after applying cap
    so_nhan_vien: int
    region: str
    min_wage: int
    lines: list[BHXHLine] = field(default_factory=list)
    total_employee: int = 0
    total_employer: int = 0
    total_monthly: int = 0  # per employee
    total_company_monthly: int = 0  # for all employees


@dataclass
class TNCNBreakdown:
    thu_nhap: int
    giam_tru_ban_than: int
    giam_tru_phu_thuoc: int
    so_nguoi_phu_thuoc: int
    total_giam_tru: int
    thu_nhap_chiu_thue: int
    brackets: list[dict]  # [{from, to, rate, tax}]
    total_tax: int
    effective_rate: float


@dataclass
class Deadline:
    date_str: str  # YYYY-MM-DD
    title: str
    description: str
    category: str  # "bhxh" | "vat" | "tncn"
    is_overdue: bool = False


# ---------------------------------------------------------------------------
# Calculation functions
# ---------------------------------------------------------------------------

def calculate_ho_kinh_doanh(doanh_thu_thang: int, loai_hinh: str) -> TaxBreakdown:
    """Calculate VAT + TNCN for ho kinh doanh ca the.

    Per Thong tu 40/2021/TT-BTC.
    """
    rates = HO_KINH_DOANH_RATES.get(loai_hinh, HO_KINH_DOANH_RATES["hoat_dong_khac"])
    vat_rate = rates["vat"]
    tncn_rate = rates["tncn"]

    vat_amount = int(doanh_thu_thang * vat_rate)
    tncn_amount = int(doanh_thu_thang * tncn_rate)
    total_tax = vat_amount + tncn_amount
    effective_rate = total_tax / doanh_thu_thang if doanh_thu_thang > 0 else 0.0

    return TaxBreakdown(
        doanh_thu=doanh_thu_thang,
        loai_hinh=loai_hinh,
        vat_rate=vat_rate,
        vat_amount=vat_amount,
        tncn_rate=tncn_rate,
        tncn_amount=tncn_amount,
        total_tax=total_tax,
        effective_rate=effective_rate,
    )


def calculate_bhxh(
    luong_dong_bhxh: int,
    so_nhan_vien: int = 1,
    region: str = "vung_1",
) -> BHXHBreakdown:
    """Calculate BHXH/BHYT/BHTN for employer + employee.

    Salary is capped at 20x base salary for BHXH/BHYT,
    and 20x min_wage for BHTN.
    """
    min_wage = MIN_WAGE_2024.get(region, MIN_WAGE_2024["vung_1"])

    # Cap salary for BHXH/BHYT at 20x luong co so
    luong_cap = min(luong_dong_bhxh, BHXH_SALARY_CAP)

    emp_rates = BHXH_RATES["employee"]
    er_rates = BHXH_RATES["employer"]

    lines = [
        BHXHLine(
            label="BHXH",
            rate_employee=emp_rates["bhxh"],
            rate_employer=er_rates["bhxh"],
            amount_employee=int(luong_cap * emp_rates["bhxh"]),
            amount_employer=int(luong_cap * er_rates["bhxh"]),
        ),
        BHXHLine(
            label="BHYT",
            rate_employee=emp_rates["bhyt"],
            rate_employer=er_rates["bhyt"],
            amount_employee=int(luong_cap * emp_rates["bhyt"]),
            amount_employer=int(luong_cap * er_rates["bhyt"]),
        ),
        BHXHLine(
            label="BHTN",
            rate_employee=emp_rates["bhtn"],
            rate_employer=er_rates["bhtn"],
            amount_employee=int(luong_cap * emp_rates["bhtn"]),
            amount_employer=int(luong_cap * er_rates["bhtn"]),
        ),
    ]

    total_employee = sum(l.amount_employee for l in lines)
    total_employer = sum(l.amount_employer for l in lines)
    total_monthly = total_employee + total_employer

    return BHXHBreakdown(
        luong_dong_bhxh=luong_dong_bhxh,
        luong_dong_bhxh_cap=luong_cap,
        so_nhan_vien=so_nhan_vien,
        region=region,
        min_wage=min_wage,
        lines=lines,
        total_employee=total_employee,
        total_employer=total_employer,
        total_monthly=total_monthly,
        total_company_monthly=(total_employee + total_employer) * so_nhan_vien,
    )


def calculate_tncn(
    thu_nhap: int,
    giam_tru_gia_canh: bool = True,
    so_nguoi_phu_thuoc: int = 0,
) -> TNCNBreakdown:
    """Calculate personal income tax (tien luong, tien cong) progressive brackets.

    Per Luat Thue TNCN + Nghi quyet 954/2020.
    """
    gt_ban_than = GIAM_TRU_BAN_THAN if giam_tru_gia_canh else 0
    gt_phu_thuoc = GIAM_TRU_PHU_THUOC * so_nguoi_phu_thuoc
    total_giam_tru = gt_ban_than + gt_phu_thuoc

    thu_nhap_chiu_thue = max(0, thu_nhap - total_giam_tru)

    # Progressive tax calculation
    brackets_detail: list[dict] = []
    remaining = thu_nhap_chiu_thue
    prev_limit = 0
    total_tax = 0

    for upper_limit, rate in TNCN_BRACKETS:
        if remaining <= 0:
            break
        bracket_size = upper_limit - prev_limit
        taxable_in_bracket = min(remaining, bracket_size)
        tax_in_bracket = int(taxable_in_bracket * rate)

        brackets_detail.append({
            "from": prev_limit,
            "to": prev_limit + taxable_in_bracket,
            "rate": rate,
            "taxable": taxable_in_bracket,
            "tax": tax_in_bracket,
        })

        total_tax += tax_in_bracket
        remaining -= taxable_in_bracket
        prev_limit = upper_limit

    effective_rate = total_tax / thu_nhap if thu_nhap > 0 else 0.0

    return TNCNBreakdown(
        thu_nhap=thu_nhap,
        giam_tru_ban_than=gt_ban_than,
        giam_tru_phu_thuoc=gt_phu_thuoc,
        so_nguoi_phu_thuoc=so_nguoi_phu_thuoc,
        total_giam_tru=total_giam_tru,
        thu_nhap_chiu_thue=thu_nhap_chiu_thue,
        brackets=brackets_detail,
        total_tax=total_tax,
        effective_rate=effective_rate,
    )


def get_monthly_deadlines(year: int, month: int) -> list[Deadline]:
    """Return compliance deadlines for a given month."""
    today = date.today()
    deadlines: list[Deadline] = []

    # BHXH — due 20th every month
    d = date(year, month, 20)
    deadlines.append(Deadline(
        date_str=d.isoformat(),
        title=f"Nộp BHXH tháng {month - 1 if month > 1 else 12}/{year if month > 1 else year - 1}",
        description=DEADLINE_RULES["bhxh"]["description"],
        category="bhxh",
        is_overdue=d < today,
    ))

    # VAT monthly — due 20th
    deadlines.append(Deadline(
        date_str=d.isoformat(),
        title=f"Nộp thuế GTGT tháng {month - 1 if month > 1 else 12}",
        description=DEADLINE_RULES["vat_monthly"]["description"],
        category="vat",
        is_overdue=d < today,
    ))

    # TNCN monthly — due 20th
    deadlines.append(Deadline(
        date_str=d.isoformat(),
        title=f"Nộp thuế TNCN khấu trừ tháng {month - 1 if month > 1 else 12}",
        description=DEADLINE_RULES["tncn_monthly"]["description"],
        category="tncn",
        is_overdue=d < today,
    ))

    # TNCN quyet toan — only in March
    if month == 3:
        d_qt = date(year, 3, 31)
        deadlines.append(Deadline(
            date_str=d_qt.isoformat(),
            title=f"Quyết toán thuế TNCN năm {year - 1}",
            description=DEADLINE_RULES["tncn_quyet_toan"]["description"],
            category="tncn",
            is_overdue=d_qt < today,
        ))

    # VAT quarterly — last month of quarter (3, 6, 9, 12), due 30th of next month
    if month in (1, 4, 7, 10):
        prev_quarter_end_month = month - 1 if month > 1 else 12
        d_vq = date(year, month, 30) if month != 1 else date(year, 1, 30)
        deadlines.append(Deadline(
            date_str=d_vq.isoformat(),
            title=f"Nộp thuế GTGT quý {(prev_quarter_end_month - 1) // 3 + 1}/{year if month > 1 else year - 1}",
            description=DEADLINE_RULES["vat_quarterly"]["description"],
            category="vat",
            is_overdue=d_vq < today,
        ))

    return sorted(deadlines, key=lambda dl: dl.date_str)

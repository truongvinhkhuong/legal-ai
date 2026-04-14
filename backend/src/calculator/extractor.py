"""LLM-based parameter extractor for natural language calculator queries.

Extracts business parameters from Vietnamese questions so the deterministic
calculator can process them. Falls back gracefully on extraction failure.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Optional

import openai

from src.config.settings import settings

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
Ban la tro ly phan tich cau hoi ve thue va BHXH cho doanh nghiep Viet Nam.
Tu cau hoi cua nguoi dung, hay trich xuat cac thong so sau (neu co):

- doanh_thu: doanh thu thang (so nguyen, don vi VND)
- loai_hinh: loai hinh kinh doanh ("dich_vu" | "thuong_mai" | "san_xuat" | "cho_thue_tai_san" | "hoat_dong_khac")
- luong_dong_bhxh: muc luong dong BHXH cua 1 nguoi (so nguyen, VND)
- so_nhan_vien: so luong nhan vien (so nguyen)
- region: khu vuc ("vung_1" | "vung_2" | "vung_3" | "vung_4")
- thu_nhap: thu nhap ca nhan hang thang (so nguyen, VND)
- so_nguoi_phu_thuoc: so nguoi phu thuoc (so nguyen)
- calculation_type: loai tinh toan ("tax" | "bhxh" | "tncn" | "all")

Chi tra ve JSON, khong giai thich. Neu khong xac dinh duoc thi de null.

Cau hoi: {question}
"""


@dataclass
class BusinessParams:
    doanh_thu: Optional[int] = None
    loai_hinh: Optional[str] = None
    luong_dong_bhxh: Optional[int] = None
    so_nhan_vien: Optional[int] = None
    region: Optional[str] = None
    thu_nhap: Optional[int] = None
    so_nguoi_phu_thuoc: Optional[int] = None
    calculation_type: Optional[str] = None


async def extract_business_params(question: str) -> BusinessParams:
    """Use LLM to extract business parameters from a natural language question."""
    try:
        client = openai.AsyncOpenAI(
            base_url=settings.deepseek_base_url,
            api_key=settings.deepseek_api_key,
        )

        response = await client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "user", "content": EXTRACTION_PROMPT.format(question=question)},
            ],
            temperature=0.0,
            max_tokens=300,
        )

        raw = response.choices[0].message.content or "{}"
        # Strip markdown code fences if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
            if raw.endswith("```"):
                raw = raw[:-3]
            raw = raw.strip()

        data = json.loads(raw)
        return BusinessParams(
            doanh_thu=_to_int(data.get("doanh_thu")),
            loai_hinh=data.get("loai_hinh"),
            luong_dong_bhxh=_to_int(data.get("luong_dong_bhxh")),
            so_nhan_vien=_to_int(data.get("so_nhan_vien")),
            region=data.get("region"),
            thu_nhap=_to_int(data.get("thu_nhap")),
            so_nguoi_phu_thuoc=_to_int(data.get("so_nguoi_phu_thuoc")),
            calculation_type=data.get("calculation_type"),
        )

    except Exception:
        logger.warning("Failed to extract business params from question", exc_info=True)
        return BusinessParams()


def _to_int(val: object) -> Optional[int]:
    if val is None:
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None

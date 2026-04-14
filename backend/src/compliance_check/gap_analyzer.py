"""Compliance gap analyzer — deterministic keyword match + optional LLM semantic match.

Step 1: Parse document text
Step 2: Keyword match each checklist item against document sections
Step 3: For unmatched items, use LLM to check semantic coverage
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field

import openai

from src.compliance_check.checklists import CHECKLISTS, ChecklistItem
from src.config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class GapItem:
    checklist_item_id: str
    title_vi: str
    legal_basis: str
    status: str  # "dat" | "khong_dat" | "khong_ro"
    matched_section: str = ""
    suggestion_vi: str = ""


@dataclass
class GapReport:
    checklist_type: str
    total_items: int
    dat_count: int
    khong_dat_count: int
    khong_ro_count: int
    coverage_pct: float
    items: list[GapItem] = field(default_factory=list)


def _normalize(text: str) -> str:
    """Lowercase, strip diacritics-insensitive for keyword matching."""
    return text.lower().replace("\n", " ").replace("\r", " ")


def _keyword_match(text_normalized: str, keywords: list[str]) -> str | None:
    """Check if any keyword group matches in the text. Returns matched keyword or None."""
    for kw in keywords:
        if kw.lower() in text_normalized:
            return kw
    return None


async def analyze_gaps(
    file_content: str,
    checklist_type: str,
) -> GapReport:
    """Analyze compliance gaps in document text against a checklist."""
    checklist = CHECKLISTS.get(checklist_type)
    if not checklist:
        return GapReport(
            checklist_type=checklist_type,
            total_items=0, dat_count=0, khong_dat_count=0, khong_ro_count=0,
            coverage_pct=0.0,
        )

    text_normalized = _normalize(file_content)
    items: list[GapItem] = []
    unmatched: list[tuple[int, ChecklistItem]] = []

    # Pass 1: deterministic keyword match
    for i, ci in enumerate(checklist):
        matched_kw = _keyword_match(text_normalized, ci.keywords)
        if matched_kw:
            # Find the surrounding context
            idx = text_normalized.find(matched_kw.lower())
            start = max(0, idx - 50)
            end = min(len(text_normalized), idx + len(matched_kw) + 100)
            context = file_content[start:end].strip()

            items.append(GapItem(
                checklist_item_id=ci.id,
                title_vi=ci.title_vi,
                legal_basis=ci.legal_basis,
                status="dat",
                matched_section=context[:200],
            ))
        else:
            items.append(GapItem(
                checklist_item_id=ci.id,
                title_vi=ci.title_vi,
                legal_basis=ci.legal_basis,
                status="khong_dat",
                suggestion_vi=f"Bổ sung nội dung về: {ci.description_vi}",
            ))
            unmatched.append((len(items) - 1, ci))

    # Pass 2: LLM semantic matching for unmatched items
    if unmatched and settings.deepseek_api_key:
        try:
            await _llm_semantic_match(file_content, items, unmatched)
        except Exception:
            logger.warning("LLM semantic matching failed, keeping keyword results",
                           exc_info=True)

    dat = sum(1 for it in items if it.status == "dat")
    khong_dat = sum(1 for it in items if it.status == "khong_dat")
    khong_ro = sum(1 for it in items if it.status == "khong_ro")

    return GapReport(
        checklist_type=checklist_type,
        total_items=len(items),
        dat_count=dat,
        khong_dat_count=khong_dat,
        khong_ro_count=khong_ro,
        coverage_pct=round(dat / len(items) * 100, 1) if items else 0.0,
        items=items,
    )


async def _llm_semantic_match(
    doc_text: str,
    items: list[GapItem],
    unmatched: list[tuple[int, ChecklistItem]],
) -> None:
    """Use LLM to check if unmatched checklist items are semantically covered."""
    # Truncate document to avoid token limits
    doc_excerpt = doc_text[:6000]

    requirements = "\n".join(
        f"- {ci.id}: {ci.title_vi} ({ci.description_vi})"
        for _, ci in unmatched
    )

    prompt = f"""\
Dua tren noi dung van ban sau, kiem tra xem cac yeu cau duoi day co duoc de cap hay khong.

Van ban:
\"\"\"
{doc_excerpt}
\"\"\"

Yeu cau kiem tra:
{requirements}

Tra ve JSON array, moi phan tu co:
- "id": ma yeu cau
- "status": "dat" neu co de cap, "khong_ro" neu khong chac chan, "khong_dat" neu chac chan khong co
- "matched_section": doan van ban lien quan (neu co, toi da 100 ky tu)

Chi tra ve JSON, khong giai thich.
"""

    client = openai.AsyncOpenAI(
        base_url=settings.deepseek_base_url,
        api_key=settings.deepseek_api_key,
    )

    response = await client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=500,
    )

    raw = response.choices[0].message.content or "[]"
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw[3:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

    results = json.loads(raw)

    # Build lookup: ci.id -> index in items
    idx_map = {ci.id: idx for idx, ci in unmatched}

    for r in results:
        rid = r.get("id", "")
        if rid in idx_map:
            item_idx = idx_map[rid]
            new_status = r.get("status", "khong_dat")
            if new_status in ("dat", "khong_ro"):
                items[item_idx].status = new_status
                items[item_idx].matched_section = r.get("matched_section", "")[:200]
                if new_status == "dat":
                    items[item_idx].suggestion_vi = ""

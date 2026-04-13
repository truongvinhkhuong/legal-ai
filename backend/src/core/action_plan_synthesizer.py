"""Action Plan Synthesizer: combine multi-query results into structured action plans."""

from __future__ import annotations

import logging
from typing import Any, AsyncGenerator

import openai

from src.config.settings import settings

logger = logging.getLogger(__name__)

ACTION_PLAN_PROMPT_VI = """Ban la tro ly phap luat than thien. Nguoi dung dang gap mot tinh huong phuc tap lien quan nhieu van de phap ly. Dua tren thong tin tu nhieu nguon van ban phap luat ben duoi, hay tao mot KE HOACH HANH DONG cu the, de hieu, giup ho xu ly tinh huong.

QUY TAC:
1. CHI dua tren thong tin trong Context. Khong bua dat.
2. PHAI trich dan chinh xac: ten van ban, so hieu, Dieu/Khoan.
3. Dung ngon ngu binh dan, giai thich thuat ngu trong ngoac.
4. Moi buoc phai cu the, co the thuc hien duoc ngay.
5. Neu co deadline hoac thoi han, ghi ro.

FORMAT BAT BUOC:

**Tom tat tinh huong:**
[1-2 cau tom tat van de chinh]

**Ke hoach hanh dong:**

**Buoc 1: [Tieu de buoc]**
[Mo ta cu the can lam gi]
Can cu: [Dieu/Khoan, ten VB]

**Buoc 2: [Tieu de buoc]**
[Mo ta cu the]
Can cu: [Dieu/Khoan, ten VB]

... (tiep tuc cac buoc)

**Luu y quan trong:**
- [Nhung dieu can de phong, rui ro]

**Can cu phap ly:**
- [Danh sach tat ca Dieu/Khoan da trich dan]

{context_str}"""


def _build_multi_context_string(
    sub_results: list[dict[str, Any]],
) -> str:
    """Build context string from multiple sub-query results."""
    parts: list[str] = []
    source_idx = 0

    for sr in sub_results:
        sub_q = sr.get("sub_question", {})
        q_text = sub_q.get("question", "") if isinstance(sub_q, dict) else getattr(sub_q, "question", "")
        topic = sub_q.get("topic_category", "") if isinstance(sub_q, dict) else getattr(sub_q, "topic_category", "")

        parts.append(f"=== Van de: {q_text} (chu de: {topic}) ===")

        for chunk in sr.get("chunks", []):
            source_idx += 1
            doc_title = chunk.get("doc_title", "")
            doc_number = chunk.get("doc_number", "")
            hierarchy = chunk.get("hierarchy_path", "")
            status = chunk.get("status", "hieu_luc")
            text = chunk.get("original_text", "")

            status_label = {
                "hieu_luc": "Con hieu luc",
                "het_hieu_luc": "Het hieu luc",
                "da_sua_doi": "Da sua doi",
            }
            status_str = status_label.get(status, status)

            parts.append(
                f"--- Nguon {source_idx} ---\n"
                f"Van ban: {doc_title} ({doc_number})\n"
                f"Vi tri: {hierarchy}\n"
                f"Hieu luc: {status_str}\n\n"
                f"{text}\n"
                f"---"
            )

        parts.append("")

    return "\n\n".join(parts)


class ActionPlanSynthesizer:
    """Synthesizes sub-query results into a structured action plan."""

    async def synthesize(
        self,
        original_question: str,
        sub_results: list[dict[str, Any]],
        llm_client: openai.AsyncOpenAI,
    ) -> AsyncGenerator[str, None]:
        """Stream the synthesized action plan as tokens."""
        context_str = _build_multi_context_string(sub_results)
        system_msg = ACTION_PLAN_PROMPT_VI.format(context_str=context_str)

        try:
            stream = await llm_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": original_question},
                ],
                temperature=settings.llm_temperature,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as primary_err:
            logger.warning("Primary LLM failed in synthesizer: %s — trying fallback", primary_err)

            fallback_client = openai.AsyncOpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None
            if fallback_client:
                try:
                    stream = await fallback_client.chat.completions.create(
                        model=settings.fallback_model,
                        messages=[
                            {"role": "system", "content": system_msg},
                            {"role": "user", "content": original_question},
                        ],
                        temperature=settings.llm_temperature,
                        stream=True,
                    )
                    async for chunk in stream:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            yield delta.content
                    return
                except Exception as fallback_err:
                    logger.error("Fallback LLM also failed in synthesizer: %s", fallback_err)

            yield settings.static_fallback_message

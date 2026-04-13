"""Query Decomposer: classify questions as simple/complex and decompose into sub-questions."""

from __future__ import annotations

import json
import logging
from typing import Any

import openai
from pydantic import BaseModel

from src.config.settings import settings

logger = logging.getLogger(__name__)


class SubQuestion(BaseModel):
    """A single sub-question extracted from a complex question."""

    question: str
    topic_category: str  # "lao_dong", "thue", "bhxh", "hop_dong", "ky_luat", "khac"


class DecompositionResult(BaseModel):
    """Result of question decomposition."""

    is_complex: bool
    sub_questions: list[SubQuestion]
    original_question: str


DECOMPOSITION_PROMPT = """Ban la mot chuyen gia phan tich cau hoi phap ly. Nhiem vu cua ban la xac dinh cau hoi co phuc tap (lien quan nhieu van de phap ly khac nhau) hay don gian (chi 1 van de).

QUY TAC:
- Neu cau hoi chi hoi ve 1 van de duy nhat → tra ve is_complex = false
- Neu cau hoi lien quan toi 2+ van de phap ly khac nhau → tra ve is_complex = true va tach thanh cac cau hoi con
- Moi cau hoi con phai doc lap, co the tra loi rieng biet
- Toi da {max_sub} cau hoi con
- topic_category la mot trong: lao_dong, thue, bhxh, hop_dong, ky_luat, boi_thuong, thue_mat_bang, dich_vu, khac

VI DU:

Cau hoi: "Quy dinh nghi phep nam cua nhan vien chinh thuc?"
→ {{"is_complex": false, "sub_questions": [{{"question": "Quy dinh nghi phep nam cua nhan vien chinh thuc?", "topic_category": "lao_dong"}}]}}

Cau hoi: "NV lam hong may tinh 20 trieu roi bo viec 3 ngay, xu ly the nao?"
→ {{"is_complex": true, "sub_questions": [{{"question": "Quy dinh ve boi thuong thiet hai tai san do nguoi lao dong gay ra", "topic_category": "boi_thuong"}}, {{"question": "Quy dinh xu ly ky luat khi nguoi lao dong tu y bo viec khong phep", "topic_category": "ky_luat"}}]}}

Cau hoi: "Thue mon bai la bao nhieu va co can dong BHXH cho nhan vien khong?"
→ {{"is_complex": true, "sub_questions": [{{"question": "Muc thue mon bai cho doanh nghiep va ho kinh doanh", "topic_category": "thue"}}, {{"question": "Quy dinh ve dong BHXH bat buoc cho nguoi lao dong", "topic_category": "bhxh"}}]}}

Cau hoi: "Hop dong thue mat bang can nhung dieu khoan gi?"
→ {{"is_complex": false, "sub_questions": [{{"question": "Hop dong thue mat bang can nhung dieu khoan gi?", "topic_category": "thue_mat_bang"}}]}}

Tra ve JSON duy nhat, KHONG co text khac."""


class QueryDecomposer:
    """Classifies questions as simple/complex and decomposes complex ones."""

    def __init__(self, llm_client: openai.AsyncOpenAI) -> None:
        self._client = llm_client

    async def decompose(self, question: str) -> DecompositionResult:
        """Decompose a question into sub-questions if complex.

        Falls back to single-question path on any error.
        """
        if not settings.decomposition_enabled:
            return self._single_result(question)

        try:
            return await self._decompose_via_llm(question)
        except Exception as e:
            logger.warning("Decomposition failed, falling back to single query: %s", e)
            return self._single_result(question)

    async def _decompose_via_llm(self, question: str) -> DecompositionResult:
        prompt = DECOMPOSITION_PROMPT.format(max_sub=settings.decomposition_max_sub_questions)

        response = await self._client.chat.completions.create(
            model=settings.deepseek_model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ],
            temperature=0.0,
            max_tokens=400,
        )

        raw = response.choices[0].message.content or ""
        raw = raw.strip()

        # Extract JSON from response (handle markdown code blocks)
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        data = json.loads(raw)

        sub_questions = [
            SubQuestion(
                question=sq["question"],
                topic_category=sq.get("topic_category", "khac"),
            )
            for sq in data.get("sub_questions", [])
        ]

        if not sub_questions:
            return self._single_result(question)

        # Cap at max sub-questions
        sub_questions = sub_questions[: settings.decomposition_max_sub_questions]

        return DecompositionResult(
            is_complex=data.get("is_complex", False),
            sub_questions=sub_questions,
            original_question=question,
        )

    @staticmethod
    def _single_result(question: str) -> DecompositionResult:
        return DecompositionResult(
            is_complex=False,
            sub_questions=[SubQuestion(question=question, topic_category="khac")],
            original_question=question,
        )

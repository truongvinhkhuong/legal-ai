"""Contextual Enricher: LLM-generated legal context prefix per chunk."""

from __future__ import annotations

import asyncio
import logging

import openai

from src.api.models import ChunkMetadata
from src.config.settings import settings

logger = logging.getLogger(__name__)

LEGAL_CONTEXT_PROMPT = """<document>
Văn bản: {doc_title}
Số hiệu: {doc_number} | Loại: {doc_type}
Ban h��nh: {issuing_authority} | Hiệu lực: {effective_date}
{doc_overview}
</document>

<chunk>
Vị trí: {hierarchy_path}
{chunk_text}
</chunk>

Viết 1-2 câu mô tả ngữ cảnh:
- Tên văn bản và số hiệu
- Chương/Điều thuộc về
- Nội dung đoạn quy định về vấn đề gì
Chỉ trả về context, không giải thích."""


class ContextualEnricher:
    """Generate LLM context prefix for each chunk to improve embedding quality."""

    def __init__(self) -> None:
        self._client = openai.AsyncOpenAI(
            base_url=settings.deepseek_base_url,
            api_key=settings.deepseek_api_key,
        )
        self._semaphore = asyncio.Semaphore(settings.enrichment_concurrency)

    async def enrich(
        self,
        chunk: ChunkMetadata,
        doc_overview: str = "",
    ) -> str:
        """Return enriched text: '[Context: ...] \\n\\n {original_text}'.

        Falls back to original text on any error.
        """
        if settings.skip_enrichment:
            return chunk.original_text

        # Skip very short chunks
        if len(chunk.original_text.strip()) < 50:
            return chunk.original_text

        prompt = LEGAL_CONTEXT_PROMPT.format(
            doc_title=chunk.doc_title,
            doc_number=chunk.doc_number,
            doc_type=chunk.doc_type,
            issuing_authority=chunk.issuing_authority,
            effective_date=chunk.effective_date or "",
            doc_overview=doc_overview[:3000],
            hierarchy_path=chunk.hierarchy_path,
            chunk_text=chunk.original_text[:2000],
        )

        try:
            async with self._semaphore:
                response = await self._client.chat.completions.create(
                    model=settings.deepseek_model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=200,
                )
            context = response.choices[0].message.content or ""
            context = context.strip()
            if context:
                return f"[{context}]\n\n{chunk.original_text}"
        except Exception:
            logger.warning(
                "Enrichment failed for chunk %s, using original text",
                chunk.chunk_id,
                exc_info=True,
            )

        return chunk.original_text

    async def enrich_batch(
        self,
        chunks: list[ChunkMetadata],
        doc_overview: str = "",
    ) -> list[str]:
        """Enrich a batch of chunks concurrently."""
        tasks = [self.enrich(chunk, doc_overview) for chunk in chunks]
        return await asyncio.gather(*tasks)

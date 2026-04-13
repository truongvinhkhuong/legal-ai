"""Multilingual Reranker: BAAI/bge-reranker-v2-m3 cross-encoder."""

from __future__ import annotations

import logging
from typing import Any

from src.config.settings import settings

logger = logging.getLogger(__name__)

_cross_encoder = None


def _load_model():
    global _cross_encoder
    if _cross_encoder is not None:
        return _cross_encoder

    try:
        from sentence_transformers import CrossEncoder

        logger.info("Loading reranker model %s ...", settings.reranker_model)
        _cross_encoder = CrossEncoder(settings.reranker_model)
        logger.info("Reranker model loaded")
    except Exception:
        logger.warning("Failed to load reranker model — using no-op fallback", exc_info=True)
        _cross_encoder = None

    return _cross_encoder


class MultilingualReranker:
    """Rerank retrieved chunks using a cross-encoder model."""

    def rerank(
        self,
        query: str,
        chunks: list[dict[str, Any]],
        top_n: int | None = None,
    ) -> list[dict[str, Any]]:
        top_n = top_n or settings.rerank_top_n
        if not chunks:
            return []

        model = _load_model()
        if model is None:
            # No-op fallback: return top_n by original score
            logger.debug("Reranker unavailable — returning chunks by original score")
            return sorted(
                chunks, key=lambda c: c.get("_score", 0), reverse=True
            )[:top_n]

        # Build query-document pairs
        texts = [c.get("_node_content", c.get("original_text", "")) for c in chunks]
        pairs = [(query, t) for t in texts]

        scores = model.predict(pairs)

        # Attach rerank score
        for chunk, score in zip(chunks, scores):
            chunk["_rerank_score"] = float(score)

        ranked = sorted(chunks, key=lambda c: c.get("_rerank_score", 0), reverse=True)
        return ranked[:top_n]

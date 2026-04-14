"""Hierarchical Retriever: Qdrant collection management, embedding, vector search."""

from __future__ import annotations

import logging
import uuid
from typing import Any

import voyageai
from qdrant_client import AsyncQdrantClient, models

from src.api.models import ChunkMetadata, ChunkPayload
from src.config.settings import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Qdrant collection management
# ---------------------------------------------------------------------------

_qdrant_client: AsyncQdrantClient | None = None


async def get_qdrant_client() -> AsyncQdrantClient:
    global _qdrant_client
    if _qdrant_client is None:
        _qdrant_client = AsyncQdrantClient(
            url=settings.qdrant_url,
            api_key=settings.qdrant_api_key or None,
        )
    return _qdrant_client


async def close_qdrant_client() -> None:
    global _qdrant_client
    if _qdrant_client is not None:
        await _qdrant_client.close()
        _qdrant_client = None


async def ensure_collection() -> None:
    """Create collection + payload indexes if they don't already exist."""
    client = await get_qdrant_client()
    collection = settings.qdrant_collection

    collections = await client.get_collections()
    existing = [c.name for c in collections.collections]

    if collection not in existing:
        logger.info("Creating Qdrant collection '%s'", collection)
        await client.create_collection(
            collection_name=collection,
            vectors_config=models.VectorParams(
                size=settings.embedding_dim,
                distance=models.Distance.COSINE,
            ),
        )

        # Keyword indexes
        for field in [
            "tenant_id",
            "doc_number", "doc_type", "article_number", "status",
            "access_level", "allowed_departments", "effective_date",
            "amended_status", "scope",
        ]:
            await client.create_payload_index(
                collection_name=collection,
                field_name=field,
                field_schema=models.PayloadSchemaType.KEYWORD,
            )

        # Integer index
        await client.create_payload_index(
            collection_name=collection,
            field_name="legal_hierarchy",
            field_schema=models.PayloadSchemaType.INTEGER,
        )

        # Full-text index for BM25 keyword search
        await client.create_payload_index(
            collection_name=collection,
            field_name="_node_content",
            field_schema=models.TextIndexParams(
                type=models.TextIndexType.TEXT,
                tokenizer=models.TokenizerType.WORD,
                min_token_len=2,
                max_token_len=40,
            ),
        )

        logger.info("Collection '%s' created with all indexes", collection)
    else:
        logger.info("Collection '%s' already exists", collection)


# ---------------------------------------------------------------------------
# Embedding (Voyage AI)
# ---------------------------------------------------------------------------

_voyage_client: voyageai.Client | None = None


def _get_voyage_client() -> voyageai.Client:
    global _voyage_client
    if _voyage_client is None:
        _voyage_client = voyageai.Client(api_key=settings.voyage_api_key)
    return _voyage_client


def embed_texts(
    texts: list[str],
    input_type: str = "document",
) -> list[list[float]]:
    """Embed texts using Voyage AI. Handles batching (max 128 per call)."""
    client = _get_voyage_client()
    batch_size = 128
    all_embeddings: list[list[float]] = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        result = client.embed(
            batch,
            model=settings.embedding_model,
            input_type=input_type,
        )
        all_embeddings.extend(result.embeddings)

    return all_embeddings


# ---------------------------------------------------------------------------
# Indexing
# ---------------------------------------------------------------------------

async def index_chunks(
    chunks: list[ChunkMetadata],
    enriched_texts: list[str],
    segmented_texts: list[str],
    tenant_id: str = "",
) -> None:
    """Embed chunks and upsert into Qdrant."""
    if not chunks:
        return

    logger.info("Embedding %d chunks...", len(chunks))
    vectors = embed_texts(enriched_texts, input_type="document")

    # Build Qdrant points
    points: list[models.PointStruct] = []
    for chunk, vector, enriched, segmented in zip(
        chunks, vectors, enriched_texts, segmented_texts
    ):
        payload = ChunkPayload.from_chunk_metadata(
            chunk,
            enriched_text=enriched,
            segmented_text=segmented,
            tenant_id=tenant_id,
        )
        point = models.PointStruct(
            id=chunk.chunk_id,
            vector=vector,
            payload=payload.to_qdrant_payload(),
        )
        points.append(point)

    # Upsert in batches
    client = await get_qdrant_client()
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        await client.upsert(
            collection_name=settings.qdrant_collection,
            points=batch,
        )
    logger.info("Indexed %d chunks into Qdrant", len(points))


# ---------------------------------------------------------------------------
# Retriever class
# ---------------------------------------------------------------------------

class HierarchicalRetriever:
    """Vector search + parent-document expansion."""

    async def retrieve(
        self,
        query: str,
        top_k: int | None = None,
        query_filter: models.Filter | None = None,
    ) -> list[dict[str, Any]]:
        """Embed query and search Qdrant. Returns list of payload dicts with score."""
        top_k = top_k or settings.retrieval_top_k
        query_vector = embed_texts([query], input_type="query")[0]

        client = await get_qdrant_client()
        results = await client.search(
            collection_name=settings.qdrant_collection,
            query_vector=query_vector,
            limit=top_k,
            query_filter=query_filter,
            with_payload=True,
        )

        hits: list[dict[str, Any]] = []
        for point in results:
            payload = dict(point.payload) if point.payload else {}
            payload["_score"] = point.score
            payload["_point_id"] = str(point.id)
            hits.append(payload)

        return hits

    async def expand_parents(
        self, chunks: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """If a retrieved chunk has a parent_chunk_id, fetch the parent too."""
        client = await get_qdrant_client()
        seen_ids: set[str] = set()
        expanded: list[dict[str, Any]] = []

        for chunk in chunks:
            chunk_id = chunk.get("chunk_id", "")
            seen_ids.add(chunk_id)

        parent_ids_to_fetch: list[str] = []
        for chunk in chunks:
            parent_id = chunk.get("parent_chunk_id")
            if parent_id and parent_id not in seen_ids:
                parent_ids_to_fetch.append(parent_id)
                seen_ids.add(parent_id)

        # Fetch parents from Qdrant
        if parent_ids_to_fetch:
            parents = await client.retrieve(
                collection_name=settings.qdrant_collection,
                ids=parent_ids_to_fetch,
                with_payload=True,
            )
            for point in parents:
                payload = dict(point.payload) if point.payload else {}
                payload["_score"] = 0.0  # parent expansion, no direct score
                payload["_point_id"] = str(point.id)
                expanded.append(payload)

        expanded.extend(chunks)
        return expanded

    async def retrieve_by_reference(
        self,
        article_number: str,
        doc_number: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve chunks by article number (+ optional doc number)."""
        conditions: list[models.Condition] = [
            models.FieldCondition(
                key="article_number",
                match=models.MatchValue(value=article_number),
            ),
        ]
        if doc_number:
            conditions.append(
                models.FieldCondition(
                    key="doc_number",
                    match=models.MatchValue(value=doc_number),
                ),
            )

        client = await get_qdrant_client()
        results, _ = await client.scroll(
            collection_name=settings.qdrant_collection,
            scroll_filter=models.Filter(must=conditions),
            limit=10,
            with_payload=True,
        )

        hits: list[dict[str, Any]] = []
        for point in results:
            payload = dict(point.payload) if point.payload else {}
            payload["_point_id"] = str(point.id)
            hits.append(payload)

        return hits

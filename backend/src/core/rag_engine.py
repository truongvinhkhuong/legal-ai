"""RAG Engine: orchestrates ingestion pipeline and query pipeline."""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, AsyncGenerator

import openai
from qdrant_client import models

from src.api.models import (
    ChatRequest,
    ChunkMetadata,
    IngestResponse,
    LegalCitation,
    UserContext,
)
from src.config.settings import settings
from src.ingestion.acl_tagger import ACLTagger
from src.ingestion.contextual_enricher import ContextualEnricher
from src.ingestion.cross_ref_linker import CrossRefLinker
from src.ingestion.format_router import FormatRouter
from src.ingestion.hierarchical_chunker import HierarchicalChunker
from src.ingestion.legal_metadata_extractor import LegalMetadataExtractor
from src.ingestion.legal_structure_parser import LegalStructureParser
from src.ingestion.vietnamese_nlp import VietnameseNLPPreprocessor
from src.core.action_plan_synthesizer import ActionPlanSynthesizer
from src.core.query_decomposer import QueryDecomposer, SubQuestion
from src.reranker.multilingual_reranker import MultilingualReranker
from src.retrieval.hierarchical_retriever import (
    HierarchicalRetriever,
    index_chunks,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# System prompt (Phase 9 from blueprint)
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_VI = """Bạn là trợ lý pháp luật thân thiện, giúp chủ doanh nghiệp nhỏ và hộ kinh doanh hiểu và hành động đúng luật. Bạn giải thích mọi thứ bằng ngôn ngữ bình dân, dễ hiểu, như đang nói chuyện với một người bạn.

QUY TẮC CHÍNH XÁC (bắt buộc):
1. CHỈ trả lời dựa trên nội dung văn bản trong Context bên dưới. Không bịa đặt.
2. PHẢI trích dẫn chính xác: tên văn bản, số hiệu, Điều/Khoản/Mục/Điểm.
3. Khi trích dẫn, đặt nguyên văn trong ngoặc kép "...".
4. Nếu Context không đủ: nói rõ "Tôi chưa tìm thấy quy định cụ thể về vấn đề này trong các văn bản hiện có. Bạn nên hỏi trực tiếp luật sư hoặc cơ quan chức năng để được tư vấn chính xác."
5. Nếu VB đã hết hiệu lực: CẢNH BÁO rõ và ghi chú VB thay thế (nếu biết).
6. Nếu có mâu thuẫn giữa các nguồn: trình bày CẢ HAI quan điểm, ghi chú VB nào ưu tiên và lý do.

QUY TẮC NGÔN NGỮ & FORMAT:
7. Dùng ngôn ngữ thường ngày, tránh thuật ngữ pháp lý khó hiểu. Khi bắt buộc dùng thuật ngữ, giải thích ngay trong ngoặc: "đơn phương chấm dứt hợp đồng (tức là một bên tự ý ngưng hợp đồng mà không cần bên kia đồng ý)".
8. Đưa ví dụ thực tế để minh họa khi phù hợp: "Ví dụ: Nhân viên làm vỡ máy tính 15 triệu, bạn có thể yêu cầu bồi thường tối đa 3 tháng lương của họ."
9. Nếu VB tham chiếu sang Điều/VB khác mà Context có: trích dẫn luôn nội dung được tham chiếu.
10. Dùng Markdown: in đậm điều khoản quan trọng, danh sách cho nhiều mục.
11. LUÔN kết thúc câu trả lời bằng phần hành động cụ thể:

**Bạn cần làm:**
1. [Bước cụ thể đầu tiên]
2. [Bước cụ thể tiếp theo]
...

Phần "Bạn cần làm" là BẮT BUỘC trong mọi câu trả lời. Nếu không có hành động cụ thể, ghi: "**Bạn cần làm:** Liên hệ luật sư hoặc cơ quan chức năng để được tư vấn chi tiết hơn."

{warnings}

THÔNG TIN TỪ VĂN BẢN:
{context_str}"""


def _build_context_string(chunks: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for i, chunk in enumerate(chunks, 1):
        doc_title = chunk.get("doc_title", "")
        doc_number = chunk.get("doc_number", "")
        hierarchy = chunk.get("hierarchy_path", "")
        status = chunk.get("status", "hieu_luc")
        text = chunk.get("original_text", "")

        status_label = {"hieu_luc": "Còn hiệu lực", "het_hieu_luc": "Hết hiệu lực", "da_sua_doi": "Đã sửa đổi"}
        status_str = status_label.get(status, status)

        parts.append(
            f"--- Nguồn {i} ---\n"
            f"Văn bản: {doc_title} ({doc_number})\n"
            f"Vị trí: {hierarchy}\n"
            f"Hiệu lực: {status_str}\n\n"
            f"{text}\n"
            f"---"
        )
    return "\n\n".join(parts)


def _build_citations(chunks: list[dict[str, Any]]) -> list[LegalCitation]:
    citations: list[LegalCitation] = []
    seen: set[str] = set()

    for chunk in chunks:
        key = f"{chunk.get('doc_number', '')}|{chunk.get('article_number', '')}|{chunk.get('clause_number', '')}"
        if key in seen:
            continue
        seen.add(key)

        article_num = chunk.get("article_number")
        clause_num = chunk.get("clause_number")
        point_val = chunk.get("point")

        citations.append(LegalCitation(
            doc_title=chunk.get("doc_title", ""),
            doc_number=chunk.get("doc_number", ""),
            doc_type=chunk.get("doc_type", ""),
            article=f"Điều {article_num}" if article_num else None,
            clause=f"Khoản {clause_num}" if clause_num else None,
            point=f"Điểm {point_val}" if point_val else None,
            hierarchy_path=chunk.get("hierarchy_path", ""),
            exact_quote=chunk.get("original_text", "")[:500],
            issuing_authority=chunk.get("issuing_authority", ""),
            effective_date=chunk.get("effective_date"),
            validity_status=chunk.get("status", "hieu_luc"),
            amended_status=chunk.get("amended_status", "original"),
        ))

    return citations


def _build_acl_filter(user_context: UserContext | None) -> models.Filter | None:
    if user_context is None:
        return None

    conditions: list[models.Condition] = []

    # Mandatory tenant isolation — always filter by tenant_id
    if user_context.tenant_id:
        conditions.append(
            models.FieldCondition(
                key="tenant_id",
                match=models.MatchValue(value=user_context.tenant_id),
            )
        )

    if user_context.access_levels:
        conditions.append(
            models.FieldCondition(
                key="access_level",
                match=models.MatchAny(any=user_context.access_levels),
            )
        )

    if "all" not in user_context.departments:
        conditions.append(
            models.FieldCondition(
                key="allowed_departments",
                match=models.MatchAny(
                    any=user_context.departments + ["all"]
                ),
            )
        )

    return models.Filter(must=conditions) if conditions else None


def _deduplicate_chunks(sub_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge chunks from multiple sub-query results, keeping highest score per chunk_id."""
    seen: dict[str, dict[str, Any]] = {}
    for sr in sub_results:
        for chunk in sr.get("chunks", []):
            cid = chunk.get("chunk_id", id(chunk))
            existing = seen.get(cid)
            if existing is None:
                seen[cid] = chunk
            else:
                # Keep the one with higher rerank/retrieval score
                new_score = chunk.get("_rerank_score", chunk.get("_score", 0))
                old_score = existing.get("_rerank_score", existing.get("_score", 0))
                if new_score > old_score:
                    seen[cid] = chunk
    return list(seen.values())


# ---------------------------------------------------------------------------
# RAG Engine
# ---------------------------------------------------------------------------

class RAGEngine:
    """Central orchestrator for ingestion and query pipelines."""

    def __init__(self) -> None:
        # Ingestion components
        self.format_router = FormatRouter()
        self.nlp = VietnameseNLPPreprocessor()
        self.structure_parser = LegalStructureParser()
        self.chunker = HierarchicalChunker()
        self.metadata_extractor = LegalMetadataExtractor()
        self.cross_ref_linker = CrossRefLinker()
        self.acl_tagger = ACLTagger()
        self.contextual_enricher = ContextualEnricher()

        # Query components
        self.retriever = HierarchicalRetriever()
        self.reranker = MultilingualReranker()

        # LLM clients
        self._llm_client = openai.AsyncOpenAI(
            base_url=settings.deepseek_base_url,
            api_key=settings.deepseek_api_key,
        )
        self._fallback_client = openai.AsyncOpenAI(
            api_key=settings.openai_api_key,
        ) if settings.openai_api_key else None

        # Agentic query components
        self.decomposer = QueryDecomposer(self._llm_client)
        self.synthesizer = ActionPlanSynthesizer()

    # ------------------------------------------------------------------
    # INGESTION PIPELINE
    # ------------------------------------------------------------------
    async def ingest(
        self,
        file_path: str,
        override_metadata: dict | None = None,
    ) -> IngestResponse:
        warnings: list[str] = []

        # 1. Parse file
        parsed = await self.format_router.parse(file_path)
        if parsed.format_hints.get("likely_scanned"):
            warnings.append("PDF appears scanned — text extraction may be incomplete")

        # 2. Normalize Vietnamese text
        normalized_text = self.nlp.normalize(parsed.raw_text)

        # 3. Parse structure
        tree = self.structure_parser.parse(normalized_text)
        logger.info("Structure detected: %s", tree.structure_type.value)

        # 4. Extract document metadata
        doc_meta = self.metadata_extractor.extract_document_metadata(
            header=tree.header,
            file_path=file_path,
            override_metadata=override_metadata,
        )

        # 5. ACL tagging
        access_level, allowed_departments = self.acl_tagger.tag(doc_meta)
        doc_meta.access_level = access_level
        doc_meta.allowed_departments = allowed_departments

        # 6. Chunk
        chunks = self.chunker.chunk(tree, doc_meta)
        if not chunks:
            return IngestResponse(
                success=False,
                doc_id=doc_meta.doc_id,
                warnings=["No chunks produced from document"],
            )

        # 7. Enrich chunk metadata + extract cross-references
        articles_found = 0
        cross_refs_total = 0
        for chunk in chunks:
            self.metadata_extractor.enrich_chunk_metadata(chunk, doc_meta)
            refs = self.cross_ref_linker.extract_reference_strings(chunk.original_text)
            chunk.cross_references = refs
            cross_refs_total += len(refs)
            if chunk.article_number:
                articles_found += 1

        # 8. Contextual enrichment
        doc_overview = normalized_text[:3000]
        enriched_texts = await self.contextual_enricher.enrich_batch(chunks, doc_overview)

        # 9. Word segmentation for BM25
        segmented_texts = [self.nlp.segment_words(c.original_text) for c in chunks]

        # 10. Index into Qdrant
        tenant_id = override_metadata.get("tenant_id", "")
        await index_chunks(chunks, enriched_texts, segmented_texts, tenant_id=tenant_id)

        return IngestResponse(
            success=True,
            doc_id=doc_meta.doc_id,
            chunks_created=len(chunks),
            structure_detected=tree.structure_type.value,
            articles_found=articles_found,
            cross_references_found=cross_refs_total,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # QUERY PIPELINE
    # ------------------------------------------------------------------
    async def query(
        self,
        request: ChatRequest,
    ) -> AsyncGenerator[dict, None]:
        """Stream SSE events: {"type": "chunk"/"done"/"error", "data": ...}"""
        conversation_id = request.conversation_id or str(uuid.uuid4())

        try:
            query_text = request.question
            acl_filter = _build_acl_filter(request.user_context)

            # Decompose: classify simple vs complex
            decomposition = await self.decomposer.decompose(query_text)

            if decomposition.is_complex and len(decomposition.sub_questions) > 1:
                # --- COMPLEX PATH: parallel retrieval + action plan ---
                async for event in self._query_complex(
                    query_text, decomposition.sub_questions, acl_filter, conversation_id
                ):
                    yield event
            else:
                # --- SIMPLE PATH: single retrieval + standard answer ---
                async for event in self._query_simple(
                    query_text, acl_filter, conversation_id
                ):
                    yield event

        except Exception as e:
            logger.error("Query pipeline error: %s", e, exc_info=True)
            yield {"type": "error", "data": f"Loi he thong: {e}"}

    async def _query_simple(
        self,
        query_text: str,
        acl_filter: models.Filter | None,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Standard single-query path."""
        raw_results = await self.retriever.retrieve(
            query_text,
            top_k=settings.retrieval_top_k,
            query_filter=acl_filter,
        )

        if not raw_results:
            yield {"type": "chunk", "data": settings.static_fallback_message}
            yield {"type": "done", "data": self._empty_done(conversation_id)}
            return

        expanded = await self.retriever.expand_parents(raw_results)
        reranked = self.reranker.rerank(query_text, expanded, top_n=settings.rerank_top_n)

        context_str = _build_context_string(reranked)
        system_msg = SYSTEM_PROMPT_VI.format(warnings="", context_str=context_str)

        async for token in self._stream_llm(system_msg, query_text):
            yield {"type": "chunk", "data": token}

        citations = _build_citations(reranked)
        yield {
            "type": "done",
            "data": {
                "confidence": min(reranked[0].get("_rerank_score", reranked[0].get("_score", 0)) * 100, 100) if reranked else 0,
                "groundedness": 0.0,
                "sources_count": len(reranked),
                "citations": [c.model_dump() for c in citations],
                "has_expired_sources": any(c.get("status") == "het_hieu_luc" for c in reranked),
                "has_conflicts": False,
                "validity_warnings": [],
                "conversation_id": conversation_id,
                "is_action_plan": False,
            },
        }

    async def _query_complex(
        self,
        original_question: str,
        sub_questions: list[SubQuestion],
        acl_filter: models.Filter | None,
        conversation_id: str,
    ) -> AsyncGenerator[dict, None]:
        """Complex path: parallel retrieval per sub-question + action plan synthesis."""
        logger.info(
            "Complex query detected: %d sub-questions", len(sub_questions)
        )

        # Parallel retrieval for each sub-question
        sub_results = await asyncio.gather(
            *[self._retrieve_sub(sq, acl_filter) for sq in sub_questions]
        )

        # Check if any results found
        all_chunks = _deduplicate_chunks(sub_results)
        if not all_chunks:
            yield {"type": "chunk", "data": settings.static_fallback_message}
            yield {"type": "done", "data": self._empty_done(conversation_id)}
            return

        # Stream synthesized action plan
        async for token in self.synthesizer.synthesize(
            original_question, sub_results, self._llm_client
        ):
            yield {"type": "chunk", "data": token}

        # Build citations from combined chunks
        citations = _build_citations(all_chunks)
        yield {
            "type": "done",
            "data": {
                "confidence": min(all_chunks[0].get("_rerank_score", all_chunks[0].get("_score", 0)) * 100, 100) if all_chunks else 0,
                "groundedness": 0.0,
                "sources_count": len(all_chunks),
                "citations": [c.model_dump() for c in citations],
                "has_expired_sources": any(c.get("status") == "het_hieu_luc" for c in all_chunks),
                "has_conflicts": False,
                "validity_warnings": [],
                "conversation_id": conversation_id,
                "is_action_plan": True,
            },
        }

    async def _retrieve_sub(
        self, sub_question: SubQuestion, acl_filter: models.Filter | None
    ) -> dict[str, Any]:
        """Retrieve, expand parents, and rerank for a single sub-question."""
        raw = await self.retriever.retrieve(
            sub_question.question,
            top_k=settings.retrieval_top_k,
            query_filter=acl_filter,
        )
        expanded = await self.retriever.expand_parents(raw)
        reranked = self.reranker.rerank(
            sub_question.question, expanded, top_n=settings.rerank_top_n
        )
        return {
            "sub_question": {
                "question": sub_question.question,
                "topic_category": sub_question.topic_category,
            },
            "chunks": reranked,
        }

    @staticmethod
    def _empty_done(conversation_id: str) -> dict:
        return {
            "confidence": 0,
            "groundedness": 0,
            "sources_count": 0,
            "citations": [],
            "has_expired_sources": False,
            "has_conflicts": False,
            "validity_warnings": [],
            "conversation_id": conversation_id,
            "is_action_plan": False,
        }

    # ------------------------------------------------------------------
    # LLM streaming
    # ------------------------------------------------------------------
    async def _stream_llm(
        self, system_msg: str, user_msg: str
    ) -> AsyncGenerator[str, None]:
        messages = [
            {"role": "system", "content": system_msg},
            {"role": "user", "content": user_msg},
        ]

        try:
            stream = await self._llm_client.chat.completions.create(
                model=settings.deepseek_model,
                messages=messages,
                temperature=settings.llm_temperature,
                stream=True,
            )
            async for chunk in stream:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta and delta.content:
                    yield delta.content

        except Exception as primary_err:
            logger.warning("Primary LLM failed: %s — trying fallback", primary_err)

            if self._fallback_client:
                try:
                    stream = await self._fallback_client.chat.completions.create(
                        model=settings.fallback_model,
                        messages=messages,
                        temperature=settings.llm_temperature,
                        stream=True,
                    )
                    async for chunk in stream:
                        delta = chunk.choices[0].delta if chunk.choices else None
                        if delta and delta.content:
                            yield delta.content
                    return
                except Exception as fallback_err:
                    logger.error("Fallback LLM also failed: %s", fallback_err)

            yield settings.static_fallback_message

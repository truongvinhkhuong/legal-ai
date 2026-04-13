"""Hierarchical Chunker: article-based chunking with parent-child relationships."""

from __future__ import annotations

import uuid

from src.api.models import (
    ChunkMetadata,
    ChunkType,
    DocumentMetadata,
    DocumentNode,
    DocumentTree,
    StructureType,
)
from src.config.settings import settings

# Approximate tokens: ~1 token per 3.5 Vietnamese characters
CHARS_PER_TOKEN = 3.5


def _estimate_tokens(text: str) -> int:
    return int(len(text) / CHARS_PER_TOKEN)


class HierarchicalChunker:
    """Chunk a parsed document tree into ChunkMetadata list."""

    def chunk(
        self,
        tree: DocumentTree,
        doc_metadata: DocumentMetadata,
    ) -> list[ChunkMetadata]:
        if tree.structure_type == StructureType.unstructured:
            return self._chunk_unstructured(tree, doc_metadata)
        return self._chunk_structured(tree, doc_metadata)

    # ------------------------------------------------------------------
    # Structured: walk tree, chunk at Điều level
    # ------------------------------------------------------------------
    def _chunk_structured(
        self, tree: DocumentTree, doc_meta: DocumentMetadata
    ) -> list[ChunkMetadata]:
        chunks: list[ChunkMetadata] = []
        articles_found = 0

        for node in tree.body:
            self._walk_node(
                node=node,
                doc_meta=doc_meta,
                chunks=chunks,
                path_parts=[],
                current_chapter=None,
                current_section=None,
            )

        # Count articles
        for c in chunks:
            if c.chunk_type == ChunkType.article.value:
                articles_found += 1

        return chunks

    def _walk_node(
        self,
        node: DocumentNode,
        doc_meta: DocumentMetadata,
        chunks: list[ChunkMetadata],
        path_parts: list[str],
        current_chapter: str | None,
        current_section: str | None,
    ) -> None:
        # Build path label for this node
        label = self._node_label(node)

        if node.type == "chuong":
            current_chapter = label
        elif node.type == "muc":
            current_section = label
        elif node.type == "phan":
            pass  # phần tracked in path_parts

        new_path = [*path_parts, label] if label else path_parts

        if node.type == "dieu":
            self._chunk_article(
                node=node,
                doc_meta=doc_meta,
                chunks=chunks,
                path_parts=new_path,
                chapter=current_chapter,
                section=current_section,
            )
            return

        # Recurse into children (phần, chương, mục)
        for child in node.children:
            self._walk_node(
                node=child,
                doc_meta=doc_meta,
                chunks=chunks,
                path_parts=new_path,
                current_chapter=current_chapter,
                current_section=current_section,
            )

    def _chunk_article(
        self,
        node: DocumentNode,
        doc_meta: DocumentMetadata,
        chunks: list[ChunkMetadata],
        path_parts: list[str],
        chapter: str | None,
        section: str | None,
    ) -> None:
        # Collect full text of the article (including all khoản/điểm)
        full_text = self._collect_full_text(node)
        article_label = self._node_label(node)
        article_path = " > ".join(path_parts)
        estimated_tokens = _estimate_tokens(full_text)

        if estimated_tokens <= settings.chunk_max_tokens or not node.children:
            # Single chunk for the whole article
            chunk = self._make_chunk(
                doc_meta=doc_meta,
                text=full_text,
                chunk_type=ChunkType.article,
                hierarchy_path=article_path,
                chapter=chapter,
                section=section,
                article_number=node.number,
                article_title=node.title,
            )
            chunks.append(chunk)
        else:
            # Parent chunk (full article text) + child chunks per khoản
            parent_chunk = self._make_chunk(
                doc_meta=doc_meta,
                text=full_text,
                chunk_type=ChunkType.article,
                hierarchy_path=article_path,
                chapter=chapter,
                section=section,
                article_number=node.number,
                article_title=node.title,
            )
            chunks.append(parent_chunk)

            # Chunk per khoản
            for child in node.children:
                if child.type == "khoan":
                    khoan_text = self._collect_full_text(child)
                    # Prefix with article context for standalone readability
                    context_prefix = f"{article_label}."
                    if node.title:
                        context_prefix += f" {node.title}"
                    prefixed_text = f"{context_prefix}\n{child.type.capitalize()} {child.number}. {khoan_text}"

                    khoan_path = f"{article_path} > Khoản {child.number}"
                    child_chunk = self._make_chunk(
                        doc_meta=doc_meta,
                        text=prefixed_text,
                        chunk_type=ChunkType.clause,
                        hierarchy_path=khoan_path,
                        chapter=chapter,
                        section=section,
                        article_number=node.number,
                        article_title=node.title,
                        clause_number=child.number,
                        parent_chunk_id=parent_chunk.chunk_id,
                    )
                    chunks.append(child_chunk)

                    # If khoản has điểm children, chunk them too if khoản is long
                    for diem in child.children:
                        if diem.type == "diem":
                            diem_path = f"{khoan_path} > Điểm {diem.number}"
                            # Điểm usually short — include in parent khoản, don't split
                            # Only create separate chunk if explicitly needed

    # ------------------------------------------------------------------
    # Unstructured fallback: sentence-based splitting
    # ------------------------------------------------------------------
    def _chunk_unstructured(
        self, tree: DocumentTree, doc_meta: DocumentMetadata
    ) -> list[ChunkMetadata]:
        full_text = ""
        for node in tree.body:
            full_text += node.text + "\n"
        full_text = full_text.strip()

        if not full_text:
            return []

        chunk_size = settings.sentence_chunk_size
        overlap = settings.chunk_overlap_tokens
        chunk_chars = int(chunk_size * CHARS_PER_TOKEN)
        overlap_chars = int(overlap * CHARS_PER_TOKEN)

        chunks: list[ChunkMetadata] = []
        sentences = self._split_sentences(full_text)
        current_chars = 0
        current_sentences: list[str] = []

        for sent in sentences:
            sent_len = len(sent)
            if current_chars + sent_len > chunk_chars and current_sentences:
                # Flush current chunk
                chunk_text = " ".join(current_sentences)
                chunk = self._make_chunk(
                    doc_meta=doc_meta,
                    text=chunk_text,
                    chunk_type=ChunkType.paragraph,
                    hierarchy_path=doc_meta.doc_title,
                )
                chunks.append(chunk)

                # Overlap: keep last few sentences
                overlap_sents: list[str] = []
                overlap_len = 0
                for s in reversed(current_sentences):
                    if overlap_len + len(s) > overlap_chars:
                        break
                    overlap_sents.insert(0, s)
                    overlap_len += len(s)
                current_sentences = overlap_sents
                current_chars = overlap_len

            current_sentences.append(sent)
            current_chars += sent_len

        # Final chunk
        if current_sentences:
            chunk_text = " ".join(current_sentences)
            chunk = self._make_chunk(
                doc_meta=doc_meta,
                text=chunk_text,
                chunk_type=ChunkType.paragraph,
                hierarchy_path=doc_meta.doc_title,
            )
            chunks.append(chunk)

        return chunks

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _collect_full_text(node: DocumentNode) -> str:
        """Recursively collect all text from a node and its children."""
        parts: list[str] = []
        if node.text:
            parts.append(node.text)
        for child in node.children:
            prefix = ""
            if child.type == "khoan" and child.number:
                prefix = f"{child.number}. "
            elif child.type == "diem" and child.number:
                prefix = f"{child.number}) "
            child_text = HierarchicalChunker._collect_full_text(child)
            if child_text:
                parts.append(f"{prefix}{child_text}")
        return "\n".join(parts)

    @staticmethod
    def _node_label(node: DocumentNode) -> str:
        labels = {
            "phan": "Phần",
            "chuong": "Chương",
            "muc": "Mục",
            "dieu": "Điều",
            "khoan": "Khoản",
            "diem": "Điểm",
        }
        prefix = labels.get(node.type, "")
        if prefix and node.number:
            return f"{prefix} {node.number}"
        return ""

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Simple Vietnamese sentence splitter."""
        # Split on period/question/exclamation followed by space/newline
        import re
        raw = re.split(r"(?<=[.?!])\s+", text)
        return [s.strip() for s in raw if s.strip()]

    @staticmethod
    def _make_chunk(
        doc_meta: DocumentMetadata,
        text: str,
        chunk_type: ChunkType,
        hierarchy_path: str,
        chapter: str | None = None,
        section: str | None = None,
        article_number: str | None = None,
        article_title: str | None = None,
        clause_number: str | None = None,
        point: str | None = None,
        parent_chunk_id: str | None = None,
    ) -> ChunkMetadata:
        return ChunkMetadata(
            chunk_id=str(uuid.uuid4()),
            doc_id=doc_meta.doc_id,
            parent_chunk_id=parent_chunk_id,
            hierarchy_path=hierarchy_path,
            chapter=chapter,
            section=section,
            article_number=article_number,
            article_title=article_title,
            clause_number=clause_number,
            point=point,
            chunk_type=chunk_type.value,
            original_text=text,
            # Document-level fields copied down
            doc_number=doc_meta.doc_number,
            doc_title=doc_meta.doc_title,
            doc_type=doc_meta.doc_type,
            effective_date=(
                doc_meta.effective_date.isoformat()
                if doc_meta.effective_date
                else None
            ),
            status=doc_meta.status,
            access_level=doc_meta.access_level,
            allowed_departments=doc_meta.allowed_departments,
            legal_hierarchy=doc_meta.legal_hierarchy,
            issuing_authority=doc_meta.issuing_authority,
            scope=doc_meta.scope,
        )

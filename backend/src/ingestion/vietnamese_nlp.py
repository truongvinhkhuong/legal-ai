"""Vietnamese NLP: Unicode normalization, OCR error correction, word segmentation."""

from __future__ import annotations

import re
import unicodedata


class VietnameseNLPPreprocessor:
    """Normalize and segment Vietnamese legal text."""

    def __init__(self) -> None:
        from underthesea import word_tokenize
        self._word_tokenize = word_tokenize

    # ------------------------------------------------------------------
    # normalize — run BEFORE structure parser
    # ------------------------------------------------------------------
    def normalize(self, text: str) -> str:
        """Unicode NFC normalization + fix common OCR artifacts."""
        text = unicodedata.normalize("NFC", text)

        # Fix common OCR errors for Vietnamese legal text
        text = text.replace("Điêu", "Điều")
        text = text.replace("Khoàn", "Khoản")
        text = text.replace("Chuơng", "Chương")
        text = text.replace("Đièu", "Điều")

        # Fix spaced-out characters from OCR
        text = re.sub(r"Đ\s*i\s*ề\s*u", "Điều", text)
        text = re.sub(r"K\s*h\s*o\s*ả\s*n", "Khoản", text)
        text = re.sub(r"C\s*h\s*ư\s*ơ\s*n\s*g", "Chương", text)

        # Normalize common Vietnamese punctuation
        text = text.replace("\u00a0", " ")  # non-breaking space
        text = text.replace("\u200b", "")  # zero-width space
        text = text.replace("\ufeff", "")  # BOM

        # Collapse multiple whitespace but preserve paragraph breaks (double newline)
        text = re.sub(r"[^\S\n]+", " ", text)  # collapse spaces/tabs within lines
        text = re.sub(r"\n{3,}", "\n\n", text)  # cap consecutive newlines at 2
        text = text.strip()

        return text

    # ------------------------------------------------------------------
    # segment_words — run AFTER chunking, for BM25 storage
    # ------------------------------------------------------------------
    def segment_words(self, text: str) -> str:
        """Vietnamese word segmentation for BM25 indexing.

        Compound words are joined with underscores:
        "nghỉ phép năm" → "nghỉ_phép năm"
        """
        return self._word_tokenize(text, format="text")

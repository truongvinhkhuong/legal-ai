"""Download diverse sample legal documents from HuggingFace dataset.

Dataset: th1nhng0/vietnamese-legal-documents
Output: data/samples/<id>.html + data/samples/manifest.json

Selection criteria:
- Documents issued after 2010 (modern structure, longer content)
- HTML content > 15KB (substantial documents with multiple articles)
- Diverse doc types: Luat, ND, TT, QD, NQ, CV, TB

Usage:
    python scripts/download_samples.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

# Target: pick documents across different doc types for diverse testing
TARGET_TYPES = {
    "Luật": 4,
    "Bộ luật": 2,
    "Nghị định": 5,
    "Thông tư": 4,
    "Thông tư liên tịch": 2,
    "Quyết định": 4,
    "Nghị quyết": 3,
    "Chỉ thị": 2,
    "Pháp lệnh": 1,
}
# Total: ~27 documents

MIN_YEAR = 2010           # Only docs issued from 2010 onwards
MIN_CONTENT_SIZE = 15000  # Minimum HTML content size in chars

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def _parse_year(date_str: str | None) -> int | None:
    """Extract year from DD/MM/YYYY date string."""
    if not date_str or "/" not in date_str:
        return None
    try:
        parts = date_str.strip().split("/")
        if len(parts) == 3:
            return int(parts[2])
    except (ValueError, IndexError):
        pass
    return None


def main() -> None:
    from huggingface_hub import hf_hub_download
    import pyarrow.parquet as pq

    # --- Step 1: Load content to build size index ---
    print("Downloading content parquet...")
    content_path = hf_hub_download(
        repo_id="th1nhng0/vietnamese-legal-documents",
        filename="data/content.parquet",
        repo_type="dataset",
    )

    print("Reading content parquet and building size index...")
    content_table = pq.read_table(content_path)
    ids_col = content_table.column("id")
    html_col = content_table.column("content_html")

    # Build id -> (html_content, size) for docs above minimum size
    content_index: dict[str, int] = {}
    content_store: dict[str, str] = {}
    for i in range(len(content_table)):
        doc_id = str(ids_col[i].as_py())
        html = str(html_col[i].as_py())
        size = len(html)
        if size >= MIN_CONTENT_SIZE:
            content_index[doc_id] = size
            content_store[doc_id] = html

    print(f"  {len(content_index):,} documents with content >= {MIN_CONTENT_SIZE:,} chars")

    # Free the large table
    del content_table, ids_col, html_col

    # --- Step 2: Load metadata and select candidates ---
    print("\nDownloading metadata parquet...")
    meta_path = hf_hub_download(
        repo_id="th1nhng0/vietnamese-legal-documents",
        filename="data/metadata.parquet",
        repo_type="dataset",
    )
    print("Reading metadata and selecting candidates...")
    meta_table = pq.read_table(meta_path)

    # Collect all eligible candidates per type, then pick best
    candidates: dict[str, list[tuple[dict, int]]] = {t: [] for t in TARGET_TYPES}

    for i in range(len(meta_table)):
        row = {col: meta_table.column(col)[i].as_py() for col in meta_table.column_names}
        loai = row.get("loai_van_ban", "") or ""

        if loai not in candidates:
            continue
        if not row.get("so_ky_hieu") or not row.get("title"):
            continue

        # Year filter
        year = _parse_year(row.get("ngay_ban_hanh"))
        if year is None or year < MIN_YEAR:
            continue

        # Content size filter
        doc_id = str(row["id"])
        content_size = content_index.get(doc_id, 0)
        if content_size < MIN_CONTENT_SIZE:
            continue

        candidates[loai].append((row, content_size))

    # Sort each type by content size descending, pick top N
    selected = []
    for loai, items in candidates.items():
        target = TARGET_TYPES[loai]
        # Sort by size descending, pick largest (but cap at 500KB to avoid extreme docs)
        items.sort(key=lambda x: x[1], reverse=True)
        # Filter out extremely large docs (>500KB) that would be slow to process
        filtered = [(r, s) for r, s in items if s <= 500_000]
        if not filtered:
            filtered = items  # fallback if all are huge
        picked = filtered[:target]
        for row, size in picked:
            selected.append(row)
        print(f"  {loai}: {len(picked)}/{len(items)} available (picked largest <= 500KB)")

    if not selected:
        print("ERROR: No documents found!")
        sys.exit(1)

    print(f"\nTotal selected: {len(selected)} documents")

    # --- Step 3: Save HTML files + manifest ---
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Clean old files
    for old in OUTPUT_DIR.glob("*.html"):
        old.unlink()

    # Map loai_van_ban -> doc_type enum
    type_map = {
        "Luật": "luat",
        "Bộ luật": "luat",
        "Nghị định": "nghi_dinh",
        "Thông tư": "thong_tu",
        "Thông tư liên tịch": "thong_tu",
        "Quyết định": "quyet_dinh",
        "Nghị quyết": "nghi_quyet",
        "Chỉ thị": "quyet_dinh",
        "Pháp lệnh": "luat",
        "Thông báo": "thong_bao",
        "Công văn": "cong_van",
    }

    manifest = []
    saved = 0

    for record in selected:
        doc_id = str(record["id"])
        html = content_store.get(doc_id)
        if not html:
            print(f"  SKIP id={doc_id} (no content in store)")
            continue

        # Map tinh_trang_hieu_luc -> status
        status_raw = record.get("tinh_trang_hieu_luc", "") or ""
        if "hết hiệu lực" in status_raw.lower():
            status = "het_hieu_luc"
        elif "sửa đổi" in status_raw.lower() or "bổ sung" in status_raw.lower():
            status = "da_sua_doi"
        else:
            status = "hieu_luc"

        filename = f"{doc_id}.html"
        filepath = OUTPUT_DIR / filename
        filepath.write_text(html, encoding="utf-8")

        entry = {
            "file": filename,
            "dataset_id": doc_id,
            "doc_number": record.get("so_ky_hieu", ""),
            "doc_title": record.get("title", ""),
            "doc_type": type_map.get(record.get("loai_van_ban", ""), "khac"),
            "issuing_authority": record.get("co_quan_ban_hanh", ""),
            "issue_date": record.get("ngay_ban_hanh", ""),
            "effective_date": record.get("ngay_co_hieu_luc", ""),
            "expiry_date": record.get("ngay_het_hieu_luc"),
            "status": status,
            "loai_van_ban_original": record.get("loai_van_ban", ""),
            "tinh_trang_original": record.get("tinh_trang_hieu_luc", ""),
            "linh_vuc": record.get("linh_vuc"),
            "nguoi_ky": record.get("nguoi_ky"),
            "content_size_kb": round(len(html) / 1024, 1),
        }
        manifest.append(entry)
        saved += 1

    # Save manifest
    manifest_path = OUTPUT_DIR / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # Summary
    total_kb = sum(e["content_size_kb"] for e in manifest)
    print(f"\nDone! Saved {saved} HTML files + manifest.json to {OUTPUT_DIR}")
    print(f"Total content: {total_kb:,.1f} KB")
    print(f"Manifest: {manifest_path}")


if __name__ == "__main__":
    main()

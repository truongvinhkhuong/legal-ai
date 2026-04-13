"""Batch ingest sample documents from data/samples/ into the RAG system.

Reads manifest.json and calls the /api/ingest endpoint for each document.

Usage:
    # Start server first: uvicorn src.main:app --port 8000
    python scripts/batch_ingest.py [--base-url http://localhost:8000]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import httpx

SAMPLES_DIR = Path(__file__).resolve().parent.parent / "data" / "samples"


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch ingest sample documents")
    parser.add_argument("--base-url", default="http://localhost:8000")
    args = parser.parse_args()

    manifest_path = SAMPLES_DIR / "manifest.json"
    if not manifest_path.exists():
        print(f"ERROR: {manifest_path} not found. Run download_samples.py first.")
        sys.exit(1)

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    print(f"Found {len(manifest)} documents in manifest\n")

    # Check server health
    try:
        resp = httpx.get(f"{args.base_url}/api/health", timeout=10)
        health = resp.json()
        print(f"Server health: {health}\n")
        if health.get("qdrant") != "connected":
            print("WARNING: Qdrant not connected. Ingestion will fail.")
    except httpx.ConnectError:
        print(f"ERROR: Cannot connect to {args.base_url}. Is the server running?")
        sys.exit(1)

    results = {"success": 0, "failed": 0, "total_chunks": 0}

    for i, entry in enumerate(manifest, 1):
        filepath = SAMPLES_DIR / entry["file"]
        if not filepath.exists():
            print(f"[{i}/{len(manifest)}] SKIP {entry['file']} (file not found)")
            results["failed"] += 1
            continue

        # Build metadata override from manifest
        metadata = {
            "doc_number": entry.get("doc_number", ""),
            "doc_title": entry.get("doc_title", ""),
            "doc_type": entry.get("doc_type", "khac"),
            "issuing_authority": entry.get("issuing_authority", ""),
            "status": entry.get("status", "hieu_luc"),
        }

        # Parse dates (DD/MM/YYYY -> YYYY-MM-DD)
        for date_field in ["effective_date", "issue_date"]:
            raw = entry.get(date_field, "")
            if raw and "/" in raw:
                try:
                    parts = raw.split("/")
                    if len(parts) == 3:
                        metadata[date_field] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                except (IndexError, ValueError):
                    pass

        print(f"[{i}/{len(manifest)}] Ingesting {entry['file']} ({entry['doc_type']}: {entry['doc_number']})...")

        try:
            with open(filepath, "rb") as f:
                resp = httpx.post(
                    f"{args.base_url}/api/ingest",
                    files={"file": (entry["file"], f, "text/html")},
                    data={"metadata": json.dumps(metadata, ensure_ascii=False)},
                    timeout=120,
                )

            if resp.status_code == 200:
                result = resp.json()
                if result.get("success"):
                    chunks = result.get("chunks_created", 0)
                    structure = result.get("structure_detected", "?")
                    articles = result.get("articles_found", 0)
                    refs = result.get("cross_references_found", 0)
                    warnings = result.get("warnings", [])

                    results["success"] += 1
                    results["total_chunks"] += chunks

                    status_line = f"  -> {chunks} chunks, structure={structure}, articles={articles}, refs={refs}"
                    if warnings:
                        status_line += f", warnings={warnings}"
                    print(status_line)
                else:
                    print(f"  -> FAILED: {result.get('warnings', [])}")
                    results["failed"] += 1
            else:
                print(f"  -> HTTP {resp.status_code}: {resp.text[:200]}")
                results["failed"] += 1

        except Exception as e:
            print(f"  -> ERROR: {e}")
            results["failed"] += 1

    print(f"\n{'='*50}")
    print(f"Results: {results['success']}/{len(manifest)} succeeded, {results['failed']} failed")
    print(f"Total chunks created: {results['total_chunks']}")


if __name__ == "__main__":
    main()

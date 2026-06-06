#!/usr/bin/env python3
"""Batch extract experimental data from a directory of PDF papers.

Pipeline: PDF -> Markdown -> LLM Extraction -> CSV/JSON output.
"""

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from pdf_to_md import pdf_to_markdown
from extract_data import extract_from_markdown, DEFAULT_FIELDS


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dict into single-level keys."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        elif isinstance(v, list):
            items.append((new_key, json.dumps(v, ensure_ascii=False)))
        else:
            items.append((new_key, v))
    return dict(items)


def load_cache(cache_path: Path) -> set:
    """Load set of already-processed filenames."""
    if cache_path.exists():
        return set(cache_path.read_text().strip().split('\n'))
    return set()


def save_cache(cache_path: Path, processed: set):
    """Save processed filenames to cache."""
    cache_path.write_text('\n'.join(sorted(processed)))


def process_batch(
    input_dir: str,
    output_path: str,
    model: str = "gpt-4.1-mini",
    fields: Optional[dict] = None,
    max_pages: int = 30,
    resume: bool = False,
    delay: float = 0.5,
) -> list[dict]:
    """Process all PDFs in a directory."""
    input_path = Path(input_dir)
    output_file = Path(output_path)

    pdf_files = sorted(input_path.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDF files found in {input_dir}")
        return []

    print(f"Found {len(pdf_files)} PDF(s) in {input_dir}")
    print(f"Model: {model} | Max pages: {max_pages} | Output: {output_path}\n")

    # Resume support
    cache_file = output_file.with_suffix(".cache")
    processed = load_cache(cache_file) if resume else set()

    # Cache dir for markdown conversions
    md_cache_dir = input_path / ".paper_md_cache"
    md_cache_dir.mkdir(exist_ok=True)

    results = []
    total = len(pdf_files)

    for i, pdf_file in enumerate(pdf_files):
        fname = pdf_file.name
        print(f"[{i+1}/{total}] {fname}", end=" ", flush=True)

        if resume and fname in processed:
            print("(cached, skip)")
            continue

        try:
            # Step 1: PDF -> Markdown
            md_cache_path = md_cache_dir / f"{pdf_file.stem}.json"
            if md_cache_path.exists():
                md_result = json.loads(md_cache_path.read_text(encoding="utf-8"))
                print("-> MD(cached)", end=" ", flush=True)
            else:
                md_result = pdf_to_markdown(str(pdf_file), max_pages=max_pages)
                md_cache_path.write_text(
                    json.dumps(md_result, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                print(f"-> MD({len(md_result['markdown'])}ch)", end=" ", flush=True)

            markdown_text = md_result["markdown"]
            if len(markdown_text) < 200:
                print("(too short, skip)")
                continue

            # Step 2: LLM Extraction
            time.sleep(delay)  # Rate limit
            extracted = extract_from_markdown(
                markdown_text,
                fields=fields,
                model=model,
            )
            print(f"-> LLM", end=" ", flush=True)

            # Merge metadata and extraction
            record = {
                "source_file": fname,
                "pdf_title": md_result["metadata"].get("title", ""),
                "pdf_pages": md_result["metadata"].get("pages", 0),
                "tables_found": len(md_result["tables"]),
            }

            if "error" in extracted:
                record["extraction_error"] = extracted.get("raw", extracted["error"])

            # Flatten extraction into CSV-compatible columns
            flat = flatten_dict(extracted)
            record.update(flat)

            results.append(record)
            print("OK")

            # Save incremental
            _save_results(results, output_file)
            if resume:
                processed.add(fname)
                save_cache(cache_file, processed)

        except Exception as e:
            print(f"ERROR: {e}")
            results.append({"source_file": fname, "extraction_error": str(e)})

    # Final save
    _save_results(results, output_file)
    print(f"\nDone. {len(results)} papers processed. Output: {output_file}")
    return results


def _save_results(results: list[dict], output_path: Path):
    """Save results to CSV/JSON based on extension."""
    if not results:
        return

    suffix = output_path.suffix.lower()

    if suffix == ".json" or suffix == ".jsonl":
        if suffix == ".jsonl":
            output_path.write_text(
                '\n'.join(json.dumps(r, ensure_ascii=False) for r in results),
                encoding="utf-8",
            )
        else:
            output_path.write_text(
                json.dumps(results, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
    else:
        # CSV
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(
        description="Batch extract experimental data from academic PDFs"
    )
    parser.add_argument("--input", "-i", required=True, help="Directory of PDF files")
    parser.add_argument("--output", "-o", default="extracted_data.csv", help="Output CSV/JSON path")
    parser.add_argument("--model", "-m", default="gpt-4.1-mini", help="OpenAI model")
    parser.add_argument("--fields", help="Custom fields JSON file")
    parser.add_argument("--max-pages", type=int, default=30, help="Max pages per paper")
    parser.add_argument("--resume", action="store_true", help="Skip already-processed papers")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between API calls (seconds)")
    args = parser.parse_args()

    # Load custom fields
    fields = None
    if args.fields:
        fields = json.loads(Path(args.fields).read_text(encoding="utf-8"))

    # Check API key
    if not os.environ.get("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set.")
        print("Set it with: $env:OPENAI_API_KEY='sk-...'")
        sys.exit(1)

    process_batch(
        input_dir=args.input,
        output_path=args.output,
        model=args.model,
        fields=fields,
        max_pages=args.max_pages,
        resume=args.resume,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()

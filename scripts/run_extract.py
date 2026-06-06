#!/usr/bin/env python3
"""Unified CLI entry for paper-data-extractor.

Supports OpenAI / Ollama backends, custom extraction fields,
and optional Markdown cache control.

Examples:
  python run_extract.py -i ./papers/ -o out.csv
  python run_extract.py -i ./papers/ -o out.csv --provider ollama --model llama3.2
  python run_extract.py -i ./papers/ -o out.csv --fields my_fields.json --no-cache
"""

import argparse
import csv
import json
import logging
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

from pdf_to_md import pdf_to_markdown
from extract_data import build_prompt, DEFAULT_FIELDS
from llm_client import LLMClient

logger = logging.getLogger("paper-data-extractor")


def setup_logging(verbose: bool = False):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
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


def extract_with_client(
    markdown_text: str,
    llm: LLMClient,
    fields: dict,
) -> dict:
    """Run extraction using the unified LLMClient (OpenAI or Ollama)."""
    prompt = build_prompt(markdown_text, fields)
    system = "You extract structured data from academic papers. Return only valid JSON."

    raw = llm.chat(system=system, user=prompt)

    # Strip code fences
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()
    if raw.startswith("```json"):
        raw = raw[7:].strip()
        if raw.endswith("```"):
            raw = raw[:-3]

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        logger.warning("JSON parse failed, returning raw")
        return {"error": "JSON parse failed", "raw": raw}


def load_cache(cache_path: Path) -> set:
    if cache_path.exists():
        return set(cache_path.read_text().strip().split("\n"))
    return set()


def save_cache(cache_path: Path, processed: set):
    cache_path.write_text("\n".join(sorted(processed)))


def run(
    input_dir: str,
    output_path: str,
    provider: str = "openai",
    model: str = "gpt-4.1-mini",
    fields: Optional[dict] = None,
    max_pages: int = 30,
    use_cache: bool = True,
    delay: float = 0.5,
) -> list[dict]:
    input_path = Path(input_dir)
    output_file = Path(output_path)

    pdf_files = sorted(input_path.glob("*.pdf"))
    if not pdf_files:
        logger.error(f"No PDF files found in {input_dir}")
        return []

    logger.info(f"Found {len(pdf_files)} PDF(s) in {input_dir}")
    logger.info(f"Provider: {provider} | Model: {model} | Cache: {use_cache}")
    logger.info(f"Output: {output_path}")

    llm = LLMClient(provider=provider, model=model)

    cache_file = output_file.with_suffix(".cache")
    processed = load_cache(cache_file) if use_cache else set()

    md_cache_dir = input_path / ".paper_md_cache"
    md_cache_dir.mkdir(exist_ok=True)

    results = []
    total = len(pdf_files)

    for i, pdf_file in enumerate(pdf_files):
        fname = pdf_file.name
        logger.info(f"[{i+1}/{total}] {fname}")

        if use_cache and fname in processed:
            logger.debug(f"  (cached, skip)")
            continue

        try:
            # PDF -> MD
            md_cache_path = md_cache_dir / f"{pdf_file.stem}.json"
            if use_cache and md_cache_path.exists():
                md_result = json.loads(md_cache_path.read_text(encoding="utf-8"))
                logger.debug(f"  MD from cache ({len(md_result['markdown'])} chars)")
            else:
                md_result = pdf_to_markdown(str(pdf_file), max_pages=max_pages)
                if use_cache:
                    md_cache_path.write_text(
                        json.dumps(md_result, ensure_ascii=False, indent=2),
                        encoding="utf-8",
                    )
                logger.debug(f"  MD converted ({len(md_result['markdown'])} chars)")

            markdown_text = md_result["markdown"]
            if len(markdown_text) < 200:
                logger.warning(f"  Too short ({len(markdown_text)} chars), skip")
                continue

            # LLM extraction
            time.sleep(delay)
            extracted = extract_with_client(markdown_text, llm, fields or DEFAULT_FIELDS)
            logger.debug(f"  Extraction done")

            record = {
                "source_file": fname,
                "pdf_title": md_result["metadata"].get("title", ""),
                "pdf_pages": md_result["metadata"].get("pages", 0),
                "tables_found": len(md_result.get("tables", [])),
            }
            if "error" in extracted:
                record["extraction_error"] = extracted.get("raw", extracted["error"])
            flat = flatten_dict(extracted)
            record.update(flat)
            results.append(record)

            _save_results(results, output_file)
            if use_cache:
                processed.add(fname)
                save_cache(cache_file, processed)

            logger.info(f"  OK")

        except Exception as e:
            logger.error(f"  FAILED: {e}")
            results.append({"source_file": fname, "extraction_error": str(e)})

    _save_results(results, output_file)
    logger.info(f"Done. {len(results)} papers processed -> {output_file}")
    return results


def _save_results(results: list[dict], output_path: Path):
    if not results:
        return
    suffix = output_path.suffix.lower()
    if suffix == ".json":
        output_path.write_text(
            json.dumps(results, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    elif suffix == ".jsonl":
        output_path.write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in results),
            encoding="utf-8",
        )
    else:
        df = pd.DataFrame(results)
        df.to_csv(output_path, index=False, encoding="utf-8-sig")


def main():
    parser = argparse.ArgumentParser(
        description="Unified CLI for paper data extraction (OpenAI / Ollama)"
    )
    parser.add_argument("--input", "-i", required=True, help="Directory of PDF files")
    parser.add_argument("--output", "-o", default="extracted_data.csv", help="Output CSV/JSON path")
    parser.add_argument("--provider", default="openai", choices=["openai", "ollama"],
                        help="LLM backend (default: openai)")
    parser.add_argument("--model", "-m", default="gpt-4.1-mini", help="Model name")
    parser.add_argument("--fields", help="Custom fields JSON file")
    parser.add_argument("--max-pages", type=int, default=30, help="Max PDF pages")
    parser.add_argument("--no-cache", action="store_true", help="Disable Markdown caching")
    parser.add_argument("--delay", type=float, default=0.5, help="Delay between API calls (s)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Debug logging")
    args = parser.parse_args()

    setup_logging(args.verbose)

    fields = None
    if args.fields:
        fields = json.loads(Path(args.fields).read_text(encoding="utf-8"))

    if args.provider == "openai" and not os.environ.get("OPENAI_API_KEY"):
        logger.error("OPENAI_API_KEY not set. Use --provider ollama or set the env var.")
        sys.exit(1)
    if args.provider == "ollama":
        logger.info(f"Using Ollama @ {os.environ.get('OLLAMA_HOST', 'http://localhost:11434/v1')}")

    run(
        input_dir=args.input,
        output_path=args.output,
        provider=args.provider,
        model=args.model,
        fields=fields,
        max_pages=args.max_pages,
        use_cache=not args.no_cache,
        delay=args.delay,
    )


if __name__ == "__main__":
    main()

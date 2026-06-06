#!/usr/bin/env python3
"""Convert academic PDF to structured Markdown using pymupdf."""

import sys
import json
import re
from pathlib import Path
from typing import Optional

import pymupdf  # fitz


def clean_text(text: str) -> str:
    """Clean extracted text: normalize whitespace, remove garbage."""
    text = re.sub(r'\s{3,}', '\n\n', text)
    text = re.sub(r'(\n\s*){3,}', '\n\n', text)
    text = re.sub(r'[^\S\n]+', ' ', text)
    return text.strip()


def detect_section_heading(line: str) -> bool:
    """Heuristic to detect section headings."""
    patterns = [
        r'^\d+\.?\s+[A-Z][A-Za-z\s]+$',
        r'^[IVX]+\.?\s+[A-Z][A-Za-z\s]+$',
        r'^(Abstract|Introduction|Related Work|Background|Method|Experiment|Results?|Discussion|Conclusion|References?|Appendix|Acknowledgments?|Supplementary)[\s\.]*$',
    ]
    return any(re.match(p, line, re.IGNORECASE) for p in patterns)


def extract_references_section(pages, start_marker="references", end_marker=None):
    """Extract structured reference entries from the bibliography section."""
    refs = []
    in_refs = False
    for page in pages:
        text = page.get_text("text")
        for line in text.split('\n'):
            line = line.strip()
            if not line:
                continue
            if re.match(r'^references?$', line, re.IGNORECASE):
                in_refs = True
                continue
            if in_refs:
                if re.match(r'^appendix|^supplementary|^acknowledgments?', line, re.IGNORECASE):
                    break
                if re.match(r'^\[\d+\]', line):
                    refs.append(line)
    return refs


def pdf_to_markdown(
    pdf_path: str,
    max_pages: int = 30,
    extract_tables: bool = True,
    extract_refs: bool = True,
) -> dict:
    """Convert a PDF to structured Markdown.

    Returns dict with keys: markdown, tables, refs, metadata.
    """
    doc = pymupdf.open(pdf_path)
    pages_to_process = min(len(doc), max_pages)

    # Extract metadata
    meta = doc.metadata or {}
    metadata = {
        "title": meta.get("title", ""),
        "author": meta.get("author", ""),
        "pages": len(doc),
        "processed_pages": pages_to_process,
    }

    # Build markdown
    lines = []
    tables_found = []

    for page_num in range(pages_to_process):
        page = doc[page_num]

        # --- Text extraction ---
        text = page.get_text("text")
        text = clean_text(text)

        # Mark section headings
        formatted_lines = []
        for line in text.split('\n'):
            stripped = line.strip()
            if not stripped:
                formatted_lines.append('')
            elif detect_section_heading(stripped):
                formatted_lines.append(f'## {stripped}')
            else:
                formatted_lines.append(stripped)

        lines.append('\n'.join(formatted_lines))

        # --- Table extraction ---
        if extract_tables:
            tabs = page.find_tables()
            for tab in tabs:
                try:
                    data = tab.extract()
                    if data and len(data) > 1:
                        tables_found.append({
                            "page": page_num + 1,
                            "rows": len(data),
                            "cols": len(data[0]) if data[0] else 0,
                            "data": data,
                        })
                except Exception:
                    pass

    # References
    refs = []
    if extract_refs and pages_to_process > len(doc) - 2:
        refs = extract_references_section(
            [doc[i] for i in range(len(doc) - 3, len(doc))]
        )

    doc.close()

    # Build table markdown append
    table_md = ""
    if tables_found:
        table_md += "\n\n## Extracted Tables\n\n"
        for i, t in enumerate(tables_found):
            table_md += f"### Table {i+1} (Page {t['page']}, {t['rows']}x{t['cols']})\n\n"
            for row in t['data']:
                table_md += "| " + " | ".join(str(c) for c in row) + " |\n"
                if row == t['data'][0]:
                    table_md += "|" + "|".join("---" for _ in row) + "|\n"
            table_md += "\n"

    full_md = '\n\n'.join(lines) + table_md

    return {
        "markdown": full_md,
        "tables": tables_found,
        "refs": refs,
        "metadata": metadata,
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert PDF to Markdown")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("--output", "-o", help="Output path (default: stdout as JSON)")
    parser.add_argument("--max-pages", type=int, default=30)
    parser.add_argument("--text-only", action="store_true", help="Output only the markdown text")
    args = parser.parse_args()

    result = pdf_to_markdown(args.pdf, max_pages=args.max_pages)

    if args.text_only:
        if args.output:
            Path(args.output).write_text(result["markdown"], encoding="utf-8")
        else:
            print(result["markdown"])
    else:
        output = json.dumps(result, ensure_ascii=False, indent=2)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            print(output)


if __name__ == "__main__":
    main()

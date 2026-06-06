---
name: paper-data-extractor
description: >-
  Bulk extract structured experimental data (methods, parameters, metrics, tables,
  results) from academic paper PDFs. Use when the user needs to extract experimental
  data from multiple papers, build a structured dataset from literature, scrape
  numerical results from PDFs, create a paper-data table, or automate the extraction
  of methods/parameters/metrics from a batch of scientific papers. Triggers on:
  "extract data from papers", "extract experimental data", "batch extract PDF",
  "paper data extraction", "extract tables from papers", "extract results from PDFs",
  "从论文提取数据", "批量提取实验数据", "提取论文表格", "论文数据抽取".
version: 1.0.0
author: Generated for bulk experimental data extraction
---

# Paper Data Extractor

Bulk extract structured experimental data from academic paper PDFs using
PDF -> Markdown conversion + LLM-powered structured extraction.

## Workflow

1. **Collect PDFs** — Place all target papers in a single directory.
2. **Convert** — Run `scripts/batch_extract.py` on the PDF directory:
   - Converts each PDF to Markdown via pymupdf (preserving structure)
   - Sends the Markdown to an LLM with a structured extraction prompt
   - Collects results into a single CSV/JSON output
3. **Review** — The output CSV contains paper-level rows with extracted fields.

## Prerequisites

- Python with `pymupdf`, `openai`, `pandas` installed
- `OPENAI_API_KEY` environment variable set

## Scripts

- `scripts/batch_extract.py` — Main entry point.
  ```
  python scripts/batch_extract.py --input ./papers/ --output ./output.csv
  ```
  Options: `--input`, `--output`, `--model` (default: gpt-4.1-mini), `--max-pages`, `--resume`

- `scripts/pdf_to_md.py` — Single-file PDF to Markdown converter.
- `scripts/extract_data.py` — Single-file LLM extractor.

## Tips

- For large batches, use `--model gpt-4.1-mini` for speed/cost.
- Use `--model gpt-4.1` for complex papers with dense tables.
- The script caches Markdown conversions so re-runs are fast.
- Review the output CSV; LLM extraction may need spot-checking.

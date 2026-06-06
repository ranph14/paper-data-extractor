---
name: paper-data-extractor
description: >-
  Bulk extract structured experimental data (methods, parameters, metrics, tables,
  results) from academic paper PDFs. Use when the user needs to extract experimental
  data from multiple papers, build a structured dataset from literature, scrape
  numerical results from PDFs, create a paper-data table, or automate the extraction
  of methods/parameters/metrics from a batch of scientific papers. Supports OpenAI
  and Ollama (local/private) backends. Triggers on:
  "extract data from papers", "extract experimental data", "batch extract PDF",
  "paper data extraction", "extract tables from papers", "extract results from PDFs",
  "从论文提取数据", "批量提取实验数据", "提取论文表格", "论文数据抽取".
version: 1.1.0
author: Generated for bulk experimental data extraction
---

# Paper Data Extractor

Bulk extract structured experimental data from academic paper PDFs using
PDF → Markdown conversion + LLM-powered structured extraction.
Supports **OpenAI (cloud)** and **Ollama (local)**.

## Workflow

1. **Collect PDFs** — Place all target papers in a single directory.
2. **Extract** — Run `scripts/run_extract.py`:
   - Converts each PDF to Markdown via pymupdf
   - Sends Markdown to LLM (OpenAI or Ollama) with a structured extraction prompt
   - Collects results into a single CSV/JSON output
3. **Review** — The output CSV contains paper-level rows with extracted fields.

## Quick Start

```bash
# Install deps
pip install -r requirements.txt

# OpenAI (needs OPENAI_API_KEY)
python scripts/run_extract.py -i ./papers/ -o results.csv

# Ollama (local, free — needs ollama running)
python scripts/run_extract.py -i ./papers/ -o results.csv --provider ollama --model llama3.2
```

## Prerequisites

- Python 3.10+ with `pymupdf`, `openai`, `pandas`, `ollama`
- OpenAI: `OPENAI_API_KEY` env var
- Ollama: `ollama` installed + model pulled (`ollama pull llama3.2`)

## Scripts

| Script | Purpose |
|--------|---------|
| `scripts/run_extract.py` | **Recommended.** Unified CLI, OpenAI + Ollama, logging, cache control |
| `scripts/batch_extract.py` | Original batch (OpenAI only), `--resume` support |
| `scripts/pdf_to_md.py` | Single-file PDF → Markdown |
| `scripts/extract_data.py` | Single-file LLM extraction (OpenAI) |
| `scripts/llm_client.py` | OpenAI / Ollama adapter layer |

## CLI Flags (run_extract.py)

`--input DIR`, `--output PATH`, `--provider openai|ollama`, `--model NAME`,
`--fields JSON`, `--max-pages N`, `--no-cache`, `--delay SEC`, `--verbose`

## Tips

- For large batches, use `--model gpt-4.1-mini` (cloud) or `llama3.2` (local).
- Use `--model gpt-4.1` for complex papers with dense tables.
- Markdown conversions are cached by default; `--no-cache` to force re-conversion.
- Review the output CSV; LLM extraction may need spot-checking.
- Ollama keeps data local — good for sensitive/private papers.

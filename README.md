# Paper Data Extractor

Bulk extract structured experimental data from academic paper PDFs using
PDF 蚤 Markdown conversion + LLM-powered extraction.
Supports **OpenAI** and **Ollama (local)** backends.

## What it does

Given a folder of academic PDFs, this skill:
1. Converts each PDF to structured Markdown (via pymupdf)
2. Sends the Markdown to an LLM (OpenAI or local Ollama) for structured extraction
3. Outputs a CSV/JSON with paper-level rows of extracted data

**Extracted fields**: title, authors, year, DOI, research domain, task, method name/category/novelty, datasets, metrics (with values), baselines, best results, hardware, main findings

## Installation

```bash
pip install -r requirements.txt
```

### Prerequisites

- Python 3.10+
- OpenAI API key (cloud) **or** [Ollama](https://ollama.com) running locally
- `OPENAI_API_KEY` env var (OpenAI mode only)

## Quick Start

```bash
# OpenAI (default)
python scripts/run_extract.py -i ./papers/ -o results.csv

# Ollama (local, free)
python scripts/run_extract.py -i ./papers/ -o results.csv --provider ollama --model llama3.2

# Custom fields + no cache
python scripts/run_extract.py -i ./papers/ -o results.csv --fields my_fields.json --no-cache
```

## CLI Reference — `run_extract.py` (recommended)

| Flag | Default | Description |
|------|---------|-------------|
| `-i, --input` | (required) | PDF directory |
| `-o, --output` | `extracted_data.csv` | Output path (.csv / .json / .jsonl) |
| `--provider` | `openai` | `openai` or `ollama` |
| `-m, --model` | `gpt-4.1-mini` | Model name (`llama3.2`, `mistral`, etc for Ollama) |
| `--fields` | built-in schema | Custom extraction fields JSON file |
| `--max-pages` | `30` | Max PDF pages to process |
| `--no-cache` | off | Disable Markdown caching |
| `--delay` | `0.5` | Seconds between LLM calls |
| `-v, --verbose` | off | Debug logging |

### Legacy Scripts

```bash
# Original batch (OpenAI only)
python scripts/batch_extract.py --input ./papers/ --output results.csv

# Single PDF to Markdown
python scripts/pdf_to_md.py paper.pdf --output paper.md

# Single-file LLM extraction
python scripts/extract_data.py paper.md --output extracted.json
```

## Ollama Setup

```bash
# Install Ollama
# macOS/Linux: curl -fsSL https://ollama.com/install.sh | sh
# Windows: https://ollama.com/download

# Pull a model
ollama pull llama3.2

# Run extraction
python scripts/run_extract.py -i ./papers/ -o results.csv --provider ollama --model llama3.2
```

Optional: set `OLLAMA_HOST` if not on default `http://localhost:11434/v1`.

## Custom Extraction Schema

Edit `references/extraction-schema.md` or pass a custom JSON file via `--fields`:

```json
{
  "title": "",
  "method": "",
  "datasets": [],
  "best_metric": {"name": "", "value": ""},
  "key_result": ""
}
```

## Features

- **Dual backend**: OpenAI (cloud) + Ollama (local, free, private)
- **Resume support**: `--resume` skips processed papers (batch_extract.py)
- **MD cache**: PDF-to-Markdown conversions cached for fast re-runs
- **Table extraction**: Auto-detects tables from PDFs
- **Flattened CSV**: Nested JSON fields flattened for spreadsheet analysis
- **Rate limiting**: Configurable `--delay` between API calls
- **Logging**: `--verbose` enables debug-level output

## Project Structure

```
scripts/
  run_extract.py    # Unified CLI (OpenAI + Ollama)
  batch_extract.py  # Original batch (OpenAI only)
  pdf_to_md.py      # PDF -> Markdown converter
  extract_data.py   # LLM extractor (OpenAI)
  llm_client.py     # OpenAI / Ollama adapter
references/
  extraction-schema.md
```

## License

MIT

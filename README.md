# Paper Data Extractor

Bulk extract structured experimental data from academic paper PDFs using
PDF → Markdown conversion + LLM-powered extraction.

## What it does

Given a folder of academic PDFs, this skill:
1. Converts each PDF to structured Markdown (via pymupdf)
2. Sends the Markdown to an LLM for structured extraction
3. Outputs a CSV/JSON with paper-level rows of extracted data

**Extracted fields**: title, authors, year, DOI, research domain, task, method name/category/novelty, datasets, metrics (with values), baselines, best results, hardware, main findings

## Installation

### As a Codex Skill

```bash
# Copy to Codex skills directory
cp -R . ~/.codex/skills/paper-data-extractor/

# Install Python dependencies
pip install pymupdf openai pandas
```

### Prerequisites

- Python 3.10+
- `pymupdf`, `openai`, `pandas`
- `OPENAI_API_KEY` environment variable

## Usage

```bash
# Batch extract from a directory of PDFs
python scripts/batch_extract.py \
  --input ./papers/ \
  --output results.csv \
  --model gpt-4.1-mini

# Resume interrupted batch
python scripts/batch_extract.py \
  --input ./papers/ \
  --output results.csv \
  --resume

# Custom extraction fields
python scripts/batch_extract.py \
  --input ./papers/ \
  --output results.json \
  --fields my_fields.json \
  --model gpt-4.1
```

## Individual Scripts

### `pdf_to_md.py` — PDF to Markdown

```bash
python scripts/pdf_to_md.py paper.pdf --output paper.md --text-only
python scripts/pdf_to_md.py paper.pdf --output paper.json  # full JSON with tables
```

### `extract_data.py` — LLM Extraction

```bash
python scripts/extract_data.py paper.md --output extracted.json --model gpt-4.1-mini
```

## Custom Extraction Schema

Edit `references/extraction-schema.md` or pass a custom JSON file:

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

- **Resume support**: `--resume` skips already-processed papers
- **MD cache**: PDF-to-Markdown conversions are cached for fast re-runs
- **Table extraction**: Automatically detects and extracts tables from PDFs
- **Flattened CSV**: Nested JSON fields are flattened for spreadsheet analysis
- **Rate limiting**: Configurable `--delay` between LLM API calls

## License

MIT

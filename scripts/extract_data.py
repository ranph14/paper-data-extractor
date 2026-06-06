#!/usr/bin/env python3
"""Extract structured experimental data from paper Markdown using LLM."""

import json
import os
import sys
from pathlib import Path
from typing import Optional

from openai import OpenAI

DEFAULT_FIELDS = {
    "paper_metadata": {
        "title": "Full paper title",
        "authors": "First author et al. or full list",
        "year": "Publication year (integer)",
        "doi": "DOI if present",
    },
    "research": {
        "domain": "e.g. NLP, Computer Vision, Materials Science, Biology",
        "task": "Specific task being solved",
        "problem_type": "classification / regression / generation / detection / etc",
    },
    "method": {
        "name": "Method or model name",
        "category": "e.g. Transformer, GNN, Diffusion, RL, CNN",
        "novelty": "What is new about this method (1-2 sentences)",
    },
    "experiment": {
        "datasets": ["List of dataset names used"],
        "metrics": {"example_metric": "value"},
        "baselines": ["Methods compared against"],
        "best_result": "Best reported result (metric name + value)",
        "ablations": "Key ablation findings (if any)",
    },
    "compute": {
        "hardware": "GPU/TPU models if reported",
        "training_time": "If reported",
    },
    "claims": {
        "main_finding": "One-sentence takeaway",
        "limitations": "Stated limitations",
    },
}


def build_prompt(markdown_text: str, fields: dict, language: str = "en") -> str:
    """Build the extraction prompt."""
    fields_json = json.dumps(fields, ensure_ascii=False, indent=2)

    prompt = f"""You are an expert scientific data extractor. Extract structured information from the following academic paper.

## Paper Content (Markdown)

{markdown_text[:30000]}

## Required Fields

Extract the following fields as a JSON object. If a field is not found, use null or empty.

{fields_json}

## Output Rules

1. Return ONLY valid JSON (no markdown fences, no explanations).
2. Extract quantitative values exactly as reported.
3. For metrics, use the exact metric names from the paper.
4. If the paper compares multiple methods, focus on the proposed method's results.
5. Be precise with numbers - do not round unless the paper does.
6. For authors, use "FirstAuthor et al." format if there are more than 3 authors.

Output ONLY the JSON object:"""
    return prompt


def extract_from_markdown(
    markdown_text: str,
    fields: Optional[dict] = None,
    model: str = "gpt-4.1-mini",
    api_key: Optional[str] = None,
) -> dict:
    """Run LLM extraction on a paper's Markdown content.

    Args:
        markdown_text: Paper content as Markdown.
        fields: Extraction schema dict (uses DEFAULT_FIELDS if None).
        model: OpenAI model name.
        api_key: OpenAI API key (defaults to OPENAI_API_KEY env var).

    Returns:
        Dict with extracted fields.
    """
    if fields is None:
        fields = DEFAULT_FIELDS

    client = OpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY"))

    prompt = build_prompt(markdown_text, fields)

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "You extract structured data from academic papers. Return only valid JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.1,
        max_tokens=4096,
    )

    raw = response.choices[0].message.content.strip()

    # Clean up markdown code fences if present
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
        result = json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract JSON object with regex
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            try:
                result = json.loads(match.group())
            except json.JSONDecodeError:
                result = {"error": "JSON parse failed", "raw": raw}
        else:
            result = {"error": "JSON parse failed", "raw": raw}

    return result


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Extract data from paper Markdown")
    parser.add_argument("input", help="Path to markdown file or JSON from pdf_to_md.py")
    parser.add_argument("--output", "-o", help="Output JSON path (default: stdout)")
    parser.add_argument("--model", default="gpt-4.1-mini", help="OpenAI model")
    parser.add_argument("--fields", help="Custom fields JSON file")
    args = parser.parse_args()

    # Load input
    input_path = Path(args.input)
    if input_path.suffix == ".json":
        data = json.loads(input_path.read_text(encoding="utf-8"))
        markdown_text = data.get("markdown", "")
    else:
        markdown_text = input_path.read_text(encoding="utf-8")

    # Load custom fields
    fields = None
    if args.fields:
        fields = json.loads(Path(args.fields).read_text(encoding="utf-8"))

    result = extract_from_markdown(markdown_text, fields=fields, model=args.model)

    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        print(output)


if __name__ == "__main__":
    main()

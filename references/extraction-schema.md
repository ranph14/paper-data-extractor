# Extraction Schema Reference

Customize which fields to extract by editing `extraction_fields.json` or passing
`--fields` to the batch script. Below is the default schema.

## Default Extraction Fields

```json
{
  "paper_metadata": {
    "title": "Full paper title",
    "authors": "First author et al. or full list",
    "year": 2024,
    "doi": "DOI if available"
  },
  "research": {
    "domain": "e.g. NLP, Computer Vision, Materials Science",
    "task": "Specific task being solved",
    "problem_type": "classification / regression / generation / detection / etc"
  },
  "method": {
    "name": "Method or model name",
    "category": "e.g. Transformer, GNN, Diffusion, RL",
    "novelty": "What is new about this method"
  },
  "experiment": {
    "datasets": ["dataset names used"],
    "metrics": {"metric_name": "value"},
    "baselines": ["compared against"],
    "best_result": "Best reported result",
    "ablations": "Key ablation findings"
  },
  "compute": {
    "hardware": "GPU/TPU models used",
    "training_time": "if reported"
  },
  "claims": {
    "main_finding": "One-sentence takeaway",
    "limitations": "Stated limitations"
  }
}
```

## Minimal Schema

For fast extraction, use a minimal schema:

```json
{
  "title": "",
  "method": "",
  "datasets": [],
  "best_metric": {"name": "", "value": ""},
  "key_result": ""
}
```

## Customization

Create a JSON file with your desired field names as keys and descriptions
as values. The LLM will be prompted to fill in each field.

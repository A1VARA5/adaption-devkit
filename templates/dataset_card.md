---
license: apache-2.0
language:
  - en
tags:
  - marketing
  - text-generation
  - synthetic
  - adaption
pretty_name: "PLACEHOLDER Dataset Name"
size_categories:
  - 1K<n<10K
---

# PLACEHOLDER Dataset Name

> Replace every PLACEHOLDER below. Remove any section that does not apply. Keep the YAML
> frontmatter above so Hugging Face renders the metadata. Save as plain UTF-8, no BOM.

## Summary

PLACEHOLDER one to three sentences. What this dataset contains, who it is for, and what task it
supports (for example, instruction tuning for short-form marketing copy in a specific brand voice).

State clearly whether rows are human-written, synthetic, or adapted with Adaption Adaptive Data, and
note that this is a community resource not affiliated with or endorsed by Adaption Labs.

- Domain: PLACEHOLDER (marketing, math and code, finance, qa, other)
- Rows: PLACEHOLDER count
- Language: PLACEHOLDER
- Format: PLACEHOLDER (csv, jsonl, parquet)
- Created by: PLACEHOLDER author and handle

## Columns

| Column | Type | Description |
|--------|------|-------------|
| `prompt` | string | PLACEHOLDER the instruction or question (anchor) |
| `completion` | string | PLACEHOLDER the target answer (anchor) |
| `context` | list of string | PLACEHOLDER optional grounding passages or brand notes |

At least one of `prompt` or `completion` is present in every row. `context` is optional and is a
list.

## How to use with Adaption

This dataset is shaped for the Adaption Adaptive Data lifecycle (ingest, adapt, evaluate, export).
The mapping below tells the platform which columns are the anchors.

```python
from adaption import Adaption

client = Adaption(api_key="pt_live_...")
ds = client.datasets.upload_file("PLACEHOLDER.jsonl", name="PLACEHOLDER-name")

run = client.datasets.run(
    ds.dataset_id,
    column_mapping={"prompt": "prompt", "completion": "completion", "context": ["context"]},
    recipe_specification={"recipes": {"deduplication": True, "prompt_rephrase": True}},
    brand_controls={"length": "concise"},
    estimate=True,  # estimate first, then set False to run for real
)
```

Notes:

- Deduplication keys on the `prompt`, so templated prompts can collapse into near duplicates. Favor
  unique prompts, the completion only shape, or `prompt_rephrase`.
- `reasoning_traces` is a recipe, not a brand control. Enable it for math, code, finance, and other
  stepwise-reasoning domains.
- For fact sensitive domains, add `brand_controls={"hallucination_mitigation": True}`.

## Provenance

PLACEHOLDER describe where the data came from. Original sources, scraping or generation method,
licenses of any upstream data, dates collected, and what transformations were applied (deduplication,
rephrasing, reasoning traces, filtering). If adapted with Adaption, record the recipes and
brand_controls used and the `improvement_percent` from evaluation if available.

## Limitations and biases

PLACEHOLDER. Known gaps, domain or language coverage limits, synthetic-data artifacts, possible
factual errors, and any content that should not be treated as professional advice (for example,
finance rows are general information, not financial advice). Note any safety filtering applied.

## License

Released under the Apache License 2.0 unless a row's upstream source requires otherwise. PLACEHOLDER
confirm that you have the right to redistribute all included content under this license.

## Citation

```bibtex
@misc{PLACEHOLDER_key,
  title  = {PLACEHOLDER Dataset Name},
  author = {PLACEHOLDER Author},
  year   = {PLACEHOLDER},
  url    = {PLACEHOLDER dataset URL}
}
```

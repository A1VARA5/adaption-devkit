# adaption-kit

Community, unofficial open source toolkit for starting fast with Adaption's
Adaptive Data and AutoScientist. Not affiliated with or endorsed by Adaption Labs.

- License: Apache-2.0
- Author: Aivaras Navardauskas (MANIFESTA), GitHub A1VARA5

It wraps the lifecycle ingest, adapt, evaluate, export, publish with a small,
typed package and a CLI. The headline feature is a preflight linter that catches
the templated prompt trap: Adaption always applies deduplication keyed on the
prompt, so prompts whose only variety is in context columns collapse to a few
rows. Catch that before you spend credits.

## Install

```bash
pip install adaption-kit            # core: lint, card, cover (HTML fallback)
pip install adaption-kit[sdk]       # adds the adaption SDK for estimate/run
pip install adaption-kit[hf]        # adds Hugging Face publishing
pip install adaption-kit[kaggle]    # adds Kaggle publishing
pip install adaption-kit[cover]     # adds Playwright for PNG cover rendering
pip install adaption-kit[parquet]   # adds pyarrow for .parquet convert
pip install adaption-kit[all]       # everything
```

Core needs no third-party packages. The SDK, Hugging Face, Kaggle, and Playwright
are optional and imported lazily, so the parts that do not need them always work.

## Configuration

Environment only. Never hardcode a host or key.

- `ADAPTION_API_KEY` - Adaption bearer key (estimate, run, download)
- `ADAPTION_BASE_URL` - REST base URL (optional; SDK default used if unset)
- `HF_TOKEN` or `HUGGINGFACE_TOKEN` - Hugging Face write token
- `KAGGLE_USERNAME` / `KAGGLE_KEY` - Kaggle credentials (or `~/.kaggle/kaggle.json`)

## CLI

Run as `adaption-kit ...` or `python -m adaption_kit ...`.

```bash
# Offline environment healthcheck (no network, no required deps)
adaption-kit doctor

# Suggest a column mapping for a CSV or JSONL (ready to paste JSON)
adaption-kit suggest data.csv

# Preflight a dataset (anchor uniqueness, near duplicates, long completions,
# empty anchors, fill rates, suspicious encodings)
adaption-kit lint data.csv --prompt instruction --completion response --context source,reference

# Convert between formats, BOM-safe in, plain utf-8 out (.parquet needs pyarrow)
adaption-kit convert data.csv data.jsonl

# Quote credits and time, no run started
adaption-kit estimate DATASET_ID --prompt instruction --completion response --deduplication

# Pilot 200 rows, then wait for run and evaluation, print improvement_percent
adaption-kit run DATASET_ID --prompt instruction --completion response \
    --pilot --deduplication --prompt-rephrase --wait

# Generate cards / Kaggle metadata
adaption-kit card dataset --title "BrandVoice" --summary "Adapted marketing corpus" \
    --tags marketing,nlp --improvement-percent 18.4 --out ./release
adaption-kit card kaggle --title "BrandVoice" --kaggle-slug a1vara5/brandvoice \
    --tags marketing,business --out ./release

# Publish a folder to Hugging Face and/or Kaggle (the 501 workaround)
adaption-kit publish ./release --hf-repo a1vara5/brandvoice --kaggle-slug a1vara5/brandvoice

# Render a cover image (Playwright if installed, else writes HTML)
adaption-kit cover ./release/cover.png --title "BrandVoice" --subtitle "Marketing, Part 1"
```

Recipe flags are tri-state: `--deduplication` turns it on, `--no-deduplication`
turns it off, and omitting it leaves the backend default. Same for
`--prompt-rephrase` and `--reasoning-traces`. `reasoning_traces` is a recipe, not
a brand control.

## Python API

```python
from adaption_kit import doctor
print(doctor().summary())          # offline healthcheck, no network

from adaption_kit import suggest_mapping
result = suggest_mapping("data.csv")
print(result.summary())
print(result.anchor, result.mapping())   # e.g. "both", {"prompt": ..., "completion": ...}

from adaption_kit import lint_dataset
report = lint_dataset("data.csv", prompt="instruction", completion="response")
print(report.summary())
print(report.status, report.duplicate_rows, report.unique_anchor_rate)
print(report.near_duplicate_rows, report.long_completion_rows,
      report.suspicious_encoding_rows)

from adaption_kit import convert_file
rows = convert_file("data.csv", "data.jsonl")   # returns the row count

from adaption_kit.run import estimate, pilot, run_full, wait_for_result
est = estimate("DATASET_ID", prompt="instruction", completion="response", deduplication=True)
pilot("DATASET_ID", prompt="instruction", completion="response", max_rows=200)
result = wait_for_result("DATASET_ID")
print(result.improvement_percent)

from adaption_kit.cards import (
    generate_dataset_card, generate_model_card, generate_kaggle_metadata,
)
from adaption_kit.publish import publish
from adaption_kit.cover import generate_cover
```

## Notes

- Always `estimate` before a real run; pilot with `max_rows` before the full corpus.
- `improvement_percent` lives in evaluation, polled separately from run status.
  `wait_for_result` polls both.
- Adaption's publish endpoint returns 501; `publish` pushes to Hugging Face and
  Kaggle manually instead.
- Kaggle accepts taxonomy tags only; `generate_kaggle_metadata` validates them.
- CSV and JSON are read BOM-safe (utf-8-sig) and written as plain utf-8.
- The package ships a `py.typed` marker, so type checkers read its annotations.

# Tests

A small, real pytest suite for the `adaption_kit` package. The point is to
verify the tools, not just assert they look plausible. Every test builds its
own tiny fixtures with pytest's `tmp_path`, so the suite never depends on the
cookbook or sample data and leaves no files behind.

## What is covered

- `test_preflight.py` - `preflight.lint_dataset`
  - a clean, all unique completion only file PASSes
  - a prompt anchor that is the same value on every row FAILs (the dedup
    collapse, the headline behavior)
  - several duplicate anchors WARN and the collapse count appears in a message
  - a file written with a UTF-8 BOM (utf-8-sig) still loads with a clean header
- `test_suggest.py` - `suggest.suggest_mapping`
  - a single answer or completion column is recommended as completion only
  - an instruction column plus a response column is recommended as both
- `test_cards.py` - `cards`
  - valid Kaggle tags pass and are normalized; invalid tags raise
    `InvalidKaggleTag` (checked against the `KAGGLE_VALID_TAGS` surface)
  - `generate_dataset_card` returns a non empty string
- `test_doctor.py` - `doctor`
  - runs with no network and returns a report whose summary mentions Python
    and the SDK
- `test_convert.py` - `convert.convert_file`
  - CSV to JSONL returns the row count and the JSONL has that many lines
  - CSV to JSONL to CSV round trips
  - a BOM source still converts
  - if `adaption_kit.convert` is not present, these tests skip cleanly so the
    rest of the suite still runs, and activate automatically once it lands

## How to run

From the package root (the directory that holds `pyproject.toml`):

Install the package plus a test runner, then run pytest. Either is fine.

```bash
pip install -e ".[dev]"   # if a dev extra exists
# or simply:
pip install pytest
pip install -e .          # so 'adaption_kit' is importable
```

Then:

```bash
pytest
```

To run just this folder, or a single file:

```bash
pytest tests
pytest tests/test_preflight.py -v
```

The tests import the package as `adaption_kit`, so it must be importable. A
plain `pip install -e .` from the package root is enough. No network access,
no API key, and no optional extras are required.

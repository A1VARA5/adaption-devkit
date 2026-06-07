# adaption-devkit cookbook

Runnable, beginner friendly notebooks for the **community, unofficial** adaption-devkit.
**Not affiliated with or endorsed by Adaption Labs.** License: Apache-2.0.
Author: Aivaras Navardauskas (MANIFESTA), GitHub [A1VARA5](https://github.com/A1VARA5).

These notebooks teach the full Adaptive Data loop: ingest, adapt, evaluate, export, publish.
They were authored, not executed, so the outputs shown inside are **illustrative**. The code is
correct by construction; fill in your own credentials and dataset names to run for real.

## Notebooks

| Notebook | What it covers |
|----------|----------------|
| [`01_first_run.ipynb`](01_first_run.ipynb) | Load the tiny local sample, build the column mapping, `estimate=True`, run a small pilot capped with `max_rows`, then read `improvement_percent`. |
| [`02_import_from_hf.ipynb`](02_import_from_hf.ipynb) | Import a dataset straight from Hugging Face (async ingest), map columns, estimate, run. |
| [`03_publish.ipynb`](03_publish.ipynb) | Download the adapted dataset and push it to Hugging Face and Kaggle with a card and cover. Notes the 501 publish endpoint. |

## Sample data

`sample_data/sample.csv` and `sample_data/sample.jsonl` are a tiny (12-row) marketing corpus in the
**completion only, high quality answers** pattern: a `completion` column plus two `context` columns
(`channel`, `audience`) and **no prompt column**. The platform synthesizes a prompt per row.

Why completion only? **Deduplication is always on and keys on the prompt.** Unique completions (or
genuinely distinct prompts) stay safe; a constant templated prompt across many rows would collapse
the whole dataset to one row. The sample shows the good pattern on purpose.

## Environment variables to set

Auth is **always** via environment variables. Never hardcode the host or any key.

| Variable | Used by | Purpose |
|----------|---------|---------|
| `ADAPTION_BASE_URL` | all notebooks | Adaption API host, e.g. `https://api.prod.adaptionlabs.ai` |
| `ADAPTION_API_KEY` | all notebooks | Adaption secret key (`pt_live_...`) |
| `ADAPTION_DATASET_ID` | `03_publish` | the `dataset_id` to publish (optional; can paste inline) |
| `HF_TOKEN` | `02`, `03` | Hugging Face write token |
| `KAGGLE_USERNAME` / `KAGGLE_KEY` | `03` | Kaggle credentials (or `~/.kaggle/kaggle.json`) |

macOS / Linux:

```bash
export ADAPTION_BASE_URL="https://api.prod.adaptionlabs.ai"
export ADAPTION_API_KEY="pt_live_..."
export HF_TOKEN="hf_..."
export KAGGLE_USERNAME="your-handle"
export KAGGLE_KEY="..."
```

Windows PowerShell:

```powershell
$env:ADAPTION_BASE_URL = "https://api.prod.adaptionlabs.ai"
$env:ADAPTION_API_KEY  = "pt_live_..."
$env:HF_TOKEN          = "hf_..."
$env:KAGGLE_USERNAME   = "your-handle"
$env:KAGGLE_KEY        = "..."
```

## Running

```bash
pip install adaption pandas huggingface_hub kaggle jupyter
jupyter lab    # then open the notebooks in order: 01, 02, 03
```

## Key habits the notebooks enforce

- **Estimate before every real run** (`estimate=True`) to quote credits without charging.
- **Pilot with `job_specification.max_rows`** before scaling to the full corpus.
- **`improvement_percent` lives in `get_evaluation`**, polled separately from run status.
- **Read CSV/JSON with `utf-8-sig`** so a byte order mark never corrupts the first column.
- The Adaption **publish endpoint returns 501**, so notebook 03 publishes manually.

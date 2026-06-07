# Quickstart: zero to first adaptation in about 5 minutes

This guide takes you from nothing to your first Adaptive Data run, with a real
`improvement_percent` number to read at the end.

> **adaption-devkit** is a community, unofficial, open source toolkit (Apache-2.0)
> by Aivaras Navardauskas (MANIFESTA), GitHub `A1VARA5`. It is **not affiliated
> with or endorsed by Adaption Labs**. The official SDK is the `adaption` package;
> this devkit only wraps it with convenience tooling.

## 0. What you need

- Python 3.9 or newer.
- An Adaption API key.
- A small data file to start with (`.csv`, `.json`, `.jsonl`, or `.parquet`).

## 1. Install

```bash
pip install adaption          # the official SDK
pip install adaption-devkit   # this community toolkit (provides the adaption-kit CLI)
```

If you are working from a checkout of this repo instead:

```bash
pip install -e .
```

## 2. Set your environment variables

The SDK reads two environment variables. Never hard-code your key or host in code
you plan to share.

macOS / Linux:

```bash
export ADAPTION_BASE_URL="https://api.prod.adaptionlabs.ai"
export ADAPTION_API_KEY="pt_live_your_key_here"
```

Windows PowerShell:

```powershell
$env:ADAPTION_BASE_URL = "https://api.prod.adaptionlabs.ai"
$env:ADAPTION_API_KEY  = "pt_live_your_key_here"
```

`ADAPTION_BASE_URL` must be configurable through this variable. Set it to whatever
host your account was issued. Do not commit a base URL into source control.

## 3. Sanity-check your data before spending anything

The devkit ships a linter that catches the mistakes that waste credits (duplicate
prompts, wrong encoding, empty anchors) before you ever call the API.

```bash
adaption-kit lint training_data.csv
```

Read the report. If it warns about duplicate prompts, see
[gotchas.md](gotchas.md) on deduplication collapse before continuing.

## 4. First run, always with estimate=True

Your first call to the platform should never start a real run. Quote the cost
first. `estimate=True` validates your mapping and returns a credit and time
estimate without consuming credits.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)

# Upload the local file. This returns a dataset id.
result = client.datasets.upload_file("training_data.csv", name="my-first-dataset")
dataset_id = result.dataset_id

# Estimate only. No credits are spent here.
quote = client.datasets.run(
    dataset_id,
    column_mapping={"prompt": "instruction", "completion": "response"},
    estimate=True,
)
print("estimated credits:", quote.estimated_credits_consumed)
print("estimated minutes:", quote.estimated_minutes)
```

If the mapping is wrong, the estimate call tells you now, for free. Fix it and
estimate again. See [column-mapping.md](column-mapping.md) to pick the right mapping.

## 5. Pilot run on a few hundred rows

When the estimate looks acceptable, do a small pilot, not the full corpus. Cap the
rows with `job_specification.max_rows`. This keeps the first real run cheap.

```python
run = client.datasets.run(
    dataset_id,
    column_mapping={"prompt": "instruction", "completion": "response"},
    recipe_specification={"recipes": {"deduplication": True}},
    job_specification={"max_rows": 300},
    estimate=False,   # this one spends credits
)
print("run id:", run.run_id)

# Wait for the adaptation run to finish.
status = client.datasets.wait_for_completion(dataset_id, timeout=1800)
print("run status:", status.status)   # "succeeded" or "failed"
```

## 6. Read the improvement number

Evaluation runs on its own schedule. The run can report `succeeded` before the
evaluation finishes, so you poll it separately.

```python
import time

ev = client.datasets.get_evaluation(dataset_id)
while ev.status in ("pending", "running"):
    time.sleep(5)
    ev = client.datasets.get_evaluation(dataset_id)

if ev.status == "succeeded" and ev.quality:
    print("score before:", ev.quality.score_before)
    print("score after: ", ev.quality.score_after)
    print("improvement_percent:", ev.quality.improvement_percent)
```

`improvement_percent` is the headline number. It is what the AutoScientist
Challenge is scored on.

## 7. Where to go next

- The pilot improved the score: lock the config and scale up. Remove `max_rows`
  (or raise it), estimate again, then run the full corpus.
- Pick better knobs for your domain: [recipes-and-controls.md](recipes-and-controls.md).
- Ship the result to Hugging Face and Kaggle: [release-checklist.md](release-checklist.md).
- Something behaved unexpectedly: [gotchas.md](gotchas.md).

## The whole loop in one place

1. `adaption-kit lint data.csv` to clean the data.
2. `run(..., estimate=True)` to quote the cost.
3. `run(..., job_specification={"max_rows": 300})` to pilot.
4. `get_evaluation(...)` to read `improvement_percent`.
5. Change one knob, re-pilot, compare. Keep what helps.
6. Scale the winning config to the full corpus.
7. Release to Hugging Face and Kaggle by hand.

# Question and answer walkthrough: a prompt and completion dataset end to end

This is the same end to end path as the marketing walkthrough, on a simpler
shape: a plain question and answer dataset with a `prompt` column and a
`completion` column. It shows the **both** mapping case, where you map a prompt
column and a completion column together so the platform adapts both sides.

Every block is a real command. Every output block is marked **illustrative**:
it shows the shape of what prints, not numbers from your account. The real
credit cost and the real `improvement_percent` depend on your data and your run.

> **adaption-devkit** is a community, unofficial, open source toolkit
> (Apache-2.0) by Aivaras Navardauskas (MANIFESTA), GitHub `A1VARA5`. It is
> **not affiliated with or endorsed by Adaption Labs**. The official SDK is the
> `adaption` package; this devkit only wraps it. Always treat the official docs
> and API as the source of truth.

## What you need

- Python 3.10 or newer.
- An Adaption API key.
- A Hugging Face write token and Kaggle credentials for the release step.
- A small CSV with one question column and one answer column.

## 0. Install

```bash
pip install adaption-kit[all]
```

The core (`doctor`, `lint`, `suggest`, `card`, `cover`) needs no extras. The SDK
backed commands (`estimate`, `run`) need the `[sdk]` extra. Each command tells
you what to add if an extra is missing.

## 1. Set your environment

Configuration is environment only. Set `ADAPTION_BASE_URL` from the environment;
the host that has been answering for participants is
`https://api.prod.adaptionlabs.ai`. Never hardcode a key or a host.

macOS or Linux:

```bash
export ADAPTION_BASE_URL="https://api.prod.adaptionlabs.ai"
export ADAPTION_API_KEY="pt_live_your_key_here"
export HF_TOKEN="hf_your_write_token"
export KAGGLE_USERNAME="your_kaggle_username"
export KAGGLE_KEY="your_kaggle_key"
```

Windows PowerShell:

```powershell
$env:ADAPTION_BASE_URL = "https://api.prod.adaptionlabs.ai"
$env:ADAPTION_API_KEY  = "pt_live_your_key_here"
$env:HF_TOKEN          = "hf_your_write_token"
$env:KAGGLE_USERNAME   = "your_kaggle_username"
$env:KAGGLE_KEY        = "your_kaggle_key"
```

## 2. The raw data

Save this as `qa.csv`. Each row is a question in `prompt` and its trusted answer
in `completion`. Save it as plain UTF-8. If your editor adds a byte order mark,
that is fine: the kit reads with `utf-8-sig`, so a BOM is stripped on input and
the first column still matches.

```csv
prompt,completion
What is the capital of France?,Paris is the capital of France.
How many days are in a leap year?,A leap year has 366 days.
What does HTTP stand for?,HTTP stands for HyperText Transfer Protocol.
Who wrote the play Hamlet?,Hamlet was written by William Shakespeare.
What is the boiling point of water at sea level?,Water boils at 100 degrees Celsius at sea level.
What is the largest planet in our solar system?,Jupiter is the largest planet in our solar system.
How many continents are there on Earth?,There are seven continents on Earth.
What language is primarily spoken in Brazil?,Portuguese is the primary language spoken in Brazil.
```

Every question is distinct, so deduplication (always on, keyed on the prompt)
will not collapse any rows. We confirm that with the linter.

## 3. doctor: is my setup ready

```bash
adaption-kit doctor
```

Illustrative output:

```
adaption-kit doctor report
============================================================
  [PASS] Python 3.11.5 (3.10 or newer)
  [PASS] adaption SDK is importable
  [PASS] ADAPTION_API_KEY is set
  [PASS] ADAPTION_BASE_URL is set
  [PASS] huggingface_hub is installed (Hugging Face publishing)
  [PASS] kaggle is installed (Kaggle publishing)
  [PASS] playwright is installed (cover image rendering)

RESULT: PASS - your environment looks ready.
```

`doctor` is offline. It never calls the network and never prints your key value.
If an extra is missing it shows a `[WARN]` with the exact `pip install` hint and
still passes overall, because the core commands work without extras.

## 4. suggest: the both mapping

Ask the kit which columns are the anchor. With headers named `prompt` and
`completion`, it recognizes both and recommends the both mapping.

```bash
adaption-kit suggest qa.csv
```

Illustrative output:

```
adaption-kit mapping suggestion
============================================================
file        : qa.csv
format      : csv
rows        : 8
columns     : prompt, completion

recommended anchor: prompt + completion (instruction plus answer pairs)

ready to paste column_mapping:

{
  "prompt": "prompt",
  "completion": "completion"
}

notes:
  - 100.0% of the anchor values are unique; dedup impact is minimal.
  - Recipes to consider: deduplication on almost always; prompt_rephrase for
    more prompt variety (skip it if prompts are gold and must stay verbatim);
    reasoning_traces for math, code, science, legal, or finance.
  - Brand controls to consider: length to match the eval's expected answer
    depth; blueprint for a consistent voice (good for marketing or language);
    hallucination_mitigation for fact sensitive domains.

Next: run 'adaption-kit lint qa.csv' with these columns to confirm the anchor
is unique before you spend credits.
```

This is the **both** case: a prompt column and a completion column mapped
together. The platform adapts both sides. Because these answers are short
factual statements, you would usually leave `prompt_rephrase` off (the questions
are fine as written) and skip `reasoning_traces` (no stepwise logic to add).

## 5. lint: confirm the anchor is unique

```bash
adaption-kit lint qa.csv --prompt prompt --completion completion
```

Illustrative output:

```
adaption-kit preflight report
============================================================
file        : qa.csv
format      : csv
encoding    : utf-8
rows        : 8
columns     : prompt, completion
anchor      : prompt -> column 'prompt'
unique anchor values: 8 / 8 (100.0%)
dedup would collapse: 0 row(s)

metadata fill rate:
  - prompt                        8 / 8  (100.0%)
  - completion                    8 / 8  (100.0%)
empty cells : 0

checks:
  [PASS] loaded 8 row(s)
  [PASS] 100.0% of anchors are unique; dedup impact is minimal

RESULT: PASS

```

All eight prompts are unique, so nothing collapses and there is no warning to
fix. If you ever see a `WARN` here about anchors being only partly unique, that
is the deduplication collapse warning: make the prompts distinct, or drop the
prompt and map only `completion` so the platform synthesizes a fresh prompt per
answer. See the marketing walkthrough for a worked fix of that warning.

## 6. Upload the file and get a dataset id

`estimate` and `run` take a `DATASET_ID`. Upload the file once with the SDK and
keep the id. If you post process the file yourself, read it back with
`utf-8-sig` so a BOM does not corrupt the first header.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)
result = client.datasets.upload_file("qa.csv", name="simple-qa")
dataset_id = result.dataset_id
print("dataset_id:", dataset_id)
```

Illustrative output:

```
dataset_id: ds_5b21e7c4a0
```

Use that id, for example `ds_5b21e7c4a0`, in the commands below.

## 7. estimate: quote the cost, start nothing

Always estimate before a run. This validates the both mapping and quotes credits
and minutes without spending anything. Deduplication is on; for short factual
answers we leave the other recipes at their backend defaults.

```bash
adaption-kit estimate ds_5b21e7c4a0 \
    --prompt prompt --completion completion \
    --deduplication
```

Illustrative output:

```
adaption-kit estimate (no run started)
------------------------------------------------------------
estimate (no run started):
  estimated_credits_consumed: 31
  estimated_minutes        : 4
```

The credit number is illustrative; your real quote depends on row count and the
knobs you enable. If the mapping were wrong, this call would tell you now, for
free, before any credits are spent.

## 8. Pilot run: small max_rows first

Pilot with a small `--max-rows`, read the number, then scale. `--wait` polls the
run and the evaluation together and prints `improvement_percent`.

```bash
adaption-kit run ds_5b21e7c4a0 \
    --prompt prompt --completion completion \
    --pilot --max-rows 8 \
    --deduplication \
    --wait
```

Illustrative output:

```
adaption-kit run
------------------------------------------------------------
run started. run_id: run_9c4d11
waiting for run and evaluation ...
run_status        : succeeded
evaluation_status : succeeded
improvement_percent: 12.3
```

`improvement_percent` is the headline number and it is illustrative here; the
real value depends on your run. The run can report `succeeded` before evaluation
finishes, which is why the kit polls evaluation separately. If the percent is
not printed yet, evaluation was not terminal; poll again.

Prefer Python? The same flow, with the both mapping spelled out:

```python
from adaption_kit.run import estimate, pilot, wait_for_result

est = estimate(
    "ds_5b21e7c4a0",
    prompt="prompt", completion="completion",
    deduplication=True,
)
print(est.estimated_credits_consumed, est.estimated_minutes)

pilot(
    "ds_5b21e7c4a0",
    prompt="prompt", completion="completion",
    deduplication=True,
    max_rows=8,
)
result = wait_for_result("ds_5b21e7c4a0")
print("improvement_percent:", result.improvement_percent)
```

## 9. Iterate, then scale

If the number is low, change one knob and re-pilot. For a factual question and
answer set the useful levers are usually `length` (to match the eval's expected
answer depth) and, when the answers benefit from explanation,
`reasoning_traces`. Add `reasoning_traces` through the recipe flag and compare:

```bash
adaption-kit estimate ds_5b21e7c4a0 \
    --prompt prompt --completion completion \
    --deduplication --reasoning-traces
```

Change exactly one thing at a time so you know what moved the score. When a
config wins, drop `--max-rows` (or raise it), estimate the full corpus, and run
it.

## 10. Cards and a cover for the release

```bash
adaption-kit card dataset \
    --title "Simple QA" \
    --summary "Adapted question and answer corpus." \
    --tags nlp,text generation \
    --improvement-percent 12.3 \
    --row-count 8 \
    --out ./release
```

Illustrative output:

```
adaption-kit card
------------------------------------------------------------
wrote release/README.md
```

```bash
adaption-kit card kaggle \
    --title "Simple QA" \
    --kaggle-slug a1vara5/simple-qa \
    --tags nlp,text generation \
    --out ./release
```

Illustrative output:

```
adaption-kit card
------------------------------------------------------------
wrote release/dataset-metadata.json
```

Kaggle accepts taxonomy tags only. The accepted set here is `marketing`, `nlp`,
`text generation`, `business`, and `internet`. The kit validates them and
rejects anything outside the taxonomy, so your release does not get bounced on
tags.

Render a cover:

```bash
adaption-kit cover ./release/cover.png \
    --title "Simple QA" \
    --subtitle "Question and answer"
```

Illustrative output:

```
adaption-kit cover
------------------------------------------------------------
cover PNG written to release/cover.png
```

If Playwright is not installed, the cover command writes the HTML next to the
PNG path and tells you how to enable PNG rendering, so it never hard fails.

## 11. Download the adapted dataset

Export the processed rows into the release folder and resave as plain UTF-8 with
no BOM so neither host chokes on the first column.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)
url = client.datasets.download("ds_5b21e7c4a0")   # presigned download URL
print(url)
```

## 12. publish: release by hand to HF and Kaggle

The platform publish endpoint returns `501 Not Implemented`, so the kit pushes
your release folder to Hugging Face and Kaggle directly using the tokens from
your environment.

```bash
adaption-kit publish ./release \
    --hf-repo a1vara5/simple-qa \
    --kaggle-slug a1vara5/simple-qa
```

Illustrative output:

```
adaption-kit publish
------------------------------------------------------------
adaption-kit publish report
============================================================
Hugging Face : https://huggingface.co/datasets/a1vara5/simple-qa
Kaggle       : a1vara5/simple-qa
note: Adaption publish endpoint returns 501; releasing manually.
note: Kaggle datasets stay private until toggled public in the UI.
```

Then:

- Toggle the Kaggle dataset public in its settings. A private dataset does not
  count as released.
- Open both public URLs in a logged out browser to confirm they render.

## The whole loop in one place

1. `adaption-kit doctor` to confirm the setup.
2. `adaption-kit suggest qa.csv` to get the both mapping.
3. `adaption-kit lint qa.csv --prompt prompt --completion completion` to confirm the anchor is unique.
4. Upload the file to get a `DATASET_ID`.
5. `adaption-kit estimate DATASET_ID ...` to quote the cost.
6. `adaption-kit run DATASET_ID ... --pilot --max-rows 8 --wait` to pilot and read `improvement_percent`.
7. Change one knob, re-estimate, re-pilot, keep what helps, then scale.
8. `adaption-kit card` and `adaption-kit cover` for the release assets.
9. `adaption-kit publish ./release --hf-repo ... --kaggle-slug ...` and toggle Kaggle public.

Credits are real and limited. Estimate before every run, pilot small, and only
scale the config that actually moved the number.

# Math and code walkthrough: verified reasoning from raw rows to a published release

This is a full, copy and paste path for a checkable domain. You start from a raw
file of math and code problems with their solutions, check your setup, get a
column mapping, lint it, then do the thing that matters most for math and code:
**verify** that each row is actually correct before you spend a credit adapting
it. After that you decontaminate against any public benchmark, quote the cost,
run a small pilot, read the improvement number, and release to Hugging Face and
Kaggle with a card and a cover.

Every block is a real command. Every output block is marked **illustrative**: it
shows the shape of what prints, not numbers from your account. Real credit costs
and the real `improvement_percent` depend on your data and your run.

> **adaption-devkit** is a community, unofficial, open source toolkit
> (Apache-2.0) by Aivaras Navardauskas (MANIFESTA), GitHub `A1VARA5`. It is
> **not affiliated with or endorsed by Adaption Labs**. The official SDK is the
> `adaption` package; this devkit only wraps it. Always treat the official docs
> and API as the source of truth.

## Why math and code are different

Marketing data is judged on voice and variety. Math and code are judged on
**correctness**, and correctness is checkable. A math answer either equals the
gold value or it does not. A code solution either passes its unit tests or it
does not. That means two things you do not get in softer domains:

- You can prove a row is right before you pay to adapt it. Adapting a row that
  was wrong to begin with teaches the model the wrong thing, and you paid credits
  for the privilege. `adaption-kit verify` keeps only the rows that pass.
- You can prove the dataset does not overlap a public benchmark. Training on rows
  that also live in a benchmark test set inflates `improvement_percent` and does
  not survive scrutiny. `adaption-kit decontaminate` removes them.

Describe the result honestly. A dataset like this is **hybrid**: real problems
paired with **verified** solutions. It is not a pile of model output you hope is
right; it is rows you checked. And the number that counts is
`improvement_percent`, the adapted model measured against the baseline, not a
quality grade you assign to the dataset yourself.

## What you need

- Python 3.10 or newer.
- An Adaption API key.
- A Hugging Face write token and Kaggle credentials for the release step.
- A small file of problems with solutions to start with. We use a tiny mixed
  math and code set below.
- For the symbolic math check, the optional `verify` extra (sympy). Without it,
  math verification still runs on string and numeric checks and tells you so.

## 0. Install

```bash
pip install adaption-kit[all]    # the CLI plus SDK, Hugging Face, Kaggle, cover, sympy
```

If you only want the offline parts first, `pip install adaption-kit` gives you
`doctor`, `lint`, `verify`, `decontaminate`, `suggest`, `card`, and `cover`. The
SDK backed commands (`estimate`, `run`) need the `[sdk]` extra, and the symbolic
math check inside `verify` needs the `[verify]` extra (sympy). Each command tells
you what to add if an extra is missing.

```bash
# just the symbolic math check, if you do not want everything
pip install adaption-kit[verify]
```

## 1. Set your environment

Configuration is environment only. Never hardcode a key or a host in code you
plan to share. Set `ADAPTION_BASE_URL` from the environment; the host that has
been answering for participants is `https://api.prod.adaptionlabs.ai`.

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

Save this as `math_rows.jsonl`. Each row is a problem in `prompt`, a proposed
answer in `answer`, and the known correct value in `gold`. One row is wrong on
purpose, so you can watch verification catch it.

```jsonl
{"prompt": "What is 12 * 12?", "answer": "144", "gold": "144"}
{"prompt": "Solve for x: 2x + 6 = 10", "answer": "x = 2", "gold": "2"}
{"prompt": "Simplify (x^2 - 1)/(x - 1)", "answer": "x + 1", "gold": "x+1"}
{"prompt": "What is 1/2 + 1/4?", "answer": "0.75", "gold": "3/4"}
{"prompt": "What is the derivative of x^2?", "answer": "2", "gold": "2*x"}
```

The last row is wrong: the derivative of `x^2` is `2*x`, not `2`. Keep it. The
verifier should drop exactly that row.

Now save this as `code_rows.jsonl`. Each row is a problem in `prompt`, a Python
solution in `solution`, and a `tests` string that exercises it. One solution is
wrong on purpose.

```jsonl
{"prompt": "Write add(a, b).", "solution": "def add(a, b):\n    return a + b", "tests": "assert add(2, 3) == 5\nassert add(-1, 1) == 0"}
{"prompt": "Write is_even(n).", "solution": "def is_even(n):\n    return n % 2 == 0", "tests": "assert is_even(4)\nassert not is_even(3)"}
{"prompt": "Write reverse(s).", "solution": "def reverse(s):\n    return s", "tests": "assert reverse('ab') == 'ba'"}
```

The `reverse` solution returns the string unchanged, so its test fails. The
verifier should drop that row.

## 3. doctor: is my setup ready

```bash
adaption-kit doctor
```

Illustrative output:

```
   _      _             _   _               _    _ _
  /_\  __| |__ _ _ __| |_(_)___ _ _      | |__(_) |_
 / _ \/ _` / _` | '_ \  _| / _ \ ' \   _ | / / |  _|
/_/ \_\__,_\__,_| .__/\__|_\___/_||_| (_)|_\_\_|\__|
------------------------------------------------------------
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

`doctor` never makes a network call and never prints your key value. If sympy is
not installed, the symbolic math check inside `verify` is skipped and the
command says so when you run it; the string and numeric checks still run.

## 4. suggest: what is my column mapping

If you are not sure which columns are the anchor, ask the kit.

```bash
adaption-kit suggest math_rows.jsonl
```

Illustrative output:

```
adaption-kit mapping suggestion
============================================================
file        : math_rows.jsonl
format      : jsonl
rows        : 5
columns     : prompt, answer, gold

recommended anchor: prompt + completion (instruction plus answer pairs)

ready to paste column_mapping:

{
  "prompt": "prompt",
  "completion": "answer"
}

notes:
  - Recipes to consider: deduplication on almost always; reasoning_traces for
    math, code, science, legal, or finance.
  - Brand controls to consider: length to match the eval's expected answer
    depth.

Next: run 'adaption-kit lint math_rows.jsonl' to confirm the anchor is unique
before you spend credits.
```

The anchor is `prompt` plus `completion`, mapping `answer` as the completion.
The `gold` column is your verification reference, not part of the mapping. For
the code set, `solution` is the completion and `tests` is the verification
reference.

## 5. lint: catch the obvious problems before you pay

```bash
adaption-kit lint math_rows.jsonl --prompt prompt --completion answer
```

Illustrative output:

```
adaption-kit preflight report
============================================================
file        : math_rows.jsonl
format      : jsonl
encoding    : utf-8
rows        : 5
columns     : prompt, answer, gold
anchor      : prompt -> column 'prompt'
unique anchor values: 5 / 5 (100.0%)
dedup would collapse: 0 row(s)

checks:
  [PASS] loaded 5 row(s)
  [PASS] 100.0% of anchors are unique; dedup impact is minimal

RESULT: PASS
```

Lint confirms the rows load, the anchors are unique, and the dedup pass will not
quietly collapse the set. It does **not** check whether the answers are correct.
That is the next step, and for math and code it is the one that matters most.

## 6. verify: prove the rows are correct before you adapt them

This is the single biggest defense against burning credits on rows that were
wrong to begin with. Verification checks each row and, with `--out`, writes only
the rows that pass.

### Math

Math answers are checked for equivalence against the `gold` column: first a
normalized string match, then a numeric match, then a symbolic match via sympy
if the `verify` extra is installed. `0.75` and `3/4` are numerically equal;
`x + 1` and `x+1` are symbolically equal. The wrong derivative row fails all
three.

```bash
adaption-kit verify math_rows.jsonl \
    --kind math \
    --completion answer --gold gold \
    --out math_verified.jsonl
```

Illustrative output:

```
adaption-kit verify (math)
------------------------------------------------------------
checked   : 5 row(s)
passed    : 4
failed    : 1
  - row 5: 'What is the derivative of x^2?' answer '2' != gold '2*x'
symbolic check: sympy available, used for equivalence
wrote 4 verified row(s) to math_verified.jsonl

RESULT: 4 / 5 rows verified correct
```

If sympy is not installed you see `symbolic check: sympy not installed, using
string and numeric checks only`. The numeric row (`0.75` vs `3/4`) still passes;
a row that needs symbolic algebra to prove equal would be reported as unverified
so you do not silently keep something unchecked.

### Code

Code solutions are executed against their unit tests in a sandboxed subprocess
and kept only if every test passes. This is pure standard library, no extra
needed.

```bash
adaption-kit verify code_rows.jsonl \
    --kind code \
    --completion solution --tests tests \
    --out code_verified.jsonl
```

Illustrative output:

```
adaption-kit verify (code)
------------------------------------------------------------
checked   : 3 row(s)
passed    : 2
failed    : 1
  - row 3: 'Write reverse(s).' tests failed (AssertionError)
wrote 2 verified row(s) to code_verified.jsonl

RESULT: 2 / 3 rows verified correct
```

You now have `math_verified.jsonl` and `code_verified.jsonl`, holding only rows
whose solutions you proved correct. Adapt these, not the raw files. The wrong
derivative and the broken `reverse` never cost you a credit.

## 7. decontaminate: remove benchmark overlap so the number is defensible

If any of your problems also appear in a public benchmark test set, training on
them inflates `improvement_percent` and the result does not hold up. Decontaminate
removes any training row that overlaps a benchmark by an n-gram (default 13).

```bash
adaption-kit decontaminate math_verified.jsonl \
    --against gsm8k_test.jsonl math_bench_test.jsonl \
    --column answer \
    --benchmark-column answer \
    --n 13 \
    --out math_clean.jsonl
```

Illustrative output:

```
adaption-kit decontaminate
------------------------------------------------------------
training rows  : 4
benchmarks     : gsm8k_test.jsonl, math_bench_test.jsonl
n-gram size    : 13
overlapping    : 1 row(s) removed
wrote 3 clean row(s) to math_clean.jsonl

RESULT: 3 / 4 rows kept after decontamination
```

Do the same for the code set against any code benchmark you might overlap. Keep
the cleaned files. Now your dataset is verified correct **and** free of benchmark
overlap, which is exactly what makes a reported improvement defensible.

## 8. Upload the cleaned file and get a dataset id

`estimate` and `run` take a `DATASET_ID`, so you upload the cleaned file once
with the SDK and keep the id.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)
result = client.datasets.upload_file("math_clean.jsonl", name="verified-math")
dataset_id = result.dataset_id
print("dataset_id:", dataset_id)
```

Illustrative output:

```
dataset_id: ds_3b91ee07ac
```

Use that id, for example `ds_3b91ee07ac`, in the commands below.

## 9. estimate: quote the cost, start nothing

Always estimate before a run. For math and code the lever is `reasoning_traces`,
which adds auditable stepwise reasoning to each completion, plus `deduplication`.

```bash
adaption-kit estimate ds_3b91ee07ac \
    --prompt prompt --completion answer \
    --deduplication --reasoning-traces
```

Illustrative output:

```
adaption-kit estimate (no run started)
------------------------------------------------------------
estimate (no run started):
  estimated_credits_consumed: 58
  estimated_minutes        : 8
```

The credit number above is illustrative. Your real quote depends on row count,
recipes, and controls. If the mapping is wrong, this call tells you now, for
free, and you fix it before paying.

## 10. Pilot run: small max_rows first

Never run the full corpus first. Pilot with a small `--max-rows`, read the
number, and only then scale. `--wait` polls both the run and the evaluation so
you get `improvement_percent` in one shot. For math and code, `length: detailed`
is a sensible starting control to match the expected stepwise answer depth.

```bash
adaption-kit run ds_3b91ee07ac \
    --prompt prompt --completion answer \
    --pilot --max-rows 3 \
    --deduplication --reasoning-traces \
    --wait
```

Illustrative output:

```
adaption-kit run
------------------------------------------------------------
run started. run_id: run_5c2d11
waiting for run and evaluation ...
run_status        : succeeded
evaluation_status : succeeded
improvement_percent: 21.4
```

The `improvement_percent` is the headline number, and it is the adapted model
measured against the baseline, not a grade you give the dataset. It is
illustrative here; the real value depends entirely on your run. The run can
report `succeeded` before evaluation finishes, which is why the kit polls the
evaluation separately. If `improvement_percent` is not printed, evaluation was
not terminal yet; poll again.

To add a brand control such as `length`, the CLI run flags do not include brand
controls, so use the Python helper:

```python
from adaption_kit.run import estimate, pilot, wait_for_result

est = estimate(
    "ds_3b91ee07ac",
    prompt="prompt", completion="answer",
    deduplication=True, reasoning_traces=True,
    brand_controls={"length": "detailed"},
)
print(est.estimated_credits_consumed, est.estimated_minutes)

pilot(
    "ds_3b91ee07ac",
    prompt="prompt", completion="answer",
    deduplication=True, reasoning_traces=True,
    brand_controls={"length": "detailed"},
    max_rows=3,
)
result = wait_for_result("ds_3b91ee07ac")
print("improvement_percent:", result.improvement_percent)
```

## 11. Iterate, then scale

If the pilot number is low, change exactly one knob, estimate again, and re-pilot.
Keep only what raises the number. When a config wins, drop `--max-rows` (or raise
it), estimate the full corpus, and run it. Changing one thing at a time is the
only way to know what moved the score.

## 12. Read the full number, then run the full corpus

Once a pilot config wins, run the verified and decontaminated corpus in full and
read the final `improvement_percent`. That number, model versus baseline, is what
you report. It is honest precisely because you verified the rows and removed
benchmark overlap before adapting them.

## 13. Cards and a cover for the release

Generate a Hugging Face dataset card. Record the `improvement_percent` you read
above, and describe the data honestly as hybrid: real problems paired with
verified solutions, decontaminated against the benchmarks you checked.

```bash
adaption-kit card dataset \
    --title "VerifiedMath" \
    --summary "Hybrid math and code corpus: real problems with verified solutions, decontaminated against public benchmarks." \
    --tags nlp,text-generation \
    --improvement-percent 21.4 \
    --row-count 3 \
    --out ./release
```

Illustrative output:

```
adaption-kit card
------------------------------------------------------------
wrote release/README.md
```

Generate the Kaggle metadata with taxonomy tags only (`nlp`, `text generation`,
`internet`, and similar). The kit validates them and rejects anything else.

```bash
adaption-kit card kaggle \
    --title "VerifiedMath" \
    --kaggle-slug a1vara5/verified-math \
    --tags nlp,internet \
    --out ./release
```

Illustrative output:

```
adaption-kit card
------------------------------------------------------------
wrote release/dataset-metadata.json
```

Render a cover image.

```bash
adaption-kit cover ./release/cover.png \
    --title "VerifiedMath" \
    --subtitle "Math and code, verified"
```

Illustrative output:

```
adaption-kit cover
------------------------------------------------------------
cover PNG written to release/cover.png
```

Put your cleaned files (or the downloaded adapted dataset) into `./release` too,
so the folder holds the data, the card, the Kaggle metadata, and the cover.

## 14. Download the adapted dataset

Export the processed rows and add them to the release folder.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)
url = client.datasets.download("ds_3b91ee07ac")   # presigned download URL
print(url)
```

## 15. publish: release by hand to HF and Kaggle

The platform publish endpoint returns `501 Not Implemented`, so the kit does not
rely on it. `adaption-kit publish` pushes your release folder to Hugging Face and
Kaggle directly, using the tokens from your environment.

```bash
adaption-kit publish ./release \
    --hf-repo a1vara5/verified-math \
    --kaggle-slug a1vara5/verified-math
```

Illustrative output:

```
adaption-kit publish
------------------------------------------------------------
adaption-kit publish report
============================================================
Hugging Face : https://huggingface.co/datasets/a1vara5/verified-math
Kaggle       : a1vara5/verified-math
note: Adaption publish endpoint returns 501; releasing manually.
note: Kaggle datasets stay private until toggled public in the UI.
```

Two honest follow ups:

- Kaggle datasets are created **private**. Open the dataset settings on Kaggle
  and toggle it public. A private dataset does not count as released.
- Open both public URLs in a logged out browser to confirm they render.

## The whole loop in one place

1. `adaption-kit doctor` to confirm the setup.
2. `adaption-kit suggest math_rows.jsonl` to get the mapping.
3. `adaption-kit lint ... --prompt prompt --completion answer` for the obvious checks.
4. `adaption-kit verify ... --kind math --completion answer --gold gold --out ...`
   and `--kind code --completion solution --tests tests --out ...`, keeping only
   the rows that pass.
5. `adaption-kit decontaminate ... --against BENCH --out ...` to remove benchmark overlap.
6. Upload the cleaned file to get a `DATASET_ID`.
7. `adaption-kit estimate DATASET_ID ...` to quote the cost.
8. `adaption-kit run DATASET_ID ... --pilot --max-rows 3 --wait` to pilot and read `improvement_percent`.
9. Change one knob, re-estimate, re-pilot, keep what helps, then run the full corpus.
10. `adaption-kit card` and `adaption-kit cover` for the release assets.
11. `adaption-kit publish ./release --hf-repo ... --kaggle-slug ...` and toggle Kaggle public.

Describe the data honestly as hybrid: real problems with verified solutions.
The number that counts is `improvement_percent`, the adapted model against the
baseline, not a quality grade you assign yourself. Credits are real and limited.
Verify and decontaminate first, estimate before every run, pilot small, and only
scale the config that actually moved the number.

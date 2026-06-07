# Marketing walkthrough: a brand voice dataset from raw CSV to a published release

This is a full, copy and paste path. You start from a raw CSV of brand voice
examples, check your setup, get a column mapping, lint and fix a warning,
quote the cost, run a small pilot, read the improvement number, then release
to Hugging Face and Kaggle with a card and a cover.

Every block is a real command. Every output block is marked **illustrative**:
it shows the shape of what prints, not numbers from your account. Real credit
costs and the real `improvement_percent` depend on your data and your run.

> **adaption-devkit** is a community, unofficial, open source toolkit
> (Apache-2.0) by Aivaras Navardauskas (MANIFESTA), GitHub `A1VARA5`. It is
> **not affiliated with or endorsed by Adaption Labs**. The official SDK is the
> `adaption` package; this devkit only wraps it. Always treat the official docs
> and API as the source of truth.

## What you need

- Python 3.10 or newer.
- An Adaption API key.
- A Hugging Face write token and Kaggle credentials for the release step.
- A small CSV to start with. We use a brand voice corpus below.

## 0. Install

```bash
pip install adaption-kit[all]    # the CLI plus SDK, Hugging Face, Kaggle, cover
```

If you only want the offline parts first, `pip install adaption-kit` gives you
`doctor`, `lint`, `suggest`, `card`, and `cover`. The SDK backed commands
(`estimate`, `run`) need the `[sdk]` extra, and each command tells you what to
add if an extra is missing.

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

Save this as `brand_voice.csv`. It is a small instruction plus answer corpus:
a marketing request in `instruction`, the on brand reply in `response`, and a
`channel` column for context. Save it as plain UTF-8. If you edit it in Excel
and it adds a byte order mark, do not worry, the kit reads everything with
`utf-8-sig` so a BOM is stripped on input.

```csv
instruction,response,channel
Write a launch tagline for an eco friendly soap,"Clean skin, cleaner planet.",social
Draft a one line value prop for our B2B analytics tool,"See the number behind every decision, in seconds.",web
Write a launch tagline for an eco friendly soap,"Gentle on you, kind to the earth.",social
Reassure a customer whose order is late,"Your order is on its way and we are tracking it closely. Here is the latest.",email
Write a subject line for a winback email,"We saved your spot. Come see what is new.",email
Explain our refund window in one friendly sentence,"You have a full 30 days to change your mind, no questions asked.",support
Write a CTA for a free trial signup,"Start free today, upgrade only if you love it.",web
Reassure a customer whose order is late,"We are sorry for the wait. Your parcel is moving and you will have it soon.",email
```

Notice the two duplicate `instruction` rows about the eco soap tagline. That is
deliberate. The linter will catch it, because deduplication is always on at the
platform and it keys on the prompt.

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

`doctor` never makes a network call and never prints your key value. If
`ADAPTION_BASE_URL` is unset it prints a `[WARN]` that points you at
`https://api.prod.adaptionlabs.ai`, the host that has been answering, but it
still passes overall. The banner shown above is illustrative; the exact ASCII
art is cosmetic.

## 4. suggest: what is my column mapping

If you are not sure which columns are the anchor, ask the kit.

```bash
adaption-kit suggest brand_voice.csv
```

Illustrative output:

```
adaption-kit mapping suggestion
============================================================
file        : brand_voice.csv
format      : csv
rows        : 8
columns     : instruction, response, channel

recommended anchor: prompt + completion (instruction plus answer pairs)

ready to paste column_mapping:

{
  "prompt": "instruction",
  "completion": "response"
}

notes:
  - Heads up: only 75.0% of the prompt anchor values are unique, so
    deduplication (always on, keyed on the prompt) would collapse many rows.
    If the prompts are templated, consider completion only instead.
  - Recipes to consider: deduplication on almost always; prompt_rephrase for
    more prompt variety (skip it if prompts are gold and must stay verbatim);
    reasoning_traces for math, code, science, legal, or finance.
  - Brand controls to consider: length to match the eval's expected answer
    depth; blueprint for a consistent voice (good for marketing or language);
    hallucination_mitigation for fact sensitive domains.

Next: run 'adaption-kit lint brand_voice.csv' with these columns to confirm the
anchor is unique before you spend credits.
```

The suggestion is `prompt` plus `completion`, and it already warns about the
duplicate prompts. Good. It did not pick up `channel` as context because that
header is not a context style name; we will leave `channel` out of the mapping,
which is fine.

## 5. lint: catch the warning before you pay

```bash
adaption-kit lint brand_voice.csv --prompt instruction --completion response
```

Illustrative output:

```
adaption-kit preflight report
============================================================
file        : brand_voice.csv
format      : csv
encoding    : utf-8
rows        : 8
columns     : instruction, response, channel
anchor      : prompt -> column 'instruction'
unique anchor values: 6 / 8 (75.0%)
dedup would collapse: 2 row(s)

metadata fill rate:
  - instruction                   8 / 8  (100.0%)
  - response                      8 / 8  (100.0%)
  - channel                       8 / 8  (100.0%)
empty cells : 0

checks:
  [PASS] loaded 8 row(s)
  [WARN] 75.0% of anchors are unique; dedup will drop roughly 2 near duplicate row(s).

RESULT: WARN
```

The `WARN` is the deduplication collapse warning. Two rows share an
`instruction` with another row, so dedup would drop two of your eight rows
before you get any value from them. On a real corpus of thousands of rows this
is exactly how you discover that a templated set collapses to a handful.

## 6. Fix the warning

You have two honest fixes. Pick one.

**Fix A, make the prompts unique.** Edit the two duplicate eco soap rows so each
asks for something genuinely different, for example one tagline for social and
one for packaging:

```csv
Write a social tagline for an eco friendly soap,"Clean skin, cleaner planet.",social
Write packaging copy for an eco friendly soap,"Gentle on you, kind to the earth.",social
```

Do the same for the two late order rows. Then re-lint:

```bash
adaption-kit lint brand_voice.csv --prompt instruction --completion response
```

Illustrative output after the fix:

```
...
unique anchor values: 8 / 8 (100.0%)
dedup would collapse: 0 row(s)
...
checks:
  [PASS] loaded 8 row(s)
  [PASS] 100.0% of anchors are unique; dedup impact is minimal

RESULT: PASS
```

**Fix B, go completion only.** If your prompts would always be templated and
the answers are the gold, drop the prompt entirely and let the platform
synthesize a distinct prompt per answer. That maps `--completion response` with
no `--prompt`. For marketing voice corpora this is often the cleaner choice.

This walkthrough continues with **Fix A** and the both mapping. The companion
[qa_walkthrough.md](qa_walkthrough.md) shows the both mapping again on a
question and answer set.

## 7. Upload the file and get a dataset id

`estimate` and `run` take a `DATASET_ID`, so you upload the cleaned file once
with the SDK and keep the id. Read the file back BOM safe with `utf-8-sig` if
you post process it yourself.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)
result = client.datasets.upload_file("brand_voice.csv", name="brandvoice")
dataset_id = result.dataset_id
print("dataset_id:", dataset_id)
```

Illustrative output:

```
dataset_id: ds_8f3c1a2b9d
```

Use that id, for example `ds_8f3c1a2b9d`, in the commands below.

## 8. estimate: quote the cost, start nothing

Always estimate before a run. This validates your mapping and quotes credits
and minutes without spending anything. For marketing, the levers are
`prompt_rephrase` for variety and a `blueprint` voice control, so we turn
`prompt_rephrase` on here.

```bash
adaption-kit estimate ds_8f3c1a2b9d \
    --prompt instruction --completion response \
    --deduplication --prompt-rephrase
```

Illustrative output:

```
adaption-kit estimate (no run started)
------------------------------------------------------------
estimate (no run started):
  estimated_credits_consumed: 42
  estimated_minutes        : 6
```

The credit number above is illustrative. Your real quote depends on row count,
recipes, and controls. If the mapping is wrong, this call tells you now, for
free, and you fix it before paying.

## 9. Pilot run: small max_rows first

Never run the full corpus first. Pilot with a small `--max-rows`, read the
number, and only then scale. `--pilot` caps the run (default 200 rows); here we
set it small to keep the first real run cheap. `--wait` polls both the run and
the evaluation so you get `improvement_percent` in one shot.

```bash
adaption-kit run ds_8f3c1a2b9d \
    --prompt instruction --completion response \
    --pilot --max-rows 8 \
    --deduplication --prompt-rephrase \
    --wait
```

Illustrative output:

```
adaption-kit run
------------------------------------------------------------
run started. run_id: run_2a7e90
waiting for run and evaluation ...
run_status        : succeeded
evaluation_status : succeeded
improvement_percent: 17.6
```

The `improvement_percent` is the headline number. It is illustrative here; the
real value depends entirely on your run. Note that the run can report
`succeeded` before evaluation finishes, which is why the kit polls the
evaluation separately. If `improvement_percent` is not printed, evaluation was
not terminal yet; poll again.

If you prefer to add a brand voice `blueprint`, the CLI run flags do not include
brand controls, so use the Python helper for that:

```python
from adaption_kit.run import estimate, pilot, wait_for_result

est = estimate(
    "ds_8f3c1a2b9d",
    prompt="instruction", completion="response",
    deduplication=True, prompt_rephrase=True,
    brand_controls={
        "blueprint": "Warm, direct brand voice. Concrete benefits. Never over promise.",
        "length": "concise",
    },
)
print(est.estimated_credits_consumed, est.estimated_minutes)

pilot(
    "ds_8f3c1a2b9d",
    prompt="instruction", completion="response",
    deduplication=True, prompt_rephrase=True,
    brand_controls={
        "blueprint": "Warm, direct brand voice. Concrete benefits. Never over promise.",
        "length": "concise",
    },
    max_rows=8,
)
result = wait_for_result("ds_8f3c1a2b9d")
print("improvement_percent:", result.improvement_percent)
```

## 10. Iterate, then scale

If the pilot number is low, change exactly one knob (a recipe or a brand
control), estimate again, and re-pilot. Keep only what raises the number. When
a config wins, drop `--max-rows` (or raise it), estimate the full corpus, and
run it. Changing one thing at a time is the only way to know what moved the
score.

## 11. Cards and a cover for the release

Generate a Hugging Face dataset card. Record the `improvement_percent` you read
above so the number is visible and reproducible.

```bash
adaption-kit card dataset \
    --title "BrandVoice" \
    --summary "Adapted marketing brand voice corpus." \
    --tags marketing,nlp \
    --improvement-percent 17.6 \
    --row-count 8 \
    --out ./release
```

Illustrative output:

```
adaption-kit card
------------------------------------------------------------
wrote release/README.md
```

Generate the Kaggle metadata. Kaggle accepts taxonomy tags only, so use tags
from the accepted set (`marketing`, `nlp`, `text generation`, `business`,
`internet`). The kit validates them and rejects anything else.

```bash
adaption-kit card kaggle \
    --title "BrandVoice" \
    --kaggle-slug a1vara5/brandvoice \
    --tags marketing,business \
    --out ./release
```

Illustrative output:

```
adaption-kit card
------------------------------------------------------------
wrote release/dataset-metadata.json
```

Render a cover image. With Playwright installed this writes a PNG; without it
the kit writes the HTML next to the PNG path so the command never hard fails.

```bash
adaption-kit cover ./release/cover.png \
    --title "BrandVoice" \
    --subtitle "Marketing, Part 1"
```

Illustrative output:

```
adaption-kit cover
------------------------------------------------------------
cover PNG written to release/cover.png
```

Put your cleaned CSV (or the downloaded adapted dataset) into `./release` too,
so the folder holds the data, the card, the Kaggle metadata, and the cover.

## 12. Download the adapted dataset

Export the processed rows and add them to the release folder. Resave as plain
UTF-8 with no BOM so neither host chokes on the first column.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)
url = client.datasets.download("ds_8f3c1a2b9d")   # presigned download URL
print(url)
```

## 13. publish: release by hand to HF and Kaggle

The platform publish endpoint returns `501 Not Implemented`, so the kit does
not rely on it. `adaption-kit publish` pushes your release folder to Hugging
Face and Kaggle directly, using the tokens from your environment.

```bash
adaption-kit publish ./release \
    --hf-repo a1vara5/brandvoice \
    --kaggle-slug a1vara5/brandvoice
```

Illustrative output:

```
adaption-kit publish
------------------------------------------------------------
adaption-kit publish report
============================================================
Hugging Face : https://huggingface.co/datasets/a1vara5/brandvoice
Kaggle       : a1vara5/brandvoice
note: Adaption publish endpoint returns 501; releasing manually.
note: Kaggle datasets stay private until toggled public in the UI.
```

Two honest follow ups:

- Kaggle datasets are created **private**. Open the dataset settings on Kaggle
  and toggle it public. A private dataset does not count as released.
- Open both public URLs in a logged out browser to confirm they render.

## The whole loop in one place

1. `adaption-kit doctor` to confirm the setup.
2. `adaption-kit suggest brand_voice.csv` to get the mapping.
3. `adaption-kit lint ... --prompt instruction --completion response` and fix the warning.
4. Upload the cleaned file to get a `DATASET_ID`.
5. `adaption-kit estimate DATASET_ID ...` to quote the cost.
6. `adaption-kit run DATASET_ID ... --pilot --max-rows 8 --wait` to pilot and read `improvement_percent`.
7. Change one knob, re-estimate, re-pilot, keep what helps, then scale.
8. `adaption-kit card` and `adaption-kit cover` for the release assets.
9. `adaption-kit publish ./release --hf-repo ... --kaggle-slug ...` and toggle Kaggle public.

Credits are real and limited. Estimate before every run, pilot small, and only
scale the config that actually moved the number.

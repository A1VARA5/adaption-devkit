# Gotchas and troubleshooting

Field notes from real runs, to read alongside the official docs. Each entry is symptom,
cause, fix. These are the small mistakes that quietly waste credits, time, or a submission,
the kind you usually only learn by hitting them once.

> **adaption-devkit** is a community, unofficial toolkit (Apache-2.0) by Aivaras
> Navardauskas (MANIFESTA), GitHub `A1VARA5`. Not affiliated with or endorsed by
> Adaption Labs. Behavior described here was observed in practice and may change;
> always re-verify against your account before a final run.

## 1. Rows vanish: deduplication collapse

**Symptom.** You upload thousands of rows but the run processes a fraction of
them. Many rows seem to disappear.

**Cause.** Deduplication is **always on** and it keys on the **prompt**. If you
built your data from a template where the prompt text is identical across rows and
only the `context` varies, every row past the first looks like a duplicate prompt
and gets dropped. Variety that lives only in `context` does not save the row.

**Fix.** Make each anchor unique. Either:

- Write genuinely distinct prompts per row, or
- Go **completion only**: map only `completion` and let the platform synthesize a
  distinct prompt for each high quality answer.

Run `adaption-kit lint data.csv` first. The linter flags duplicate prompt columns
so you catch the collapse before spending credits.

## 2. A run cost more than expected: you skipped the estimate

**Symptom.** Credits dropped faster than you planned. The hackathon budget is
limited and you burned a chunk on one run.

**Cause.** You called `datasets.run(...)` with `estimate=False` (the default once
you remove the flag) before quoting the cost, or you ran the full corpus instead
of a pilot.

**Fix.** Always quote first, then pilot.

```python
quote = client.datasets.run(dataset_id, column_mapping=mapping, estimate=True)
print(quote.estimated_credits_consumed, quote.estimated_minutes)
```

Then run a pilot with `job_specification={"max_rows": 300}` and only scale the one
config that actually moved `improvement_percent`. Change one knob at a time so you
can attribute the change.

## 3. improvement_percent is empty: evaluation is a separate job

**Symptom.** The run says `succeeded` but `improvement_percent` is `None`, empty,
or missing.

**Cause.** Evaluation runs on its **own schedule**, independent of the adaptation
run. `get_status` does not include evaluation. A run can finish well before its
evaluation does.

**Fix.** Poll `get_evaluation` separately until it reaches a terminal state.

```python
import time
ev = client.datasets.get_evaluation(dataset_id)
while ev.status in ("pending", "running"):
    time.sleep(5)
    ev = client.datasets.get_evaluation(dataset_id)
if ev.status == "succeeded" and ev.quality:
    print(ev.quality.improvement_percent)
```

## 4. publish returns 501

**Symptom.** Calling the publish endpoint (or `adaption-kit publish` against it)
returns `501 Not Implemented`.

**Cause.** The server-side publish endpoint is not implemented yet. It cannot push
to Hugging Face or Kaggle for you.

**Fix.** Release by hand. `download` the processed dataset and push it to Hugging
Face and Kaggle yourself with `huggingface_hub` and the `kaggle` CLI. The
`adaption-kit publish` command in this devkit generates the cards and metadata and
walks you through the manual upload rather than relying on the dead endpoint. See
[release-checklist.md](release-checklist.md). Re-check the endpoint before your
final submission in case it ships.

## 5. Garbled first column or stray characters: BOM encoding

**Symptom.** The first header or the first cell has invisible junk in front of it
(often shown as a `ï»¿` prefix), or the first column name fails to match your
column mapping even though it looks correct.

**Cause.** The file was saved as UTF-8 **with a BOM** (byte order mark), commonly
by Excel or some Windows editors. The BOM bytes get attached to the first field.

**Fix.** Read with `utf-8-sig` so the BOM is stripped on input, and write plain
`utf-8` with **no BOM** on output.

```python
import csv

with open("in.csv", encoding="utf-8-sig", newline="") as f:
    rows = list(csv.DictReader(f))

with open("out.csv", "w", encoding="utf-8", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)
```

`adaption-kit lint data.csv` warns when it detects a BOM so you can resave before
uploading.

## 6. Kaggle rejects your tags

**Symptom.** Kaggle refuses your dataset metadata or strips your tags, complaining
they are invalid.

**Cause.** Kaggle only accepts tags from its own **taxonomy**. Free-form tags such
as your project name or model name are not valid. Valid taxonomy tags for this kind
of work include `marketing`, `nlp`, `text generation`, `business`, and `internet`.

**Fix.** Use only taxonomy tags. `adaption-kit` generates Kaggle metadata with
taxonomy safe tags by default. Do not invent tags. If you need a custom label, put
it in the title or description, not the tag list.

## 7. Your published dataset is invisible: private by default

**Symptom.** You uploaded to Kaggle but reviewers or teammates cannot see it.

**Cause.** Kaggle datasets are created **private** by default.

**Fix.** Toggle the dataset to public in the Kaggle dataset settings after upload.
For the hackathon a private dataset does not count as released. Confirm the public
toggle is on, then open the public URL in a logged out browser to verify.

## 8. A 503 or connection error on the default host

**Symptom.** Requests return 503, time out, or never respond, even with a valid key.

**Cause.** The host the SDK and the docs point to is not always the host your account
actually talks to. One can return 503 while the other answers normally. This catches
almost everyone on the first run, and it is easy to mistake for a key or network problem.

**Fix.** Do not hardcode a host. Set `ADAPTION_BASE_URL` in the environment and pass it
through. The host that has been answering for participants is
`https://api.prod.adaptionlabs.ai`, so start there if the default returns 503:

```python
import os
from adaption import Adaption
client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],  # e.g. https://api.prod.adaptionlabs.ai
    api_key=os.environ["ADAPTION_API_KEY"],
)
```

Reading the host from an environment variable means you can switch it later without
touching code, which matters because it can change. Never commit a base URL or an API
key to source control. Keep both in environment variables or a local `.env` that git ignores.

## 9. chat conflicts with prompt/completion

**Symptom.** The run rejects your column mapping or behaves oddly when you map
`chat` alongside `prompt` or `completion`.

**Cause.** `chat` is **mutually exclusive** with `prompt`, `completion`, and
`context`. You cannot mix conversational mapping with the prompt/completion anchors.

**Fix.** Choose one shape. Use `chat` for multi turn conversations on its own, or
use `prompt`/`completion`/`context` for instruction-style data. See
[column-mapping.md](column-mapping.md).

## 10. reasoning_traces in the wrong place

**Symptom.** `reasoning_traces` appears to do nothing, or the run rejects your
`brand_controls`.

**Cause.** `reasoning_traces` is a **recipe**, not a brand control. It belongs in
`recipe_specification.recipes`, not in `brand_controls`.

**Fix.**

```python
recipe_specification={"recipes": {"reasoning_traces": True, "deduplication": True}}
```

Brand controls are `blueprint`, `length`, `safety_categories`, and
`hallucination_mitigation`. See [recipes-and-controls.md](recipes-and-controls.md).

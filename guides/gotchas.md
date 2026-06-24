# Gotchas and troubleshooting

Field notes from real runs, to read alongside the official docs. Each entry is symptom,
cause, fix. These are the small mistakes that quietly waste credits, time, or a submission,
the kind you usually only learn by hitting them once.

> **adaption-devkit** is a community, unofficial toolkit (Apache-2.0) by Aivaras
> Navardauskas (MANIFESTA), GitHub `A1VARA5`. Not affiliated with or endorsed by
> Adaption Labs. Behavior described here was observed in practice and may change;
> always reverify against your account before a final run.

Last checked: June 2026. If a fix here no longer matches what you see, please open
an issue so it can be corrected.

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

## 11. You changed five things and cannot tell what moved the score

**Symptom.** You enabled `reasoning_traces`, added a `length` control, rewrote half
your prompts, swapped the column mapping, and bumped `max_rows`, all in one run.
`improvement_percent` moved, but you have no idea which change did it, so your next
run is a guess.

**Cause.** More than one lever changed between two runs. With several variables in
play at once, the result is unattributable. You cannot keep the part that helped or
drop the part that hurt because you do not know which part is which.

**Fix.** Change one lever at a time. Pick a baseline config, run a small pilot, read
the number, then change exactly one thing and pilot again. Keep the change only if
the number went up. It feels slower but it is faster, because every run teaches you
something instead of leaving you to guess. This also protects your credits: you stop
paying for runs whose result you cannot interpret.

## 12. doctor or run reports 503 on the documented host

**Symptom.** `adaption-kit doctor` or a run says the host is unreachable or returns
503, even though your key is valid and your network is fine.

**Cause.** The documented default host is not always the host your account talks to.
One can return 503 while the other answers normally. See entry 8 above for the same
root cause from the SDK side; this entry is the same trap seen through the CLI.

**Fix.** Set `ADAPTION_BASE_URL` in your environment before you run `doctor` so the
CLI checks the host that actually answers:

```bash
export ADAPTION_BASE_URL="https://api.prod.adaptionlabs.ai"
adaption-kit doctor
```

If `doctor` is green on `https://api.prod.adaptionlabs.ai` but red on the documented
default, that is the bug, not your setup. Keep the working host in the environment so
every command picks it up.

## 13. Your local CSV and JSONL disagree on row count after an edit

**Symptom.** You keep a CSV and a JSONL of the same dataset side by side, edit one,
and a later run or lint processes a different number of rows than you expected
because the two files drifted apart.

**Cause.** Two copies of the same data in two formats fall out of sync the moment you
edit one and forget the other. Nothing forces them to match.

**Fix.** Treat one file as the source of truth and regenerate the other from it,
rather than hand editing both. Run `adaption-kit lint` on whichever file you are
about to upload, not on the stale copy. The linter reports the row count and the
columns it sees, so a quick lint on each file makes drift obvious before you pay for
a run on the wrong one.

## 14. Empty or whitespace only completions silently weaken a run

**Symptom.** The run succeeds and processes your rows, but the quality gain is
smaller than the same dataset earned before, and you cannot see why in the data.

**Cause.** A handful of rows have an empty `completion`, or a completion that is only
quotes, whitespace, or a stray delimiter left over from a spreadsheet export. They
pass as rows but carry no usable answer, so they dilute the signal the platform
learns from.

**Fix.** Lint before every run. `adaption-kit lint data.csv` flags empty anchors and
whitespace only completions so you can drop or fix them first. Completion only data
lives and dies on the quality of each answer, so a few blank ones cost more than
their share.

## 15. Adapting unverified rows wastes credits

**Symptom.** You adapt a math or code dataset, the run succeeds, and
`improvement_percent` is flat or worse than a cleaner set earned, even though the
recipes looked right.

**Cause.** Some of the rows were wrong to begin with. A math answer that does not
match the gold value, or a code solution that fails its own tests, teaches the model
the wrong thing, and you paid credits to do it. A second cause is benchmark overlap:
rows that also appear in a public benchmark test set inflate the number and do not
survive scrutiny.

**Fix.** Adapting unverified rows wastes credits. For checkable domains run
`adaption-kit verify` first and adapt only the rows that pass; run
`adaption-kit decontaminate` against any public benchmark so the number is
defensible.

```bash
adaption-kit verify rows.jsonl --kind math --completion answer --gold gold --out verified.jsonl
adaption-kit verify rows.jsonl --kind code --completion solution --tests tests --out verified.jsonl
adaption-kit decontaminate verified.jsonl --against bench.jsonl --out clean.jsonl
```

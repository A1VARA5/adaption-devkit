# Examples

Two fully worked, copy and paste walkthroughs. Each one takes you the whole way,
from a raw CSV to a published release on Hugging Face and Kaggle, using the real
`adaption-kit` commands in the order you would actually run them.

Both walkthroughs are honest about what is real and what is illustrative. The
commands are real. The output blocks are marked **illustrative**: they show the
shape of what prints, not numbers from your account. Real credit costs and the
real `improvement_percent` depend on your data and your run.

> **adaption-devkit** is a community, unofficial, open source toolkit
> (Apache-2.0) by Aivaras Navardauskas (MANIFESTA), GitHub `A1VARA5`. It is
> **not affiliated with or endorsed by Adaption Labs**. Always treat the
> official docs and API as the source of truth.

## The walkthroughs

| File | What it teaches | Mapping shape |
|------|------------------|---------------|
| [marketing_walkthrough.md](marketing_walkthrough.md) | The full path on a brand voice marketing dataset, including a deduplication collapse warning and two honest ways to fix it, plus a brand voice `blueprint` brand control. | `prompt` + `completion` (with a fix), or `completion` only |
| [qa_walkthrough.md](qa_walkthrough.md) | The same end to end path on a plain question and answer dataset where every row is already unique. The clean **both** mapping case. | `prompt` + `completion` (both) |

## What each one covers

Both walkthroughs walk the same lifecycle so you can see the whole thing once
and trust it:

1. **doctor** to confirm your Python, SDK, env vars, and host are ready.
2. **suggest** to get a ready to paste column mapping from your file.
3. **lint** to catch the deduplication collapse before you spend credits.
   (Deduplication is always on and keys on the prompt.)
4. **fix** the warning, then re-lint to confirm it is gone.
5. Upload the file to get a `DATASET_ID`.
6. **estimate** to quote credits and minutes, starting nothing.
7. **run** a small pilot with `--max-rows` and `--wait`.
8. Poll for **improvement_percent** (evaluation runs separately from the run).
9. **card** and **cover** to build the release assets.
10. **publish** to Hugging Face and Kaggle by hand, because the platform publish
    endpoint returns `501`.

## Who this is for

- A newcomer or a student who wants to see the whole path once, end to end,
  before spending any credits.
- Anyone deciding which column mapping fits their data: start with the QA
  walkthrough for the clean both case, then read the marketing one for the
  templated prompt trap and how to escape it.
- Anyone who wants the exact commands and the order to run them in, without
  guessing.

## Before you start

Set your environment variables (never hardcode a key or a host). The host that
has been answering for participants is `https://api.prod.adaptionlabs.ai`.

```bash
export ADAPTION_BASE_URL="https://api.prod.adaptionlabs.ai"
export ADAPTION_API_KEY="pt_live_your_key_here"
```

On Windows PowerShell:

```powershell
$env:ADAPTION_BASE_URL = "https://api.prod.adaptionlabs.ai"
$env:ADAPTION_API_KEY  = "pt_live_your_key_here"
```

Then install the kit and open a walkthrough:

```bash
pip install adaption-kit[all]
```

For the bigger picture, see the [guides](../guides/) folder:
[quickstart](../guides/quickstart.md),
[column-mapping](../guides/column-mapping.md),
[recipes-and-controls](../guides/recipes-and-controls.md),
[gotchas](../guides/gotchas.md), and
[release-checklist](../guides/release-checklist.md).

## A standing reminder on credits

Credits are real and limited. Estimate before every run, pilot with a small
`max_rows`, read the number, change one knob at a time, and only scale the
config that actually moved `improvement_percent`.

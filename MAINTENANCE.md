# How current is this kit?

Last checked: June 2026.

This page is an honest account of what has actually been run versus what is
written to be correct but has not yet been exercised against the live platform.
adaption-devkit is a community, unofficial project. It is not affiliated with or
endorsed by Adaption Labs. The platform moves, so some of what is here will drift
over time. If something below stops matching reality, please open an issue and it
will be fixed. We would rather be told than quietly be wrong.

## What "verified" means here

Two honest categories, and we try not to blur them:

- **Verified by running.** The command or generator was run locally against real
  files and produced the expected output. No live credits or network were needed
  to confirm it works.
- **Correct by construction, not yet run live.** The code follows the documented
  SDK and REST behavior and reads correctly, but it has not been run end to end
  against the live API because doing so spends real credits. Treat these as
  carefully written but unproven until someone runs them with a funded account.

## Status table

| Part | Status | How it was checked |
|------|--------|--------------------|
| `lint` (preflight linter) | Verified by running | Run on local CSV and JSONL; flags dedup collapse, BOM, and empty anchors. Pure standard library, no network. |
| `doctor` | Verified by running | Run locally; reports Python version, SDK presence, env vars, and host reachability. |
| `suggest` | Verified by running | Run on local files; prints a recommended column mapping. Reads the file only. |
| `card` (card and metadata generators) | Verified by running | Generated dataset cards, model cards, and Kaggle metadata locally and inspected the output. |
| `cover` (cover image generator) | Verified by running | Rendered a cover image locally and inspected it. |
| `estimate` | Correct by construction, not yet run live | Wraps the SDK estimate call. Reads correctly against the documented SDK but needs a funded account to confirm the quote shape. |
| `run` (adaptation run helper) | Correct by construction, not yet run live | Needs real credits to run end to end. Written to estimate first, pilot small, and poll evaluation, but not yet exercised against the live API. |
| `publish` (release helper) | Correct by construction, not yet run live | The platform publish endpoint returns 501, so this packages a manual release for Hugging Face and Kaggle. The packaging is exercised locally; the live release is done by hand and depends on your own accounts. |

## A few things known to be true as of the last check

These are the facts the kit is built around. They were true when last checked and
may change, so reverify before a final run:

- Deduplication is always on and keys on the prompt. Variety that lives only in a
  context column does not save a row from being collapsed.
- The publish endpoint returns 501, so you release to Hugging Face and Kaggle by
  hand. The kit packages the release rather than relying on the dead endpoint.
- Evaluation runs as a separate job. A run can report succeeded while
  `improvement_percent` is still empty; poll the evaluation separately.
- Kaggle datasets are created private. They stay invisible until you flip them
  public in the dataset settings.
- Read input files with `utf-8-sig` so a byte order mark does not break a loader
  or a column match.
- Set `ADAPTION_BASE_URL` from the environment. The host that has been answering
  for participants is `https://api.prod.adaptionlabs.ai`; the documented default
  can return 503.

## If something here is wrong

This is a community project and the platform moves. If a command, a fact, or a fix
on this page no longer matches what you see, please open an issue so it can be
corrected. Concrete reports, with the command you ran and what you got back, are
the fastest way to keep this honest.

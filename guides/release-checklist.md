# Release checklist: shipping to Hugging Face and Kaggle by hand

The platform `publish` endpoint returns `501 Not Implemented`, so you release your
adapted dataset and weights manually. This guide is the step by step, plus a
pre-submission checklist.

> **adaption-devkit** is a community, unofficial toolkit (Apache-2.0) by Aivaras
> Navardauskas (MANIFESTA), GitHub `A1VARA5`. Not affiliated with or endorsed by
> Adaption Labs.

## Why manual

`POST /publish` (and any `adaption-kit publish` call that targets it) returns
`501`. It cannot push to Hugging Face or Kaggle for you. The `adaption-kit publish`
command in this devkit instead generates the dataset card, model card, and Kaggle
metadata, then walks you through the manual upload. Re-check the endpoint before
your final submission in case it ships.

## Step 0: export the adapted dataset

Download the processed rows with the SDK, then verify them.

```python
import os
from adaption import Adaption

client = Adaption(
    base_url=os.environ["ADAPTION_BASE_URL"],
    api_key=os.environ["ADAPTION_API_KEY"],
)
url = client.datasets.download(dataset_id)   # presigned download URL
print(url)
```

Save the file locally. Read it back with `utf-8-sig` and resave as plain `utf-8`
with no BOM so neither Hugging Face nor Kaggle chokes on the first column. See
[gotchas.md](gotchas.md) on BOM encoding.

## Step 1: generate cards and metadata

```bash
adaption-kit publish ./adapted_dataset.csv
```

This produces:

- `README.md` dataset card (Hugging Face front matter plus description),
- a model card if you are releasing weights,
- `dataset-metadata.json` for Kaggle, with **taxonomy safe tags only**.

Record your `improvement_percent` in the cards. The AutoScientist Challenge
requires a measurable percentage improvement versus the baseline, so make it
visible and reproducible.

## Step 2: release to Hugging Face

```bash
pip install huggingface_hub
huggingface-cli login   # paste a write token
```

Upload the dataset (and weights, if any):

```bash
huggingface-cli upload <your-username>/<repo-name> ./adapted_dataset.csv
huggingface-cli upload <your-username>/<repo-name> ./README.md
```

Or push a whole folder:

```bash
huggingface-cli upload <your-username>/<repo-name> ./release_folder --repo-type=dataset
```

Then open the public Hugging Face URL in a logged out browser to confirm it is
visible and the card renders.

## Step 3: release to Kaggle

```bash
pip install kaggle
# Put kaggle.json (API token) in ~/.kaggle/ (or %USERPROFILE%\.kaggle\ on Windows)
```

Use the generated `dataset-metadata.json`. Tags must come from the Kaggle
**taxonomy** only. Valid tags for this kind of work include `marketing`, `nlp`,
`text generation`, `business`, and `internet`. Do not invent tags or use your
project name as a tag.

```bash
kaggle datasets create -p ./release_folder
```

To update an existing dataset:

```bash
kaggle datasets version -p ./release_folder -m "Adapted with Adaptive Data, +X.X% improvement"
```

**Kaggle datasets are private by default.** Open the dataset settings on Kaggle and
toggle it to public. A private dataset does not count as released. Verify by opening
the public URL in a logged out browser.

## Pre-submission checklist

Tick every box before you submit.

- [ ] You ran `estimate=True` before the final real run and the cost was expected.
- [ ] The winning config was chosen by changing one knob at a time on pilots.
- [ ] `get_evaluation(...).status == "succeeded"` and you recorded
      `improvement_percent`.
- [ ] The improvement is a measurable percentage versus a stated baseline, and it
      is reproducible.
- [ ] The dataset was exported with `download` and resaved as plain `utf-8`
      (no BOM).
- [ ] Hugging Face release is **public** and the dataset card renders, with the
      improvement number stated.
- [ ] Kaggle release uses **taxonomy tags only** and is toggled **public**.
- [ ] Both public URLs open in a logged out browser.
- [ ] No API key, write token, or internal base URL is committed anywhere in the
      release or the repo.
- [ ] `ADAPTION_BASE_URL` and `ADAPTION_API_KEY` are read from the environment, not
      hardcoded.
- [ ] Cards state clearly that adaption-devkit is community and unofficial, not
      affiliated with or endorsed by Adaption Labs.
- [ ] You re-checked whether the `publish` endpoint still returns `501` (in case it
      shipped and you can use it instead).

## If something is wrong

- 501 from publish: expected. Release by hand as above.
- Kaggle rejects tags: use taxonomy tags only.
- Dataset invisible: it is private. Toggle public.
- Garbled first column: BOM. Resave as plain `utf-8`.

See [gotchas.md](gotchas.md) for the full troubleshooting list.

# adaption-devkit templates

Ready to-use templates for starting with Adaption Adaptive Data and AutoScientist. Community and
unofficial. Apache-2.0. Author Aivaras Navardauskas (MANIFESTA), GitHub A1VARA5. Not affiliated with
or endorsed by Adaption Labs, Hugging Face, or Kaggle.

Everything here is generic and reusable by anyone. Copy a template, replace the PLACEHOLDER values,
and you have a dataset, a release card, a Kaggle manifest, and a cover image ready to go.

## What is here

```
templates/
  dataset_schemas/         starter CSV and JSONL schemas with example rows, plus a sidecar README
    marketing.csv / .jsonl
    math-and-code.csv / .jsonl
    finance.csv / .jsonl
    qa.csv / .jsonl
    qa_completion_only.jsonl
    README.md              the anchor rule, dedup collapse risk, mappings, recipes per domain
  dataset_card.md          Hugging Face dataset card with YAML frontmatter and placeholders
  model_card.md            Hugging Face model card for LoRA or fine tuned weights
  kaggle-dataset-metadata.json   Kaggle dataset-metadata.json starter
  kaggle-metadata-README.md      the tag rules and publishing steps for Kaggle
  cover/
    cover.html             brandless dark 1200x630 cover, renders to PNG
    README.md              how to customize and render the cover
  README.md                this file
```

## Core concepts baked into these templates

- Anchor: every Adaption run needs a `prompt` column or a `completion` column. Completion only is a
  high quality answers corpus from which the platform synthesizes prompts.
- `context` is an optional list of grounding columns.
- Deduplication is always on and keys on the `prompt`. Templated prompts can collapse into
  near duplicates and get dropped. Favor unique anchors, the completion only shape, or
  `prompt_rephrase`.
- Recipes: `deduplication`, `prompt_rephrase`, `reasoning_traces`. `reasoning_traces` is a recipe,
  not a brand control.
- brand_controls: `blueprint`, `length`, `safety_categories`, `hallucination_mitigation`.
- Kaggle accepts only valid taxonomy tags (marketing, nlp, text generation, business, internet).
  New datasets are private until you toggle them public.
- Write all files as plain UTF-8 with no byte order mark.

## Step by step

### 1. Pick and fill a dataset schema

1. Open `dataset_schemas/` and copy the CSV or JSONL for your domain (marketing, math-and-code,
   finance, qa).
2. Replace the example rows with your data, keeping the column shape.
3. Read `dataset_schemas/README.md` for the column mapping and the recommended recipes and
   brand_controls for your domain.

### 2. Adapt with Adaption

Upload, estimate, pilot, then run the full corpus.

```python
from adaption import Adaption

client = Adaption(api_key="pt_live_...")
ds = client.datasets.upload_file("your-data.jsonl", name="your-name")

# Estimate first.
client.datasets.run(
    ds.dataset_id,
    column_mapping={"prompt": "prompt", "completion": "completion", "context": ["context"]},
    recipe_specification={"recipes": {"deduplication": True, "prompt_rephrase": True}},
    brand_controls={"length": "concise"},
    estimate=True,
)
```

Then pilot with `job_specification={"max_rows": 300}`, read
`get_evaluation(ds.dataset_id).quality.improvement_percent`, change one lever, and keep what helps.

### 3. Write the cards

- Copy `dataset_card.md` to your dataset repo as `README.md` and fill the placeholders.
- If you release weights, copy `model_card.md` to your model repo as `README.md` and fill it.

### 4. Make the cover

- Open `cover/cover.html`, replace the placeholders, and render to PNG using `cover/README.md`.
- Use the PNG as the card image on Hugging Face and the cover on Kaggle.

### 5. Publish

- Hugging Face: push the data file and the dataset card with `huggingface_hub`, then add the cover.
- Kaggle: copy `kaggle-dataset-metadata.json` next to your data as `dataset-metadata.json`, set
  valid taxonomy tags, run `kaggle datasets create -p ./folder`, then toggle the dataset public. See
  `kaggle-metadata-README.md`.

Note: the Adaption `publish` endpoint may not be available, so plan to download the adapted dataset
and push to Hugging Face and Kaggle yourself.

## License

Apache-2.0. Reuse freely, including commercially, with attribution per the license.

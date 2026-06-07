# Kaggle dataset metadata template

`kaggle-dataset-metadata.json` is a starter `dataset-metadata.json` for publishing a dataset with
the Kaggle CLI. Community, unofficial, Apache-2.0. Not affiliated with or endorsed by Kaggle or
Adaption Labs.

## The tag rule (important)

Kaggle does not accept arbitrary tags. The `keywords` array accepts only valid Kaggle taxonomy
tags, and an invalid tag makes the upload fail or silently drop the tag. Known-valid tags for this
kind of dataset:

- `marketing`
- `nlp`
- `text generation`
- `business`
- `internet`

Pick the subset that actually describes your data. Do not invent tags. If you need a tag not listed
here, confirm it exists in the Kaggle taxonomy before using it.

## Fields to replace

- `title`: human-readable title shown on the dataset page.
- `id`: must be `your-kaggle-username/your-dataset-slug`. The slug is lowercase with hyphens.
- `licenses`: keep `Apache 2.0` unless an upstream source requires otherwise. Use a name from
  Kaggle's accepted license list.
- `keywords`: valid taxonomy tags only (see above).
- `resources`: one entry per data file. Set `path` to the filename as it sits next to this JSON,
  add a `description`, and list the `schema.fields` so Kaggle shows column docs.

## Privacy default

New Kaggle datasets are private until you toggle them public. The hackathon requires a public
release, so remember to flip visibility to public after the upload succeeds and you have confirmed
the files and card look right.

## Publishing steps

1. Put `dataset-metadata.json` (this template, renamed) in a folder next to your data file or files.
2. Add a cover image and a dataset card for a good release (see the cover and dataset_card
   templates).
3. Create the dataset:

   ```bash
   kaggle datasets create -p ./your-folder
   ```

4. To push an update later:

   ```bash
   kaggle datasets version -p ./your-folder -m "PLACEHOLDER changelog note"
   ```

5. Toggle the dataset to public from the dataset settings page when ready.

## Encoding

Save this JSON and all data files as plain UTF-8 with no byte order mark.

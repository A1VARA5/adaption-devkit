# Dataset schema starters

Community, unofficial starter schemas for Adaption Adaptive Data. Apache-2.0. Author Aivaras
Navardauskas (MANIFESTA), GitHub A1VARA5. These are reference shapes only. They are not affiliated
with or endorsed by Adaption Labs.

Each domain ships a CSV and a matching JSONL with a few example rows. Pick whichever format your
tooling prefers. Adaption accepts `.csv`, `.json`, `.jsonl`, and `.parquet`.

## The anchor rule (read this first)

Every run needs at least one anchor column: a `prompt` column OR a `completion` column.

- `prompt` + `completion`: instruction and answer pairs. The most common shape. Both get adapted.
- `prompt` only: the platform generates completions for you.
- `completion` only: a high quality answers corpus. The platform synthesizes matching prompts. See
  `qa_completion_only.jsonl` for this shape.
- `context`: an optional list of grounding columns (passages, brand notes, references). In JSONL it
  is a JSON array. In CSV, keep it a single column and split values yourself downstream, or map
  several CSV columns to `context` as a list in your run config.

## Deduplication and the templated prompt collapse risk

Deduplication is always on and it keys on the `prompt`. If your prompts are templated and only a
variable slot changes (for example "Write a tweet about {product}"), many rows can be treated as
near duplicates and dropped, which shrinks your usable corpus and wastes credits.

Mitigations:

- Favor genuinely unique prompts, or
- Use the `completion`-only shape so the platform synthesizes varied prompts for you, or
- Turn on `prompt_rephrase` to diversify prompts (skip it if prompts must stay verbatim).

## Column mapping per file

When you call `datasets.run`, map your columns. Examples below assume the column names in these
templates.

| File | column_mapping |
|------|----------------|
| `marketing.*` | `{"prompt": "prompt", "completion": "completion", "context": ["context"]}` |
| `math-and-code.*` | `{"prompt": "prompt", "completion": "completion"}` |
| `finance.*` | `{"prompt": "prompt", "completion": "completion", "context": ["context"]}` |
| `qa.*` | `{"prompt": "prompt", "completion": "completion", "context": ["context"]}` |
| `qa_completion_only.jsonl` | `{"completion": "completion"}` |

## Recommended recipes and brand_controls per domain

Start here, then change one lever at a time and keep what lifts `improvement_percent`. `length`
values are `minimal`, `concise`, `detailed`, `extensive`. `reasoning_traces` is a recipe, not a
brand control.

### marketing

- recipes: `deduplication: true`, `prompt_rephrase: true`
- brand_controls: `blueprint` for voice, tone, and target language, `length` to taste
- why: marketing wins on voice and diversity, not stepwise reasoning

```json
{
  "column_mapping": {"prompt": "prompt", "completion": "completion", "context": ["context"]},
  "recipe_specification": {"recipes": {"deduplication": true, "prompt_rephrase": true}},
  "brand_controls": {"blueprint": "PLACEHOLDER voice, tone, and audience as a system prompt.", "length": "concise"}
}
```

### math-and-code

- recipes: `deduplication: true`, `reasoning_traces: true`
- brand_controls: `length: detailed`
- why: correct stepwise reasoning is the lever, and an objective eval makes the gain defensible

```json
{
  "column_mapping": {"prompt": "prompt", "completion": "completion"},
  "recipe_specification": {"recipes": {"deduplication": true, "reasoning_traces": true}},
  "brand_controls": {"length": "detailed"}
}
```

### finance

- recipes: `deduplication: true`, `reasoning_traces: true`
- brand_controls: `hallucination_mitigation: true`, `length: detailed`, `safety_categories` per your
  policy (treat the API schema as the source of truth for category names)
- why: grounding is the lever for fact sensitive domains

```json
{
  "column_mapping": {"prompt": "prompt", "completion": "completion", "context": ["context"]},
  "recipe_specification": {"recipes": {"deduplication": true, "reasoning_traces": true}},
  "brand_controls": {"hallucination_mitigation": true, "length": "detailed"}
}
```

### qa

- recipes: `deduplication: true`. Add `prompt_rephrase: true` for diversity. For grounded QA with a
  `context` passage, consider `hallucination_mitigation: true`.
- brand_controls: `length: concise` for short factual answers
- why: short factual answers rarely need reasoning traces, so keep tokens lean

```json
{
  "column_mapping": {"prompt": "prompt", "completion": "completion", "context": ["context"]},
  "recipe_specification": {"recipes": {"deduplication": true, "prompt_rephrase": true}},
  "brand_controls": {"length": "concise"}
}
```

For the completion only QA file, drop `prompt` from the mapping: `{"completion": "completion"}`.

## Workflow reminder

1. Estimate first with `estimate=true`.
2. Pilot with `job_specification.max_rows` of 200 to 500.
3. Read `get_evaluation(...).quality.improvement_percent`.
4. Change one lever, rerun the pilot, compare.
5. Lock the winner, then run the full corpus.

## Encoding

Save all data files as plain UTF-8 with no byte order mark.

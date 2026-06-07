# Recipes and brand controls

Once your column mapping is right, recipes and brand controls decide **how** the
data is built and **what** quality bar it meets. This guide is a matrix of every
knob with when to use it, plus a domain-to-config table you can copy.

> **adaption-devkit** is a community, unofficial toolkit (Apache-2.0) by Aivaras
> Navardauskas (MANIFESTA), GitHub `A1VARA5`. Not affiliated with or endorsed by
> Adaption Labs.

## Two groups of knobs

- **Recipes** (`recipe_specification.recipes`) shape how the data is built.
- **Brand controls** (`brand_controls`) encode the specification: quality, safety,
  and voice.

A common mistake: `reasoning_traces` is a **recipe**, not a brand control. Put it
in `recipe_specification.recipes`. See [gotchas.md](gotchas.md).

## Recipes matrix

| Recipe            | What it does                              | Turn ON for                                              | Skip when                                            |
|-------------------|-------------------------------------------|----------------------------------------------------------|------------------------------------------------------|
| `deduplication`   | Drops near duplicate rows                 | Almost always. Cleaner signal, fewer wasted credits.     | Tiny, already-clean sets. (Note: dedup is always on at the platform level anyway; this is the recipe-level switch.) |
| `prompt_rephrase` | Rephrases prompts for variety and clarity | Boosting diversity and robustness; thin prompt variety.  | Prompts are gold or curated and must stay verbatim.  |
| `reasoning_traces`| Adds chain-of-thought to completions      | Math, code, science, legal, finance. Anything where stepwise reasoning lifts accuracy and must be auditable. | Short factual or extraction answers; when minimizing tokens and cost. |

Omitted recipes use backend defaults. You can set several at once.

```python
recipe_specification={"recipes": {
    "deduplication": True,
    "prompt_rephrase": True,
    "reasoning_traces": True,
}}
```

## Brand controls matrix

| Control                    | Values                                           | Use for                                                                 |
|----------------------------|--------------------------------------------------|-------------------------------------------------------------------------|
| `hallucination_mitigation` | bool                                             | Web-search grounding. Finance, legal, healthcare, science, RAG, anything fact sensitive. |
| `length`                   | `minimal` / `concise` / `detailed` / `extensive` | Match the target answer depth. Align with the eval's expected output length. |
| `safety_categories`        | list of category names                           | Policy-aligned data. Completions violating any listed category are filtered out. Treat the API schema as the source of truth for the exact names. |
| `blueprint`                | freeform string                                  | Qualitative voice, persona, language, or policy applied as a system prompt on every completion. |

All brand controls compose on a single run.

```python
brand_controls={
    "hallucination_mitigation": True,
    "length": "detailed",
    "safety_categories": ["..."],   # use exact names from the API schema
    "blueprint": "Warm, direct brand voice. Never over promise. UK English.",
}
```

## Domain to starting config

Start here, then iterate on `improvement_percent` one knob at a time.

| Domain                     | Recipes                                                  | Brand controls                                                            |
|----------------------------|----------------------------------------------------------|---------------------------------------------------------------------------|
| Math / code                | `reasoning_traces: True`, `deduplication: True`          | `length: detailed`                                                        |
| Finance                    | `reasoning_traces: True`, `deduplication: True`          | `hallucination_mitigation: True`, `length: detailed`, `safety_categories` per policy |
| Marketing                  | `prompt_rephrase: True`, `deduplication: True`           | `blueprint` for voice/tone/language, `length` to taste                    |
| Healthcare / legal         | `reasoning_traces: True`, `deduplication: True`          | `hallucination_mitigation: True`, `length: detailed`, `safety_categories` per policy |
| General / unsure           | `deduplication: True`, `prompt_rephrase: True`           | Add `reasoning_traces` and `hallucination_mitigation`, keep what lifts the score |

Notes on the picks:

- **Math and code.** The win is correct stepwise reasoning, and an objective eval
  makes the percentage defensible. Reasoning traces are the lever.
- **Finance, healthcare, legal.** These are fact sensitive and policy-bound.
  Grounding via `hallucination_mitigation` is the main lever; add reasoning traces
  for auditability and `safety_categories` for policy alignment.
- **Marketing.** Voice and diversity matter more than stepwise logic. Encode the
  voice in `blueprint` and widen variety with `prompt_rephrase`. Reasoning traces
  usually add tokens without lifting the score here.
- **General.** Start minimal, then A/B add `reasoning_traces` and
  `hallucination_mitigation`, keeping only what raises `improvement_percent`.

## The iterate-cheaply loop

1. `estimate=True` to quote credits and time.
2. Pilot with `job_specification={"max_rows": 200}` to `500`.
3. Read `get_evaluation(...).quality.improvement_percent`.
4. Change **one** knob, rerun the pilot, compare. Keep what helps.
5. Lock the winning config, then run the full corpus.

If you change several knobs at once you cannot tell which one moved the score.

## Worked example: marketing run

```python
run = client.datasets.run(
    dataset_id,
    column_mapping={"completion": "answer"},   # completion only voice corpus
    recipe_specification={"recipes": {
        "deduplication": True,
        "prompt_rephrase": True,
    }},
    brand_controls={
        "blueprint": "Warm, direct brand voice. Concrete benefits. UK English. Never over promise.",
        "length": "concise",
    },
    job_specification={"max_rows": 300},
    estimate=True,   # quote first, always
)
```

## Debugging "quality did not improve"

- `improvement_percent` empty: evaluation runs separately and is not done yet.
  Poll `get_evaluation` until `succeeded`. See [gotchas.md](gotchas.md).
- Wrong anchor mapping: the platform synthesized the wrong field. Recheck
  [column-mapping.md](column-mapping.md).
- Verbatim prompts got mangled: turn `prompt_rephrase` off.
- Fact-heavy domain still hallucinating: enable `hallucination_mitigation`.
- Answers too long or too short for the eval: adjust `length`.
- Changed many knobs at once: you cannot attribute the delta. One at a time.

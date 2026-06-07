# Column mapping decision guide

Column mapping is the single most important choice in a run. Get it right first;
everything else builds on it. This guide gives you a decision tree and a worked
example for each case.

> **adaption-devkit** is a community, unofficial toolkit (Apache-2.0) by Aivaras
> Navardauskas (MANIFESTA), GitHub `A1VARA5`. Not affiliated with or endorsed by
> Adaption Labs.

## The rule that governs everything

A run needs **at least one anchor**: a `prompt` column **or** a `completion`
column. From there:

- `prompt` only: the platform **generates** completions for your prompts.
- `completion` only: the platform **synthesizes** a matching prompt for each
  high quality answer.
- `prompt` + `completion`: the platform adapts both. Most common.
- `context` is a **list** of columns, passed at generation as grounding.
- `chat` is **mutually exclusive** with `prompt`, `completion`, and `context`.

Two facts that change your decision:

1. **Deduplication is always on and keys on the prompt.** Templated prompts that
   only vary in `context` collapse to one row. Either make prompts unique or go
   completion only.
2. `prompt` and `completion` cells accept plain text **or** JSON chat-turn arrays.

## Decision tree

```
Is your data multi turn conversations (a messages list per row)?
|
+-- YES -> map {"chat": "messages"}
|          (do NOT also map prompt/completion/context)
|
+-- NO
    |
    Do you have answers you trust as gold?
    |
    +-- YES, and you also have the matching questions
    |        -> map {"prompt": <question col>, "completion": <answer col>}
    |
    +-- YES, but you only have the answers (no questions)
    |        -> map {"completion": <answer col>}   (prompts get synthesized)
    |
    +-- NO, you only have prompts/questions
             -> map {"prompt": <prompt col>}       (completions get generated)

Then: is each answer grounded in source passages you want used?
    +-- YES -> add {"context": [<passage col>, <ref col>, ...]}
               (context is a list; it can include image columns)

Before you run, ask: are my prompts unique?
    +-- NO (templated, vary only in context) -> dedup will collapse them.
            Make prompts unique OR drop the prompt and go completion only.
```

## Case 1: instruction + answer pairs

You have a question column and a trusted answer column. This is the most common
shape.

Data:

| instruction                     | response                          |
|---------------------------------|-----------------------------------|
| Summarize this refund policy.   | Refunds are issued within 14 days |
| Write a tagline for an eco soap | Clean skin, cleaner planet        |

Mapping:

```python
column_mapping={"prompt": "instruction", "completion": "response"}
```

The platform adapts both sides. Make sure the instructions are not all identical,
or deduplication will collapse them.

## Case 2: prompt-only

You have prompts but no answers, and you want the platform to generate the
completions.

Data:

| query                                  |
|----------------------------------------|
| Draft a product description for X      |
| Explain compound interest to a teen    |

Mapping:

```python
column_mapping={"prompt": "query"}
```

The platform generates a completion for each prompt. Prompts must be distinct.

## Case 3: completion only (high quality answers corpus)

You have a corpus of answers you trust but no questions. This is also the **escape
hatch for deduplication collapse**: when your prompts would be templated and
identical, drop the prompt entirely and let the platform synthesize a distinct
prompt per answer.

Data:

| answer                                                        |
|---------------------------------------------------------------|
| Our brand voice is warm, direct, and never over promises.     |
| For B2B emails, lead with the outcome, then the proof point.  |

Mapping:

```python
column_mapping={"completion": "answer"}
```

Use this when your answers are gold and the questions are obvious, missing, or
would otherwise all be the same.

## Case 4: RAG / grounded with context

You have a query, the gold answer, and source passages that should ground the
generation. `context` is a list so you can tag several columns.

Data:

| query                       | passage                                 | citation        | gold                        |
|-----------------------------|-----------------------------------------|-----------------|-----------------------------|
| What is the warranty period | All units carry a 24-month warranty.    | policy_v3.pdf   | The warranty lasts 24 months|

Mapping:

```python
column_mapping={
    "prompt": "query",
    "context": ["passage", "citation"],
    "completion": "gold",
}
```

Context columns can carry images for multimodal grounding. Important: if your
`query` text is the same across many rows and only the `passage` differs,
deduplication still collapses on the prompt. Vary the query, or go completion only.

## Case 5: chat (multi turn conversations)

You have full conversations, one messages list per row. The platform extracts
prompt and completion from the turns.

Data (the `messages` cell holds a JSON array of turns):

| messages                                                                                  |
|-------------------------------------------------------------------------------------------|
| `[{"role":"user","content":"Hi"},{"role":"assistant","content":"Hello, how can I help?"}]`|

Mapping:

```python
column_mapping={"chat": "messages"}
```

Do not also map `prompt`, `completion`, or `context`. `chat` stands alone.

## Quick reference

| Your data                       | Mapping                                                        |
|---------------------------------|---------------------------------------------------------------|
| Instruction + answer pairs      | `{"prompt": ..., "completion": ...}`                          |
| Prompts only                    | `{"prompt": ...}`                                              |
| High quality answers only       | `{"completion": ...}`                                          |
| RAG / grounded                  | `{"prompt": ..., "context": [...], "completion": ...}`        |
| Multi turn conversations        | `{"chat": ...}`                                                |

## Before you run

- Run `adaption-kit lint data.csv` to catch duplicate prompts and encoding issues.
- Quote with `estimate=True` to confirm the mapping validates without spending
  credits.
- See [gotchas.md](gotchas.md) for deduplication collapse and the `chat`
  exclusivity rule.

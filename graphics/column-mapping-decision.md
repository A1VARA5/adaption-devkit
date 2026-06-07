# Column mapping decision tree

Adaptive Data needs to know what each column in your dataset is. The mapping you
choose changes how the recipe reads your rows. Use this tree to pick one. The
full reasoning lives in `guides/column-mapping.md`.

```mermaid
flowchart TD
    Start([What is in your dataset?]) --> Q1{Do you have prompts<br/>and answers together?}
    Q1 -- Yes --> Both[Map both<br/>prompt + completion]
    Q1 -- No --> Q2{Which one do you have?}
    Q2 -- Answers only --> Completion[Map as completion<br/>target text to learn]
    Q2 -- Prompts only --> Prompt[Map as prompt<br/>inputs to respond to]
    Q2 -- Reference passages --> Context[Map as context<br/>source material to ground on]

    classDef q fill:#e7f5ff,stroke:#1c7ed6,color:#0b4884;
    classDef out fill:#0b7285,stroke:#08505c,color:#ffffff;
    class Q1,Q2 q;
    class Both,Completion,Prompt,Context out;
```

## Quick rules

- Both prompts and answers in your rows: map **both** (`prompt` + `completion`).
- Answers only, no questions: map as **completion**.
- Prompts only, no answers: map as **prompt**.
- Reference passages or source documents: map as **context**.

When in doubt, run `adaption-kit lint data.csv`. The linter reports the columns it
sees and warns when a mapping looks wrong before you spend credits.

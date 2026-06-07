# Lifecycle: ingest to publish

The Adaptive Data lifecycle has five stages. adaption-devkit adds a preflight
linter before you spend any credits, an estimate step before each run, and a
publish helper for the stage where the official endpoint currently returns 501.

```mermaid
flowchart LR
    A[ingest<br/>upload your data] --> B[adapt<br/>run a recipe]
    B --> C[evaluate<br/>measure improvement_percent]
    C --> D[export<br/>download the adapted model or data]
    D --> E[publish<br/>release to Hugging Face and Kaggle]

    L([adaption-kit lint<br/>catch the dedup collapse first]) -.-> A
    M([adaption-kit estimate<br/>price the run before you pay]) -.-> B
    P([adaption-kit publish<br/>helper for the 501 endpoint]) -.-> E

    classDef stage fill:#0b7285,stroke:#08505c,color:#ffffff;
    classDef helper fill:#f1f3f5,stroke:#adb5bd,color:#212529;
    class A,B,C,D,E stage;
    class L,M,P helper;
```

## What each stage means

- **ingest** - upload a dataset (CSV or JSONL) and map its columns.
- **adapt** - run a recipe over the data to adapt a frontier model.
- **evaluate** - the run reports an `improvement_percent` versus the baseline.
- **export** - download the adapted artifact for your own use.
- **publish** - release the result so others can reproduce it.

## Where the devkit helps

- Run `adaption-kit lint` before ingest. The platform deduplication pass is
  always on, and near duplicate rows can collapse your dataset to a fraction of
  its size after you have already paid. The linter flags that risk first.
- Run `adaption-kit estimate` before adapt so you know the credit cost up front.
- Use `adaption-kit publish` for the publish stage, since the official publish
  endpoint currently returns HTTP 501.

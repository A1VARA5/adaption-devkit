# The credit safe run loop

Spend the least to find the best setup. Estimate, pilot on a small slice, read the
improvement number, change one lever, then repeat. Only scale to the full corpus once
a small run looks good. This is the habit the toolkit is built to encourage.

```mermaid
flowchart TD
    A([lint your dataset]) --> V[verify math and code rows<br/>keep only the ones that pass]
    V --> X[decontaminate against benchmarks]
    X --> B[estimate the run]
    B --> C[pilot on a small max_rows slice]
    C --> D{improvement_percent}
    D -- low --> E[change one lever<br/>a recipe or a brand control]
    E --> B
    D -- good --> F[run the full corpus]
    F --> G([publish to Hugging Face and Kaggle])
    classDef step fill:#0b7285,stroke:#08505c,color:#ffffff;
    classDef gate fill:#e7f5ff,stroke:#1c7ed6,color:#0b4884;
    class A,V,X,B,C,E,F,G step;
    class D gate;
```

Change one lever at a time, so you can tell what actually moved the number.

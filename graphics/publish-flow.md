# Publishing your release

The publish endpoint currently returns 501, so you release by hand. The publish helper
packages this for you: it downloads the adapted dataset, writes a card, renders a cover,
and pushes to Hugging Face and Kaggle.

```mermaid
flowchart LR
    A[run done] --> B[download the adapted dataset]
    B --> C[write a dataset card]
    C --> D[render a cover image]
    D --> E[push to Hugging Face]
    D --> F[push to Kaggle]
    classDef step fill:#0b7285,stroke:#08505c,color:#ffffff;
    class A,B,C,D,E,F step;
```

Kaggle datasets start private, so flip the dataset to public when you are ready.

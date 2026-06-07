# Which command do I run

A quick route from a standing start to a published release. Each box is a command, so
you never have to wonder what comes next.

```mermaid
flowchart TD
    S([new here? start here]) --> Doc[adaption-kit doctor]
    Doc --> Q1{know your column mapping?}
    Q1 -- no --> Sug[adaption-kit suggest]
    Q1 -- yes --> Lint[adaption-kit lint]
    Sug --> Lint
    Lint --> Est[adaption-kit estimate]
    Est --> Run[adaption-kit run<br/>pilot first]
    Run --> Q2{number look good?}
    Q2 -- no --> Tune[change one lever]
    Tune --> Est
    Q2 -- yes --> Full[adaption-kit run<br/>full corpus]
    Full --> Pub[adaption-kit publish]
    classDef cmd fill:#0b7285,stroke:#08505c,color:#ffffff;
    classDef gate fill:#e7f5ff,stroke:#1c7ed6,color:#0b4884;
    class Doc,Sug,Lint,Est,Run,Tune,Full,Pub cmd;
    class Q1,Q2 gate;
```

If you only remember one thing: run lint before you spend a credit.

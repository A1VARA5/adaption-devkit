# FAQ

Honest questions a newcomer actually asks, with short answers. This is a
community, unofficial toolkit; it is not affiliated with or endorsed by Adaption
Labs. For anything about the platform itself, the official Adaption documentation
and API are the source of truth.

## How do I start?

Install the kit, set your environment variables, then lint your data before you
spend anything.

```bash
pip install -e .
export ADAPTION_BASE_URL="https://api.prod.adaptionlabs.ai"
export ADAPTION_API_KEY="your-key-here"
adaption-kit lint data.csv
```

Then follow `guides/quickstart.md` from estimate, to pilot, to reading
`improvement_percent`. The full walkthrough lives there.

## Why did my dataset shrink after a run?

Deduplication is always on and it keys on the prompt. If you built your data from
a template where the prompt text is identical across rows and only the context
varies, every row past the first looks like a duplicate prompt and gets dropped.
Variety that lives only in the context does not save the row.

Fix it one of two ways: write genuinely distinct prompts per row, or go completion
only, mapping only the completion column and letting the platform synthesize a
distinct prompt for each high quality answer. Run `adaption-kit lint` first; it
flags duplicate prompts so you catch the collapse before paying.

## Why do I get a 503?

The host the SDK and the docs point to is not always the host your account
actually talks to. One can return 503 while the other answers normally. This is
easy to mistake for a key or network problem.

Do not hardcode a host. Set `ADAPTION_BASE_URL` in the environment. The host that
has been answering for participants is `https://api.prod.adaptionlabs.ai`, so
start there if the documented default returns 503. Reading the host from the
environment means you can switch it later without touching code.

## How do I publish if the endpoint returns 501?

The platform publish endpoint currently returns `501 Not Implemented`, so it
cannot push to Hugging Face or Kaggle for you. You release by hand. Download the
processed dataset, then push it to Hugging Face and Kaggle yourself.

`adaption-kit publish` does the packaging for you: it generates the cards and
metadata and walks you through the manual upload rather than relying on the dead
endpoint. See `guides/release-checklist.md`. Check the endpoint again before your
final submission in case it ships.

## How are credits spent, and how do I not waste them?

Credits are spent when you start a real adaptation run (estimate calls do not
spend them). The common ways people waste credits:

- Running before linting, so a dedup collapse processes far fewer rows than paid
  for.
- Running the full corpus first instead of a small pilot.
- Changing several knobs at once, so you cannot tell which one helped and end up
  running again.

The habit that saves credits: lint, then `estimate` to quote the cost, then
`run --pilot` on a few hundred rows, then change one knob at a time and keep only
what raises `improvement_percent`. Scale the winning config last.

## What is the difference between a recipe and a brand control?

A recipe shapes how the data is built. Recipes are `deduplication`,
`prompt_rephrase`, and `reasoning_traces`, and they go in
`recipe_specification.recipes`. A brand control encodes the specification the data
must meet: quality, safety, and voice. Brand controls are `blueprint`, `length`,
`safety_categories`, and `hallucination_mitigation`, and they go in
`brand_controls`.

A common slip: `reasoning_traces` is a recipe, not a brand control. See
`guides/recipes-and-controls.md` for the full matrix.

## Do I need the SDK installed for the linter?

No. The preflight linter reads your local file and needs no network and no SDK.
The core linter, the guides, the cards, and the cover all work with no extras.
Only the SDK backed commands, `estimate` and `run`, need the optional `adaption`
SDK (`pip install -e ".[sdk]"`). If an extra is missing, the matching command
tells you what to add.

## Where is the official reference?

The official Adaption documentation and API are the source of truth for the
platform: how Adaptive Data and AutoScientist work, every parameter, and any
behavior that changes over time. This kit is a community companion that helps you
move faster; when the two ever disagree, trust the official docs and please open
an issue here so we can fix the kit.

# Glossary

Plain language definitions of the terms a beginner meets in this kit and in the
Adaptive Data lifecycle. Friendly and short. For the precise platform meaning,
the official Adaption documentation is the source of truth.

**Anchor.** The column a run hangs on. A run needs at least one anchor, either a
prompt column or a completion column. Everything else builds on the anchor you
choose.

**Prompt.** The question, instruction, or input side of an example. If you map
prompts only, the platform generates a matching completion for each one.

**Completion.** The answer or output side of an example. If you map completions
only, the platform synthesizes a matching prompt for each high quality answer.

**Context.** Optional source passages, references, or images passed at generation
time to ground the answer. Context is a list, so you can tag several columns. It
is supporting material, not an anchor on its own.

**Chat.** A mapping for multi turn conversations, where each row holds a list of
message turns. Chat stands alone; it is mutually exclusive with prompt,
completion, and context.

**Recipe.** A switch that shapes how the data is built. The recipes are
deduplication, prompt rephrase, and reasoning traces. They go in the recipe
specification.

**Brand control.** A setting that encodes the specification your data must meet:
quality, safety, and voice. The brand controls are blueprint, length, safety
categories, and hallucination mitigation.

**Blueprint.** A brand control: a freeform instruction applied as a system prompt
on every completion, used to set voice, persona, language, or policy. This is
where you put your brand tone.

**Deduplication.** A recipe that drops near duplicate rows. It is always on at the
platform level and keys on the prompt, so templated prompts that differ only in
context collapse to one row. Make prompts unique or go completion only.

**Prompt rephrase.** A recipe that rephrases prompts for variety and clarity. Turn
it on to widen thin prompt variety; turn it off when your prompts are curated and
must stay verbatim.

**Reasoning traces.** A recipe that adds step by step reasoning to completions.
Useful for math, code, science, finance, and legal work where stepwise reasoning
lifts accuracy and must be auditable. It is a recipe, not a brand control.

**Estimate.** A quote of the credits and time a run would cost, returned without
starting the run or spending credits. Always estimate before you run.

**Pilot.** A small capped run, often a few hundred rows, used to test a config
cheaply before scaling to the full corpus. Iterate on pilots, then lock the
winner.

**improvement_percent.** The headline number from evaluation: how much the adapted
model improved over the baseline. It is what the AutoScientist Challenge is scored
on. Evaluation runs on its own schedule, so you poll for it separately.

**Adaptive Data.** Adaption's platform that jointly optimizes data and training to
adapt frontier models. Its lifecycle is ingest, adapt, evaluate, export, publish.

**AutoScientist.** Adaption's offering and the challenge this kit was built around,
where a measurable percentage improvement over a baseline is the goal.

**Dataset card.** The README that ships with a published dataset, describing what
it is, how it was built, and its measured improvement. `adaption-kit card dataset`
generates one.

**Model card.** The README that ships with a published model, describing the base
model, the data it was adapted on, and its results. `adaption-kit card model`
generates one.

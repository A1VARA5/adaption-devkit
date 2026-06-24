# Changelog

All notable changes to adaption-devkit are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

adaption-devkit is a community, unofficial project. It is not affiliated with or
endorsed by Adaption Labs.

## [Unreleased]

### Added

- `verify` command (`adaption-kit verify`) to prove rows are correct before you
  adapt them: math answers are checked for equivalence against a gold column
  (normalized string, then numeric, then symbolic via sympy if installed), and
  code solutions are executed against their unit tests in a sandboxed subprocess
  and kept only if every test passes. With `--out` it writes only the verified
  rows. Symbolic math needs the optional `verify` extra (sympy); without it, math
  falls back to string and numeric checks and says so. Code verification is pure
  standard library.
- `decontaminate` command (`adaption-kit decontaminate`) to remove any training
  row that overlaps a benchmark test set by an n-gram (default 13), so the
  improvement number is not inflated by benchmark overlap. With `--out` it writes
  the cleaned rows.
- Optional `verify` extra (`pip install -e ".[verify]"`) that adds sympy for the
  symbolic math equivalence check.
- `doctor` command to check your environment and configuration (in progress).
- `suggest` command to recommend recipes and brand controls for your domain
  (in progress).

## [0.1.0] - 2026-06-07

### Added

- Preflight dataset linter (`adaption-kit lint`) that catches the always on
  deduplication collapse, encoding issues, and empty anchors before you spend
  credits.
- Estimate first run helpers (`adaption-kit estimate` and `adaption-kit run`),
  with a pilot mode and the option to wait and print `improvement_percent`.
- Publish helper (`adaption-kit publish`) that packages a release for Hugging
  Face and Kaggle, a workaround for the platform publish endpoint returning 501.
- Card generators (`adaption-kit card`) for dataset cards, model cards, and
  Kaggle metadata.
- Cover generator (`adaption-kit cover`) to render a release cover image.
- Five guides: quickstart, gotchas, column mapping, recipes and controls, and the
  release checklist.
- A cookbook of runnable notebooks covering the full lifecycle.
- Templates for dataset schemas, dataset and model cards, a cover, and Kaggle
  metadata.

[Unreleased]: https://github.com/A1VARA5/adaption-devkit/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/A1VARA5/adaption-devkit/releases/tag/v0.1.0

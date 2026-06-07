# Contributing to adaption-devkit

Thank you for helping. This is a community, unofficial project. It is not
affiliated with or endorsed by Adaption Labs. The goal is to help beginners and
students start fast with Adaptive Data and AutoScientist without wasting credits.

By contributing, you agree that your contribution is licensed under Apache-2.0,
the same license as the project.

## The quality bar

This kit exists to save people time and credits, so correctness matters more than
volume.

- Only add content you have **verified to be correct**. If you have run it and
  seen it work, say so.
- Anything you have **not tested**, mark it clearly as untested. Use a short note
  like `Note: untested, based on the docs as of <date>`. A reviewer can verify it
  later. Do not present a guess as a confirmed fact.
- When a behavior comes from the official Adaption docs or API, link or name the
  source so a reader can check it. The official docs and API are the source of
  truth, not this kit.
- If you find something in this kit that is wrong or out of date, a fix is one of
  the most valuable contributions you can make.

## Style

- No em dashes. Use a comma, a period, or parentheses instead.
- No exclamation marks.
- Clear, beginner friendly tone. Assume the reader is new to Adaptive Data. Spell
  out the step they might not know.
- Short sentences and concrete examples beat clever prose.
- Never hardcode an API key or base URL. Configuration goes through the
  environment variables `ADAPTION_BASE_URL` and `ADAPTION_API_KEY`.

## How to run the package locally

```bash
git clone https://github.com/A1VARA5/adaption-devkit.git
cd adaption-devkit
pip install -e .
```

For the SDK-backed run and publish helpers, install the optional extra:

```bash
pip install -e ".[sdk]"
```

For the cookbook notebooks:

```bash
pip install -e ".[notebooks]"
```

Set your environment before any command that talks to the API:

```bash
export ADAPTION_BASE_URL="https://api.prod.adaptionlabs.ai"
export ADAPTION_API_KEY="your-key-here"
```

Smoke test the CLI without spending any credits:

```bash
adaption-kit lint cookbook/sample_data/sample.csv
```

The linter and the guides need no credits and no extras, so start there.

## Submitting a change

1. Fork the repo and create a branch with a short, descriptive name.
2. Make your change. Keep pull requests focused on one thing.
3. Run the linter and any relevant cookbook cell to confirm nothing broke.
4. Update the matching guide, template, or graphic if your change affects it.
5. Open a pull request using the template. Describe what you changed, how you
   verified it, and flag anything that is untested.

## Reporting bugs and ideas

Use the issue templates. The bug report asks for steps to reproduce. The idea
template asks what problem you want solved. Both are welcome.

## Code of conduct

This project follows the [Contributor Covenant v2.1](./CODE_OF_CONDUCT.md). By
taking part you agree to uphold it.

## Development

This section covers the tooling for working on the code itself: how to set up a
development environment, run the tests, and run the linter and formatter.

Install the package in editable mode along with the test tools. If a `dev`
extra is not defined, the command falls back to a plain editable install plus
the tools we need:

```bash
pip install -e ".[dev]" || pip install -e .
pip install pytest ruff
```

If you have `make`, the same setup is one target:

```bash
make install
```

Run the test suite with pytest:

```bash
pytest
# or
make test
```

Run the linter and the formatter with ruff. The configuration lives in
`ruff.toml` (line length 100, target Python 3.10):

```bash
ruff check .     # lint, or: make lint
ruff format .    # auto format, or: make format
```

The `all` target runs the linter and then the tests in one go:

```bash
make all
```

CI runs the same checks on every push and pull request to `main`, across Python
3.10, 3.11, and 3.12. See `.github/workflows/ci.yml`. Please run `ruff check .`
and `pytest` locally before opening a pull request so the build stays green.

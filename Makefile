.PHONY: install test lint format all

install:
	pip install -e ".[dev]" || pip install -e .
	pip install pytest ruff

test:
	pytest

lint:
	ruff check .

format:
	ruff format .

all: lint test

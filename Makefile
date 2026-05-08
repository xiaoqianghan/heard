.PHONY: check test lint sync

sync:
	uv sync --all-extras --all-groups

test:
	uv run pytest -v

lint:
	uv run pylint src/heard/

check: lint test

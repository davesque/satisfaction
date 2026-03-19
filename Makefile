.PHONY: setup
setup:
	uv sync --group dev

.PHONY: test
test:
	uv run pytest -vv --cov-report term-missing --cov=satisfaction .

.PHONY: lint
lint:
	uv run ruff format --diff .
	uv run ruff check .

.PHONY: typecheck
typecheck:
	uv run ty check satisfaction

.PHONY: clean
clean:
	rm -rf .venv *.egg-info

VENV := venv
PIP := $(VENV)/bin/pip
PYTEST := $(VENV)/bin/pytest

.PHONY: setup
setup:
	python3 -mvenv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e .[dev]

.PHONY: test
test:
	$(PYTEST) -vv --cov-report term-missing --cov=satellite .

.PHONY: clean
clean:
	rm -r $(VENV) *.egg-info

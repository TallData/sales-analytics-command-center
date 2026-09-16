PYTHON ?= python3
VENV ?= .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_RUFF := $(VENV)/bin/ruff
VENV_PYTEST := $(VENV)/bin/pytest

.PHONY: setup generate warehouse qa test lint refresh bad-data-demo clean-data

setup:
	$(PYTHON) -m venv $(VENV)
	$(VENV_PYTHON) -m pip install -r requirements.txt

generate:
	$(VENV_PYTHON) -m src.generate_synthetic_data --all

warehouse:
	$(VENV_PYTHON) -m src.ingest

qa:
	$(VENV_PYTHON) -m src.qa

lint:
	$(VENV_RUFF) check src tests

test:
	$(VENV_PYTEST) -q

refresh: generate warehouse qa

bad-data-demo:
	$(VENV_PYTHON) -m src.generate_synthetic_data --bad-data-fixture
	$(VENV_PYTHON) -m src.qa --input-root data/fixtures/bad-2026-09 --expect-failure

clean-data:
	$(VENV_PYTHON) -m src.generate_synthetic_data --clean

PYTHON ?= python
.PHONY: install test lint run migrate
install:
	$(PYTHON) -m pip install -e '.[dev,api]'
test:
	$(PYTHON) -m pytest
lint:
	ruff check .
run:
	uvicorn api.server:app --host 0.0.0.0 --port 8000
migrate:
	$(PYTHON) scripts/migrate.py

# Cross-platform targets (GNU Make). Windows: use `.\scripts\demo.ps1` equivalently.
.PHONY: install test demo lint

install:
	python -m pip install -e ".[dev]"

test:
	python -m pytest -q

lint:
	python -m ruff check src tests

demo: install
	python -m skills_eval --demo

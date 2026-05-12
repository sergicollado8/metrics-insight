.PHONY: install test lint run compare build docker-build docker-run help docs docs-serve

help:
	@echo "Available commands:"
	@echo "  install      Install local dependencies"
	@echo "  test         Run all tests (unit, integration, acceptance)"
	@echo "  lint         Run ruff and mypy for static analysis"
	@echo "  run          Execute the fetch command (requires GITHUB_TOKEN)"
	@echo "               Example: make run ARGS=\"--repo owner/repo --start 2024-01-01 --end 2024-03-31\""
	@echo "  compare      Compare sprints trajectories"
	@echo "               Example: make compare ARGS=\"--repo owner/repo --start 2024-01-01 --weeks 2 --sprints 4\""
	@echo "  build        Build the package locally"
	@echo "  docs         Generate documentation"
	@echo "  docs-serve   Serve documentation locally"
	@echo "  docker-build Build the Docker image"
	@echo "  docker-run   Run the tool from Docker"

install:
	pip install --upgrade pip
	pip install -e .[dev]

test:
	PYTHONPATH=. pytest tests/

lint:
	ruff check .
	mypy src/

run:
	python3 -m src.metrics_insight.infrastructure.cli.main fetch $(ARGS)

compare:
	python3 -m src.metrics_insight.infrastructure.cli.main compare $(ARGS)

actions:
	python3 -m src.metrics_insight.infrastructure.cli.main actions $(ARGS)

build:
	python3 -m build

docs:
	mkdocs build

docs-serve:
	mkdocs serve

docker-build:
	docker build -t metrics-insight:latest .

docker-run:
	docker run --rm -v $(PWD)/output:/app/output --env-file .env metrics-insight:latest $(ARGS)

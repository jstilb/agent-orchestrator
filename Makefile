.PHONY: install test lint format type-check coverage clean build demo serve help

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -e ".[dev]"

test: ## Run tests
	pytest -v

coverage: ## Run tests with coverage report
	pytest --cov=src --cov-report=term-missing --cov-report=html

lint: ## Run linter
	ruff check src/ tests/

format: ## Format code
	ruff format src/ tests/

type-check: ## Run type checker
	mypy src/

demo: ## Run demo (no API keys needed)
	python -m src.cli demo

serve: ## Start API server
	uvicorn src.api.app:app --reload --host 0.0.0.0 --port 8000

clean: ## Clean build artifacts
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ .mypy_cache/ .coverage htmlcov/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true

build: clean ## Build distribution
	pip install build
	python -m build

ci: lint type-check test ## Run all CI checks

all: install lint type-check coverage ## Full development workflow

.PHONY: install setup lint format typecheck test train collect features mlflow-ui clean clean-all help

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install project dependencies
	uv sync --all-extras

setup: install ## Install dependencies and set up pre-commit hooks
	uv run pre-commit install

lint: ## Run linter and format check
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format: ## Auto-format code
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck: ## Run mypy type checker
	uv run mypy src/

test: ## Run tests
	uv run pytest

collect: ## Collect data from all APIs
	uv run python -m playerpulse.collectors.run_all

features: ## Build features from raw data
	uv run python -m playerpulse.features.build

train: ## Train all models with MLflow tracking
	uv run python -m playerpulse.models.train


mlflow-ui: ## Launch MLflow experiment tracking UI
	uv run mlflow ui --backend-store-uri sqlite:///.mlflow/mlflow.db

clean: ## Remove caches and build artifacts
	rm -rf .ruff_cache .mypy_cache .pytest_cache htmlcov dist
	find . -type d -name __pycache__ -exec rm -rf {} +

clean-all: clean ## Remove caches, models, and MLflow data
	rm -rf .mlflow models/*.joblib models/*.pkl

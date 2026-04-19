.PHONY: install setup lint format typecheck test train collect features mlflow-ui release-models clean clean-all help

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


release-models: ## Create a GitHub Release and upload trained .joblib files (requires gh CLI)
	@echo "Creating GitHub Release $(TAG) and uploading model files..."
	@test -n "$(TAG)" || (echo "Usage: make release-models TAG=v1.0-models" && exit 1)
	@for f in models/lightgbm.joblib models/xgboost.joblib models/catboost.joblib \
	           models/ensemble.joblib models/logistic_regression.joblib models/scaler.joblib; do \
	    test -f $$f || (echo "Missing $$f — run 'make train' first" && exit 1); \
	done
	gh release create $(TAG) \
	    models/lightgbm.joblib \
	    models/xgboost.joblib \
	    models/catboost.joblib \
	    models/ensemble.joblib \
	    models/logistic_regression.joblib \
	    models/scaler.joblib \
	    --title "$(TAG) Production Models" \
	    --notes "Trained on real OpenDota + Steam + Riot data. Set MODEL_RELEASE_URL=https://github.com/nshreeyut/PlayerPulse/releases/download/$(TAG) in Render env vars."
	@echo ""
	@echo "Done. Set this in Render dashboard:"
	@echo "  MODEL_RELEASE_URL=https://github.com/nshreeyut/PlayerPulse/releases/download/$(TAG)"

mlflow-ui: ## Launch MLflow experiment tracking UI
	uv run mlflow ui --backend-store-uri sqlite:///.mlflow/mlflow.db

sync-demo-models: ## Copy freshly trained models into models/demo/ and commit (keeps demo in sync)
	@echo "Syncing models/ → models/demo/ ..."
	@for f in lightgbm.joblib xgboost.joblib catboost.joblib ensemble.joblib logistic_regression.joblib scaler.joblib; do \
	    test -f models/$$f && cp models/$$f models/demo/$$f && echo "  copied $$f"; \
	done
	git add models/demo/
	git commit -m "Sync demo models after retrain"
	@echo "Done. Push to deploy updated demo."

clean: ## Remove caches and build artifacts
	rm -rf .ruff_cache .mypy_cache .pytest_cache htmlcov dist
	find . -type d -name __pycache__ -exec rm -rf {} +

clean-all: clean ## Remove caches, models, and MLflow data
	rm -rf .mlflow models/*.joblib models/*.pkl

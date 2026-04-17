# PlayerPulse

AI-powered player churn prediction platform for game studios. A multi-agent pipeline scores churn risk, explains predictions with SHAP, and lets analysts ask questions in plain English through a conversational dashboard.

**[Try the demo](https://playerpulse.vercel.app/demo)** — no account or API keys needed.

## Features

- Collects player data from OpenDota, Steam, and RAWG.io
- 4 ML models + soft-voting ensemble (XGBoost, LightGBM, CatBoost, Logistic Regression)
- SHAP explainability — per-player factors driving churn score
- Network telemetry layer (NVIDIA Sionna) — links 5G/6G signal quality to churn
- Conversational AI analyst powered by Groq (free) or OpenAI/Anthropic/Gemini/Mistral/NVIDIA
- Demo mode with synthetic data — shareable link, no setup required

## Quick Start

```bash
# Install dependencies
uv pip install -e ".[dev]"
cd frontend && npm install

# Start backend
uv run python -m uvicorn api.main:app --reload

# Start frontend (separate terminal)
cd frontend && npm run dev
```

Demo runs at `http://localhost:5173/demo`

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
STEAM_API_KEY=     # Steam Web API key
RAWG_API_KEY=      # RAWG.io API key

LLM_PROVIDER=groq  # groq | openai | anthropic | gemini | mistral | nvidia | ollama
GROQ_API_KEY=      # default LLM — free at console.groq.com
```

## ML Pipeline

```bash
make collect    # pull data from OpenDota + Steam
make features   # engineer behavioral features
make train      # train models + log to MLflow
make mlflow-ui  # view results at localhost:5000
```

## Tech Stack

| | |
|---|---|
| ML | XGBoost, LightGBM, CatBoost, scikit-learn, SHAP, MLflow |
| Network | NVIDIA Sionna (5G/6G physical layer simulation) |
| Backend | FastAPI, LangChain, 7 LLM providers |
| Frontend | React, Vite, Recharts |
| Data | Polars, Pydantic |
| Database | Supabase (Postgres + Auth + Storage) |
| Deployment | Render (backend), Vercel (frontend) |

## License

MIT

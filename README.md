# Game Churn Prediction

Multi-platform player churn prediction platform for game studios. A multi-agent AI pipeline scores churn risk, explains predictions with SHAP, and lets analysts ask questions in plain English through a conversational dashboard.

**[Try the demo](https://yourapp.vercel.app/demo)** — no account or API keys needed.

## Features

- Collects player data from OpenDota, Steam, and RAWG.io
- 4 ML models + soft-voting ensemble (XGBoost, LightGBM, CatBoost, Logistic Regression)
- SHAP explainability — per-player factors driving churn score
- Conversational AI analyst powered by Groq (free) or OpenAI
- Demo mode with synthetic data — shareable link, no setup required

## Quick Start

```bash
# Install dependencies
make install
cd frontend && npm install

# Start backend
uvicorn api.main:app --reload --port 8000

# Start frontend (separate terminal)
cd frontend && npm run dev
```

## Environment Variables

Copy `.env.example` to `.env` and fill in your keys:

```env
STEAM_API_KEY=           # Steam Web API key
GAME_CHURN_RAWG_API_KEY= # RAWG.io API key

GROQ_API_KEY=            # default LLM (free at console.groq.com)
LLM_PROVIDER=groq        # groq | openai
OPENAI_API_KEY=          # optional, only if LLM_PROVIDER=openai
```

For the frontend, set `VITE_API_URL` in `frontend/.env` to your backend URL in production.

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
| Backend | FastAPI, LangChain, Groq / OpenAI |
| Frontend | React, Vite, Recharts |
| Data | Polars, Pydantic |
| Deployment | Render (backend), Vercel (frontend) |

## License

MIT

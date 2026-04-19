# PlayerPulse — Implementation Workflow

Track progress here. Check off each step as it's done. Read this at the start of every session to resume where you left off.

**Legend:** `[ ]` not started · `[x]` done · `[-]` blocked/skipped

---

## Product Overview

PlayerPulse is an AI-powered player churn prediction platform for game studios. Three tiers:

| Tier | Who | How |
|---|---|---|
| **Demo mode** | Recruiters, investors | Synthetic data, no auth, instant access at `/demo` |
| **Hosted platform** | Small/non-technical studios | Sign up, upload CSV or Excel, see dashboard |
| **SDK (PyPI)** | Technical studios / data teams | `pip install player-pulse`, CLI, direct DB connection |

All three tiers share the same backend ML pipeline and dashboard components. The network telemetry layer (NVIDIA Sionna) is the core competitive moat — no competitor links 5G/6G network quality to churn.

---

## Deployment Architecture

```
Studio browser
      ↓
   Vercel          ← React + Vite (frontend)
      ↓
   Render          ← FastAPI + Background worker
      ↓
   Supabase        ← Postgres + Auth + File Storage
```

---

## Architecture Decisions (Locked In)

| Decision | Choice | Notes |
|---|---|---|
| Database | Supabase (hosted Postgres) | Auth + storage included; migrate to own hardware as revenue grows |
| Auth (browser) | Supabase Auth | Email/password + magic link, zero auth code |
| Auth (SDK/API) | Custom API keys | Generated on signup, hashed in `studios` table, one per account |
| File upload | FastAPI BackgroundTasks | No extra infra, sufficient for v1 |
| Website file formats | CSV + Excel (.xlsx) | Covers all non-technical studios |
| SDK file formats | Any (CSV, Excel, Parquet, JSON, direct DB) | Technical studios bring data any way they have it |
| Multi-tenancy | Row-level with `studio_id` | Simple, can migrate to schema-level later |
| Model serving | Shared model v1 → per-studio v2 | Per-studio = premium tier in v2 |
| Network features | Sionna from day one | Bootstraps model before real studio data arrives |
| Deployment | Render + Supabase + Vercel | All free tier until paying studios |

---

## Database Schema (Supabase Postgres)

```sql
studios       — id, name, email, api_key_hash, created_at, plan (free/pro)
players       — id, studio_id, player_id, platform, created_at, updated_at
features      — id, player_id, studio_id, feature_vector (JSONB), updated_at
predictions   — id, player_id, studio_id, churn_probability, risk_level, model_version, created_at
shap_values   — id, player_id, studio_id, shap_vector (JSONB), created_at
upload_jobs   — id, studio_id, filename, status (pending/processing/done/failed), row_count, created_at
outcomes      — id, player_id, studio_id, predicted_churn_prob, prediction_date, actually_churned (bool), churned_date, reported_at
```

---

## What's Already Built

- [x] OpenDota collector (`collectors/opendota.py`)
- [x] RAWG collector with review fetching (`collectors/rawg.py`)
- [x] Steam collector (`collectors/steam.py`) — playtime, recently played, friends, reviews
- [x] Feature engineering (`features/engineer.py`, `standardize.py`, `build.py`)
- [x] ML model training — XGBoost, LightGBM, CatBoost, Ensemble, SHAP (`models/train.py`)
- [x] Synthetic data generation — 5 archetypes (Elite/Core/Casual/At-Risk/Churned), `Player_N` IDs (`models/synthetic.py`)
- [x] Model artifacts (`models/*.joblib`)
- [x] NLP notebook (`notebooks/01_review_text_analysis.ipynb`) — RoBERTa + GPT summaries
- [x] Model evaluation notebook (`notebooks/03_model_evaluation.ipynb`) — CV, ROC, SHAP, platform distribution (loads real parquet)
- [x] FastAPI app structure (`api/main.py`, `api/config.py`)
- [x] Registries (`api/registry/game_registry.py`, `model_registry.py`)
- [x] Router signatures (`api/routers/players.py`, `chat.py`)
- [x] Service stubs (`api/services/data_service.py`, `model_service.py`, `shap_service.py`)
- [x] Agent stub (`api/agents/churn_analyst.py`)
- [x] `get_llm()` factory — 7 providers via `LLM_PROVIDER` env var (Groq/OpenAI/Anthropic/Gemini/Mistral/NVIDIA/Ollama)
- [x] Demo mode — fully working at `http://localhost:5173/demo`
  - [x] `api/services/demo_service.py` — `_churn_score()` formula, 50 synthetic players, SHAP cached
  - [x] `api/routers/demo.py` — `/api/v1/demo/*` (summary, players, player, chat streaming)
  - [x] `frontend/src/api/demo.js` — all demo API calls + streaming chat
  - [x] `frontend/src/pages/Demo.jsx` — fleet summary bar, view tabs, sidebar search, risk filters
  - [x] `frontend/src/components/DemoBanner/` — centered "Demo Mode" header, styled exit button
  - [x] `frontend/src/components/FleetOverview/` — risk donut, churn histogram, engagement scatter, platform bar
  - [x] `frontend/src/components/ShapChart/` — Recharts horizontal bar (red/green, top 8 features)
  - [x] `frontend/src/components/AnalyticsPanel/` — churn %, risk badge, 4-stat grid, SHAP chart
  - [x] `frontend/src/components/ChatPanel/` — streaming bubbles, suggested questions prop
  - [x] `frontend/src/hooks/useChat.js` — streaming bug fixed, optional `streamFn` param
  - [x] `frontend/src/api/chat.js` — `streamChat` implemented
  - [x] Home page — empty state with "Try the Demo →" link
- [x] Demo UI layout polish
  - [x] Fixed `max-width: 1400px` inherited from global `main` CSS (was creating right-side gap)
  - [x] Chat panel sizing and gap consistency between sidebar/charts/chat

---

## Sprint 1 — Branding + Module Rename

> Clean foundation before building. No functionality changes.

- [x] Rename `src/game_churn/` → `src/playerpulse/` (~30 import files to update)
- [x] `pyproject.toml` — `name = "player-pulse"`, updated description, add authors/license/readme/classifiers/URLs
- [x] `README.md` — title, correct run commands, placeholder Vercel URL
- [x] `api/main.py` — `title="PlayerPulse API"`
- [x] `render.yaml` — `name: playerpulse-api`, fix broken `buildCommand` (remove reference to missing `api/requirements.txt`)
- [x] `.env.example` — header comment
- [x] `src/playerpulse/models/train.py` — `mlflow.set_experiment("playerpulse")`
- [x] Verify: `uv run python -m uvicorn api.main:app --reload` still starts, `/docs` shows "PlayerPulse API"

---

## Sprint 2 — Network Telemetry (NVIDIA Sionna)

> Bake in the competitive moat before building the product. Train model with network features from day one using Sionna synthetic telemetry. Studios optionally provide real network data later to improve accuracy.

- [x] `pyproject.toml` — add `[network]` optional dep group: `sionna`, `tensorflow`
- [x] `src/playerpulse/features/schema.py` — add `NetworkFeatures` Pydantic model
  - [x] Fields: `avg_sinr_db`, `p95_latency_ms`, `packet_loss_rate`, `jitter_ms`, `disconnect_count`, `peak_hour_latency_ms`
- [x] `src/playerpulse/features/network_features.py` — Sionna + statistical fallback
  - [x] `simulate_network_conditions(n_players, scenario)` — dual mode (Sionna TDL / numpy 3GPP distributions)
  - [x] `telemetry_to_features(raw_telemetry) -> pl.DataFrame` — SINR/BLER/delay → engineered features
- [x] `api/services/network_sim_service.py` — simulation runner
  - [x] `generate_synthetic_telemetry(n_players) -> pl.DataFrame`
  - [x] Save output parquet to `data/network_sim/`
- [-] `src/playerpulse/features/standardize.py` — merge `NetworkFeatures` into `PlayerActivity` (skipped — network features added directly in synthetic.py; real pipeline adds them at collection time)
- [x] `src/playerpulse/models/train.py` — 6 network feature cols added to `FEATURE_COLS`; `--synthetic` flag added
- [x] `src/playerpulse/models/synthetic.py` — all 5 archetypes have archetype-aware network features
- [x] `api/services/demo_service.py` — network cols, labels, `_churn_score()` updated (network = 20% weight)
---

## Sprint 2.5 — Real Data + Model Retrain
> Collect real player data across multiple games. Dev key is free and regenerable at developer.riotgames.com — apply for a production key when deploying.

- [x] Add required API keys to `.env`
- [x] Pipeline proven end-to-end: `make collect → make features → make train` working
- [x] Real data collection: 129 OpenDota (13 seed pros + 116 random), 12 Steam, 10 LoL, 5 Valorant
- [x] Feature engineering: 94 players, 27 features, behavioral + network proxies + Sionna joined → `data/03_features/player_features.parquet`
- [x] Models trained and saved: XGBoost, LightGBM, CatBoost, Ensemble, LogisticRegression, Scaler, SHAP (AUC=1.0 — heuristic label trivially separable)
- [x] `platform_encoded` added as 27th feature: 0=opendota, 1=steam, 2=riot_lol, 3=riot_valorant
- [x] `src/playerpulse/collectors/riot.py` — RiotLoLCollector + RiotValorantCollector built
- [x] Rate limit fixed: `time.sleep(6.0)` between OpenDota players (5 req/player @ 60 req/min)
- [x] OpenDota /explorer fixed: `player_matches TABLESAMPLE SYSTEM(0.01)` (old `players` table + `win`/`lose` cols no longer exist)
- [x] `notebooks/03_model_evaluation.ipynb` — model evaluation notebook built (loads real parquet, CV, SHAP, ROC)
- [x] GitHub Release `v1.0-models` created with all 7 .joblib files
- [x] `train.py` SHAP: switched to LightGBM (XGBoost 2.x `[6E-1]` base_score parse error)

---

## Sprint 2.6 — Real Network Signals + Sionna Rearchitecture
> Fix the circular network feature problem. Sionna CAN strengthen the model — but only once real signals anchor it. Build in stages: real proxies first, then ground Sionna with those proxies + ping, then use Sionna for chat agent what-if analysis.

**The problem with the current approach:**
`behavior → archetype → Sionna scenario → network features → model`
Network features are a function of behavioral features. The model learns a circular relationship, not a real one.

**The progression:**
| Stage | Network features | Model value |
|---|---|---|
| Current | Archetype → Sionna (circular) | Noise |
| Step 1 | Real API proxies (abandon_rate, etc.) | Real signal |
| Step 2 | Proxies + ping → Sionna (grounded) | Real + fuller picture |
| Studio data | Real network logs → Sionna validation | Best possible |

**Step 1 — Extract real network proxies from existing API data**
- [x] `src/playerpulse/features/engineer.py` — add `compute_network_proxy_features()`:
  - OpenDota: `abandon_rate` (leaver_status != 0), `abnormal_duration_rate` (duration < 5min or > 2h)
  - Riot LoL: `remake_rate` (games < 5 min), `early_exit_rate` (5–20 min)
  - Riot Valorant: `early_exit_rate` (match length < 10 min)
  - Steam: `short_session_rate` (sessions < 10 min as fraction of total)
- [x] Replace synthetic `p95_latency_ms`, `packet_loss_rate`, `jitter_ms`, `disconnect_count` in `FEATURE_COLS` (`train.py`) with real proxy features above
- [x] Update `build.py` to only join `avg_sinr_db` + `peak_hour_latency_ms` from Sionna output
- [x] Update `synthetic.py` to generate plausible proxy values for demo players

**Step 2 — Ground Sionna with real inputs**
- [ ] Frontend: optional "Your average ping (ms)" input in `PlayerSearch.jsx`
- [ ] `api/services/data_service.py` `get_player_live()`: accept optional `ping_ms` param
  - If provided: use ping + real proxy signals to select Sionna scenario → derive `avg_sinr_db` + `peak_hour_latency_ms` (now grounded, not guessed)
  - If not provided: fall back to archetype-inferred scenario
- [ ] Keep `avg_sinr_db` and `peak_hour_latency_ms` in FEATURE_COLS — grounded by ping when available
- [ ] Once real proxies exist: feed them as conditioning inputs to Sionna → Sionna expands proxies into a fuller network picture → this IS genuine feature engineering, not circular

**Step 3 — Sionna as what-if analysis in the chat agent**
- [ ] `api/agents/churn_analyst.py` — add `analyze_network_risk` tool:
  - Takes player's network scenario (from ping or proxy signals)
  - Uses Sionna to model degradation: "at 200ms latency, disconnect rate increases 3x for this archetype"
  - Returns plain-English network risk statement for the LLM to include in chat responses
  - This is the visible competitive moat — network-aware churn explanations no competitor offers

**Step 4 — Retrain**
- [ ] `make features && make train`
  - Verify: real proxy features appear in parquet
  - Verify: SHAP surfaces `abandon_rate` or `remake_rate` as top drivers for at least one segment
  - Verify: MLflow AUC improves vs previous run (real signals > synthetic noise)

---

## Sprint 4 — Backend Live Lookup (NO Supabase)
> Implement the service stubs and wire up the live player lookup flow. No auth, no database — just the core prediction loop. Supabase is deferred to Sprint 3 (after deploy).

**Architecture:** `GET /api/v1/players/{platform}/{player_id}` → live API call → feature engineering → model prediction → SHAP → response

```
collector.collect(player_id)          saves JSON to data/01_raw/{platform}/
standardize_{platform}(player_id)     reads those files → list[PlayerActivity]
build_features_for_player(...)        behavioral features + real network proxies
                                      (abandon_rate, remake_rate, short_session_rate, etc.)
ping_ms (optional, from frontend)     grounds avg_sinr_db + peak_hour_latency_ms via Sionna scenario
predict_churn(features)               ensemble.predict_proba()[0][1]
compute_shap_live(features)           TreeExplainer on-the-fly (explainer cached)
analyze_network_risk (chat agent)     Sionna what-if analysis for network-aware explanations
```

**Files (implement in this order):**

- [x] `api/services/model_service.py` — FEATURE_COLUMNS fixed + all functions implemented
- [x] `api/services/shap_service.py` — live TreeExplainer (lru_cache), compute_shap_live(), FEATURE_LABELS updated (27 features)
- [x] `api/services/data_service.py` — all functions + get_player_live() implemented
- [x] `api/registry/game_registry.py` — riot_lol + riot_valorant added
- [x] `api/routers/players.py` — search_players + get_player_analytics implemented (uses get_player_live for live lookup)
- [x] `api/agents/churn_analyst.py` — all 4 tools + get_agent() implemented (direct LLM streaming; LangChain 1.2.x changed AgentExecutor API)
- [x] `api/routers/chat.py` — streaming endpoint implemented (same pattern as demo chat)
- [ ] Verify via `/docs`:
  - `GET /api/v1/players/games` returns 4 platforms including riot_lol + riot_valorant
  - `GET /api/v1/players/opendota/87278757` returns `prediction.churn_probability` + `shap_values` array
  - Chat endpoint streams a real answer mentioning player-specific context

---

## Sprint 6 — Frontend Live Lookup
> Wire the game selector → player ID → analytics flow. Components are already built — this is mostly implementing 3 stubs and wiring them together.

- [x] `frontend/src/api/players.js` — fetchSupportedGames, fetchPlayerAnalytics, fetchModels, fetchPlayers implemented
- [x] `frontend/src/hooks/usePlayer.js` — fetchPlayer + useEffect implemented
- [x] `frontend/src/components/PlayerSearch/PlayerSearch.jsx` — form + CSS implemented
- [x] `frontend/src/pages/Home.jsx` — already complete (PlayerSearch + usePlayer + AnalyticsPanel + ChatPanel already wired)

- [ ] Verify end-to-end:
  - `http://localhost:5173` → select "Dota 2" → enter `87278757` → see AnalyticsPanel with churn score
  - ShapChart renders with network features visible
  - ChatPanel responds with player-specific context
  - Select "League of Legends" → enter `Faker#KR1` → same flow works

---

## Sprint 8 — Deploy
> Get the live product accessible at a real URL.

- [x] Backend → Render — https://playerpulse-cfyi.onrender.com
- [x] Frontend → Vercel — https://player-pulse-ashen.vercel.app
- [x] Demo page works end-to-end (synthetic players, SHAP, streaming chat)
- [x] Demo models fix: `models/demo/` committed to git; `demo_service.py` loads from `DEMO_MODELS_DIR` (never from `MODELS_DIR`) — demo works on Render without a persistent disk
- [x] `api/startup.py` — `ensure_models()`: on cold start, downloads missing .joblib files from `MODEL_RELEASE_URL` (GitHub Release). Subsequent starts skip if files exist.
- [x] `api/main.py` — lifespan hook calls `ensure_models()` on startup
- [x] `api/config.py` — `MODEL_RELEASE_URL` env var added
- [x] `Makefile` — `make release-models TAG=v1.0-models` (gh CLI upload to GitHub Release)
- [x] `Makefile` — `make sync-demo-models` (copies models/ → models/demo/, commits)
- [x] GitHub Release `v1.0-models` live: https://github.com/nshreeyut/PlayerPulse/releases/tag/v1.0-models

- [ ] **ONE STEP REMAINING** — do in Render browser dashboard:
  1. `playerpulse-api` → Disks → Add Disk: name=`models`, mount=`/var/data`, size=1 GB
  2. Environment → add `MODELS_DIR` = `/var/data/models`
  3. Environment → add `MODEL_RELEASE_URL` = `https://github.com/nshreeyut/PlayerPulse/releases/download/v1.0-models`
  4. Trigger Manual Deploy → models auto-download → live player lookup works

- [ ] Verify production end-to-end: https://player-pulse-ashen.vercel.app → select Dota 2 → enter `87278757` → see prediction + SHAP

**Future retrains (after more data / Riot production key):**
```bash
make collect
make features
make train
make release-models TAG=v1.1-models
# Update MODEL_RELEASE_URL in Render → trigger redeploy
```

---

## Data Expansion (ongoing, after deploy)
> Strengthen the model on your own — no studios needed.

- [ ] Scale OpenDota: `run_all.py` line 135 → change `target=200` to `target=5000`. Free, no rate limit.
- [ ] Apply for Riot production key at developer.riotgames.com (persistent, 500 req/10s) → enables 10k+ LoL players
- [ ] Add Chess.com collector: `src/playerpulse/collectors/chess_com.py` — public API, no key, 150M players, very clear churn signal (daily puzzle/game frequency drops sharply before churn)
- [ ] Fix churn labels: update `churn_threshold_days` logic to forward-looking definition (inactive 14d AND still inactive 14d later = true churn, not just point-in-time snapshot)
- [ ] Retrain after each data expansion: `make collect → make features → make train`

---

## Sprint 3 — Database + Auth (DEFERRED — after deploy)
> Replace flat files with real persistence. Only needed when external studios sign up.

- [ ] Supabase project setup — create project, run schema migrations
- [ ] `api/middleware/auth.py` — validate `X-API-Key` header → attach `studio_id`; exclude `/api/v1/demo/*`
- [ ] `api/routers/studios.py` — `POST /api/v1/studios`, `GET /api/v1/studios/me`
- [ ] `api/models/studio.py` — Pydantic schemas: `Studio`, `StudioCreate`
- [ ] `api/services/studio_service.py` — create studio, hash API key, validate key
- [ ] Update `data_service.py` to query Supabase instead of parquet (swap one file, no router changes)
- [ ] `api/main.py` — register studios router + auth middleware

---

## Sprint 5 — File Upload Pipeline (DEFERRED — after Sprint 3)
> Studio self-serve CSV/Excel ingestion. Requires Supabase (Sprint 3) first.

- [ ] `api/routers/ingest.py` — `POST /api/v1/ingest/upload`, `GET /api/v1/ingest/jobs/{job_id}`
- [ ] `api/agents/schema_agent.py` — Nemotron column mapping
- [ ] `api/services/ingest_service.py` — BackgroundTask: schema mapping → standardize → engineer → score → store
- [ ] `api/services/mapping_service.py` — apply saved `FieldMap` to raw rows
- [ ] Verify: upload CSV with non-standard column names → schema agent maps them → players appear with scores

---

## Sprint 7 — PyPI SDK + CLI (DEFERRED)

- [ ] `src/playerpulse/cli.py` — Typer CLI: `playerpulse connect`, `playerpulse sync`
- [ ] `pyproject.toml` — add `[project.scripts]` entry
- [ ] Publish: `uv build && uv publish`

---

## Blockers / Decisions Log

| Date | Issue | Resolution |
|---|---|---|
| 2026-03-09 | Dropped Chess.com + Riot — too niche / requires key for demo | Replaced with Steam |
| 2026-03-09 | Prefect removed — over-engineered | Training triggered by `training_service.py` via API |
| 2026-03-09 | Default LLM switched to Groq | Free tier, fast, good tool-calling. Switch via `LLM_PROVIDER` env var |
| 2026-03-15 | Inserted Phase 6: NVIDIA Sionna network telemetry | 6G Developer Program integration — physically grounded synthetic telemetry; publish notebook as artifact |
| 2026-03-23 | Tree models give binary 0/1 on clean synthetic data | Replaced `ensemble.predict_proba()` with `_churn_score()` formula in demo; SHAP still from XGBoost |
| 2026-03-23 | LLM provider locked to Groq/OpenAI only | Expanded `get_llm()` to 7 providers; NVIDIA NIM added for Nemotron |
| 2026-03-23 | Product name clarified | Product = **PlayerPulse**. Internal Python package stays `game_churn` until renamed to `playerpulse` in Sprint 1 |
| 2026-03-23 | Architecture decisions locked | DB: Supabase. Auth: Supabase Auth (browser) + custom API keys (SDK). File upload: FastAPI BackgroundTasks. Multi-tenancy: row-level `studio_id`. Deployment: Render + Supabase + Vercel |
| 2026-03-23 | Three-tier product structure defined | Demo (synthetic, no auth) / Website (CSV+Excel, non-technical studios) / SDK/PyPI (any format, direct DB, technical studios) |
| 2026-03-23 | Sionna moved to Sprint 2 (was Phase 6) | Train with network features from day one. Sionna bootstraps before real studio data. Network data = competitive moat — no competitor has this |
| 2026-03-23 | Shared model for v1, per-studio for v2 | v2 per-studio models = premium tier |
| 2026-03-23 | Outcomes table added to DB schema | Tracks whether predictions were correct (actually_churned bool). Critical for the feedback loop — model retrains on real outcomes over time. Without this the model never learns if it was right. Studios report outcomes via SDK or dashboard. |
| 2026-03-23 | PyPI SDK planned | PyPI name: `player-pulse`. Module rename: `src/game_churn/` → `src/playerpulse/`. CLI built with Typer: `playerpulse connect`, `playerpulse sync` |
| 2026-04-05 | Sprint 2 model retrain deferred | All network feature code is done (schema, simulation, synthetic data, train.py, demo_service). Retrain deferred until real API data is collected — avoids training twice. Run: `python -m playerpulse.models.train --synthetic` for synthetic baseline or wait for real data. |
| 2026-04-05 | Sprint 2 notebook deferred | `notebooks/02_network_telemetry.ipynb` paused — will create once model is trained on real data so SHAP plots are meaningful. |
| 2026-04-06 | RAWG API budget optimization | 20k req/month limit. Changes: (1) disk cache-first on `get_game_by_slug` and `collect` — skips API if file < 30 days old; (2) `max_review_pages` default lowered 5→2 (40 reviews, sufficient for NLP); (3) `force=True` param added to bypass cache. Per-game cost drops from 6 → 3 req on first fetch, 0 on cache hits. |
| 2026-04-06 | Real data pipeline network feature gap fixed | `schema.py` `PlayerFeatures` now includes all 6 network fields. `build.py` now infers archetype from behavioral profile and runs Sionna simulation for each player before saving parquet — real data path now produces all 25 FEATURE_COLS. `make features` → `make train` is now fully functional. |
| 2026-04-13 | Sprint ordering changed | Sprint 4 (backend live lookup) + Sprint 6 (frontend) moved before Sprint 3 (Supabase). Ship the live product first, add multi-tenancy when studios exist. |
| 2026-04-13 | Live lookup architecture | `data_service.get_player_live()` calls `collector.collect()` (saves to disk) then uses existing `standardize_*()` functions — reuses all existing code, no in-memory variants needed. |
| 2026-04-13 | SHAP approach changed | Pre-computed SHAP (200 test-set players) replaced with live TreeExplainer computation. Explainer object cached with lru_cache. Works for any player, not just training set. |
| 2026-04-13 | model_service.py FEATURE_COLUMNS bug | FEATURE_COLUMNS in model_service.py has wrong column names vs train.py FEATURE_COLS — must fix before any prediction works. |
| 2026-04-13 | Sionna role rearchitected | Sionna moved OUT of feature engineering pipeline. Real network proxies (abandon_rate, remake_rate, short_session_rate) extracted from API data instead. Sionna reframed as what-if analysis tool in the chat agent — takes player ping/scenario, models degradation, returns network risk statement. Self-reported ping from frontend grounds avg_sinr_db + peak_hour_latency_ms via Sionna scenario selection. |
| 2026-04-13 | Riot API key strategy | Dev key (24h) is free to regenerate at developer.riotgames.com — use it for local data collection. Apply for production key (500 req/10s, persistent) when deploying. |
| 2026-04-17 | XGBoost 2.x + SHAP incompatibility | shap.TreeExplainer fails on XGBoost 2.x models (base_score serialized as string). Fixed: shap_service.py and demo_service.py now use LightGBM for SHAP. Equivalent quality. |
| 2026-04-17 | LangChain 1.2.x API change | create_tool_calling_agent + AgentExecutor removed in LangChain 1.2.x. Fixed: chat.py uses direct LLM streaming (same as demo). churn_analyst.py keeps tool definitions but get_agent() returns LLM directly. |
| 2026-04-17 | Sprint ordering / completion | Sprint 2.6 Step 1 + Sprint 4 + Sprint 6 fully implemented. Feature set: 27 cols (19 behavioral + 5 real network proxies + 2 Sionna + platform_encoded). Model retrained on synthetic data. |
| 2026-04-19 | Demo players blank on live site | `demo_service.py` loaded from `MODELS_DIR` = `/var/data/models` (Render persistent disk, empty) → FileNotFoundError. Fix: created `models/demo/` with synthetic-trained .joblib files committed to git. `demo_service.py` hardcoded to `MODELS_DIR / "demo"` — never affected by the env var. |
| 2026-04-19 | OpenDota /explorer query broken | `players` table no longer has `win`/`lose` columns and is permission-denied. Fix: use `player_matches TABLESAMPLE SYSTEM(0.01)` — fast random sample on large table. `DISTINCT + ORDER BY RANDOM()` times out; `round(200/10_000_000, 4)` rounds to 0.0 — hardcode 0.01%. |
| 2026-04-19 | OpenDota rate limiting (429s) | 1s sleep between players = ~5 req/s → rate limited. Fix: 6s sleep between players (5 req/player ÷ 60 req/min free tier = 1 player/5s, 6s adds buffer). |
| 2026-04-19 | Model deployment to Render | No SSH on free tier; Render CLI has no disk upload; web shell has no file upload widget. Solution: GitHub Releases + `api/startup.py` auto-download on cold start. `ensure_models()` checks MODELS_DIR on startup, fetches missing files from MODEL_RELEASE_URL. Zero manual uploads after initial Render disk setup. |
| 2026-04-19 | train.py SHAP used XGBoost | XGBoost 2.x `[6E-1]` base_score parse error in SHAP. Fixed: `generate_shap_plots()` in `train.py` now uses LightGBM (consistent with shap_service.py and demo_service.py). |

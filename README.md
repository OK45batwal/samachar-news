# Samachar News

Real-time news intelligence platform with AI-powered insights, RSS ingestion, and SuperTokens authentication.

## Deploy to Render (1-Click)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/OK45batwal/samachar-news)

Or manually:

1. **Create Web Service** → connect `OK45batwal/samachar-news`
2. **Create PostgreSQL** database (free tier)
3. **Set env vars**: `SUPERTOKENS_CONNECTION_URI`, `SAMACHAR_SECRET_KEY`, `CORS_ORIGINS`, `PROMETHEUS_ENABLED=false`
4. **Deploy** — the `render.yaml` / `Procfile` handles everything

## Local Dev

```bash
source .venv/bin/activate
uvicorn backend.app:app --reload --port 8000
# Open http://localhost:8000
```

## Tests

```bash
pytest tests/ -v                    # unit + integration
npx playwright test tests/e2e/      # e2e (server must be running)
```

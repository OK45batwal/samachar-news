<div align="center">
  <h1>📰 Samachar News</h1>
  <p><strong>Real-time news intelligence platform</strong> — RSS ingestion, AI-powered insights, interactive world map.</p>
  <p>
    <a href="https://samachar-news.onrender.com/"><strong>🌐 Visit Samachar News →</strong></a>
  </p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11-blue?style=flat-square&logo=python">
    <img src="https://img.shields.io/badge/FastAPI-0.138+-00C853?style=flat-square&logo=fastapi">
    <img src="https://img.shields.io/badge/PostgreSQL-Async-316192?style=flat-square&logo=postgresql">
    <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square">
  </p>
  <p>
    <img src="docs/screenshots/landing.png" alt="Samachar Landing Page" width="800">
  </p>
  <br>
</div>

## ✨ Features

<table>
<tr>
  <td width="50%">
    <h3>📰 Live News Feed</h3>
    <p>60+ RSS sources — BBC, TechCrunch, ESPN, The Guardian, and more. Auto-ingested every 30 minutes.</p>
  </td>
  <td width="50%">
    <h3>🧠 AI Insights</h3>
    <p>Sentiment analysis, trending topic extraction, and risk indexing powered by scikit-learn & TextBlob.</p>
  </td>
</tr>
<tr>
  <td width="50%">
    <h3>🗺️ Interactive World Map</h3>
    <p>Live event heatmap with country-level sentiment, top keywords, and severity indicators. Powered by Leaflet.</p>
  </td>
  <td width="50%">
    <h3>🔍 Smart Search</h3>
    <p>Full-text search across all articles with category filters and instant results.</p>
  </td>
</tr>
<tr>
  <td width="50%">
    <h3>🔐 Secure Auth</h3>
    <p>SuperTokens-based login/register with session management, OAuth ready (Google, GitHub, Facebook).</p>
  </td>
  <td width="50%">
    <h3>🌓 Dark/Light Theme</h3>
    <p>Persistent theme toggle with smooth CSS transitions. Choose your vibe.</p>
  </td>
</tr>
<tr>
  <td width="50%">
    <h3>📌 Bookmarks</h3>
    <p>Save articles to organised folders. Never lose a story you care about.</p>
  </td>
  <td width="50%">
    <h3>📱 Responsive</h3>
    <p>Mobile-first layout. Works seamlessly on every screen size.</p>
  </td>
</tr>
</table>

## 📸 Screenshots

<table>
<tr>
  <td><img src="docs/screenshots/home.png" alt="Home page" width="400"></td>
  <td><img src="docs/screenshots/latest.png" alt="Latest news" width="400"></td>
</tr>
<tr>
  <td align="center"><em>🏠 Home Page</em></td>
  <td align="center"><em>📋 Latest News</em></td>
</tr>
<tr>
  <td><img src="docs/screenshots/map.png" alt="World map" width="400"></td>
  <td><img src="docs/screenshots/article.png" alt="Article view" width="400"></td>
</tr>
<tr>
  <td align="center"><em>🗺️ World Map</em></td>
  <td align="center"><em>📄 Article View</em></td>
</tr>
<tr>
  <td><img src="docs/screenshots/ai.png" alt="AI insights" width="400"></td>
  <td><img src="docs/screenshots/login.png" alt="Login page" width="400"></td>
</tr>
<tr>
  <td align="center"><em>🧠 AI Insights</em></td>
  <td align="center"><em>🔐 Login</em></td>
</tr>
</table>

## 🛠️ Tech Stack

<table>
<tr>
  <th>Layer</th>
  <th>Technologies</th>
</tr>
<tr>
  <td><strong>Backend</strong></td>
  <td>FastAPI · SQLAlchemy · SuperTokens · Alembic · Prometheus · Sentry · structlog</td>
</tr>
<tr>
  <td><strong>Frontend</strong></td>
  <td>Vanilla HTML/CSS/JS · Vite · Leaflet</td>
</tr>
<tr>
  <td><strong>Infrastructure</strong></td>
  <td>PostgreSQL · Redis · Docker · Render · GitHub Actions</td>
</tr>
<tr>
  <td><strong>AI/ML</strong></td>
  <td>scikit-learn · TextBlob · NumPy</td>
</tr>
</table>

## 🚀 Local Dev

```bash
# Setup
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Start the server
uvicorn backend.app:app --reload --port 8000
# Open http://localhost:8000
```

### 🌱 Seed & Ingest

```bash
python -m backend.seed                        # categories + sources
python -c "import asyncio; from backend.services.news_service import ingest_feeds; asyncio.run(ingest_feeds())"
```

### 🧪 Tests

```bash
python -m pytest tests/ -v                    # unit + integration
npx playwright test tests/e2e/                # e2e (server must be running)
```

## 📁 Project Structure

```
samachar-news/
├── backend/
│   ├── app.py              # FastAPI application & lifespan
│   ├── config.py           # Settings & env vars
│   ├── models/             # SQLAlchemy models
│   ├── routes/             # API endpoints
│   ├── services/           # Business logic (ingestion, feeds)
│   ├── auth/               # Authentication (JWT + SuperTokens)
│   ├── ai/                 # ML insights pipeline
│   └── websocket/          # Real-time updates
├── frontend/
│   ├── assets/             # Static assets (CSS, JS, images)
│   └── *.html              # Multi-page app (19 pages)
├── tests/                  # Pytest + Playwright e2e
└── scripts/                # Utility scripts
```

---

<div align="center">
  <p>Built with ❤️ — <a href="https://samachar-news.onrender.com/">Samachar News</a></p>
</div>

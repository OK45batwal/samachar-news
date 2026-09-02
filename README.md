# 📰 Samachar — Autonomous Truth-First News Intelligence Network

[![Tests & Build](https://img.shields.io/badge/tests-12%20passed%20%7C%2014%20pages%20verified-00F59B?style=for-the-badge&logo=pytest&logoColor=black)](https://github.com/OK45batwal/samachar-news)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Firebase Hosting](https://img.shields.io/badge/Firebase%20Hosting-Deployed%20Live-FFA611?style=for-the-badge&logo=firebase&logoColor=black)](https://samachar-news-2026.web.app)
[![Vite](https://img.shields.io/badge/Vite-6.4+-646CFF?style=for-the-badge&logo=vite&logoColor=white)](https://vitejs.dev)
[![Python 3.14](https://img.shields.io/badge/Python-3.14+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)

**Samachar** is an autonomous news intelligence network engineered to restore factual clarity to digital journalism. It continuously ingests and triangulates real-time dispatches from **25+ accredited international wire services** (Reuters, BBC, AP, The Hindu, Nature, TechCrunch, Bloomberg), strips sensationalist hyperbole, decomposes complex articles into atomic verifiable claims, and computes transparent **0–100% Truth Scorecards**.

🌐 **Live Deployment**: **[https://samachar-news-2026.web.app](https://samachar-news-2026.web.app)**

---

## 🌟 Key Highlights & Live Capabilities

### 1. ⚡ Autonomous 24x7 Real-World News Ingestion Pipeline
- **Continuous Multi-Wire Ingestion**: Automatic hourly GitHub Action (`.github/workflows/live_news_updater.yml`) scraping 25+ global RSS wire endpoints into a structured real-world dataset (`frontend/assets/data/news.json`).
- **Semantic Wire Triangulation**: Corroborates breaking stories across multiple independent newsrooms (e.g., verifying a tech breakthrough across Reuters, IEEE Spectrum, and Bloomberg).
- **Sensationalism & Clickbait Penalty Engine**: Detects emotional hyperbole and uncredited assertions, deducting up to 40% from the credibility index.
- **Atomic Claim Extraction**: Automatically parses key assertions, quotes, and primary evidence citations.

### 2. 🛡️ High-Security One-Step Authentication & Data Rights
- **Direct 1-Step Auth**: Instant registration and login with Argon2/PBKDF2 salted password hashing and JWT sessions.
- **Brute-Force Lockout Defense**: Progressive lockout (5 failed attempts triggers temporary security lockout).
- **Universal Permanent Account Deletion**: Full user data sovereignty with instant `DELETE /api/auth/account` erasing tokens, bookmarks, and activity logs.
- **Enterprise Security Headers**: Strict HSTS (`max-age=31536000`), `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, and `X-XSS-Protection`.

### 3. 🎨 Obsidian Truth Design System (TasteSkill Tokens)
- **Visual Design**: Obsidian Dark (`#08090C`) and Editorial Light modes with Emerald Glow accents (`#00F59B`).
- **Bento Grid Hero Layout**: Interactive spotlight lead stories with live credibility metrics and wire attribution tags.
- **Interactive Claim Workbench (`factcheck.html`)**: Instant in-page claim verifier with sample tests (`#MalariaVaccine`, `#1.4nmChips`, `#ClickbaitTest`).
- **Encrypted Bookmarks Archive (`bookmarks.html`)**: Local and cloud-synchronized saved reading lists.
- **User Preference Center (`profile.html`)**: Custom truth thresholds, edition switchers, and reading stats.

---

## 🏛️ System Architecture

```mermaid
graph TD
    subgraph Ingestion ["24x7 Wire Ingestion & AI Engine"]
        Cron["GitHub Actions Hourly Cron"] --> IngestScript["scripts/cron_ingest.py"]
        IngestScript --> RSS["25+ Global RSS Wire Feeds"]
        RSS --> FactCheckEngine["MEKA 3.0 Fact-Checker (backend/ai/fact_checker.py)"]
        FactCheckEngine --> DatasetExport["frontend/assets/data/news.json (150+ Live Stories)"]
    end

    subgraph CDN ["Static Distribution Layer (Firebase CDN)"]
        DatasetExport --> FirebaseHosting["Firebase Global Edge Network"]
        HTMLPages["14 Optimized Pages (home, factcheck, profile, etc.)"] --> FirebaseHosting
    end

    subgraph Client ["Client Browser Execution"]
        FirebaseHosting --> BrowserApp["Samachar Web App (Vanilla JS + Modern CSS)"]
        BrowserApp --> CacheEngine["Local Storage & Token Session"]
        BrowserApp --> SearchPalette["Instant ⌘K Command Palette"]
    end

    subgraph Backend ["Optional Local/Dedicated API (:8000)"]
        FastAPI["FastAPI REST Services"]
        DB[(SQLite / PostgreSQL)]
        FastAPI --> DB
        BrowserApp -.->|Local Dev Fallback| FastAPI
    end
```

---

## 🚀 Quickstart & Setup

### Prerequisites
- **Python 3.11+** (Python 3.14 recommended)
- **Node.js 18+** & **npm**

### 1. Clone the Repository
```bash
git clone https://github.com/OK45batwal/samachar-news.git
cd samachar-news
```

### 2. Backend Setup & Run (Port 8000)
```bash
# Create & activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run automated 24x7 news ingestion & dataset update
python3 scripts/cron_ingest.py

# Start FastAPI server
uvicorn backend.app:app --reload --port 8000
```
- **Backend API**: `http://localhost:8000/api`
- **Interactive OpenAPI Docs**: `http://localhost:8000/docs`

### 3. Frontend Setup & Run (Port 5173)
```bash
# Install frontend dependencies
npm install

# Start Vite development server
npm run dev
```
- **Public Landing Page**: `http://localhost:5173/index.html`
- **Live News Portal**: `http://localhost:5173/home.html`
- **Fact-Checking Tool**: `http://localhost:5173/factcheck.html`
- **User Profile & Account Deletion**: `http://localhost:5173/profile.html`

---

## 🧪 Comprehensive Verification & Test Suite

Run the end-to-end verification pipeline (UI page audit, backend pytest, Vite production build):

```bash
npm test
```

### Individual Test Commands
```bash
# 1. Run 12 Backend unit & integration test suites
pytest tests/ -v

# 2. Run UI/UX structure & link audit across all 14 HTML pages
npm run audit:ui

# 3. Compile Vite production bundle
npm run build
```

---

## 🔮 Strategic Product Roadmap & System Improvements (Research-Backed 2026/2027)

Based on emerging industry standards in automated fact-checking, bias transparency, and news intelligence (such as **Full Fact AI**, **Ground News**, and **Community Notes consensus algorithms**), here are the top recommended features and architectural upgrades for Samachar:

### 1. 🧠 Multi-Model AI Consensus Engine (Hallucination Proofing)
- **Problem**: Relying on a single AI model can introduce hallucination risks or subtle training biases.
- **Upgrade**: Implement a multi-model consensus verification pipeline (querying Gemini 2.5, Claude 3.7, and o3-mini in parallel). If all models agree on evidence citations, the claim receives a *Triple-Verified* badge; if they diverge, the claim is flagged for human editorial triage.

### 2. ⚖️ Media Bias Spectrum & Coverage Blindspot Heatmaps (Ground News Paradigm)
- **Problem**: Readers are often trapped in partisan echo chambers without knowing how other outlets frame the same event.
- **Upgrade**: Add an **Ideological Distribution Bar** (Left / Center / Right) on every article scorecard showing how major outlets across the political spectrum are covering the topic, highlighting which perspective is under-reporting a given story.

### 3. 👥 Algorithmic Community Notes (Bridging Consensus Model)
- **Problem**: Centralized fact-checking can be perceived as top-down.
- **Upgrade**: Implement a decentralized context-addition mechanism inspired by X Community Notes. When readers submit factual context or primary documents, the note only becomes public if readers across diverse past voting profiles rate it as *Helpful* and *Well-Sourced*.

### 4. 🔍 Deepfake & Synthetic Media Forensic Scanner (C2PA Integration)
- **Problem**: Generative AI imagery and synthetic video are increasingly distributed as breaking news.
- **Upgrade**: Integrate C2PA (Coalition for Content Provenance and Authenticity) cryptographic provenance verification and neural noise-pattern analysis to detect AI-generated or manipulated images in breaking wire dispatches.

### 5. 🏷️ Schema.org `ClaimReview` Structured Data Export
- **Problem**: Fact-checks should be discoverable by search engines and international fact-checking repositories.
- **Upgrade**: Automatically embed JSON-LD `ClaimReview` markup on every article and fact-check result, making Samachar's scorecards indexable by Google Fact Check Tools and ClaimReview search explorers.

### 6. ⚡ Sub-Second Vector Search & Semantic RAG (pgvector / Qdrant)
- **Problem**: Keyword search misses conceptual relationships between breaking claims and past debunks.
- **Upgrade**: Store dense vector embeddings (using `text-embedding-3-small` or `nomic-embed-text`) for all ingested news stories to enable sub-50ms semantic search, instant repeat-claim detection, and automated historical timeline reconstruction.

### 7. 📲 Progressive Web App (PWA) Offline Sync & Breaking News Web Push
- **Problem**: Readers in low-connectivity areas or transit lose access to news feeds.
- **Upgrade**: Enhance the service worker with Background Sync and IndexedDB to cache the entire latest 150-story dataset for complete offline reading, paired with encrypted Web Push notifications for major breaking verified events.

---

## 📁 Repository Structure

```
samachar-news/
├── backend/
│   ├── ai/               # MEKA 3.0 Fact-checking NLP & claim extractor
│   ├── api/              # FastAPI router endpoints (auth, news, bookmarks, factcheck)
│   ├── models/           # SQLAlchemy database models (User, Article, Source, Bookmark)
│   ├── services/         # Rate limiting, news aggregation, and wire collectors
│   ├── app.py            # Headless FastAPI application & CORS configuration
│   ├── config.py         # Security settings & JWT configuration
│   └── seed.py           # Database seeder with benchmark stories
├── frontend/
│   ├── assets/
│   │   ├── css/          # TasteSkill tokens (variables.css, layout.css, style.css)
│   │   ├── js/           # Resilient API client (api.js), layout controller (layout.js)
│   │   ├── data/         # Live 24x7 ingested news dataset (news.json)
│   │   └── icons/        # SVG brand assets & favicons
│   ├── index.html        # Public marketing landing page & in-page fact verifier
│   ├── home.html         # Main authenticated news dashboard & bento hero
│   ├── latest.html       # Channel feeds (World, Tech & AI, India, Business, etc.)
│   ├── factcheck.html    # Interactive claim verification workbench
│   ├── login.html        # 1-step sign in with brute-force protection
│   ├── register.html     # 1-step instant account creation
│   ├── bookmarks.html    # Saved reading list & research archive
│   ├── profile.html      # User preferences, reading stats, & permanent delete account
│   ├── article.html      # Article view with truth scorecard & audio reader
│   ├── trending.html     # High-engagement verified stories
│   ├── about.html        # 4-stage pipeline & credibility index spectrum
│   ├── privacy.html      # Privacy policy & data protection guarantees
│   └── terms.html        # Terms of service & verification disclaimers
├── scripts/
│   ├── cron_ingest.py    # 24x7 RSS wire ingester and dataset exporter
│   └── ui_audit.py       # Automated UI structure & navigation audit script
├── tests/                # Pytest suites for auth, fact-checking & API endpoints
├── firebase.json         # Firebase Hosting & security headers configuration
└── package.json          # Vite bundler, scripts, and test runner
```

---

## 📜 License

Distributed under the **MIT License**. Engineered with precision for absolute factual clarity.

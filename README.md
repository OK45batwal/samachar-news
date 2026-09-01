# 📰 Samachar — Truth-First News Intelligence Platform

Samachar is an autonomous, fact-checking news intelligence platform. It ingests 60+ global and regional news feeds, extracts structured factual assertions, detects sensationalism and clickbait, and provides transparent Truth Scorecards across breaking stories.

---

## ✨ Key Capabilities

1. **Truth Scorecard & Verification Engine**:
   - Automated credibility scoring (0–100%)
   - Deconstructs stories into structured claims (`Data-Backed Assertion`, `Official Statement`, `Verified Fact`)
   - Cross-source wire corroboration (Reuters, AP, BBC, Nature, The Hindu, Bloomberg, etc.)
   - Sensationalism & clickbait penalty index

2. **Interactive Fact-Checking Workbench (`factcheck.html`)**:
   - Test any news headline, quote, or viral statement in real time
   - Instant evidence decomposition and corroboration network graph

3. **High-Taste Editorial UI/UX**:
   - Deep Obsidian Dark (`#07090E`) & Clean Editorial Light modes
   - Bento Grid Hero layout with Truth Radar spotlight
   - Live ticker marquee with WebSocket real-time updates
   - Text-to-speech audio reader on articles
   - Interactive Geopolitical Fact Map with Leaflet

---

## 🚀 Quickstart

### 1. Start Server
```bash
# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Start FastAPI server on port 8000
uvicorn backend.app:app --reload --port 8000
```

### 2. Open in Browser
- **Main Portal**: `http://localhost:8000/home.html`
- **Fact-Check Tool**: `http://localhost:8000/factcheck.html`
- **Landing Page**: `http://localhost:8000/index.html`
- **API Docs**: `http://localhost:8000/docs`

---

## 🧪 Testing

```bash
.venv/bin/pytest tests/ -v
```

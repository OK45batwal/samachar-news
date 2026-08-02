# Contributing to Samachar News

Thank you for your interest in contributing to **Samachar News**! We welcome contributions from developers, designers, and documentation writers of all skill levels.

---

## 🚀 Quick Start Guide

### 1. Prerequisites
- **Python**: `3.10+` (Virtual environment recommended)
- **Node.js**: `18+` & `npm`

### 2. Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/OK45batwal/samachar-news.git
cd samachar-news

# Set up Python virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install
```

### 3. Running Locally

```bash
# Start the FastAPI backend server
uvicorn backend.app:app --reload --port 8000

# In a separate terminal, start the Vite frontend dev server
npm run dev
```

Visit `http://localhost:8000` or `http://localhost:5173` in your browser.

---

## 🧪 Testing & Linting

Before opening a Pull Request, make sure all tests pass and code styling adheres to our linter rules:

```bash
# Run backend test suite
.venv/bin/pytest

# Run Ruff code linter
.venv/bin/ruff check --fix .

# Verify frontend production build
npm run build
```

---

## 📝 Commit Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat: ...` for new features (e.g., `feat(ai): Add sentiment analyzer`)
- `fix: ...` for bug fixes (e.g., `fix(db): Add SQLite WAL mode pragma`)
- `docs: ...` for documentation updates
- `style: ...` for formatting and styling changes

---

## 🔀 Submitting Pull Requests

1. Fork the repository on GitHub.
2. Create a feature branch: `git checkout -b feature/amazing-feature`.
3. Make your changes and commit with descriptive messages.
4. Run tests and linting to ensure zero regressions.
5. Push to your branch: `git push origin feature/amazing-feature`.
6. Open a Pull Request on the main repository explaining your changes.

---

## 📜 Code of Conduct

Please be respectful and polite in all issues, pull requests, and discussions. We are dedicated to providing a friendly and welcoming environment for everyone.

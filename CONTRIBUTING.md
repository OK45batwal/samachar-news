# Contributing to Samachar News 📰

Thank you for your interest in contributing to **Samachar News**! We welcome contributions from developers of all skill levels. Whether you are fixing bugs, improving documentation, adding new features, or optimizing performance, your help is greatly appreciated.

---

## 📜 Table of Contents

1. [Code of Conduct](#-code-of-conduct)
2. [How Can I Contribute?](#-how-can-i-contribute)
   - [Reporting Bugs](#reporting-bugs)
   - [Suggesting Enhancements](#suggesting-enhancements)
   - [Submitting Pull Requests](#submitting-pull-requests)
3. [Local Development Setup](#-local-development-setup)
4. [Coding & Style Guidelines](#-coding--style-guidelines)
5. [Running Tests & Quality Checks](#-running-tests--quality-checks)
6. [Commit Message Conventions](#-commit-message-conventions)

---

## 📜 Code of Conduct

By participating in this project, you agree to maintain a respectful, inclusive, and friendly environment for everyone. Please treat all contributors with kindness, empathy, and professional respect.

---

## 💡 How Can I Contribute?

### Reporting Bugs

If you find a bug or unexpected behavior:
1. Check the existing [GitHub Issues](https://github.com/OK45batwal/samachar-news/issues) to ensure it hasn't already been reported.
2. Open a new issue with a clear, descriptive title.
3. Include detailed steps to reproduce the issue, expected vs. actual behavior, and environment details (Python version, OS, browser).

### Suggesting Enhancements

Feature requests and architectural suggestions are always welcome!
1. Check existing issues or discussions before creating a new one.
2. Clearly explain the proposed feature, why it is beneficial, and potential implementation ideas.

### Submitting Pull Requests

1. **Fork** the repository and clone your fork locally.
2. Create a descriptive feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```
3. Make your code modifications and ensure tests pass locally.
4. Push your branch to GitHub and create a **Pull Request (PR)** targeting the `main` branch.
5. Provide a clear PR description summarizing your changes.

---

## 🛠️ Local Development Setup

### 1. Prerequisites
- Python 3.10+
- Node.js 18+ and npm
- Git

### 2. Setup Environment
```bash
# Clone the repository
git clone https://github.com/OK45batwal/samachar-news.git
cd samachar-news

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install Python dependencies
pip install -r requirements.txt

# Install Node dependencies
npm install
```

### 3. Running Dev Servers
```bash
# Run FastAPI Backend (runs on http://localhost:8000)
uvicorn backend.app:app --reload --port 8000

# Run Vite Frontend Dev Server (runs on http://localhost:5173)
npm run dev
```

---

## 🎨 Coding & Style Guidelines

- **Python Code**: Follow PEP 8 standards. Use type annotations where applicable. We enforce linting via `ruff`.
- **Frontend Code**: Keep HTML/CSS/JS modular and clean. Avoid third-party bloated libraries where vanilla JS or native CSS variables suffice.
- **Security**: Never commit sensitive secrets, API keys, or credentials. Use `.env` files and `.env.example`.
- **Documentation**: Update [brain.md](file:///Users/omkar/samachar-news/brain.md) or [README.md](file:///Users/omkar/samachar-news/README.md) if adding new core architecture or endpoints.

---

## 🧪 Running Tests & Quality Checks

Before pushing your changes, run the test and linting suite to make sure all checks pass:

```bash
# 1. Run Ruff Linter
ruff check .

# 2. Run Pytest Integration & Unit Tests
pytest

# 3. Run Playwright End-to-End Tests (Optional, requires dev server running)
npx playwright test tests/e2e/
```

---

## 📝 Commit Message Conventions

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

- `feat:` A new feature for the user or system
- `fix:` A bug fix
- `docs:` Documentation changes only
- `style:` Code style fixes (formatting, missing semi-colons, etc.)
- `refactor:` Code restructuring without changing external behavior
- `test:` Adding or updating unit/integration tests
- `chore:` Build process, dependency updates, or tool changes

**Example Commit:**
```bash
git commit -m "feat: Add sentiment score filtering to news endpoint"
```

---

## 💖 Questions or Help?

If you need help getting started or have questions, feel free to open a [GitHub Issue](https://github.com/OK45batwal/samachar-news/issues) or start a discussion. Happy coding! 🚀

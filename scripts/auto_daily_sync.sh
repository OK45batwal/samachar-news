#!/usr/bin/env bash
# ==============================================================================
# SAMACHAR DAILY AUTONOMOUS NEWS INGESTION & DATASET UPDATER
# Can be run via crontab, systemd timer, or launchd every day or hourly.
# ==============================================================================

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${PROJECT_DIR}/logs"
LOCK_DIR="${LOG_DIR}/daily_sync.lockdir"
LOG_FILE="${LOG_DIR}/daily_sync.log"

mkdir -p "${LOG_DIR}"

# 1. Concurrency guard: POSIX atomic lock directory (compatible with macOS & Linux)
if ! mkdir "${LOCK_DIR}" 2>/dev/null; then
    PID_FILE="${LOCK_DIR}/pid"
    if [ -f "${PID_FILE}" ] && kill -0 "$(cat "${PID_FILE}")" 2>/dev/null; then
        echo "[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️ Another news sync task is actively running (PID $(cat "${PID_FILE}")). Exiting." >> "${LOG_FILE}"
        exit 0
    else
        # Stale lock cleanup
        rm -rf "${LOCK_DIR}"
        mkdir "${LOCK_DIR}"
    fi
fi
echo $$ > "${LOCK_DIR}/pid"
trap 'rm -rf "${LOCK_DIR}"' EXIT INT TERM

echo "=================================================================" >> "${LOG_FILE}"
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Starting Autonomous Daily News Synchronization..." >> "${LOG_FILE}"

cd "${PROJECT_DIR}"

# 2. Select Python executable (.venv or system python)
if [ -f "${PROJECT_DIR}/.venv/bin/python" ]; then
    PYTHON_BIN="${PROJECT_DIR}/.venv/bin/python"
else
    PYTHON_BIN="python3"
fi

# 3. Execute Wire Ingestion & MEKA 3.0 Fact-Checking Engine
echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📡 Fetching 25+ global wire feeds & updating DB/JSON/Sitemap..." >> "${LOG_FILE}"
"${PYTHON_BIN}" -m scripts.cron_ingest >> "${LOG_FILE}" 2>&1

# 4. Rebuild Production Frontend Assets (updates frontend/dist)
if command -v npm >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 📦 Rebuilding production distribution bundle..." >> "${LOG_FILE}"
    npm run build >> "${LOG_FILE}" 2>&1 || true
fi

# 5. Check if Firebase CLI is available to auto-push to live hosting
if command -v firebase >/dev/null 2>&1; then
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] 🚀 Deploying updated dataset to Firebase Hosting..." >> "${LOG_FILE}"
    firebase deploy --only hosting --project samachar-news-2026 >> "${LOG_FILE}" 2>&1 || true
fi

echo "[$(date '+%Y-%m-%d %H:%M:%S')] ✅ Daily News Sync completed successfully." >> "${LOG_FILE}"
echo "=================================================================" >> "${LOG_FILE}"

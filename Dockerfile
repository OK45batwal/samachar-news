# =======================================================
# Stage 1: Build Frontend Assets with Node.js
# =======================================================
FROM node:20-alpine AS frontend-builder
WORKDIR /app
COPY package.json ./
RUN npm install --ignore-scripts
COPY . .
RUN npm run build

# =======================================================
# Stage 2: Production Python Backend & Static Server
# =======================================================
FROM python:3.12-slim AS runner

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    PORT=8000

WORKDIR /app

# Install runtime system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY backend/ ./backend/
COPY scripts/ ./scripts/
COPY pyproject.toml ./
COPY --from=frontend-builder /app/frontend/dist/ ./frontend/dist/
COPY --from=frontend-builder /app/frontend/assets/ ./frontend/assets/

EXPOSE 8000

# Health check probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]

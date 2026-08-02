import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: 'tests/e2e',
  timeout: 30000,
  retries: 1,
  use: {
    headless: true,
    viewport: { width: 1280, height: 720 },
  },
  webServer: {
    command: process.env.CI ? 'python -m uvicorn backend.app:app --port 8000' : '.venv/bin/python -m uvicorn backend.app:app --port 8000',
    url: 'http://127.0.0.1:8000/health',
    reuseExistingServer: true,
    timeout: 20000,
  },
});

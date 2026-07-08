import { chromium } from 'playwright';
import { writeFileSync, mkdirSync } from 'fs';

const BASE = 'http://localhost:8000';
const OUT = 'docs/screenshots';

const pages = [
  { path: '/', name: 'landing', width: 1280, height: 800 },
  { path: '/home.html', name: 'home', width: 1280, height: 800 },
  { path: '/latest.html', name: 'latest', width: 1280, height: 800 },
  { path: '/map.html', name: 'map', width: 1280, height: 800 },
  { path: '/article.html?id=1', name: 'article', width: 1280, height: 800 },
  { path: '/login.html', name: 'login', width: 1280, height: 800 },
  { path: '/ai.html', name: 'ai', width: 1280, height: 800 },
];

const browser = await chromium.launch({ headless: true });
const ctx = await browser.newContext({ viewport: { width: 1280, height: 800 } });

for (const p of pages) {
  const page = await ctx.newPage();
  try {
    await page.goto(BASE + p.path, { waitUntil: 'networkidle', timeout: 15000 });
    await page.waitForTimeout(500);
    await page.screenshot({ path: `${OUT}/${p.name}.png`, fullPage: false });
    console.log(`✓ ${p.name}`);
  } catch (e) {
    console.log(`✗ ${p.name}: ${e.message}`);
  }
  await page.close();
}

await browser.close();

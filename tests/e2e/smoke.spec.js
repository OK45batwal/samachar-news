// @ts-check
import { test, expect } from '@playwright/test';

const BASE = 'http://localhost:8000';

test.describe('Critical user path', () => {

  test('home page loads and shows top stories', async ({ page }) => {
    await page.goto(BASE);
    await expect(page.locator('.hero-title')).toContainText('Real-Time News');
    await expect(page.locator('#featuredGrid')).toBeVisible();
  });

  test('latest page loads articles', async ({ page }) => {
    await page.goto(`${BASE}/latest.html`);
    await expect(page.locator('h1')).toContainText('Latest News');
    await expect(page.locator('.news-card').first()).toBeVisible({ timeout: 10000 });
    expect(await page.locator('.news-card').count()).toBeGreaterThanOrEqual(1);
  });

  test('category tab filters articles', async ({ page }) => {
    await page.goto(`${BASE}/latest.html`);
    const techTab = page.locator('button[data-cat="technology"]');
    await techTab.click();
    await expect(page).toHaveURL(/cat=technology/);
    await expect(page.locator('.news-card').first()).toBeVisible({ timeout: 10000 });
  });

  test('article page opens', async ({ page }) => {
    await page.goto(`${BASE}/latest.html`);
    await expect(page.locator('.news-card').first()).toBeVisible({ timeout: 10000 });
    await page.locator('.news-card').first().click();
    await expect(page).toHaveURL(/article\.html\?id=\d+/);
    await expect(page.locator('#articleTitle')).toBeVisible({ timeout: 5000 });
  });

  test('register and login flow', async ({ page }) => {
    const ts = Date.now();
    const email = `e2e_${ts}@test.com`;
    // Register
    await page.goto(`${BASE}/register.html`);
    await page.fill('#regName', 'E2E User');
    await page.fill('#regEmail', email);
    await page.fill('#regPassword', 'TestPass123');
    await page.fill('#regConfirm', 'TestPass123');
    await page.click('button[type="submit"]');
    // Should redirect to index after register
    await expect(page).toHaveURL(/index\.html/);

    // Login
    await page.goto(`${BASE}/login.html`);
    // Register used email as username (part before @)
    await page.fill('#loginUsername', `e2e_${ts}`);
    await page.fill('#loginPassword', 'TestPass123');
    await page.click('button[type="submit"]');
    // Should see username in header
    await expect(page.locator('.header-right')).toContainText(`e2e_${ts}`);
  });

});

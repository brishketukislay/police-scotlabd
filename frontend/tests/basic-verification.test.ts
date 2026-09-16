import { test, expect } from '@playwright/test';

test('should load application and show correct title', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait for app to load
  await page.waitForTimeout(5000);

  // Check page title
  const title = await page.title();
  expect(title).toBe('QuestHub — Dashboard Prototype');

  // Take screenshot
  await page.screenshot({ path: 'application-loaded.png', fullPage: true });
});
import { test, expect } from '@playwright/test';

test('debug: check for specific text that should be on login screen', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait for the app to finish checking (loader disappears) - wait longer
  await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 15000 });

  // Wait additional time for React to render
  await page.waitForTimeout(5000);

  // Check for the specific h1 text from Login.tsx
  const headingText = await page.locator('h1').textContent();
  console.log(`H1 text content: "${headingText}"`);

  // This should be "Enter the climb." if we're on the login screen
  expect(headingText).toContain('Enter the climb.');

  // Also take a screenshot
  await page.screenshot({ path: 'debug-h1-check.png', fullPage: true });
});
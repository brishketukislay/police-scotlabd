import { test, expect } from '@playwright/test';

test('debug: show what visible text is on the page by failing with information', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait for the app to finish checking (loader disappears)
  await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

  // Get all visible text content from the page using locator
  const textContent = await page.locator('body').textContent();

  // Deliberately fail the test to show the text content in the error message
  expect(textContent).toContain('VIEW PUBLIC DASHBOARD'); // This will fail and show us the actual text
});
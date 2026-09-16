import { test, expect } from '@playwright/test';

test('debug: check what text is actually on the page', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait for the app to finish checking (loader disappears)
  await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

  // Get all text content from the page
  const textContent = await page.textContent('body');

  // Log first 1000 characters to see what we're dealing with
  console.log('=== PAGE TEXT CONTENT (first 1000 chars) ===');
  console.log(textContent?.substring(0, 1000));
  console.log('=== END PAGE TEXT CONTENT ===');

  // Check for various possible variations of the public button text
  const possibleTexts = [
    'View public dashboard',
    'Public dashboard',
    'View Dashboard',
    'Public',
    'view public dashboard',
    'View Public Dashboard'
  ];

  console.log('\\n=== CHECKING FOR PUBLIC BUTTON TEXTS ===');
  for (const text of possibleTexts) {
    const found = textContent?.includes(text);
    console.log(`"${text}": ${found}`);
  }

  // Take screenshot
  await page.screenshot({ path: 'debug-actual-content.png', fullPage: true });
});
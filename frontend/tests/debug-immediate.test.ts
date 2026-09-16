import { test, expect } from '@playwright/test';

test('debug: check what is visible immediately after navigation', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait a bit for initial load
  await page.waitForTimeout(3000);

  // Take a screenshot
  await page.screenshot({ path: 'debug-immediate.png', fullPage: true });

  // Check for the checking text
  const checkingText = await page.locator('text=Connecting to QuestHub…').count();
  console.log(`Found "Connecting to QuestHub…" elements: ${checkingText}`);

  // Check for loader ring
  const loaderRing = await page.locator('.loader-ring').count();
  console.log(`Found .loader-ring elements: ${loaderRing}`);

  // Check for center-screen
  const centerScreen = await page.locator('.center-screen').count();
  console.log(`Found .center-screen elements: ${centerScreen}`);

  // Check if we can find any text at all
  const allText = await page.locator('body').textContent();
  console.log(`First 200 chars of body text: "${allText?.substring(0, 200)}"`);

  // Check for login screen elements directly (without waiting for checking to finish)
  const loginScreen = await page.locator('.login-screen').count();
  console.log(`Found .login-screen elements immediately: ${loginScreen}`);

  const loginCard = await page.locator('.login-card').count();
  console.log(`Found .login-card elements immediately: ${loginCard}`);
});
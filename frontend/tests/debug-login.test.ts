import { test, expect } from '@playwright/test';

test('debug: check login screen elements', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait for the app to finish checking (loader disappears)
  await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

  console.log('=== CHECKING IF WE ARE ON LOGIN SCREEN ===');

  // Check for Login component specific elements from Login.tsx
  const elementsToCheck = [
    { selector: 'text=Sign in', description: 'Sign in button' },
    { selector: 'text=View public dashboard', description: 'View public dashboard button' },
    { selector: '.login-screen', description: 'Login screen container' },
    { selector: '.login-card', description: 'Login card container' },
    { selector: '.brand', description: 'Brand container' },
    { selector: 'text=QUEST', description: 'QUEST text' },
    { selector: 'text=HUB', description: 'HUB text' },
    { selector: 'input[type="text"]', description: 'Username input' },
    { selector: 'input[type="password"]', description: 'Password input' }
  ];

  for (const { selector, description } of elementsToCheck) {
    try {
      const locator = page.locator(selector);
      const count = await locator.count();
      const visible = count > 0 ? await locator.first().isVisible() : false;
      console.log(`${description} (${selector}): count=${count}, visible=${visible}`);
    } catch (e) {
      console.log(`${description} (${selector}): ERROR - ${e.message}`);
    }
  }

  // Take a screenshot
  await page.screenshot({ path: 'debug-login-screen.png', fullPage: true });
});
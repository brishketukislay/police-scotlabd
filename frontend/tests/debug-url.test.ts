import { test, expect } from '@playwright/test';

test('debug: check current URL and take screenshot after load', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait a bit longer for app to initialize
  await page.waitForTimeout(3000);

  // Get current URL
  const url = page.url();
  console.log(`Current URL: ${url}`);

  // Take a screenshot
  await page.screenshot({ path: 'debug-url-check.png', fullPage: true });

  // Check if we can find any button at all
  const buttonCount = await page.locator('button').count();
  console.log(`Found ${buttonCount} button elements on page`);

  // If there are buttons, get their text content
  if (buttonCount > 0) {
    const buttons = page.locator('button');
    for (let i = 0; i < Math.min(buttonCount, 5); i++) {
      const buttonText = await buttons.nth(i).textContent();
      console.log(`Button ${i} text: "${buttonText}"`);
    }
  }

  // Pass the test so we can see the output
  expect(true).toBeTruthy();
});
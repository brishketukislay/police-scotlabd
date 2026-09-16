import { test, expect } from '@playwright/test';

test('debug: find the Public button on login page', async ({ page }) => {
  // Start from homepage
  await page.goto('http://localhost:5173', {
    waitUntil: 'networkidle'
  });

  // Wait for the app to finish checking (loader disappears)
  await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

  // Try multiple selectors for the Public button
  const selectors = [
    'button:has-text("Public")',
    'button:has-text("public")',
    'button:has-text("PUBLIC")',
    'button:has-text(" Public ")',
    '[role="button"]:has-text("Public")',
    'button >> text=Public'
  ];

  for (const selector of selectors) {
    console.log(`Trying selector: ${selector}`);
    const locator = page.locator(selector);
    const count = await locator.count();
    if (count > 0) {
      const visible = await locator.first().isVisible();
      console.log(`  Found ${count} elements, first visible: ${visible}`);
      if (visible) {
        console.log(`  SUCCESS: Using selector "${selector}"`);
        // Try to click it
        await locator.first().click();
        console.log(`  Clicked the button`);
        break;
      }
    } else {
      console.log(`  No elements found`);
    }
  }

  // Also check all button elements and their text content
  console.log(`\\n=== ALL BUTTON ELEMENTS ===`);
  const allButtons = page.locator('button');
  const buttonCount = await allButtons.count();
  console.log(`Total buttons: ${buttonCount}`);

  for (let i = 0; i < Math.min(buttonCount, 10); i++) {
    const button = allButtons.nth(i);
    const text = await button.textContent();
    const visible = await button.isVisible();
    const enabled = await button.isEnabled();
    console.log(`  Button ${i}: "${text?.trim()}" | visible: ${visible} | enabled: ${enabled}`);
  }

  // Take screenshot
  await page.screenshot({ path: 'debug-login.png', fullPage: true });
});
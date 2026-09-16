import { test, expect } from '@playwright/test';

test.describe('PublicView Component', () => {
  test('should render public dashboard after switching to public mode from login', async ({ page }) => {
    // Start from homepage
    await page.goto('http://localhost:5173', {
      waitUntil: 'networkidle'
    });

    // Wait for the app to finish checking (loader disappears)
    await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

    // On login screen, click the "View public dashboard" button
    const publicButton = page.locator('button:has-text("View public dashboard")');
    await expect(publicButton).toBeVisible({ timeout: 10000 });
    await publicButton.click();

    // Wait for navigation to public dashboard
    await page.waitForURL(/.*/);

    // Should now be in public mode - check for public dashboard title
    await expect(page.locator('h1:has-text("Public Dashboard")')).toBeVisible();

    // Check that PublicView component is rendered by looking for key elements
    await expect(page.locator('text=QuestHub Public Display')).toBeVisible();
    await expect(page.locator('text=Community Progress Dashboard')).toBeVisible();

    // Take a screenshot for visual verification
    await page.screenshot({ path: 'public-view-mode.png', fullPage: true });
  });

  test('should toggle fullscreen in public mode', async ({ page }) => {
    // Start from homepage
    await page.goto('http://localhost:5173', {
      waitUntil: 'networkidle'
    });

    // Wait for the app to finish checking (loader disappears)
    await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

    // On login screen, click the "View public dashboard" button
    const publicButton = page.locator('button:has-text("View public dashboard")');
    await expect(publicButton).toBeVisible({ timeout: 10000 });
    await publicButton.click();

    // Wait for navigation
    await page.waitForURL(/.*/);

    // Look for fullscreen button and click it
    const fullscreenButton = page.locator('button:has-text("Fullscreen")');
    await expect(fullscreenButton).toBeVisible({ timeout: 10000 });

    // Click to enter fullscreen
    await fullscreenButton.click();

    // Wait a bit for transition
    await page.waitForTimeout(1000);

    // Check if button changed to "Exit Full" (icon-only button now)
    const exitFullscreenButton = page.locator('button:has-text("Exit Full")');
    // Wait for the button to update
    await expect(exitFullscreenButton).toBeVisible({ timeout: 5000 });

    // Exit fullscreen
    await exitFullscreenButton.click();
    await page.waitForTimeout(1000);

    // Should be back to "Fullscreen" button
    await expect(fullscreenButton).toBeVisible({ timeout: 5000 });
  });
});
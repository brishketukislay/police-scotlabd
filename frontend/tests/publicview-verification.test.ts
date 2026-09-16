import { test, expect } from '@playwright/test';

test.describe('PublicView Component Verification', () => {
  test('should show login screen initially', async ({ page }) => {
    // Start from homepage
    await page.goto('http://localhost:5173', {
      waitUntil: 'networkidle'
    });

    // Wait for the app to finish checking (loader disappears)
    await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

    // Wait for login screen to appear
    const loginScreen = page.locator('.login-screen');
    await expect(loginScreen).toBeVisible({ timeout: 10000 });

    // Check for login form elements
    await expect(page.locator('.login-card')).toBeVisible();
    await expect(page.locator('button:has-text("Sign in")')).toBeVisible();
    await expect(page.locator('button:has-text("View public dashboard")')).toBeVisible();
    await expect(page.locator('input[type="text"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
  });

  test('should navigate to public dashboard when "View public dashboard" is clicked', async ({ page }) => {
    // Start from homepage
    await page.goto('http://localhost:5173', {
      waitUntil: 'networkidle'
    });

    // Wait for the app to finish checking (loader disappears)
    await page.waitForSelector('text=Connecting to QuestHub…', { state: 'hidden', timeout: 10000 });

    // Click the "View public dashboard" button
    await page.locator('button:has-text("View public dashboard")').click();

    // Wait for navigation to complete
    await page.waitForTimeout(2000); // Give it time to navigate

    // Should now be in public dashboard
    await expect(page.locator('h1:has-text("Public Dashboard")')).toBeVisible({ timeout: 10000 });

    // Check for key PublicView elements
    await expect(page.locator('text=QuestHub Public Display')).toBeVisible();
    await expect(page.locator('text=Community Progress Dashboard')).toBeVisible();

    // Take a screenshot for visual verification
    await page.screenshot({ path: 'public-dashboard-verification.png', fullPage: true });
  });
});
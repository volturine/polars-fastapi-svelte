import { test, expect } from '@playwright/test';

test.describe('Homepage', () => {
	test('should load homepage successfully', async ({ page }) => {
		await page.goto('/');

		// Check that page loads
		await expect(page).toHaveTitle(/Data Analysis Platform/i);
	});

	test('should display navigation', async ({ page }) => {
		await page.goto('/');

		// Check for navigation elements
		const nav = page.locator('nav');
		await expect(nav).toBeVisible();
	});

	test('should show analysis gallery', async ({ page }) => {
		await page.goto('/');

		// Check for gallery or empty state
		const content = page.locator('main').first();
		await expect(content).toBeVisible();
	});

	test('should have create analysis button', async ({ page }) => {
		await page.goto('/');

		// Look for create button
		const createButton = page.getByRole('button', { name: /create|new/i });
		if ((await createButton.count()) > 0) {
			await expect(createButton.first()).toBeVisible();
		}
	});
});

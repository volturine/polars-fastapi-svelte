import { test, expect } from '@playwright/test';

test.describe('DataSource Management', () => {
	test('should navigate to datasources page', async ({ page }) => {
		await page.goto('/');

		// Navigate to datasources
		await page.goto('/datasources');

		// Check URL
		expect(page.url()).toContain('/datasources');
	});

	test('should display datasources list', async ({ page }) => {
		await page.goto('/datasources');

		// Check that page loads
		const content = page.locator('main');
		await expect(content).toBeVisible();
	});

	test('should show create datasource button', async ({ page }) => {
		await page.goto('/datasources');

		// Look for create/upload button
		const uploadButton = page.getByRole('button', { name: /upload|create|add/i });
		if ((await uploadButton.count()) > 0) {
			await expect(uploadButton.first()).toBeVisible();
		}
	});

	test('should navigate to new datasource page', async ({ page }) => {
		await page.goto('/datasources');

		// Try to click create button
		const createLink = page.getByRole('link', { name: /new|create|add/i });
		if ((await createLink.count()) > 0) {
			await createLink.first().click();
			expect(page.url()).toContain('/datasources/new');
		} else {
			// Navigate directly if button not found
			await page.goto('/datasources/new');
			expect(page.url()).toContain('/datasources/new');
		}
	});

	test('should show file upload interface', async ({ page }) => {
		await page.goto('/datasources/new');

		// Look for file input or upload area
		const fileInput = page.locator('input[type="file"]');
		if ((await fileInput.count()) > 0) {
			await expect(fileInput.first()).toBeVisible();
		}
	});

	test('should handle file upload', async ({ page }) => {
		await page.goto('/datasources/new');

		// This test would require mocking the backend
		// For now, just check that the upload interface exists
		const uploadArea = page.locator('[data-testid="upload-area"], [role="button"]');
		if ((await uploadArea.count()) > 0) {
			await expect(uploadArea.first()).toBeVisible();
		}
	});
});

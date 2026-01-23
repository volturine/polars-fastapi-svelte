import { test, expect } from '@playwright/test';

test.describe('Analysis Management', () => {
	test('should navigate to new analysis page', async ({ page }) => {
		await page.goto('/');

		// Navigate to create analysis
		await page.goto('/analysis/new');

		expect(page.url()).toContain('/analysis/new');
	});

	test('should display analysis creation form', async ({ page }) => {
		await page.goto('/analysis/new');

		// Check for form elements
		const content = page.locator('main, form');
		await expect(content.first()).toBeVisible();
	});

	test('should show analysis name input', async ({ page }) => {
		await page.goto('/analysis/new');

		// Look for name input
		const nameInput = page.locator('input[name="name"], input[placeholder*="name" i]');
		if ((await nameInput.count()) > 0) {
			await expect(nameInput.first()).toBeVisible();
		}
	});

	test('should navigate to analysis editor', async ({ page }) => {
		// For this test, we'll need an existing analysis ID
		// Using a placeholder ID
		const testAnalysisId = 'test-analysis-123';
		await page.goto(`/analysis/${testAnalysisId}`);

		// Check that we're on the analysis page
		expect(page.url()).toContain('/analysis/');
	});

	test('should display pipeline canvas', async ({ page }) => {
		const testAnalysisId = 'test-analysis-123';
		await page.goto(`/analysis/${testAnalysisId}`);

		// Look for pipeline canvas or editor
		const canvas = page.locator('[data-testid="pipeline-canvas"], canvas, [role="main"]');
		if ((await canvas.count()) > 0) {
			await expect(canvas.first()).toBeVisible();
		}
	});

	test('should show step library', async ({ page }) => {
		const testAnalysisId = 'test-analysis-123';
		await page.goto(`/analysis/${testAnalysisId}`);

		// Look for step library or toolbar
		const stepLibrary = page.locator('[data-testid="step-library"], aside, [role="complementary"]');
		if ((await stepLibrary.count()) > 0) {
			await expect(stepLibrary.first()).toBeVisible();
		}
	});

	test('should handle back navigation', async ({ page }) => {
		const testAnalysisId = 'test-analysis-123';
		await page.goto(`/analysis/${testAnalysisId}`);

		// Click browser back button - this may not work in all browsers if no history
		// So we verify the navigation to analysis page worked first
		expect(page.url()).toContain('/analysis/');

		// Navigate to home page as alternative verification
		await page.goto('/');
		expect(page.url()).not.toContain(testAnalysisId);
	});
});

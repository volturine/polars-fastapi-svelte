import { test, expect } from './fixtures.js';
import { waitForAppShell, waitForLayoutReady } from './utils/readiness.js';
import { uid } from './utils/uid.js';

test.describe('Pure e2e – authenticated shell', () => {
	test('home page renders Analyses shell for a signed-in user', async ({ page }) => {
		await page.goto('/');
		await waitForLayoutReady(page);
		await expect(page.getByRole('heading', { name: 'Analyses', level: 1 })).toBeVisible();
	});

	test('profile page is reachable from the sidebar', async ({ page }) => {
		await page.goto('/');
		await waitForAppShell(page);
		await page.getByRole('link', { name: 'Profile' }).click();
		await expect(page).toHaveURL(/\/profile/, { timeout: 10_000 });
		await expect(page.getByRole('heading', { name: 'Profile', level: 1 })).toBeVisible();
	});

	test('namespace selection persists across refresh', async ({ page }) => {
		const namespace = `e2e-ui-${uid()}`;
		await page.goto('/');
		await waitForAppShell(page);
		await page.getByRole('button', { name: 'Select namespace' }).click();
		const dialog = page
			.getByRole('dialog')
			.filter({ has: page.getByRole('textbox', { name: 'Search namespaces' }) });
		await expect(dialog).toBeVisible({ timeout: 5_000 });
		await dialog.getByRole('textbox', { name: 'Search namespaces' }).fill(namespace);
		await dialog.locator(`[data-namespace-create="${namespace}"]`).click();
		await expect(dialog).not.toBeVisible({ timeout: 5_000 });
		await expect(page.getByLabel('Main navigation').getByText(namespace)).toBeVisible();
		await page.reload({ waitUntil: 'networkidle' });
		await waitForAppShell(page);
		await expect(page.getByLabel('Main navigation').getByText(namespace)).toBeVisible();
	});
});

import { test, expect } from './fixtures.js';
import {
	selectDatasourceAndWaitForConfig,
	waitForDatasourceList,
	waitForLayoutReady
} from './utils/readiness.js';
import { deleteDatasourceViaUI } from './utils/ui-cleanup.js';
import { uploadCsvDatasource } from './utils/user-flows.js';
import { uid } from './utils/uid.js';

test.describe('Pure e2e – datasource flows', () => {
	test('user can upload a CSV datasource from the UI', async ({ page }) => {
		const name = `e2e-upload-${uid()}`;
		const description = 'Uploaded fully through the user-visible datasource flow.';
		try {
			await uploadCsvDatasource(page, name, { description });
			const row = page.locator(`[data-ds-row="${name}"]`);
			await expect(row).toBeVisible();
			await expect(row.getByText(description)).toBeVisible();
		} finally {
			await deleteDatasourceViaUI(page, name);
		}
	});

	test('uploaded datasource renders preview and config details', async ({ page }) => {
		const name = `e2e-preview-${uid()}`;
		try {
			await uploadCsvDatasource(page, name);
			await page.goto('/datasources');
			await waitForDatasourceList(page);
			await selectDatasourceAndWaitForConfig(page, name);
			await expect(page.locator('[data-preview-ready="true"]')).toBeVisible({ timeout: 30_000 });
			await expect(page.locator('[data-column-id="name"]')).toBeVisible();
			await expect(page.locator('[data-column-id="city"]')).toBeVisible();
			await expect(page.getByTestId('datasource-row-count')).toHaveText('3', { timeout: 10_000 });
		} finally {
			await deleteDatasourceViaUI(page, name);
		}
	});

	test('upload form exposes both file and database paths', async ({ page }) => {
		await page.goto('/datasources/new');
		await waitForLayoutReady(page);
		await expect(page.getByRole('button', { name: 'File Upload' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'External DB' })).toBeVisible();
		await page.getByRole('button', { name: 'External DB' }).click();
		await expect(page.locator('#connection-string')).toBeVisible({ timeout: 8_000 });
	});
});

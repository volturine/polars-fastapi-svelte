import { test, expect } from './fixtures.js';
import {
	deleteDatasourceViaUI,
	deleteHealthCheckViaUI,
	deleteScheduleViaUI
} from './utils/ui-cleanup.js';
import { uploadCsvDatasource } from './utils/user-flows.js';
import { uid } from './utils/uid.js';

test.describe('Pure e2e – monitoring flows', () => {
	test('user can create a schedule from the Monitoring UI', async ({ page }) => {
		test.setTimeout(90_000);
		const datasourceName = `e2e-schedule-ds-${uid()}`;
		try {
			await uploadCsvDatasource(page, datasourceName);
			await page.goto('/monitoring?tab=schedules');
			await expect(page.getByRole('button', { name: /New Schedule/i })).toBeVisible({
				timeout: 10_000
			});
			await page.getByRole('button', { name: /New Schedule/i }).click();
			const datasourceSelect = page.locator('#schedule-datasource');
			await expect(datasourceSelect).toBeVisible({ timeout: 5_000 });
			await datasourceSelect.selectOption({ label: datasourceName });
			const createBtn = page.getByRole('button', { name: 'Create Schedule' });
			await expect(createBtn).toBeEnabled({ timeout: 5_000 });
			await createBtn.click();
			const row = page
				.locator('tr')
				.filter({ has: page.getByLabel('Delete schedule') })
				.filter({ hasText: 'Every hour' });
			await expect(row).toBeVisible({ timeout: 10_000 });
		} finally {
			await deleteScheduleViaUI(page, datasourceName);
			await deleteDatasourceViaUI(page, datasourceName);
		}
	});

	test('user can create a health check from the Monitoring UI', async ({ page }) => {
		test.setTimeout(90_000);
		const suffix = uid();
		const datasourceName = `e2e-health-ds-${suffix}`;
		const checkName = `e2e UI Check ${suffix}`;
		try {
			await uploadCsvDatasource(page, datasourceName);
			await page.goto('/monitoring?tab=health');
			await expect(page.getByRole('button', { name: /New Check/i })).toBeVisible({
				timeout: 10_000
			});
			await page.getByRole('button', { name: /New Check/i }).click();
			const datasourceSelect = page.locator('#hc-target');
			await expect(datasourceSelect).toBeVisible({ timeout: 5_000 });
			await datasourceSelect.selectOption({ label: datasourceName });
			await page.locator('#hc-name').fill(checkName);
			await page.locator('#hc-min-rows').fill('1');
			const saveBtn = page.getByRole('button', { name: 'Save Check' });
			await expect(saveBtn).toBeEnabled({ timeout: 5_000 });
			await saveBtn.click();
			const row = page.locator(`[data-healthcheck-name="${checkName}"]`);
			await expect(row).toBeVisible({ timeout: 10_000 });
		} finally {
			await deleteHealthCheckViaUI(page, checkName);
			await deleteDatasourceViaUI(page, datasourceName);
		}
	});
});

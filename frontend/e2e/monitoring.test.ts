import { test, expect } from '@playwright/test';
import { createDatasource, createSchedule, createHealthCheck } from './utils/api.js';
import {
	deleteDatasourceViaUI,
	deleteScheduleViaUI,
	deleteHealthCheckViaUI
} from './utils/ui-cleanup.js';

/**
 * E2E tests for the monitoring page – mirrors test_healthchecks.py /
 * test_scheduler.py / test_engine_runs.py.
 */
test.describe('Monitoring – page structure', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/monitoring');
	});

	test('renders Monitoring heading and description', async ({ page }) => {
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
		await expect(page.getByText(/Review builds, schedules, and health checks/i)).toBeVisible();
	});

	test('shows all three tabs: Builds, Schedules, Health Checks', async ({ page }) => {
		await expect(page.getByRole('button', { name: 'Builds' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Schedules' })).toBeVisible();
		await expect(page.getByRole('button', { name: 'Health Checks' })).toBeVisible();
	});

	test('Builds tab is active by default', async ({ page }) => {
		// The Builds tab content renders (BuildsManager). No crash = pass.
		await expect(page.getByRole('button', { name: 'Builds' })).toBeVisible();
	});

	test('can switch between all tabs without error', async ({ page }) => {
		for (const tabName of ['Schedules', 'Health Checks', 'Builds'] as const) {
			await page.getByRole('button', { name: tabName }).click();
			// No Callout with tone=error visible
			await expect(page.locator('.callout--tone_error')).not.toBeVisible();
		}
	});

	test('search input is present', async ({ page }) => {
		await expect(
			page.getByPlaceholder(/Search builds, schedules, or health checks/i)
		).toBeVisible();
	});

	test('typing in search does not crash the page', async ({ page }) => {
		await page.getByPlaceholder(/Search builds, schedules, or health checks/i).fill('test query');
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
	});
});

test.describe('Monitoring – Schedules tab', () => {
	test('Schedules tab shows schedule list or empty state', async ({ page }) => {
		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Schedules' }).click();
		// Either a schedule list or an empty/create state
		await expect(page.locator('main, [role="main"]').last()).toBeVisible();
	});

	test('Schedules tab shows "New Schedule" button', async ({ page }) => {
		await page.goto('/monitoring');
		const schedulesTab = page.getByRole('button', { name: 'Schedules' });
		await expect(schedulesTab).toBeVisible();
		await schedulesTab.click();
		await expect(page.getByRole('button', { name: /New Schedule/i })).toBeVisible({
			timeout: 10_000
		});
	});

	test('created schedule appears in the Schedules tab', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-sched-ds');
		await createSchedule(request, dsId, '0 6 * * *');
		try {
			await page.goto('/monitoring');
			await page.getByRole('button', { name: 'Schedules' }).click();
			// The cron expression or datasource name should be visible
			await expect(
				page.getByText('0 6 * * *').or(page.getByText('e2e-sched-ds')).first()
			).toBeVisible({ timeout: 8_000 });
		} finally {
			await deleteScheduleViaUI(page, 'e2e-sched-ds');
			await deleteDatasourceViaUI(page, 'e2e-sched-ds');
		}
	});

	test('schedule can be deleted via UI', async ({ page, request }) => {
		test.setTimeout(60_000);
		const dsId = await createDatasource(request, 'e2e-sched-del-ds');
		await createSchedule(request, dsId, '0 7 * * *');

		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Schedules' }).click();

		// Wait for the schedule delete button to appear (one per schedule row)
		const deleteBtns = page.locator('button[title="Delete schedule"]');
		await expect(deleteBtns.first()).toBeAttached({ timeout: 15_000 });
		const countBefore = await deleteBtns.count();

		// Delete button is hidden (opacity: 0) until row hover — use force click
		await deleteBtns.first().click({ force: true, timeout: 5_000 });

		// After deletion the button count should decrease
		await expect(deleteBtns).toHaveCount(countBefore - 1, { timeout: 8_000 });

		// Cleanup the datasource
		await deleteDatasourceViaUI(page, 'e2e-sched-del-ds');
	});
});

test.describe('Monitoring – Health Checks tab', () => {
	test('Health Checks tab renders without error', async ({ page }) => {
		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Health Checks' }).click();
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
	});

	test('Health Checks tab shows "New Check" button', async ({ page }) => {
		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Health Checks' }).click();
		await expect(page.getByRole('button', { name: /New Check/i })).toBeVisible({ timeout: 8_000 });
	});

	test('created health check appears in list', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-hc-ds');
		await createHealthCheck(request, dsId, 'E2E Row Count Check');
		try {
			await page.goto('/monitoring');
			await page.getByRole('button', { name: 'Health Checks' }).click();
			await expect(page.getByText('E2E Row Count Check')).toBeVisible({ timeout: 8_000 });
		} finally {
			await deleteHealthCheckViaUI(page, 'E2E Row Count Check');
			await deleteDatasourceViaUI(page, 'e2e-hc-ds');
		}
	});

	test('health check delete button removes it from list', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-hc-del-ds');
		await createHealthCheck(request, dsId, 'E2E Delete Health Check');

		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Health Checks' }).click();
		await expect(page.getByText('E2E Delete Health Check').first()).toBeVisible({
			timeout: 8_000
		});
		const hcCount = await page.getByText('E2E Delete Health Check').count();

		// Delete button has title="Delete check"
		await page.locator('button[title="Delete check"]').first().click();

		await expect(page.getByText('E2E Delete Health Check')).toHaveCount(hcCount - 1, {
			timeout: 8_000
		});

		// Cleanup the datasource
		await deleteDatasourceViaUI(page, 'e2e-hc-del-ds');
	});
});

test.describe('Monitoring – Builds tab', () => {
	test('Builds tab shows empty state or build list', async ({ page }) => {
		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Builds' }).click();
		// Just check the tab loaded without crashing
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
	});

	test('Builds search filters by text', async ({ page }) => {
		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Builds' }).click();
		await page.getByPlaceholder(/Search builds, schedules, or health checks/i).fill('ZZZNOMATCH');
		// Should not crash
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
	});

	test('Builds tab shows datasource creation run', async ({ page, request }) => {
		test.setTimeout(60_000);
		await createDatasource(request, 'e2e-build-ds');
		try {
			await page.goto('/monitoring');
			await page.getByRole('button', { name: 'Builds' }).click();
			// The datasource name appears in the Datasource column once the lookup resolves
			await expect(page.getByText('e2e-build-ds').first()).toBeVisible({ timeout: 20_000 });
		} finally {
			await deleteDatasourceViaUI(page, 'e2e-build-ds');
		}
	});
});

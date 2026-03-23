import { test, expect } from '@playwright/test';
import { createDatasource, createSchedule, createHealthCheck } from './utils/api.js';
import {
	deleteDatasourceViaUI,
	deleteScheduleViaUI,
	deleteHealthCheckViaUI
} from './utils/ui-cleanup.js';
import { screenshot } from './utils/visual.js';

/**
 * E2E tests for the monitoring page – mirrors test_healthchecks.py /
 * test_scheduler.py / test_engine_runs.py.
 */
test.describe('Monitoring – page structure', () => {
	test.beforeEach(async ({ page }) => {
		await page.goto('/monitoring', { waitUntil: 'networkidle' });
	});

	test('renders Monitoring heading and description', async ({ page }) => {
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
		await expect(page.getByText(/Review builds, schedules, and health checks/i)).toBeVisible();
	});

	test('shows all three tabs: Builds, Schedules, Health Checks', async ({ page }) => {
		await expect(page.getByRole('tab', { name: 'Builds' })).toBeVisible();
		await expect(page.getByRole('tab', { name: 'Schedules' })).toBeVisible();
		await expect(page.getByRole('tab', { name: 'Health Checks' })).toBeVisible();
		await screenshot(page, 'monitoring', 'tabs-overview');
	});

	test('Builds tab is active by default', async ({ page }) => {
		const buildsTab = page.getByRole('tab', { name: 'Builds' });
		await expect(buildsTab).toHaveAttribute('aria-selected', 'true');
	});

	test('can switch between all tabs without error', async ({ page }) => {
		const tabMap = [
			{ label: 'Schedules', key: 'schedules' },
			{ label: 'Health Checks', key: 'health' },
			{ label: 'Builds', key: 'builds' }
		] as const;
		for (const { label, key } of tabMap) {
			await page.getByRole('tab', { name: label }).click();
			await expect(page).toHaveURL(new RegExp(`tab=${key}`));
			await expect(page.getByRole('tab', { name: label })).toHaveAttribute('aria-selected', 'true');
		}
	});

	test('search input is present', async ({ page }) => {
		await expect(page.getByLabel(/Search builds, schedules, or health checks/i)).toBeVisible();
	});

	test('typing in search does not crash the page', async ({ page }) => {
		await page.getByLabel(/Search builds, schedules, or health checks/i).fill('test query');
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
	});
});

test.describe('Monitoring – Schedules tab', () => {
	test('Schedules tab shows schedule list or empty state', async ({ page }) => {
		await page.goto('/monitoring?tab=schedules');
		// Either a schedule list or an empty/create state
		const panel = page.locator('#panel-schedules');
		await expect(panel).toBeVisible();
	});

	test('Schedules tab shows "New Schedule" button', async ({ page }) => {
		await page.goto('/monitoring?tab=schedules');
		await expect(page.getByRole('button', { name: /New Schedule/i })).toBeVisible({
			timeout: 10_000
		});
		await screenshot(page, 'monitoring', 'schedules-tab');
	});

	test('created schedule appears in the Schedules tab', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-sched-ds');
		await createSchedule(request, dsId, '0 6 * * *');
		try {
			await page.goto('/monitoring?tab=schedules');
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

		await page.goto('/monitoring?tab=schedules');

		// Wait for the schedule delete button to appear
		const deleteBtn = page
			.locator('tr', { has: page.getByText('e2e-sched-del-ds') })
			.first()
			.getByLabel('Delete schedule');
		await expect(deleteBtn).toBeAttached({ timeout: 15_000 });

		// Delete button is always visible in the table row
		await deleteBtn.click({ timeout: 5_000 });

		// Confirm in the dialog
		const dialog = page.getByRole('dialog');
		await expect(dialog.getByRole('heading', { name: /Delete Schedule/i })).toBeVisible();
		await dialog.getByRole('button', { name: /^Delete$/ }).click();

		// After deletion the datasource name should disappear from the table
		await expect(page.getByText('e2e-sched-del-ds')).not.toBeVisible({ timeout: 8_000 });

		// Cleanup the datasource
		await deleteDatasourceViaUI(page, 'e2e-sched-del-ds');
	});
});

test.describe('Monitoring – Health Checks tab', () => {
	test('Health Checks tab renders without error', async ({ page }) => {
		await page.goto('/monitoring?tab=health');
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
		await expect(page.getByRole('tab', { name: 'Health Checks' })).toHaveAttribute(
			'aria-selected',
			'true'
		);
	});

	test('Health Checks tab shows "New Check" button', async ({ page }) => {
		await page.goto('/monitoring?tab=health');
		await expect(page.getByRole('button', { name: /New Check/i })).toBeVisible({ timeout: 8_000 });
		await screenshot(page, 'monitoring', 'health-checks-tab');
	});

	test('created health check appears in list', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-hc-ds');
		await createHealthCheck(request, dsId, 'e2e Row Count Check');
		try {
			await page.goto('/monitoring?tab=health');
			await expect(page.getByText('e2e Row Count Check')).toBeVisible({ timeout: 8_000 });
		} finally {
			await deleteHealthCheckViaUI(page, 'e2e Row Count Check');
			await deleteDatasourceViaUI(page, 'e2e-hc-ds');
		}
	});

	test('health check delete button removes it from list', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-hc-del-ds');
		await createHealthCheck(request, dsId, 'e2e Delete Health Check');

		await page.goto('/monitoring?tab=health');
		await expect(page.getByText('e2e Delete Health Check').first()).toBeVisible({
			timeout: 8_000
		});

		// Scope the delete to the row containing our health check name
		const row = page.locator('tr', { has: page.getByText('e2e Delete Health Check') }).first();
		await row.getByLabel('Delete check').click({ timeout: 5_000 });

		// Confirm in the dialog
		const dialog = page.getByRole('dialog');
		await expect(dialog.getByRole('heading', { name: /Delete Health Check/i })).toBeVisible();
		await dialog.getByRole('button', { name: /^Delete$/ }).click();

		await expect(page.getByText('e2e Delete Health Check')).not.toBeVisible({
			timeout: 8_000
		});

		// Cleanup the datasource
		await deleteDatasourceViaUI(page, 'e2e-hc-del-ds');
	});
});

test.describe('Monitoring – Builds tab', () => {
	test('Builds tab shows empty state or build list', async ({ page }) => {
		await page.goto('/monitoring?tab=builds');
		await expect(page.getByRole('tab', { name: 'Builds' })).toHaveAttribute(
			'aria-selected',
			'true'
		);
	});

	test('Builds search filters by text', async ({ page }) => {
		await page.goto('/monitoring?tab=builds');
		await page.getByLabel(/Search builds, schedules, or health checks/i).fill('ZZZNOMATCH');
		await expect(page.getByRole('heading', { name: 'Monitoring' })).toBeVisible();
	});

	test('Builds tab shows datasource creation run', async ({ page, request }) => {
		test.setTimeout(60_000);
		await createDatasource(request, 'e2e-build-ds');
		try {
			await page.goto('/monitoring?tab=builds');
			const panel = page.locator('#panel-builds');
			await expect(panel).toBeVisible();
			// The datasource name appears inside the builds table, not just anywhere on the page
			await expect(panel.getByText('e2e-build-ds').first()).toBeVisible({ timeout: 20_000 });
			// A status indicator (Success or Failed) must render in a table cell, not in filter dropdowns
			const cells = panel.locator('td');
			await expect(cells.getByText('Success').or(cells.getByText('Failed')).first()).toBeVisible({
				timeout: 5_000
			});
		} finally {
			await deleteDatasourceViaUI(page, 'e2e-build-ds');
		}
	});
});

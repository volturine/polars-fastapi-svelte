import { test, expect } from './fixtures.js';
import type { Page } from '@playwright/test';
import { createLargeDatasource, createLongRunningAnalysis } from './utils/api.js';
import { deleteAnalysisViaUI, deleteDatasourceViaUI } from './utils/ui-cleanup.js';
import { waitForLayoutReady } from './utils/readiness.js';
import { gotoAnalysisEditor } from './utils/analysis.js';
import { uid } from './utils/uid.js';

async function startBuildFromAnalysisPage(page: Page, analysisId: string) {
	await gotoAnalysisEditor(page, analysisId);
	const buildBtn = page.locator('[data-testid="output-build-button"]');
	await expect(buildBtn).toBeVisible({ timeout: 10_000 });
	// analysisPipeline may take a moment to populate after the lock is acquired;
	// give the button a generous timeout so we fail fast instead of consuming the
	// full 240 s test budget.
	await buildBtn.click({ timeout: 30_000 });
	await expect(page.locator('[data-testid="output-build-preview-trigger"]')).toBeVisible({
		timeout: 30_000
	});
}

async function gotoMonitoringBuilds(page: Page, analysisId?: string) {
	const params = new URLSearchParams({ tab: 'builds' });
	if (analysisId) params.set('analysis_id', analysisId);
	await page.goto(`/monitoring?${params.toString()}`);
	await waitForLayoutReady(page);
	await expect(page.getByRole('tab', { name: 'Builds', selected: true })).toBeVisible({
		timeout: 15_000
	});
	await expect(page.locator('#panel-builds')).toBeVisible({ timeout: 15_000 });
}

function buildHistoryRow(
	panel: ReturnType<Page['locator']>,
	analysisId: string,
	status: 'running' | 'completed' | 'failed' | 'cancelled',
	kind?: 'preview' | 'datasource_create' | 'datasource_update'
) {
	let selector = `[data-build-analysis-id="${analysisId}"]`;
	selector += `[data-build-status="${status}"]`;
	if (kind) selector += `[data-build-kind="${kind}"]`;
	return panel.locator(selector).first();
}

async function refreshBuildHistory(page: Page) {
	await page.getByRole('button', { name: /Refresh History/i }).click({ timeout: 15_000 });
}

async function waitForBuildHistoryRow(
	page: Page,
	panel: ReturnType<Page['locator']>,
	analysisId: string,
	statuses: Array<'running' | 'completed' | 'failed' | 'cancelled'>,
	timeout = 90_000,
	kinds: Array<'preview' | 'datasource_create' | 'datasource_update'> = [
		'datasource_create',
		'preview',
		'datasource_update'
	]
) {
	const started = Date.now();
	while (Date.now() - started < timeout) {
		for (const status of statuses) {
			for (const kind of kinds) {
				const row = buildHistoryRow(panel, analysisId, status, kind);
				if (await row.isVisible().catch(() => false)) return row;
			}
		}
		await refreshBuildHistory(page);
		await page.waitForTimeout(1_000);
	}
	throw new Error(`Timed out waiting for build history row for analysis ${analysisId}`);
}

async function openCancelDialogFromRow(page: Page, row: ReturnType<Page['locator']>) {
	const btn = row.getByLabel('Cancel build');
	await expect(btn).toBeVisible({ timeout: 10_000 });
	await btn.click({ timeout: 10_000 });
	await expect(
		page.getByRole('dialog').getByRole('heading', { name: 'Cancel this build?' })
	).toBeVisible({ timeout: 10_000 });
}

async function openCancelDialogFromPreview(page: Page, preview: ReturnType<Page['locator']>) {
	const btn = preview.locator('[data-testid="build-cancel-button"]');
	await expect(btn).toBeVisible({ timeout: 30_000 });
	await btn.click();
	await expect(
		page.getByRole('dialog').getByRole('heading', { name: 'Cancel this build?' })
	).toBeVisible({ timeout: 10_000 });
}

async function previewBuildId(preview: ReturnType<Page['locator']>) {
	const id = preview.locator('[data-testid="build-preview-engine-run-id"]');
	await expect(id).toHaveText(/\S+/, { timeout: 30_000 });
	return (await id.textContent())?.trim() ?? '';
}

function cancelDialog(page: Page) {
	const title = page.getByRole('heading', { name: 'Cancel this build?' });
	return page.getByRole('dialog').filter({ has: title });
}

async function waitForBuildRowById(
	page: Page,
	panel: ReturnType<Page['locator']>,
	runId: string,
	status: 'running' | 'completed' | 'failed' | 'cancelled',
	timeout = 30_000
) {
	const row = panel.locator(`[data-build-row="${runId}"][data-build-status="${status}"]`);
	const started = Date.now();
	while (Date.now() - started < timeout) {
		if (await row.isVisible().catch(() => false)) return row;
		await refreshBuildHistory(page);
		await page.waitForTimeout(1_000);
	}
	throw new Error(`Timed out waiting for build row ${runId} to reach ${status}`);
}

test.describe('Cancel Build – e2e', () => {
	test.describe.configure({ mode: 'serial' });

	test('cancel from build preview marks run as cancelled with details', async ({
		page,
		request
	}) => {
		test.setTimeout(240_000);
		const dsName = `e2e-cancel-preview-ds-${uid()}`;
		const analysisName = `E2E Cancel Preview ${uid()}`;
		const dsId = await createLargeDatasource(request, dsName, 225_000);
		const analysisId = await createLongRunningAnalysis(request, analysisName, dsId);
		try {
			await startBuildFromAnalysisPage(page, analysisId);
			const openPreviewBtn = page.locator('[data-testid="output-build-preview-trigger"]');
			await expect(openPreviewBtn).toBeVisible({ timeout: 10_000 });
			await openPreviewBtn.click();

			const preview = page.locator('[data-testid="build-preview"]');
			await expect(preview).toBeVisible({ timeout: 10_000 });
			await previewBuildId(preview);
			await openCancelDialogFromPreview(page, preview);

			const dialog = cancelDialog(page);
			await expect(dialog.getByRole('heading', { name: 'Cancel this build?' })).toBeVisible();
			const cancelled = page.waitForResponse(
				(response) =>
					response.url().includes('/api/v1/compute/cancel/') && response.status() === 200
			);
			await dialog.getByRole('button', { name: 'Cancel Build', exact: true }).click();
			const payload = await cancelled.then((response) => response.json());
			expect(payload.status).toBe('cancelled');
			await expect(dialog).not.toBeVisible({
				timeout: 15_000
			});
			await expect(page.locator('[data-testid="build-cancel-error"]')).not.toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, analysisName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('cancel from monitoring build history row works', async ({ page, request }) => {
		test.setTimeout(240_000);
		const dsName = `e2e-cancel-history-ds-${uid()}`;
		const analysisName = `E2E Cancel History ${uid()}`;
		const dsId = await createLargeDatasource(request, dsName, 250_000);
		const analysisId = await createLongRunningAnalysis(request, analysisName, dsId);
		try {
			await startBuildFromAnalysisPage(page, analysisId);

			// Navigate to monitoring and find the running build by analysis name
			await gotoMonitoringBuilds(page, analysisId);
			const panel = page.locator('#panel-builds');
			const runningRow = await waitForBuildHistoryRow(
				page,
				panel,
				analysisId,
				['running'],
				60_000,
				['datasource_create', 'preview', 'datasource_update']
			);
			await expect(runningRow).toHaveAttribute('data-build-status', 'running', { timeout: 30_000 });
			await expect(runningRow.getByLabel('Cancel build')).toBeVisible({ timeout: 30_000 });
			const runId = await runningRow.getAttribute('data-build-row', { timeout: 10_000 });
			expect(runId).toBeTruthy();
			await openCancelDialogFromRow(page, runningRow);

			const dialog = cancelDialog(page);
			await expect(dialog.getByRole('heading', { name: 'Cancel this build?' })).toBeVisible();
			const cancelled = page.waitForResponse(
				(response) =>
					response.url().includes('/api/v1/compute/cancel/') && response.status() === 200
			);
			await dialog.getByRole('button', { name: 'Cancel Build', exact: true }).click({
				timeout: 10_000
			});
			const payload = await cancelled.then((response) => response.json());
			expect(payload.status).toBe('cancelled');
			await expect(dialog).not.toBeVisible({
				timeout: 15_000
			});
			await expect(page.locator('[data-testid="build-cancel-error"]')).not.toBeVisible({
				timeout: 5_000
			});

			const cancelledRow = await waitForBuildRowById(page, panel, runId ?? '', 'cancelled', 30_000);
			await expect(cancelledRow).toHaveAttribute('data-build-status', 'cancelled', {
				timeout: 30_000
			});
			await expect(cancelledRow.getByText('Cancelled')).toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, analysisName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});
});

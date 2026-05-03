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

async function refreshBuildHistory(page: Page) {
	await page.getByRole('button', { name: /Refresh History/i }).click({ timeout: 15_000 });
}

async function openCancelDialogFromRow(page: Page, row: ReturnType<Page['locator']>) {
	const btn = row.getByLabel('Cancel build');
	await expect(btn).toBeVisible({ timeout: 10_000 });
	await expect(btn).toBeEnabled({ timeout: 10_000 });
	await btn.scrollIntoViewIfNeeded();
	await btn.click({ force: true, timeout: 10_000 });
	await expect(cancelDialog(page)).toBeVisible({ timeout: 10_000 });
}

async function openCancelDialogFromPreview(page: Page, preview: ReturnType<Page['locator']>) {
	await expect(preview.locator('[data-testid="build-preview-engine-run-id"]')).toHaveText(/\S+/, {
		timeout: 30_000
	});
	await expect(preview.getByText(/Connecting|Running/)).toBeVisible({ timeout: 30_000 });
	const btn = preview.locator('[data-testid="build-cancel-button"]');
	await expect(btn).toBeVisible({ timeout: 30_000 });
	await expect(btn).toBeEnabled({ timeout: 30_000 });
	await btn.scrollIntoViewIfNeeded();
	await btn.click({ force: true, timeout: 10_000 });
	await expect(cancelDialog(page)).toBeVisible({ timeout: 10_000 });
}

function cancelDialog(page: Page) {
	const title = page.getByRole('heading', { name: 'Cancel this build?' });
	return page.getByRole('dialog').filter({ has: title });
}

async function confirmCancelDialog(page: Page) {
	const dialog = cancelDialog(page);
	const confirmButton = dialog.getByRole('button', { name: 'Cancel Build', exact: true });
	await expect(dialog.getByRole('heading', { name: 'Cancel this build?' })).toBeVisible({
		timeout: 10_000
	});
	await expect(confirmButton).toBeVisible({ timeout: 10_000 });
	await expect(confirmButton).toBeEnabled({ timeout: 10_000 });
	const responsePromise = page
		.waitForResponse(
			(apiResponse) =>
				apiResponse.url().includes('/api/v1/compute/cancel/') && apiResponse.status() === 200,
			{ timeout: 15_000 }
		)
		.then(async (response) => (await response.json()) as { status: string })
		.catch(() => null);
	await confirmButton.click({ force: true, timeout: 10_000 });
	return responsePromise;
}

async function waitForBuildRowByAnalysisId(
	page: Page,
	panel: ReturnType<Page['locator']>,
	analysisId: string,
	status: 'running' | 'completed' | 'failed' | 'cancelled',
	timeout = 30_000
) {
	const row = panel.locator(
		`[data-build-analysis-id="${analysisId}"][data-build-status="${status}"]`
	);
	const started = Date.now();
	while (Date.now() - started < timeout) {
		if (
			await row
				.first()
				.isVisible()
				.catch(() => false)
		)
			return row.first();
		await refreshBuildHistory(page);
		await page.waitForTimeout(1_000);
	}
	throw new Error(`Timed out waiting for analysis ${analysisId} to reach ${status}`);
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
		const dsId = await createLargeDatasource(request, dsName, 2_000_000);
		const analysisId = await createLongRunningAnalysis(request, analysisName, dsId);
		try {
			await startBuildFromAnalysisPage(page, analysisId);
			const openPreviewBtn = page.locator('[data-testid="output-build-preview-trigger"]');
			await expect(openPreviewBtn).toBeVisible({ timeout: 10_000 });
			await openPreviewBtn.click();

			const preview = page.locator('[data-testid="build-preview"]');
			await expect(preview).toBeVisible({ timeout: 10_000 });
			await openCancelDialogFromPreview(page, preview);

			const dialog = cancelDialog(page);
			const payload = await confirmCancelDialog(page);
			if (payload) {
				expect(payload.status).toBe('cancelled');
			}
			await expect(dialog).not.toBeVisible({ timeout: 15_000 });
			await expect(page.locator('[data-testid="build-cancel-error"]')).not.toBeVisible();

			await gotoMonitoringBuilds(page, analysisId);
			const panel = page.locator('#panel-builds');
			const cancelledRow = await waitForBuildRowByAnalysisId(
				page,
				panel,
				analysisId,
				'cancelled',
				30_000
			);
			await expect(cancelledRow).toHaveAttribute('data-build-status', 'cancelled', {
				timeout: 30_000
			});
			await expect(cancelledRow.getByText('Cancelled')).toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, analysisName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('cancel from monitoring build history row works', async ({ page, request }) => {
		test.setTimeout(240_000);
		const dsName = `e2e-cancel-history-ds-${uid()}`;
		const analysisName = `E2E Cancel History ${uid()}`;
		const dsId = await createLargeDatasource(request, dsName, 1_100_000);
		const analysisId = await createLongRunningAnalysis(request, analysisName, dsId);
		try {
			await startBuildFromAnalysisPage(page, analysisId);

			// Monitoring history is explicit-refresh only, so refresh until the analysis row
			// appears as running before attempting the cancel action.
			await gotoMonitoringBuilds(page, analysisId);
			const panel = page.locator('#panel-builds');
			const targetRow = await waitForBuildRowByAnalysisId(
				page,
				panel,
				analysisId,
				'running',
				90_000
			);
			await expect(targetRow).toBeVisible({ timeout: 10_000 });
			await expect(targetRow).toHaveAttribute('data-build-status', 'running', { timeout: 30_000 });
			await expect(targetRow.getByLabel('Cancel build')).toBeVisible({ timeout: 30_000 });
			await openCancelDialogFromRow(page, targetRow);

			const dialog = cancelDialog(page);
			const payload = await confirmCancelDialog(page);
			if (payload) {
				expect(payload.status).toBe('cancelled');
			}
			await expect(dialog).not.toBeVisible({ timeout: 15_000 });
			await expect(page.locator('[data-testid="build-cancel-error"]')).not.toBeVisible({
				timeout: 5_000
			});

			const cancelledRow = await waitForBuildRowByAnalysisId(
				page,
				panel,
				analysisId,
				'cancelled',
				30_000
			);
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

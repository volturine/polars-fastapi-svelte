import { test, expect, type Page } from '@playwright/test';
import { createLargeDatasource, createLongRunningAnalysis } from './utils/api.js';
import { deleteAnalysisViaUI, deleteDatasourceViaUI } from './utils/ui-cleanup.js';
import { waitForLayoutReady } from './utils/readiness.js';
import { uid } from './utils/uid.js';

async function startBuildFromAnalysisPage(page: Page, analysisId: string) {
	await page.goto(`/analysis/${analysisId}`);
	await waitForLayoutReady(page);
	await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });
	const buildBtn = page.locator('[data-testid="output-build-button"]');
	await expect(buildBtn).toBeVisible({ timeout: 10_000 });
	await buildBtn.click();
}

test.describe('Cancel Build – e2e', () => {
	test('cancel from build preview marks run as cancelled with details', async ({
		page,
		request
	}) => {
		test.setTimeout(240_000);
		const dsName = `e2e-cancel-preview-ds-${uid()}`;
		const analysisName = `E2E Cancel Preview ${uid()}`;
		const dsId = await createLargeDatasource(request, dsName, 40_000);
		const analysisId = await createLongRunningAnalysis(request, analysisName, dsId, 10);
		try {
			await startBuildFromAnalysisPage(page, analysisId);
			const openPreviewBtn = page.locator('[data-testid="output-build-preview-trigger"]');
			await expect(openPreviewBtn).toBeVisible({ timeout: 10_000 });
			await openPreviewBtn.click();

			const preview = page.locator('[data-testid="build-preview"]');
			await expect(preview).toBeVisible({ timeout: 10_000 });
			const cancelBtn = preview.locator('[data-testid="build-cancel-button"]');
			await expect(cancelBtn).toBeVisible({ timeout: 30_000 });
			await cancelBtn.click();

			const dialog = page.getByRole('dialog');
			await expect(dialog.getByRole('heading', { name: 'Cancel this build?' })).toBeVisible();
			await dialog.getByRole('button', { name: 'Cancel Build' }).click();

			await expect(page.locator('[data-testid="build-cancel-toast"]')).toContainText(
				'Build cancelled',
				{
					timeout: 15_000
				}
			);
			await expect(preview.getByText('Cancelled', { exact: true })).toBeVisible({
				timeout: 30_000
			});

			await page.goto('/monitoring?tab=builds');
			const row = page.locator('tr[data-build-row]', { hasText: analysisName }).first();
			await expect(row).toBeVisible({ timeout: 30_000 });
			await expect(row).toHaveAttribute('data-build-status', 'cancelled', { timeout: 30_000 });

			const runId = await row.getAttribute('data-build-row');
			await row.click();
			await expect(page.locator(`tr[data-build-detail="${runId}"]`)).toBeVisible({
				timeout: 10_000
			});
			const detail = page.locator(`tr[data-build-detail="${runId}"]`);
			await expect(detail.getByText('Cancelled At:')).toBeVisible();
			await expect(detail.getByText('Cancelled By:')).toBeVisible();
			await expect(detail.getByText('Last Completed Step:')).toBeVisible();

			await detail.getByRole('button', { name: 'Result' }).click();
			await expect(detail.getByText('No result data available for cancelled build')).toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, analysisName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('cancel from monitoring build history row works', async ({ page, request }) => {
		test.setTimeout(240_000);
		const dsName = `e2e-cancel-history-ds-${uid()}`;
		const analysisName = `E2E Cancel History ${uid()}`;
		const dsId = await createLargeDatasource(request, dsName, 40_000);
		const analysisId = await createLongRunningAnalysis(request, analysisName, dsId, 10);
		try {
			await startBuildFromAnalysisPage(page, analysisId);

			await page.goto('/monitoring?tab=builds');
			const row = page.locator('tr[data-build-row]', { hasText: analysisName }).first();
			await expect(row).toBeVisible({ timeout: 30_000 });
			const cancelBtn = row.getByLabel('Cancel build');
			await expect(cancelBtn).toBeVisible({ timeout: 30_000 });
			await cancelBtn.click();

			const dialog = page.getByRole('dialog');
			await expect(dialog.getByRole('heading', { name: 'Cancel this build?' })).toBeVisible();
			await dialog.getByRole('button', { name: 'Cancel Build' }).click();

			await expect(row).toHaveAttribute('data-build-status', 'cancelled', { timeout: 30_000 });
			await expect(row.getByText('Cancelled')).toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, analysisName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});
});

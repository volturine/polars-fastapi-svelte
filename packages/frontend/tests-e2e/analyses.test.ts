import { test, expect } from './fixtures.js';
import { waitForLayoutReady } from './utils/readiness.js';
import { deleteAnalysisViaUI, deleteDatasourceViaUI } from './utils/ui-cleanup.js';
import {
	createAnalysisViaUI,
	uploadCsvDatasource,
	waitForBuildTerminal
} from './utils/user-flows.js';
import { uid } from './utils/uid.js';

test.describe('Pure e2e – analysis flows', () => {
	test('user can create an analysis entirely through the wizard', async ({ page }) => {
		test.setTimeout(90_000);
		const datasourceName = `e2e-analysis-ds-${uid()}`;
		const analysisName = `E2E UI Analysis ${uid()}`;
		try {
			await uploadCsvDatasource(page, datasourceName);
			const analysisId = await createAnalysisViaUI(page, analysisName, datasourceName);
			await page.goto(`/analysis/${analysisId}`);
			await waitForLayoutReady(page);
			await expect(page.getByRole('heading', { name: analysisName, level: 1 })).toBeVisible({
				timeout: 15_000
			});
			await expect(page.locator('[role="application"]')).toHaveAttribute(
				'data-editor-access-state',
				'editable'
			);
		} finally {
			await deleteAnalysisViaUI(page, analysisName);
			await deleteDatasourceViaUI(page, datasourceName);
		}
	});

	test('user can build a newly created analysis and inspect the preview', async ({ page }) => {
		test.setTimeout(180_000);
		const datasourceName = `e2e-build-ds-${uid()}`;
		const analysisName = `E2E UI Build ${uid()}`;
		try {
			await uploadCsvDatasource(page, datasourceName);
			const analysisId = await createAnalysisViaUI(page, analysisName, datasourceName);
			await page.goto(`/analysis/${analysisId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });
			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();
			const openPreviewBtn = page.locator('[data-testid="output-build-preview-trigger"]');
			await expect(openPreviewBtn).toBeVisible({ timeout: 10_000 });
			await openPreviewBtn.click();
			const preview = page.locator('[data-testid="build-preview"]');
			await expect(preview).toBeVisible({ timeout: 10_000 });
			await waitForBuildTerminal(preview, 90_000);
			await expect(preview.locator('[data-testid="build-steps-panel"]')).toBeVisible({
				timeout: 5_000
			});
		} finally {
			await deleteAnalysisViaUI(page, analysisName);
			await deleteDatasourceViaUI(page, datasourceName);
		}
	});
});

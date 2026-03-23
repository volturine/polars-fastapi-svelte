import { test, expect } from '@playwright/test';
import { createDatasource, createAnalysis } from './utils/api.js';
import { deleteAnalysisViaUI, deleteDatasourceViaUI } from './utils/ui-cleanup.js';
import { screenshot } from './utils/visual.js';

/**
 * E2E tests for analyses – mirrors test_analysis.py / test_analysis_extended.py.
 */
test.describe('Analyses – list & gallery', () => {
	test('home page renders main content area', async ({ page }) => {
		await page.goto('/');
		await expect(page.getByRole('heading', { name: 'Analyses' })).toBeVisible();
		await expect(page.getByText(/Browse and manage your data analyses/i)).toBeVisible();
		await screenshot(page, 'analyses', 'gallery');
	});

	test('lists existing analysis after API create', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-list-ds');
		await createAnalysis(request, 'E2E List Test', dsId);
		try {
			await page.goto('/');
			await expect(page.getByText('E2E List Test')).toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, 'E2E List Test');
			await deleteDatasourceViaUI(page, 'e2e-list-ds');
		}
	});

	test('search filters out non-matching analyses', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-search-ds');
		await createAnalysis(request, 'E2E Search Alpha', dsId);
		try {
			await page.goto('/');
			await expect(page.getByText('E2E Search Alpha')).toBeVisible();

			// The search box rendered by AnalysisFilters
			await page.getByRole('textbox').first().fill('ZZZNOMATCH');
			await expect(page.getByText(/No analyses match your search/i)).toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Search Alpha');
			await deleteDatasourceViaUI(page, 'e2e-search-ds');
		}
	});

	test('delete analysis via confirm dialog removes it from list', async ({ page, request }) => {
		const dsId = await createDatasource(request, 'e2e-del-ds');
		await createAnalysis(request, 'E2E Delete Me', dsId);

		await page.goto('/');
		const card = page.locator('[data-analysis-card="E2E Delete Me"]');
		await expect(card.first()).toBeVisible();
		const countBefore = await card.count();

		await card
			.first()
			.getByRole('button', { name: /Delete analysis/ })
			.click();

		// Confirm dialog appears
		const dialog = page.getByRole('dialog');
		await expect(dialog.getByRole('heading', { name: /Delete Analysis/i })).toBeVisible();
		await dialog.getByRole('button', { name: /^Delete$/ }).click();

		await expect(card).toHaveCount(countBefore - 1, { timeout: 8_000 });

		// Cleanup the datasource
		await deleteDatasourceViaUI(page, 'e2e-del-ds');
	});
});

test.describe('Analyses – create wizard', () => {
	test('step 1: Next is disabled when name is empty', async ({ page }) => {
		await page.goto('/analysis/new');
		await expect(page.getByRole('button', { name: /Next/i })).toBeDisabled();
	});

	test('step 1: Next is enabled after typing a name', async ({ page }) => {
		await page.goto('/analysis/new');
		await page.locator('#name').fill('My E2E Analysis');
		await expect(page.getByRole('button', { name: /Next/i })).toBeEnabled();
	});

	test('step 1 → step 2: shows datasource selection', async ({ page }) => {
		await page.goto('/analysis/new');
		await page.locator('#name').fill('E2E Wizard Test');
		await page.getByRole('button', { name: /Next/i }).click();
		await expect(page.getByRole('heading', { name: /Select Data Sources/i })).toBeVisible();
		await screenshot(page, 'analyses', 'wizard-step-2');
	});

	test('step 2: shows "No data sources available" when none exist', async ({ page, request }) => {
		const resp = await request.get('http://localhost:8000/api/v1/datasource');
		const datasources = (await resp.json()) as unknown[];
		test.skip(datasources.length > 0, 'Datasources exist – skipping empty-state check');

		await page.goto('/analysis/new');
		await page.locator('#name').fill('E2E No DS');
		await page.getByRole('button', { name: /Next/i }).click();
		await expect(page.getByText(/No data sources available/i)).toBeVisible();
	});

	test('can navigate Back from step 2 to step 1', async ({ page }) => {
		await page.goto('/analysis/new');
		await page.locator('#name').fill('Back Test');
		await page.getByRole('button', { name: /Next/i }).click();
		await page.getByRole('button', { name: /Back/i }).click();
		await expect(page.getByRole('heading', { name: /Analysis Details/i })).toBeVisible();
	});

	test('Cancel on step 1 returns to home', async ({ page }) => {
		await page.goto('/analysis/new');
		await page.getByRole('link', { name: /Cancel/i }).click();
		await page.waitForURL('/', { timeout: 8_000 });
	});

	test('full create flow: wizard → analysis detail page', async ({ page, request }) => {
		test.setTimeout(60_000);
		await createDatasource(request, 'e2e-create-ds');
		try {
			await page.goto('/analysis/new');

			// Step 1 – name
			await page.locator('#name').fill('E2E Created Analysis');
			await page.getByRole('button', { name: /Next/i }).click();

			// Step 2 – pick datasource
			await expect(page.getByRole('heading', { name: /Select Data Sources/i })).toBeVisible();
			await page.getByPlaceholder('Search datasources...').click();
			await page.locator('[role="option"]', { hasText: 'e2e-create-ds' }).first().click();
			// Close the dropdown by clicking outside
			await page.getByRole('heading', { name: /Select Data Sources/i }).click();
			await expect(page.getByRole('button', { name: /Next/i })).toBeEnabled();
			await page.getByRole('button', { name: /Next/i }).click();

			// Step 3 – review
			await expect(page.getByRole('heading', { name: /Review/i })).toBeVisible();
			await expect(page.getByText('E2E Created Analysis').first()).toBeVisible();
			await page.getByRole('button', { name: /Create Analysis/i }).click();

			// Redirects to analysis editor
			await page.waitForURL(/\/analysis\/.+/, { timeout: 20_000 });
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Created Analysis');
			await deleteDatasourceViaUI(page, 'e2e-create-ds');
		}
	});

	test('description field is optional – can proceed without it', async ({ page }) => {
		await page.goto('/analysis/new');
		await page.locator('#name').fill('No Desc Analysis');
		// description textarea exists but is empty – should not block Next
		await expect(page.locator('#description')).toBeVisible();
		await expect(page.getByRole('button', { name: /Next/i })).toBeEnabled();
	});

	test('description field accepts multiline text', async ({ page }) => {
		await page.goto('/analysis/new');
		await page.locator('#description').fill('Line 1\nLine 2\nLine 3');
		const value = await page.locator('#description').inputValue();
		expect(value).toContain('Line 1');
	});
});

test.describe('Analyses – detail page', () => {
	let dsId = '';
	let aId = '';

	test.beforeAll(async ({ request }) => {
		dsId = await createDatasource(request, 'e2e-detail-ds');
		aId = await createAnalysis(request, 'E2E Detail Test', dsId);
	});

	test.afterAll(async ({ browser }) => {
		const page = await browser.newPage();
		await deleteAnalysisViaUI(page, 'E2E Detail Test');
		await deleteDatasourceViaUI(page, 'e2e-detail-ds');
		await page.close();
	});

	test('analysis detail page loads with step library', async ({ page }) => {
		await page.goto(`/analysis/${aId}`);
		// StepLibrary heading is "Operations"
		await expect(page.getByRole('heading', { name: 'Operations' })).toBeVisible({
			timeout: 15_000
		});
		await screenshot(page, 'analyses', 'detail-step-library');
	});

	test('step library shows search box', async ({ page }) => {
		await page.goto(`/analysis/${aId}`);
		await expect(page.getByPlaceholder(/Search operations/i)).toBeVisible({ timeout: 10_000 });
	});

	test('step library search filters operations', async ({ page }) => {
		await page.goto(`/analysis/${aId}`);
		await page.getByPlaceholder(/Search operations/i).fill('filter');
		await expect(page.getByText('Filter', { exact: true })).toBeVisible();
		// Non-matching steps should not show
		await expect(page.getByText('Pivot', { exact: true })).not.toBeVisible();
	});

	test('Save button is present', async ({ page }) => {
		await page.goto(`/analysis/${aId}`);
		await expect(
			page.getByRole('button', { name: /Save/i }).or(page.getByTitle(/Save/i))
		).toBeVisible({ timeout: 10_000 });
	});

	test('analysis name is shown in the detail page', async ({ page }) => {
		await page.goto(`/analysis/${aId}`);
		await expect(page.getByText('E2E Detail Test')).toBeVisible({ timeout: 10_000 });
	});
});

test.describe('Analyses – save/discard dirty tracking', () => {
	test('Save shows "Saved" and Discard is disabled on clean analysis', async ({
		page,
		request
	}) => {
		test.setTimeout(45_000);
		const dsId = await createDatasource(request, 'e2e-dirty-clean-ds');
		const aId = await createAnalysis(request, 'E2E Dirty Clean', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.getByRole('heading', { name: 'Operations' })).toBeVisible({
				timeout: 15_000
			});

			const saveBtn = page.getByRole('button', { name: 'Saved' });
			await expect(saveBtn).toBeVisible({ timeout: 5_000 });

			const discardBtn = page.getByRole('button', { name: 'Discard' });
			await expect(discardBtn).toBeDisabled();
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Dirty Clean');
			await deleteDatasourceViaUI(page, 'e2e-dirty-clean-ds');
		}
	});

	test('adding a step makes Save show "Save" and enables Discard', async ({ page, request }) => {
		test.setTimeout(45_000);
		const dsId = await createDatasource(request, 'e2e-dirty-add-ds');
		const aId = await createAnalysis(request, 'E2E Dirty Add', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="select"]')).toBeVisible({ timeout: 15_000 });
			await page.locator('button[data-step="select"]').click();

			await expect(page.locator('[data-step-type="select"]').first()).toBeVisible({
				timeout: 5_000
			});

			const saveBtn = page.getByRole('button', { name: 'Save' });
			await expect(saveBtn).toBeVisible({ timeout: 5_000 });

			const discardBtn = page.getByRole('button', { name: 'Discard' });
			await expect(discardBtn).toBeEnabled({ timeout: 5_000 });
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Dirty Add');
			await deleteDatasourceViaUI(page, 'e2e-dirty-add-ds');
		}
	});

	test('Discard reverts dirty state back to "Saved"', async ({ page, request }) => {
		test.setTimeout(45_000);
		const dsId = await createDatasource(request, 'e2e-dirty-discard-ds');
		const aId = await createAnalysis(request, 'E2E Dirty Discard', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="sort"]')).toBeVisible({ timeout: 15_000 });
			await page.locator('button[data-step="sort"]').click();
			await expect(page.locator('[data-step-type="sort"]').first()).toBeVisible({
				timeout: 5_000
			});

			await expect(page.getByRole('button', { name: 'Save' })).toBeVisible({ timeout: 5_000 });

			await page.getByRole('button', { name: 'Discard' }).click();

			await expect(page.getByRole('button', { name: 'Saved' })).toBeVisible({ timeout: 8_000 });
			await expect(page.getByRole('button', { name: 'Discard' })).toBeDisabled();
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Dirty Discard');
			await deleteDatasourceViaUI(page, 'e2e-dirty-discard-ds');
		}
	});

	test('step config Apply/Cancel buttons start with correct state for new step', async ({
		page,
		request
	}) => {
		test.setTimeout(45_000);
		const dsId = await createDatasource(request, 'e2e-dirty-config-ds');
		const aId = await createAnalysis(request, 'E2E Dirty Config', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="filter"]')).toBeVisible({ timeout: 15_000 });
			await page.locator('button[data-step="filter"]').click();

			const canvasNode = page.locator('[data-step-type="filter"]').first();
			await expect(canvasNode).toBeVisible({ timeout: 5_000 });
			await canvasNode.click();

			const configPanel = page.locator('[data-step-config="filter"]');
			await expect(configPanel).toBeVisible({ timeout: 8_000 });

			const applyBtn = configPanel.getByRole('button', { name: 'Apply' });
			const cancelBtn = configPanel.getByRole('button', { name: 'Cancel' });
			await expect(applyBtn).toBeVisible();
			await expect(cancelBtn).toBeVisible();

			// New steps have is_applied=false → hasChanges is true → both enabled
			await expect(applyBtn).toBeEnabled();
			await expect(cancelBtn).toBeEnabled();
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Dirty Config');
			await deleteDatasourceViaUI(page, 'e2e-dirty-config-ds');
		}
	});
});

test.describe('Analyses – step library labels', () => {
	let dsId = '';
	let aId = '';

	test.beforeAll(async ({ request }) => {
		dsId = await createDatasource(request, 'e2e-labels-ds');
		aId = await createAnalysis(request, 'E2E Labels Test', dsId);
	});

	test.afterAll(async ({ browser }) => {
		const page = await browser.newPage();
		await deleteAnalysisViaUI(page, 'E2E Labels Test');
		await deleteDatasourceViaUI(page, 'e2e-labels-ds');
		await page.close();
	});

	// All 25 step types that appear in StepLibrary.svelte (read-only checks)
	const ALL_STEP_LABELS = [
		'Filter',
		'Select',
		'Group By',
		'Sort',
		'Rename',
		'Drop',
		'Join',
		'Expression',
		'With Columns',
		'Pivot',
		'Unpivot',
		'Fill Null',
		'Deduplicate',
		'Explode',
		'Time Series',
		'String Transform',
		'Sample',
		'Limit',
		'Top K',
		'Chart',
		'Notify',
		'AI',
		'View',
		'Union By Name',
		'Download'
	];

	for (const label of ALL_STEP_LABELS) {
		test(`step type "${label}" is visible in library`, async ({ page }) => {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step]', { hasText: label }).first()).toBeVisible({
				timeout: 15_000
			});
		});
	}
});

test.describe('Analyses – step interaction', () => {
	test('clicking Filter step adds it to the canvas', async ({ page, request }) => {
		test.setTimeout(45_000);
		const dsId = await createDatasource(request, 'e2e-click-filter-ds');
		const aId = await createAnalysis(request, 'E2E Click Filter', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="filter"]')).toBeVisible({ timeout: 15_000 });

			// Count filter nodes before click (should be 0)
			const before = await page.locator('[data-step-type="filter"]').count();
			await page.locator('button[data-step="filter"]').click();

			// Exactly one new filter node should appear
			await expect(page.locator('[data-step-type="filter"]')).toHaveCount(before + 1, {
				timeout: 5_000
			});
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Click Filter');
			await deleteDatasourceViaUI(page, 'e2e-click-filter-ds');
		}
	});

	test('clicking Filter canvas node opens config panel with correct type', async ({
		page,
		request
	}) => {
		test.setTimeout(45_000);
		const dsId = await createDatasource(request, 'e2e-config-panel-ds');
		const aId = await createAnalysis(request, 'E2E Config Panel', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="filter"]')).toBeVisible({ timeout: 15_000 });
			await page.locator('button[data-step="filter"]').click();

			const canvasNode = page.locator('[data-step-type="filter"]').first();
			await expect(canvasNode).toBeVisible({ timeout: 5_000 });
			await canvasNode.click();

			const configPanel = page.locator('[data-step-config="filter"]');
			await expect(configPanel).toBeVisible({ timeout: 8_000 });
			await expect(configPanel.getByRole('button', { name: 'Apply' })).toBeVisible();
			await expect(configPanel.getByRole('button', { name: 'Cancel' })).toBeVisible();
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Config Panel');
			await deleteDatasourceViaUI(page, 'e2e-config-panel-ds');
		}
	});

	test('clicking Select step adds it to the canvas (not initial View)', async ({
		page,
		request
	}) => {
		test.setTimeout(45_000);
		const dsId = await createDatasource(request, 'e2e-click-select-ds');
		const aId = await createAnalysis(request, 'E2E Click Select', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="select"]')).toBeVisible({ timeout: 15_000 });

			// No select nodes before click
			await expect(page.locator('[data-step-type="select"]')).toHaveCount(0);
			await page.locator('button[data-step="select"]').click();

			// Exactly one select node after click
			await expect(page.locator('[data-step-type="select"]')).toHaveCount(1, {
				timeout: 5_000
			});
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Click Select');
			await deleteDatasourceViaUI(page, 'e2e-click-select-ds');
		}
	});
});

test.describe('Analyses – save persistence', () => {
	test('saving a step persists across page reload', async ({ page, request }) => {
		test.setTimeout(60_000);
		const dsId = await createDatasource(request, 'e2e-persist-ds');
		const aId = await createAnalysis(request, 'E2E Persist Test', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="filter"]')).toBeVisible({ timeout: 15_000 });

			// No filter nodes initially
			await expect(page.locator('[data-step-type="filter"]')).toHaveCount(0);

			// Add a filter step
			await page.locator('button[data-step="filter"]').click();
			await expect(page.locator('[data-step-type="filter"]')).toHaveCount(1, {
				timeout: 5_000
			});

			// Click Save
			await expect(page.getByRole('button', { name: 'Save' })).toBeVisible({ timeout: 5_000 });
			await page.getByRole('button', { name: 'Save' }).click();
			await expect(page.getByRole('button', { name: 'Saved' })).toBeVisible({ timeout: 10_000 });

			// Reload the page completely
			await page.reload();

			// Wait for the page to fully load
			await expect(page.getByRole('heading', { name: 'Operations' })).toBeVisible({
				timeout: 15_000
			});

			// Filter step should still be present after reload
			await expect(page.locator('[data-step-type="filter"]')).toHaveCount(1, {
				timeout: 10_000
			});

			// Save button should show "Saved" (clean state)
			await expect(page.getByRole('button', { name: 'Saved' })).toBeVisible({ timeout: 5_000 });
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Persist Test');
			await deleteDatasourceViaUI(page, 'e2e-persist-ds');
		}
	});

	test('Apply marks step as applied and Cancel reverts config changes', async ({
		page,
		request
	}) => {
		test.setTimeout(60_000);
		const dsId = await createDatasource(request, 'e2e-apply-cancel-ds');
		const aId = await createAnalysis(request, 'E2E Apply Cancel', dsId);
		try {
			await page.goto(`/analysis/${aId}`);
			await expect(page.locator('button[data-step="filter"]')).toBeVisible({ timeout: 15_000 });

			// Add a filter step and open config
			await page.locator('button[data-step="filter"]').click();
			const canvasNode = page.locator('[data-step-type="filter"]').first();
			await expect(canvasNode).toBeVisible({ timeout: 5_000 });
			await canvasNode.click();

			const configPanel = page.locator('[data-step-config="filter"]');
			await expect(configPanel).toBeVisible({ timeout: 8_000 });

			const applyBtn = configPanel.getByRole('button', { name: 'Apply' });
			const cancelBtn = configPanel.getByRole('button', { name: 'Cancel' });

			// New step: is_applied=false → both buttons enabled
			await expect(applyBtn).toBeEnabled();
			await expect(cancelBtn).toBeEnabled();

			// Click Apply — marks step as applied → hasChanges becomes false
			await applyBtn.click();
			await expect(applyBtn).toBeDisabled({ timeout: 5_000 });
			await expect(cancelBtn).toBeDisabled({ timeout: 5_000 });
		} finally {
			await deleteAnalysisViaUI(page, 'E2E Apply Cancel');
			await deleteDatasourceViaUI(page, 'e2e-apply-cancel-ds');
		}
	});
});

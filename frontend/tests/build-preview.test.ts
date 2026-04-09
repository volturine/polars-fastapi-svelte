import { test, expect } from '@playwright/test';
import { createDatasource, createAnalysis } from './utils/api.js';
import { deleteAnalysisViaUI, deleteDatasourceViaUI } from './utils/ui-cleanup.js';
import { waitForLayoutReady } from './utils/readiness.js';
import { uid } from './utils/uid.js';
import { screenshot } from './utils/visual.js';

// ── Build Preview modal ─────────────────────────────────────────────────────

test.describe('Build Preview – modal lifecycle', () => {
	test('clicking Build opens the Build Preview modal', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-open-ds-${uid()}`;
		const aName = `E2E BPrev Open ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: 'mock-build-001',
								analysis_id: aId,
								status: 'running',
								progress: 0,
								current_step: null,
								started_at: new Date().toISOString(),
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			await expect(page.getByText('Build Preview')).toBeVisible({ timeout: 10_000 });
			await expect(page.locator('[data-testid="build-preview"]')).toBeVisible({ timeout: 5_000 });

			const closeBtn = page.locator('[aria-label="Close build preview"]');
			await expect(closeBtn).toBeVisible();

			await screenshot(page, 'build-preview', 'modal-opened');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('close button dismisses the Build Preview modal', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-close-ds-${uid()}`;
		const aName = `E2E BPrev Close ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: 'mock-build-002',
								analysis_id: aId,
								status: 'running',
								progress: 10,
								current_step: 'Loading data',
								started_at: new Date().toISOString(),
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			await expect(page.locator('[data-testid="build-preview"]')).toBeVisible({ timeout: 10_000 });

			const closeBtn = page.locator('[aria-label="Close build preview"]');
			await expect(closeBtn).toBeVisible();
			await closeBtn.click();

			await expect(page.locator('[role="dialog"]')).not.toBeVisible({ timeout: 5_000 });

			await screenshot(page, 'build-preview', 'modal-closed');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});
});

// ── Build Preview – progress and status ─────────────────────────────────────

test.describe('Build Preview – progress states', () => {
	test('shows connecting state before snapshot arrives', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-connect-ds-${uid()}`;
		const aName = `E2E BPrev Connect ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, () => {});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			await expect(page.locator('[data-testid="build-preview"]')).toBeVisible({ timeout: 10_000 });

			await expect(page.locator('[data-testid="build-steps-panel"]')).toBeVisible({
				timeout: 5_000
			});
			await expect(page.getByText('Waiting for build to start...')).toBeVisible({
				timeout: 5_000
			});

			const progressBar = page.locator('[data-testid="build-progress-bar"]');
			await expect(progressBar).toBeVisible();
			await expect(progressBar).toHaveAttribute('aria-valuenow', '0');

			await expect(page.getByText('Connecting')).toBeVisible();

			await screenshot(page, 'build-preview', 'connecting-state');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('shows steps as they stream in', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-steps-ds-${uid()}`;
		const aName = `E2E BPrev Steps ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			const buildId = 'mock-build-steps';
			const now = new Date().toISOString();
			const base = { build_id: buildId, analysis_id: aId, emitted_at: now };

			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: buildId,
								analysis_id: aId,
								status: 'running',
								progress: 0,
								current_step: null,
								started_at: now,
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'step_start',
								step_index: 0,
								step_name: 'Load source data',
								tab_id: 'tab-1',
								tab_name: 'Source 1'
							})
						);
					}, 100);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'progress',
								progress: 50,
								elapsed_ms: 1000,
								estimated_remaining_ms: 1000,
								current_step: 'Load source data',
								current_step_index: 0,
								total_steps: 2
							})
						);
					}, 200);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'step_complete',
								step_index: 0,
								step_name: 'Load source data',
								duration_ms: 450,
								tab_id: 'tab-1',
								tab_name: 'Source 1'
							})
						);
					}, 300);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'step_start',
								step_index: 1,
								step_name: 'Write output',
								tab_id: 'tab-1',
								tab_name: 'Source 1'
							})
						);
					}, 400);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			await expect(page.locator('[data-testid="build-preview"]')).toBeVisible({ timeout: 10_000 });

			const step0 = page.locator('[data-testid="build-step-0"]');
			await expect(step0).toBeVisible({ timeout: 5_000 });
			await expect(step0).toHaveAttribute('data-step-status', 'complete', { timeout: 5_000 });
			await expect(step0).toContainText('Load source data');

			const step1 = page.locator('[data-testid="build-step-1"]');
			await expect(step1).toBeVisible({ timeout: 5_000 });
			await expect(step1).toHaveAttribute('data-step-status', 'running', { timeout: 5_000 });
			await expect(step1).toContainText('Write output');

			const progressBar = page.locator('[data-testid="build-progress-bar"]');
			await expect(progressBar).toHaveAttribute('aria-valuenow', '50', { timeout: 5_000 });

			await screenshot(page, 'build-preview', 'steps-streaming');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('shows complete state with results', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-complete-ds-${uid()}`;
		const aName = `E2E BPrev Complete ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			const buildId = 'mock-build-complete';
			const now = new Date().toISOString();
			const base = { build_id: buildId, analysis_id: aId, emitted_at: now };

			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: buildId,
								analysis_id: aId,
								status: 'running',
								progress: 0,
								current_step: null,
								started_at: now,
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'step_start',
								step_index: 0,
								step_name: 'Write output',
								tab_id: 'tab-1',
								tab_name: 'Source 1'
							})
						);
					}, 50);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'step_complete',
								step_index: 0,
								step_name: 'Write output',
								duration_ms: 200,
								tab_id: 'tab-1',
								tab_name: 'Source 1'
							})
						);
					}, 100);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'complete',
								duration_ms: 1250,
								results: [{ tab_id: 'tab-1', tab_name: 'Source 1', status: 'success', error: null }]
							})
						);
					}, 150);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			const preview = page.locator('[data-testid="build-preview"]');
			await expect(preview).toBeVisible({ timeout: 10_000 });

			await expect(preview.getByText('Complete', { exact: true })).toBeVisible({ timeout: 10_000 });

			const progressBar = page.locator('[data-testid="build-progress-bar"]');
			await expect(progressBar).toHaveAttribute('aria-valuenow', '100', { timeout: 5_000 });

			await expect(page.locator('[data-testid="build-results"]')).toBeVisible({ timeout: 5_000 });
			await expect(
				page.locator('[data-testid="build-results"]').getByText('Source 1')
			).toBeVisible();
			await expect(
				page.locator('[data-testid="build-results"]').getByText('success')
			).toBeVisible();

			await expect(preview.getByText('Finished in 1.25s')).toBeVisible({ timeout: 5_000 });

			await screenshot(page, 'build-preview', 'complete-state');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('shows failed state with error', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-fail-ds-${uid()}`;
		const aName = `E2E BPrev Fail ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			const buildId = 'mock-build-fail';
			const now = new Date().toISOString();
			const base = { build_id: buildId, analysis_id: aId, emitted_at: now };

			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: buildId,
								analysis_id: aId,
								status: 'running',
								progress: 0,
								current_step: null,
								started_at: now,
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'step_start',
								step_index: 0,
								step_name: 'Load source data',
								tab_id: 'tab-1',
								tab_name: 'Source 1'
							})
						);
					}, 50);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'step_failed',
								step_index: 0,
								step_name: 'Load source data',
								error: 'Column "missing_col" not found',
								tab_id: 'tab-1',
								tab_name: 'Source 1'
							})
						);
					}, 100);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'failed',
								error: 'Build failed: Column "missing_col" not found'
							})
						);
					}, 150);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			const preview = page.locator('[data-testid="build-preview"]');
			await expect(preview).toBeVisible({ timeout: 10_000 });

			await expect(preview.getByText('Failed', { exact: true })).toBeVisible({ timeout: 10_000 });

			await expect(page.locator('[data-testid="build-error"]')).toBeVisible({ timeout: 5_000 });
			await expect(page.locator('[data-testid="build-error"]')).toContainText(
				'Build failed: Column "missing_col" not found'
			);

			const step0 = page.locator('[data-testid="build-step-0"]');
			await expect(step0).toHaveAttribute('data-step-status', 'failed', { timeout: 5_000 });

			await screenshot(page, 'build-preview', 'failed-state');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});
});

// ── Build Preview – tabs ────────────────────────────────────────────────────

test.describe('Build Preview – tab navigation', () => {
	test('Plan tab appears when plan event is received', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-plan-ds-${uid()}`;
		const aName = `E2E BPrev Plan ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			const buildId = 'mock-build-plan';
			const now = new Date().toISOString();
			const base = { build_id: buildId, analysis_id: aId, emitted_at: now };

			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: buildId,
								analysis_id: aId,
								status: 'running',
								progress: 0,
								current_step: null,
								started_at: now,
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'plan',
								plan: 'SELECT id, name FROM source_table\nWHERE age > 25'
							})
						);
					}, 100);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			await expect(page.locator('[data-testid="build-preview"]')).toBeVisible({ timeout: 10_000 });

			const planTab = page
				.locator('[data-testid="build-preview"]')
				.getByRole('tab', { name: 'Plan' });
			await expect(planTab).toBeVisible({ timeout: 5_000 });
			await planTab.click();

			await expect(page.locator('[data-testid="build-plan-panel"]')).toBeVisible({
				timeout: 5_000
			});
			await expect(page.getByText('SELECT id, name FROM source_table')).toBeVisible();

			await screenshot(page, 'build-preview', 'plan-tab');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('Resources tab appears when resources event is received', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-res-ds-${uid()}`;
		const aName = `E2E BPrev Resources ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			const buildId = 'mock-build-resources';
			const now = new Date().toISOString();
			const base = { build_id: buildId, analysis_id: aId, emitted_at: now };

			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: buildId,
								analysis_id: aId,
								status: 'running',
								progress: 0,
								current_step: null,
								started_at: now,
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'resources',
								cpu_percent: 42.5,
								memory_mb: 256,
								memory_limit_mb: 1024,
								active_threads: 4,
								max_threads: 8
							})
						);
					}, 100);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			await expect(page.locator('[data-testid="build-preview"]')).toBeVisible({ timeout: 10_000 });

			const resTab = page
				.locator('[data-testid="build-preview"]')
				.getByRole('tab', { name: 'Resources' });
			await expect(resTab).toBeVisible({ timeout: 5_000 });
			await resTab.click();

			await expect(page.locator('[data-testid="build-resources-panel"]')).toBeVisible({
				timeout: 5_000
			});
			await expect(page.getByText('42.5%')).toBeVisible();
			await expect(page.getByText('256 MB')).toBeVisible();
			await expect(page.getByText('4/8 threads')).toBeVisible();

			await screenshot(page, 'build-preview', 'resources-tab');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});

	test('Logs tab appears when log events arrive', async ({ page, request }) => {
		test.setTimeout(90_000);
		const dsName = `e2e-bprev-logs-ds-${uid()}`;
		const aName = `E2E BPrev Logs ${uid()}`;
		const dsId = await createDatasource(request, dsName);
		const aId = await createAnalysis(request, aName, dsId);
		try {
			const buildId = 'mock-build-logs';
			const now = new Date().toISOString();
			const base = { build_id: buildId, analysis_id: aId, emitted_at: now };

			await page.routeWebSocket(/\/v1\/compute\/ws\/build(\?|$)/, (ws) => {
				ws.onMessage(() => {
					ws.send(
						JSON.stringify({
							type: 'snapshot',
							build: {
								build_id: buildId,
								analysis_id: aId,
								status: 'running',
								progress: 0,
								current_step: null,
								started_at: now,
								tab_count: 1,
								steps: [],
								logs: [],
								plan: null,
								resources: null,
								results: [],
								error: null
							}
						})
					);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'log',
								level: 'info',
								message: 'Starting build pipeline'
							})
						);
					}, 50);

					setTimeout(() => {
						ws.send(
							JSON.stringify({
								...base,
								type: 'log',
								level: 'debug',
								message: 'Resolved 3 columns from schema'
							})
						);
					}, 100);
				});
			});

			await page.goto(`/analysis/${aId}`);
			await waitForLayoutReady(page);
			await expect(page.locator('[role="application"]')).toBeVisible({ timeout: 15_000 });

			const buildBtn = page.locator('[data-testid="output-build-button"]');
			await expect(buildBtn).toBeVisible({ timeout: 10_000 });
			await buildBtn.click();

			await expect(page.locator('[data-testid="build-preview"]')).toBeVisible({ timeout: 10_000 });

			const logsTab = page
				.locator('[data-testid="build-preview"]')
				.getByRole('tab', { name: /Logs/ });
			await expect(logsTab).toBeVisible({ timeout: 5_000 });
			await logsTab.click();

			await expect(page.locator('[data-testid="build-logs-panel"]')).toBeVisible({
				timeout: 5_000
			});
			await expect(page.getByText('[info] Starting build pipeline')).toBeVisible();
			await expect(page.getByText('[debug] Resolved 3 columns from schema')).toBeVisible();

			await screenshot(page, 'build-preview', 'logs-tab');
		} finally {
			await deleteAnalysisViaUI(page, aName);
			await deleteDatasourceViaUI(page, dsName);
		}
	});
});

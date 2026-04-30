import fs from 'node:fs';
import { chromium } from '@playwright/test';
import {
	AUTH_DIR,
	META_FILE,
	deleteAccount,
	readStoredSessionToken,
	workerAuthFile
} from './utils/api.js';
import {
	createCleanupPage,
	deleteAnalysisViaUI,
	deleteDatasourceViaUI,
	deleteHealthCheckViaUI,
	deleteScheduleViaUI,
	deleteUdfViaUI
} from './utils/ui-cleanup.js';

const MAX_CLEANUP_PASSES = 25;

async function cleanSchedules(page: import('@playwright/test').Page): Promise<void> {
	for (let attempt = 0; attempt < MAX_CLEANUP_PASSES; attempt += 1) {
		const row = page
			.locator('tr')
			.filter({ has: page.getByLabel('Delete schedule') })
			.filter({ hasText: 'e2e-' })
			.first();
		try {
			await row.waitFor({ state: 'visible', timeout: 1_000 });
		} catch {
			return;
		}
		await deleteScheduleViaUI(page, await row.textContent().then((text) => text ?? ''));
	}
	console.warn('[e2e] globalTeardown schedule cleanup hit max passes');
}

async function cleanHealthChecks(page: import('@playwright/test').Page): Promise<void> {
	for (let attempt = 0; attempt < MAX_CLEANUP_PASSES; attempt += 1) {
		await page.goto('/monitoring?tab=health', { waitUntil: 'domcontentloaded' });
		const row = page.locator('[data-healthcheck-name^="e2e"]').first();
		try {
			await row.waitFor({ state: 'visible', timeout: 1_000 });
		} catch {
			return;
		}
		const name = await row.getAttribute('data-healthcheck-name');
		if (!name) return;
		await deleteHealthCheckViaUI(page, name);
	}
	console.warn('[e2e] globalTeardown health-check cleanup hit max passes');
}

async function cleanAnalyses(page: import('@playwright/test').Page): Promise<void> {
	for (let attempt = 0; attempt < MAX_CLEANUP_PASSES; attempt += 1) {
		await page.goto('/', { waitUntil: 'domcontentloaded' });
		const card = page.locator('[data-analysis-card^="E2E"]').first();
		try {
			await card.waitFor({ state: 'visible', timeout: 1_000 });
		} catch {
			return;
		}
		const name = await card.getAttribute('data-analysis-card');
		if (!name) return;
		await deleteAnalysisViaUI(page, name, { skipNavigation: true });
	}
	console.warn('[e2e] globalTeardown analysis cleanup hit max passes');
}

async function cleanDatasources(page: import('@playwright/test').Page): Promise<void> {
	for (let attempt = 0; attempt < MAX_CLEANUP_PASSES; attempt += 1) {
		await page.goto('/datasources', { waitUntil: 'domcontentloaded' });
		const toggle = page.locator('button[title="Show auto-generated datasources"]');
		if (await toggle.isVisible().catch(() => false)) {
			await toggle.click();
		}
		const row = page.locator('[data-ds-row^="e2e-"]').first();
		try {
			await row.waitFor({ state: 'visible', timeout: 1_000 });
		} catch {
			return;
		}
		const name = await row.getAttribute('data-ds-row');
		if (!name) return;
		await deleteDatasourceViaUI(page, name);
	}
	console.warn('[e2e] globalTeardown datasource cleanup hit max passes');
}

async function cleanUdfs(page: import('@playwright/test').Page): Promise<void> {
	for (let attempt = 0; attempt < MAX_CLEANUP_PASSES; attempt += 1) {
		await page.goto('/udfs', { waitUntil: 'domcontentloaded' });
		const card = page.locator('[data-udf-card^="e2e"]').first();
		try {
			await card.waitFor({ state: 'visible', timeout: 1_000 });
		} catch {
			return;
		}
		const name = await card.getAttribute('data-udf-card');
		if (!name) return;
		await deleteUdfViaUI(page, name);
	}
	console.warn('[e2e] globalTeardown UDF cleanup hit max passes');
}

export default async function globalTeardown(): Promise<void> {
	const authFiles = fs.existsSync(AUTH_DIR)
		? fs.readdirSync(AUTH_DIR).filter((f) => f.startsWith('state-w') && f.endsWith('.json'))
		: [];

	for (const entry of authFiles) {
		const match = entry.match(/^state-w(\d+)\.json$/);
		if (!match) continue;
		const workerIndex = parseInt(match[1], 10);
		const authFile = workerAuthFile(workerIndex);
		const token = readStoredSessionToken(authFile);

		if (fs.existsSync(authFile)) {
			const browser = await chromium.launch();
			const { page, context } = await createCleanupPage(browser, workerIndex);
			try {
				await cleanSchedules(page);
				await cleanHealthChecks(page);
				await cleanAnalyses(page);
				await cleanDatasources(page);
				await cleanUdfs(page);
			} catch {
				// Best-effort suite cleanup should not hide the real test result.
			} finally {
				await context.close();
				await browser.close();
			}
		}

		if (token) {
			await deleteAccount(token).catch(() => {});
		}

		try {
			fs.unlinkSync(authFile);
		} catch {
			// already removed by worker teardown
		}
	}

	for (const entry of fs.readdirSync(AUTH_DIR).filter((f) => f.startsWith('state-w'))) {
		try {
			fs.unlinkSync(`${AUTH_DIR}/${entry}`);
		} catch {
			// already removed by worker teardown
		}
	}

	try {
		fs.unlinkSync(META_FILE);
	} catch {
		// meta file may not exist if setup failed
	}
}

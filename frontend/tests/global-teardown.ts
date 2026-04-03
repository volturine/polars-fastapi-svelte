import { chromium } from '@playwright/test';
import { AUTH_FILE } from './utils/api.js';

const port = parseInt(process.env.FRONTEND_PORT || '3000', 10);
const baseURL = `http://localhost:${port}`;

/** Max time to wait for data-driven elements to appear after navigation. */
const ELEMENT_TIMEOUT = 10_000;
const DIALOG_TIMEOUT = 10_000;

export default async function globalTeardown() {
	const browser = await chromium.launch();
	const context = await browser.newContext({ storageState: AUTH_FILE, baseURL });
	const page = await context.newPage();

	try {
		await cleanVisibleRows(page, '/monitoring?tab=schedules', 'Delete schedule');
		await cleanVisibleRows(page, '/monitoring?tab=health', 'Delete check');
		await cleanAnalyses(page);
		await cleanDatasources(page);
		await cleanUdfs(page);
		console.log('[teardown] cleanup complete');
	} catch (err) {
		console.log(`[teardown] error during cleanup: ${err}`);
	} finally {
		await context.close();
		await browser.close();
	}
}

/**
 * Delete all visible rows matching the given delete button label.
 * Navigates fresh for each deletion to avoid DOM instability from TanStack Query refetches.
 */
async function cleanVisibleRows(
	page: import('@playwright/test').Page,
	url: string,
	deleteLabel: string
) {
	while (true) {
		try {
			await page.goto(url, { waitUntil: 'domcontentloaded' });
			const rows = page.locator('tr').filter({ has: page.getByLabel(deleteLabel) });
			try {
				await rows.first().waitFor({ state: 'visible', timeout: ELEMENT_TIMEOUT });
			} catch {
				return; // No rows to clean
			}
			await rows.first().getByLabel(deleteLabel).click();
			const dialog = page.getByRole('dialog');
			await dialog.getByRole('button', { name: /^Delete$/ }).click();
			await dialog.waitFor({ state: 'hidden', timeout: DIALOG_TIMEOUT });
		} catch (e: unknown) {
			console.log(`[teardown] cleanVisibleRows(${deleteLabel}) stopped:`, e);
			return;
		}
	}
}

async function cleanAnalyses(page: import('@playwright/test').Page) {
	while (true) {
		try {
			await page.goto('/', { waitUntil: 'domcontentloaded' });
			// Clear persisted search filter that may hide cards
			const searchBox = page.getByRole('textbox').first();
			try {
				await searchBox.waitFor({ state: 'visible', timeout: 5_000 });
				const value = await searchBox.inputValue();
				if (value) await searchBox.fill('');
			} catch {
				// Proceed — search box may not exist
			}
			const cards = page.locator('[data-analysis-card]');
			try {
				await cards.first().waitFor({ state: 'visible', timeout: ELEMENT_TIMEOUT });
			} catch {
				return;
			}
			const card = cards.first();
			const name = await card.getAttribute('data-analysis-card');
			await card.getByRole('button', { name: /Delete analysis/ }).click();
			const dialog = page.getByRole('dialog');
			await dialog.getByRole('button', { name: /^Delete$/ }).click();
			await dialog.waitFor({ state: 'hidden', timeout: DIALOG_TIMEOUT });
			console.log(`[teardown] deleted analysis "${name}"`);
		} catch (e: unknown) {
			console.log('[teardown] cleanAnalyses stopped:', e);
			return;
		}
	}
}

async function cleanDatasources(page: import('@playwright/test').Page) {
	while (true) {
		try {
			await page.goto('/datasources', { waitUntil: 'domcontentloaded' });
			const rows = page.locator('[data-ds-row]');
			try {
				await rows.first().waitFor({ state: 'visible', timeout: ELEMENT_TIMEOUT });
			} catch {
				return;
			}
			const row = rows.first();
			const name = await row.getAttribute('data-ds-row');
			await row.locator('button[title="Delete"]').click();
			const dialog = page.getByRole('dialog');
			await dialog.getByRole('button', { name: /^Delete$/ }).click();
			await dialog.waitFor({ state: 'hidden', timeout: DIALOG_TIMEOUT });
			console.log(`[teardown] deleted datasource "${name}"`);
		} catch (e: unknown) {
			console.log('[teardown] cleanDatasources stopped:', e);
			return;
		}
	}
}

async function cleanUdfs(page: import('@playwright/test').Page) {
	while (true) {
		try {
			await page.goto('/udfs', { waitUntil: 'domcontentloaded' });
			const cards = page.locator('[data-udf-card]');
			try {
				await cards.first().waitFor({ state: 'visible', timeout: ELEMENT_TIMEOUT });
			} catch {
				return;
			}
			const card = cards.first();
			const name = await card.getAttribute('data-udf-card');
			await card.getByRole('button', { name: /^Delete$/i }).click();
			await card.getByRole('button', { name: /Confirm/i }).click();
			console.log(`[teardown] deleted UDF "${name}"`);
		} catch (e: unknown) {
			console.log('[teardown] cleanUdfs stopped:', e);
			return;
		}
	}
}

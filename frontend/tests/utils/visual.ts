import { mkdirSync } from 'fs';
import { dirname, resolve } from 'path';
import type { Page } from '@playwright/test';

const SCREENSHOTS_DIR = resolve(import.meta.dirname, '..', 'screenshots');

function sanitize(raw: string): string {
	return raw
		.toLowerCase()
		.replace(/[^a-z0-9]+/g, '-')
		.replace(/^-|-$/g, '')
		.slice(0, 120);
}

/**
 * Wait for the page to reach a visually stable state before capturing.
 * Clears common loading indicators: spinners, skeleton loaders, and
 * TanStack Query loading states.
 */
async function waitForStableUI(page: Page, timeout = 10_000): Promise<void> {
	const deadline = Date.now() + timeout;

	const loadingSelectors = [
		'[class*="spinner"]',
		'[data-loading="true"]',
		'text="Loading..."',
		'text="Loading lineage..."',
		'text="Loading UDF..."'
	];

	for (const selector of loadingSelectors) {
		const remaining = deadline - Date.now();
		if (remaining <= 0) break;
		await page
			.locator(selector)
			.first()
			.waitFor({ state: 'hidden', timeout: Math.max(remaining, 500) })
			.catch(() => {
				// Indicator was never present or already hidden
			});
	}

	// Brief settle for CSS transitions / paint
	await page.waitForTimeout(150);
}

/**
 * Capture a curated screenshot into `frontend/tests/screenshots/<suite>/<name>.png`.
 *
 * - `suite` groups shots by feature area (e.g. "navigation", "datasources")
 * - `name` is a short descriptor for this specific capture point
 * - Waits for loading indicators to clear before capturing
 * - Directories are created automatically; names are sanitized to filesystem-safe strings
 */
export async function screenshot(page: Page, suite: string, name: string): Promise<void> {
	await waitForStableUI(page);
	const path = `${SCREENSHOTS_DIR}/${sanitize(suite)}/${sanitize(name)}.png`;
	mkdirSync(dirname(path), { recursive: true });
	await page.screenshot({ path, fullPage: true });
}

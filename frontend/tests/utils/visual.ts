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
 * Capture a curated screenshot into `frontend/tests/screenshots/<suite>/<name>.png`.
 *
 * - `suite` groups shots by feature area (e.g. "navigation", "datasources")
 * - `name` is a short descriptor for this specific capture point
 * - Directories are created automatically; names are sanitized to filesystem-safe strings
 */
export async function screenshot(page: Page, suite: string, name: string): Promise<void> {
	const path = `${SCREENSHOTS_DIR}/${sanitize(suite)}/${sanitize(name)}.png`;
	mkdirSync(dirname(path), { recursive: true });
	await page.screenshot({ path, fullPage: true });
}

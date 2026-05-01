import type { Locator, Page } from '@playwright/test';
import { waitForDatasourceList } from './readiness.js';

const ELEMENT_VISIBLE_TIMEOUT = 10_000;
const DIALOG_HIDDEN_TIMEOUT = 10_000;

function confirmDialog(page: Page, heading: string | RegExp): Locator {
	return page.getByRole('dialog').filter({ has: page.getByRole('heading', { name: heading }) });
}

export async function deleteDatasourceViaUI(page: Page, name: string): Promise<void> {
	try {
		await page.goto('/datasources', { waitUntil: 'domcontentloaded' });
		await waitForDatasourceList(page, ELEMENT_VISIBLE_TIMEOUT);
		const row = page.locator(`[data-ds-row="${name}"]`);
		if (!(await row.isVisible().catch(() => false))) return;
		await row.locator('button[title="Delete"]').click();
		const dialog = confirmDialog(page, 'Delete Datasource');
		await dialog.getByRole('button', { name: /^Delete$/ }).click();
		await dialog.waitFor({ state: 'hidden', timeout: DIALOG_HIDDEN_TIMEOUT });
	} catch (error) {
		console.warn(`[pure-e2e] deleteDatasourceViaUI failed for "${name}":`, error);
	}
}

export async function deleteAnalysisViaUI(page: Page, name: string): Promise<void> {
	try {
		await page.goto('/', { waitUntil: 'domcontentloaded' });
		const card = page.locator(`[data-analysis-card="${name}"]`);
		await card.waitFor({ state: 'visible', timeout: ELEMENT_VISIBLE_TIMEOUT });
		await card.getByRole('button', { name: /Delete analysis/ }).click();
		const dialog = confirmDialog(page, 'Delete Analysis');
		await dialog.getByRole('button', { name: /^Delete$/ }).click();
		await dialog.waitFor({ state: 'hidden', timeout: DIALOG_HIDDEN_TIMEOUT });
	} catch (error) {
		console.warn(`[pure-e2e] deleteAnalysisViaUI failed for "${name}":`, error);
	}
}

export async function deleteScheduleViaUI(page: Page, datasourceName: string): Promise<void> {
	try {
		await page.goto('/monitoring?tab=schedules', { waitUntil: 'domcontentloaded' });
		const row = page
			.locator('tr')
			.filter({ has: page.getByLabel('Delete schedule') })
			.filter({ hasText: datasourceName });
		await row.waitFor({ state: 'visible', timeout: ELEMENT_VISIBLE_TIMEOUT });
		await row.getByLabel('Delete schedule').click();
		const dialog = confirmDialog(page, 'Delete Schedule');
		await dialog.getByRole('button', { name: /^Delete$/ }).click();
		await dialog.waitFor({ state: 'hidden', timeout: DIALOG_HIDDEN_TIMEOUT });
	} catch (error) {
		console.warn(`[pure-e2e] deleteScheduleViaUI failed for "${datasourceName}":`, error);
	}
}

export async function deleteHealthCheckViaUI(page: Page, name: string): Promise<void> {
	try {
		await page.goto('/monitoring?tab=health', { waitUntil: 'domcontentloaded' });
		const row = page.locator(`[data-healthcheck-name="${name}"]`);
		await row.waitFor({ state: 'visible', timeout: ELEMENT_VISIBLE_TIMEOUT });
		await row.getByLabel('Delete check').click();
		const dialog = confirmDialog(page, 'Delete Health Check');
		await dialog.getByRole('button', { name: /^Delete$/ }).click();
		await dialog.waitFor({ state: 'hidden', timeout: DIALOG_HIDDEN_TIMEOUT });
	} catch (error) {
		console.warn(`[pure-e2e] deleteHealthCheckViaUI failed for "${name}":`, error);
	}
}

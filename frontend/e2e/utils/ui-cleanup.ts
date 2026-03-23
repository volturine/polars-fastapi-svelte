import type { Page } from '@playwright/test';

/**
 * UI-based cleanup helpers. Each function navigates to the relevant page,
 * finds the resource by name, and deletes it through the application's own
 * delete flow. Errors are silently caught so these are safe to call from
 * `finally` blocks even when the test has already failed.
 */

export async function deleteDatasourceViaUI(page: Page, name: string): Promise<void> {
	try {
		await page.goto('/datasources');
		const row = page.locator('button', { hasText: name }).locator('..');
		const deleteBtn = row.locator('button[title="Delete"]');
		await deleteBtn.click({ timeout: 5_000 });
		const dialog = page.getByRole('dialog');
		await dialog.getByRole('button', { name: /^Delete$/ }).click({ timeout: 5_000 });
		await page.getByText(name).waitFor({ state: 'hidden', timeout: 8_000 });
	} catch {
		// Best-effort — global teardown will catch stragglers
	}
}

export async function deleteAnalysisViaUI(page: Page, name: string): Promise<void> {
	try {
		await page.goto('/');
		const card = page.locator('h3', { hasText: name }).first().locator('..');
		await card.locator('svg').click({ timeout: 5_000 });
		const dialog = page.getByRole('dialog');
		await dialog.getByRole('button', { name: /^Delete$/ }).click({ timeout: 5_000 });
		await page.locator('h3', { hasText: name }).waitFor({ state: 'hidden', timeout: 8_000 });
	} catch {
		// Best-effort
	}
}

export async function deleteUdfViaUI(page: Page, name: string): Promise<void> {
	try {
		await page.goto('/udfs');
		const row = page.locator('h3', { hasText: name }).first().locator('../../..');
		await row.getByRole('button', { name: /^Delete$/i }).click({ timeout: 5_000 });
		await row.getByRole('button', { name: /Confirm/i }).click({ timeout: 5_000 });
		await page
			.locator('h3', { hasText: name })
			.first()
			.waitFor({ state: 'hidden', timeout: 8_000 });
	} catch {
		// Best-effort
	}
}

export async function deleteScheduleViaUI(page: Page, cronOrName: string): Promise<void> {
	try {
		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Schedules' }).click();
		const text = page.getByText(cronOrName).first();
		await text.waitFor({ state: 'visible', timeout: 8_000 });
		// Find the closest row and its delete button
		await page
			.locator('button[title="Delete schedule"]')
			.first()
			.click({ force: true, timeout: 5_000 });
		await text.waitFor({ state: 'hidden', timeout: 8_000 });
	} catch {
		// Best-effort
	}
}

export async function deleteHealthCheckViaUI(page: Page, name: string): Promise<void> {
	try {
		await page.goto('/monitoring');
		await page.getByRole('button', { name: 'Health Checks' }).click();
		const text = page.getByText(name).first();
		await text.waitFor({ state: 'visible', timeout: 8_000 });
		await page.locator('button[title="Delete check"]').first().click({ timeout: 5_000 });
		await text.waitFor({ state: 'hidden', timeout: 8_000 });
	} catch {
		// Best-effort
	}
}

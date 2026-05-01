import { expect, type Locator, type Page } from '@playwright/test';

async function waitForAnyVisible(locator: Locator, timeout: number): Promise<void> {
	await expect
		.poll(
			async () => {
				const count = await locator.count();
				for (let index = 0; index < count; index += 1) {
					if (
						await locator
							.nth(index)
							.isVisible()
							.catch(() => false)
					) {
						return true;
					}
				}
				return false;
			},
			{ timeout }
		)
		.toBe(true);
}

export async function waitForAppShell(page: Page, timeout = 15_000): Promise<void> {
	await expect(page.getByLabel('Main navigation')).toBeVisible({ timeout });
	await expect(page.locator('[data-shell-interactive="true"]')).toBeVisible({ timeout });
}

export async function waitForLayoutReady(page: Page, timeout = 30_000): Promise<void> {
	await waitForAppShell(page, timeout);
	await waitForAnyVisible(page.locator('main'), timeout);
}

export async function waitForDatasourceList(page: Page, timeout = 15_000): Promise<void> {
	const terminal = page.locator(
		'[data-ds-row], :text("No data sources yet"), :text("No datasources match"), [aria-live="polite"]'
	);
	await waitForAnyVisible(terminal, timeout);
}

export async function selectDatasourceAndWaitForConfig(
	page: Page,
	name: string,
	timeout = 15_000
): Promise<void> {
	await waitForDatasourceList(page, timeout);
	const row = page.locator(`[data-ds-row="${name}"]`);
	await expect(row).toBeVisible({ timeout });
	await row.click();
	const config = page.locator('[data-ds-config]');
	await expect(config).toBeVisible({ timeout });
	await expect(config.locator('[role="tab"][aria-selected="true"]')).toBeVisible({ timeout });
}

export async function gotoNewAnalysis(page: Page, timeout = 15_000): Promise<void> {
	await page.goto('/analysis/new');
	await waitForLayoutReady(page, timeout);
	await expect(page.locator('#name')).toBeVisible({ timeout });
}

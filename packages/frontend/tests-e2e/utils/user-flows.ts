import { expect, type Locator, type Page } from '@playwright/test';
import { gotoNewAnalysis, waitForDatasourceList, waitForLayoutReady } from './readiness.js';

const SAMPLE_CSV = 'id,name,age,city\n1,Alice,30,London\n2,Bob,25,Paris\n3,Charlie,35,Berlin\n';

function generateLargeCsv(rows: number): string {
	const names = ['Alice', 'Bob', 'Charlie', 'Diana', 'Eve', 'Frank'];
	const cities = ['London', 'Paris', 'Berlin', 'Tokyo', 'Sydney', 'Oslo'];
	const lines = ['id,name,age,city'];
	for (let index = 1; index <= rows; index += 1) {
		lines.push(
			`${index},${names[index % names.length]},${20 + (index % 50)},${cities[index % cities.length]}`
		);
	}
	return `${lines.join('\n')}\n`;
}

export async function uploadCsvDatasource(
	page: Page,
	name: string,
	options?: { description?: string; rows?: number }
): Promise<void> {
	await page.goto('/datasources/new');
	await waitForLayoutReady(page);
	await page.locator('#file-input').setInputFiles({
		name: `${name}.csv`,
		mimeType: 'text/csv',
		buffer: Buffer.from(options?.rows ? generateLargeCsv(options.rows) : SAMPLE_CSV)
	});
	if (options?.description) {
		await page.locator('#file-description').fill(options.description);
	}
	const uploadBtn = page.getByRole('button', { name: 'Upload', exact: true });
	await expect(uploadBtn).toBeEnabled({ timeout: 10_000 });
	await uploadBtn.click();
	await expect(page).toHaveURL(/\/datasources/, { timeout: 30_000 });
	await waitForDatasourceList(page, 15_000);
	await expect(page.locator(`[data-ds-row="${name}"]`)).toBeVisible({ timeout: 15_000 });
}

export async function createAnalysisViaUI(
	page: Page,
	name: string,
	datasourceName: string
): Promise<string> {
	await gotoNewAnalysis(page);
	await page.locator('#name').fill(name);
	await page.getByRole('button', { name: /Next/i }).click();
	await expect(page.getByRole('heading', { name: /Select Data Sources/i })).toBeVisible();
	await page.getByPlaceholder('Search datasources...').click();
	await page.locator(`[data-picker-option="${datasourceName}"]`).click();
	await page.getByRole('heading', { name: /Select Data Sources/i }).click();
	await page.getByRole('button', { name: /Next/i }).click();
	await expect(page.getByRole('heading', { name: /Choose Template/i })).toBeVisible();
	await page.getByRole('button', { name: /Next/i }).click();
	await expect(page.getByRole('heading', { name: /Configure Outputs/i })).toBeVisible();
	await page.getByRole('button', { name: /Next/i }).click();
	await expect(page.getByRole('heading', { name: /Review/i })).toBeVisible();
	await page.getByRole('button', { name: /Create Analysis/i }).click();
	await expect(page).toHaveURL(
		(url) => url.pathname.startsWith('/analysis/') && url.pathname !== '/analysis/new',
		{ timeout: 30_000 }
	);
	const match = page.url().match(/\/analysis\/([^/?#]+)/);
	if (!match || match[1] === 'new') {
		throw new Error(`Could not extract analysis id from URL: ${page.url()}`);
	}
	return match[1];
}

export async function waitForBuildTerminal(preview: Locator, timeout = 120_000): Promise<void> {
	await expect(preview.getByText(/^(Complete|Failed)$/)).toBeVisible({ timeout });
}

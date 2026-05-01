import fs from 'node:fs';
import path from 'node:path';
import type { Browser, Page } from '@playwright/test';
import { test as base } from '@playwright/test';
import { E2E_PASSWORD, type E2ERequest, workerAuthFile } from './utils/api.js';

export { expect } from '@playwright/test';

const port = parseInt(process.env.FRONTEND_PORT || '3000', 10);
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${port}`;
const authRequired = process.env.AUTH_REQUIRED !== 'false';
const runStamp = process.env.E2E_RUN_STAMP || `${Date.now().toString(36)}-${process.pid}`;
const authDir = path.resolve('tests/.auth');

interface WorkerAuth {
	authFile: string;
	workerIndex: number;
}

async function expectSignedIn(page: Page): Promise<void> {
	await page.getByLabel('Main navigation').waitFor({ state: 'visible', timeout: 15_000 });
}

async function createAuthFile(browser: Browser, workerAuth: WorkerAuth): Promise<void> {
	fs.mkdirSync(authDir, { recursive: true });
	const context = await browser.newContext({ baseURL });
	const page = await context.newPage();
	try {
		if (authRequired) {
			const email = `e2e-ui-${runStamp}-w${workerAuth.workerIndex}@example.com`;
			await page.goto('/register');
			await page.locator('#name').fill(`E2E UI Worker ${workerAuth.workerIndex}`);
			await page.locator('#email').fill(email);
			await page.locator('#password').fill(E2E_PASSWORD);
			await page.locator('#confirm').fill(E2E_PASSWORD);
			await page.getByRole('button', { name: 'Create account', exact: true }).click();
			const continueLink = page.getByRole('link', { name: /Continue/i });
			await Promise.race([
				continueLink.waitFor({ state: 'visible', timeout: 15_000 }),
				page.getByLabel('Main navigation').waitFor({ state: 'visible', timeout: 15_000 }),
				page.getByText(/Account created\./i).waitFor({ state: 'visible', timeout: 15_000 })
			]).catch(() => undefined);
			if (await continueLink.isVisible().catch(() => false)) {
				await continueLink.click();
			} else {
				await page.goto('/', { waitUntil: 'domcontentloaded' });
			}
			await expectSignedIn(page);
		}
		await context.storageState({ path: workerAuth.authFile });
	} finally {
		await context.close();
	}
}

async function ensureAuthFileReady(browser: Browser, workerAuth: WorkerAuth): Promise<void> {
	if (fs.existsSync(workerAuth.authFile)) return;
	await createAuthFile(browser, workerAuth);
}

export const test = base.extend<{ page: Page; request: E2ERequest }, { workerAuth: WorkerAuth }>({
	workerAuth: [
		async ({ browser }, use, workerInfo) => {
			const authFile = workerAuthFile(workerInfo.workerIndex);
			const workerAuth = { authFile, workerIndex: workerInfo.workerIndex };
			await ensureAuthFileReady(browser, workerAuth);
			await use(workerAuth);
			try {
				fs.unlinkSync(authFile);
			} catch {
				// already removed
			}
		},
		{ scope: 'worker' }
	],

	page: async ({ browser, workerAuth }, use) => {
		await ensureAuthFileReady(browser, workerAuth);
		const context = await browser.newContext({
			baseURL,
			storageState: workerAuth.authFile
		});
		const page = await context.newPage();
		await use(page);
		await context.close();
	},

	request: async ({ browser, workerAuth }, use) => {
		await ensureAuthFileReady(browser, workerAuth);
		await use({
			browser,
			authFile: workerAuth.authFile,
			workerIndex: workerAuth.workerIndex,
			baseURL
		} as unknown as import('@playwright/test').APIRequestContext);
	}
});

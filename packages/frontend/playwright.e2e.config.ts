/// <reference types="node" />
import { defineConfig, devices } from '@playwright/test';

const port = parseInt(process.env.FRONTEND_PORT || '3000', 10);
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${port}`;
const ciArgs = process.env.CI ? ['--disable-dev-shm-usage', '--disable-gpu'] : [];
const workers = parseInt(process.env.PLAYWRIGHT_WORKERS || '3', 10);

export default defineConfig({
	testDir: './tests-e2e',
	timeout: 30_000,
	expect: { timeout: 10_000 },
	fullyParallel: false,
	workers,
	retries: 1,
	outputDir: './tests-e2e/test-results',
	reporter: [['html', { open: 'never', outputFolder: 'tests-e2e/playwright-report' }], ['line']],
	use: {
		baseURL,
		trace: 'on-first-retry',
		screenshot: 'only-on-failure'
	},
	projects: [
		{
			name: 'chromium',
			use: {
				...devices['Desktop Chrome'],
				viewport: { width: 1920, height: 1080 },
				launchOptions: ciArgs.length === 0 ? undefined : { args: ciArgs }
			}
		}
	]
});

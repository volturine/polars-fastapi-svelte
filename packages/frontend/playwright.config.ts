/// <reference types="node" />
import { defineConfig, devices } from '@playwright/test';

const port = parseInt(process.env.FRONTEND_PORT || '3000', 10);
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${port}`;
const webServerCommand = process.env.PLAYWRIGHT_WEB_SERVER_COMMAND || 'bun run dev';
const webServerReuseExisting = process.env.PLAYWRIGHT_REUSE_WEB_SERVER !== 'false';
const disableWebServer = process.env.PLAYWRIGHT_DISABLE_WEB_SERVER === 'true';
const ciArgs = process.env.CI ? ['--disable-dev-shm-usage', '--disable-gpu'] : [];
const workers = process.env.PLAYWRIGHT_WORKERS
	? parseInt(process.env.PLAYWRIGHT_WORKERS, 10)
	: process.env.CI
		? 1
		: 3;

export default defineConfig({
	testDir: './tests',
	globalSetup: './tests/global-setup.ts',
	globalTeardown: './tests/global-teardown.ts',
	timeout: 30_000,
	expect: { timeout: 10_000 },
	fullyParallel: true,
	workers,
	retries: 0,
	outputDir: './tests/test-results',
	reporter: [['html', { open: 'never', outputFolder: 'tests/playwright-report' }], ['line']],
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
	],
	...(disableWebServer
		? {}
		: {
				webServer: {
					command: webServerCommand,
					url: baseURL,
					reuseExistingServer: webServerReuseExisting,
					timeout: 60_000
				}
			})
});

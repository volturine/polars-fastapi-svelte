/// <reference types="node" />
import { defineConfig, devices } from '@playwright/test';

const port = parseInt(process.env.FRONTEND_PORT || '3000', 10);
const baseURL = process.env.PLAYWRIGHT_BASE_URL || `http://localhost:${port}`;
const ciArgs = process.env.CI ? ['--disable-dev-shm-usage', '--disable-gpu'] : [];
const workers = parseInt(process.env.PLAYWRIGHT_WORKERS || '3', 10);
const shardCurrent = process.env.PLAYWRIGHT_SHARD_CURRENT;
const shardTotal = process.env.PLAYWRIGHT_SHARD_TOTAL;
const shardSuffix = shardCurrent && shardTotal ? `-shard-${shardCurrent}-of-${shardTotal}` : '';

export default defineConfig({
	testDir: './tests',
	timeout: 30_000,
	expect: { timeout: 10_000 },
	fullyParallel: false,
	workers,
	retries: 1,
	outputDir: `./tests/test-results${shardSuffix}`,
	reporter: [
		['html', { open: 'never', outputFolder: `tests/playwright-report${shardSuffix}` }],
		['line']
	],
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

import { defineConfig } from 'vitest/config';
import { svelte } from '@sveltejs/vite-plugin-svelte';

export default defineConfig({
	plugins: [
		svelte({
			preprocess: []
		})
	],
	resolve: {
		conditions: ['browser']
	},
	test: {
		include: ['src/**/*.{test,spec}.{js,ts}', 'tests/**/*.test.{js,ts}'],
		exclude: ['tests/e2e/**'],
		globals: true,
		environment: 'jsdom',
		setupFiles: ['./src/test-setup.ts'],
		ssr: false,
		pool: 'forks',
		deps: {
			optimizer: {
				web: {
					include: ['svelte']
				}
			}
		},
		coverage: {
			provider: 'v8',
			reporter: ['text', 'json', 'html', 'lcov'],
			include: ['src/**/*.{js,ts,svelte}'],
			exclude: [
				'src/**/*.{test,spec}.{js,ts}',
				'src/test-setup.ts',
				'src/test-utils.ts',
				'**/*.d.ts',
				'**/node_modules/**'
			],
			all: true,
			lines: 80,
			functions: 80,
			branches: 80,
			statements: 80
		}
	}
});

import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
	preprocess: [vitePreprocess()],

	onwarn: (warning, handler) => {
		// css_unused_selector: Panda CSS generates selectors consumed at runtime — cannot be resolved statically
		if (warning.code === 'css_unused_selector') return;
		// state_referenced_locally / non_reactive_update: tracked as tech debt in AGENTS.md
		if (warning.code === 'state_referenced_locally') return;
		if (warning.code === 'non_reactive_update') return;
		handler(warning);
	},

	kit: {
		adapter: adapter({
			pages: 'build',
			assets: 'build',
			fallback: '200.html',
			precompress: false,
			strict: true
		}),
		alias: {
			'styled-system': './styled-system/*'
		},
		paths: {
			base: ''
		}
	},

	// Enable runes for all project files; leave dependencies as-is
	vitePlugin: {
		dynamicCompileOptions({ filename }) {
			if (filename.includes('node_modules')) return;
			return { runes: true };
		}
	}
};

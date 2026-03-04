<script lang="ts">
	import { css } from '$lib/styles/panda';

	interface Props {
		config?: {
			fraction?: number;
			seed?: number;
		};
	}

	let { config = $bindable({ fraction: 0.5, seed: 42 }) }: Props = $props();
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Sample configuration"
>
	<div class={css({ marginBottom: '5' })}>
		<label for="sample-input-fraction">Fraction</label>
		<input
			id="sample-input-fraction"
			data-testid="sample-fraction-input"
			type="number"
			bind:value={config.fraction}
			min="0"
			max="1"
			step="0.01"
			placeholder="e.g., 0.5"
		/>
	</div>

	<div class={css({ marginBottom: '0' })}>
		<label for="sample-input-seed">Random seed (optional)</label>
		<input
			id="sample-input-seed"
			data-testid="sample-seed-input"
			type="number"
			bind:value={config.seed}
			min="0"
			placeholder="e.g., 42"
		/>
	</div>
</div>

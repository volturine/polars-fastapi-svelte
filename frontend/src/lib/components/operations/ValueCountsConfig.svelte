<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import ColumnDropdown from '$lib/components/common/ColumnDropdown.svelte';
	import { css } from '$lib/styles/panda';

	interface Props {
		schema: Schema;
		config?: { column?: string; normalize?: boolean; sort?: boolean };
	}

	let { schema, config = $bindable({}) }: Props = $props();

	// Helper to get config value with default
	const get = <T,>(key: keyof typeof config, defaultValue: T): T =>
		(config[key] as T) ?? defaultValue;
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
>
	<div class={css({ marginBottom: '5' })}>
		<div
			class={css({
				display: 'block',
				fontSize: 'xs',
				fontWeight: '600',
				color: 'fg.muted',
				marginBottom: '1.5',
				textTransform: 'uppercase',
				letterSpacing: 'wider'
			})}
		>
			Column to count
		</div>
		<ColumnDropdown
			{schema}
			value={config.column ?? ''}
			onChange={(val) => (config.column = val)}
			placeholder="Select column..."
		/>
	</div>

	<div class={css({ marginBottom: '5' })}>
		<label class={css({ display: 'flex', cursor: 'pointer', alignItems: 'center', gap: '3' })}>
			<input id="normalize" type="checkbox" bind:checked={config.normalize} />
			<span>Normalize (show proportions instead of counts)</span>
		</label>
	</div>

	<div class={css({ marginBottom: '0' })}>
		<label class={css({ display: 'flex', cursor: 'pointer', alignItems: 'center', gap: '3' })}>
			<input
				id="sort"
				type="checkbox"
				checked={get('sort', true)}
				onchange={(e) => (config.sort = e.currentTarget.checked)}
			/>
			<span>Sort by count</span>
		</label>
	</div>
</div>

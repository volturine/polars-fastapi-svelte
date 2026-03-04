<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import { css } from '$lib/styles/panda';

	interface SelectConfigData {
		columns: string[];
	}

	interface Props {
		schema: Schema;
		config?: SelectConfigData;
	}

	let { schema, config = $bindable({ columns: [] }) }: Props = $props();

	const safeColumns = $derived(Array.isArray(config.columns) ? config.columns : []);
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Select columns configuration"
>
	<div
		class={css({
			marginBottom: '0',
			padding: '0 0 1.25rem 0',
			backgroundColor: 'transparent',
			borderRadius: '0',
			border: 'none'
		})}
	>
		<div
			class={css({
				display: 'block',
				fontSize: '0.6875rem',
				fontWeight: '600',
				color: 'fg.muted',
				marginBottom: '1.5',
				textTransform: 'uppercase',
				letterSpacing: '0.05em'
			})}
		>
			Columns to keep
		</div>
		<MultiSelectColumnDropdown
			{schema}
			value={safeColumns}
			onChange={(val) => (config.columns = val)}
			placeholder="Select columns to keep..."
		/>
	</div>

	{#if safeColumns.length > 0}
		<div
			class={css({
				padding: '0.625rem 0.75rem',
				border: 'none',
				borderLeft: '2px solid',
				borderRadius: '0',
				marginTop: '0.75rem',
				marginBottom: '0',
				fontSize: '0.75rem',
				lineHeight: '1.5',
				backgroundColor: 'transparent',
				borderLeftColor: 'accent.secondary',
				color: 'fg.tertiary'
			})}
			aria-live="polite"
		>
			<strong>Selected {safeColumns.length} column{safeColumns.length !== 1 ? 's' : ''}</strong>
		</div>
	{/if}
</div>

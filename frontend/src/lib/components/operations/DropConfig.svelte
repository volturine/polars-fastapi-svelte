<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import { AlertTriangle } from 'lucide-svelte';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import { css } from '$lib/styles/panda';

	interface DropConfigData {
		columns: string[];
	}

	interface Props {
		schema: Schema;
		config?: DropConfigData;
	}

	let { schema, config = $bindable({ columns: [] }) }: Props = $props();

	const safeColumns = $derived(Array.isArray(config.columns) ? config.columns : []);
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Drop columns configuration"
>
	<h3 class={css({ marginBottom: '2' })}>Drop Columns</h3>

	<p
		class={css({
			marginTop: '0',
			marginBottom: '3',
			color: 'fg.tertiary',
			fontSize: 'xs',
			lineHeight: '1.6'
		})}
	>
		Select the columns you want to drop (remove) from the dataset.
	</p>

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
			Columns to drop
		</div>
		<MultiSelectColumnDropdown
			{schema}
			value={safeColumns}
			onChange={(val) => (config.columns = val)}
			placeholder="Select columns to drop..."
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
				borderLeftColor: 'warning.border',
				color: 'fg.tertiary'
			})}
			aria-live="polite"
		>
			<strong class={css({ display: 'inline-flex', alignItems: 'center', gap: '2' })}>
				<AlertTriangle size={14} />
				Columns to Drop ({safeColumns.length}):
			</strong>
			<p>These columns will be removed from the dataset.</p>
		</div>
	{:else}
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
				borderLeftColor: 'warning.border',
				color: 'fg.tertiary'
			})}
			role="alert"
		>
			<strong>Warning:</strong> No columns selected. This operation will have no effect.
		</div>
	{/if}
</div>

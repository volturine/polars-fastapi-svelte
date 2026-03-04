<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import { css } from '$lib/styles/panda';

	interface ExplodeConfigData {
		columns: string[];
	}

	interface Props {
		schema: Schema;
		config?: ExplodeConfigData;
	}

	let { schema, config = $bindable({ columns: [] }) }: Props = $props();

	const hasListColumns = $derived(
		schema.columns.some(
			(col) =>
				col.dtype.toLowerCase().includes('list') ||
				col.dtype.toLowerCase().includes('array') ||
				col.dtype.toLowerCase().startsWith('list[')
		)
	);

	function isListColumn(col: { name: string; dtype: string }): boolean {
		const d = col.dtype.toLowerCase();
		return d.includes('list') || d.includes('array');
	}
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
>
	<p
		class={css({
			marginTop: '0',
			marginBottom: '3',
			color: 'fg.tertiary',
			fontSize: 'xs',
			lineHeight: '1.6'
		})}
	>
		Transform list/array columns into multiple rows. Each list element becomes a separate row.
	</p>

	<div class={css({ marginBottom: '5' })}>
		<h4
			class={css({
				marginTop: '0',
				marginBottom: '3',
				fontSize: '0.6875rem',
				fontWeight: '600',
				color: 'fg.muted',
				textTransform: 'uppercase',
				letterSpacing: '0.08em'
			})}
		>
			Columns to Explode
		</h4>

		{#if !hasListColumns}
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
			>
				No list/array columns detected. This operation requires columns with list or array types.
			</div>
		{:else}
			<MultiSelectColumnDropdown
				{schema}
				value={config.columns ?? []}
				onChange={(val) => (config.columns = val)}
				filter={isListColumn}
				showSelectAll={false}
				placeholder="Select list columns..."
			/>

			{#if (config.columns ?? []).length > 0}
				<span class={css({ marginTop: '2', display: 'block', fontSize: 'xs', color: 'fg.muted' })}>
					{(config.columns ?? []).length} column{(config.columns ?? []).length !== 1 ? 's' : ''} selected:
					{(config.columns ?? []).join(', ')}
				</span>
			{/if}
		{/if}
	</div>

	<div class={css({ fontSize: 'xs', color: 'fg.muted', lineHeight: 'relaxed' })}>
		Each list element becomes a new row. Other column values are duplicated. Null values are
		preserved; empty lists create no rows.
	</div>
</div>

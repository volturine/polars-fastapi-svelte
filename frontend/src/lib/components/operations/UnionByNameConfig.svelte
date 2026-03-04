<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import { analysisStore } from '$lib/stores/analysis.svelte';
	import { datasourceStore } from '$lib/stores/datasource.svelte';
	import { schemaStore } from '$lib/stores/schema.svelte';
	import DatasourcePicker from '$lib/components/common/DatasourcePicker.svelte';
	import { css, cx } from '$lib/styles/panda';

	interface UnionByNameConfigData {
		sources: string[];
		allow_missing: boolean;
	}

	const defaultConfig: UnionByNameConfigData = {
		sources: [],
		allow_missing: true
	};

	interface Props {
		schema: Schema;
		config?: UnionByNameConfigData;
	}

	let { schema, config = $bindable(defaultConfig) }: Props = $props();

	let selectedSources = $state<string[]>(config.sources ?? []);
	let loadedSources = $state<string[]>([]);

	const currentTabDatasource = $derived(analysisStore.activeTab?.datasource.id ?? null);
	const currentDatasource = $derived(
		datasourceStore.datasources.find((ds) => ds.id === currentTabDatasource)
	);
	const datasourceOptions = $derived(datasourceStore.datasources);

	// Sync selectedSources with config.sources
	// Subscription: $derived can't sync selected sources to config.
	$effect(() => {
		config.sources = selectedSources;
	});

	// Load schemas for selected sources
	// Network: $derived can't fetch source schemas.
	$effect(() => {
		const selected = new Set(selectedSources);
		for (const sourceId of selectedSources) {
			if (!loadedSources.includes(sourceId)) {
				loadSourceSchema(sourceId);
			}
		}
		const removed = loadedSources.filter((id) => !selected.has(id));
		if (removed.length === 0) return;
		for (const sourceId of removed) {
			schemaStore.removeJoinDatasource(sourceId);
		}
		loadedSources = loadedSources.filter((id) => selected.has(id));
	});

	async function loadSourceSchema(datasourceId: string) {
		const schemaInfo = await datasourceStore.getSchema(datasourceId);
		const unionSchema: Schema = {
			columns: schemaInfo.columns.map((c) => ({
				name: c.name,
				dtype: c.dtype,
				nullable: c.nullable
			})),
			row_count: schemaInfo.row_count
		};
		schemaStore.setJoinDatasource(datasourceId, unionSchema);
		if (!loadedSources.includes(datasourceId)) {
			loadedSources = [...loadedSources, datasourceId];
		}
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
		Combine rows from multiple datasources using matching column names.
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
			Base Datasource
		</h4>
		<div class={css({ display: 'flex', flexDirection: 'column', gap: '1' })}>
			{#if currentDatasource}
				<strong>{currentDatasource.name}</strong>
				<span class={css({ fontSize: 'xs', color: 'fg.tertiary' })}
					>{schema.columns.length} columns</span
				>
			{:else}
				<span class={css({ color: 'fg.muted' })}>No active datasource selected</span>
			{/if}
		</div>
	</div>

	<div
		class={cx(
			css({
				marginBottom: '0',
				padding: '0 0 1.25rem 0',
				backgroundColor: 'transparent',
				borderRadius: '0',
				border: 'none'
			}),
			css({ paddingTop: '1.25rem', borderTop: '1px solid var(--color-border-tertiary)' })
		)}
	>
		<div
			class={css({
				display: 'flex',
				justifyContent: 'space-between',
				alignItems: 'center',
				marginBottom: '5'
			})}
		>
			<h4
				class={cx(
					css({
						marginTop: '0',
						marginBottom: '3',
						fontSize: '0.6875rem',
						fontWeight: '600',
						color: 'fg.muted',
						textTransform: 'uppercase',
						letterSpacing: '0.08em'
					}),
					css({ marginBottom: '0' })
				)}
			>
				Union Sources
			</h4>
		</div>

		{#if datasourceOptions.length === 0}
			<p class={css({ marginY: '2', fontStyle: 'italic', color: 'fg.muted' })}>
				Add another datasource to enable unions.
			</p>
		{:else}
			<DatasourcePicker
				datasources={datasourceOptions}
				bind:selected={selectedSources}
				mode="multi"
				showChips={true}
				showBulkActions={true}
				onSelect={(id) => loadSourceSchema(id)}
			/>
		{/if}

		{#if selectedSources.length === 0}
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
				Select at least one datasource to union.
			</div>
		{/if}
	</div>

	<div
		class={cx(
			css({
				marginBottom: '0',
				padding: '0 0 1.25rem 0',
				backgroundColor: 'transparent',
				borderRadius: '0',
				border: 'none'
			}),
			css({ paddingTop: '1.25rem', borderTop: '1px solid var(--color-border-tertiary)' })
		)}
	>
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
			Column Matching
		</h4>
		<label class={css({ display: 'flex', alignItems: 'center', gap: '3' })}>
			<input id="allow-missing" type="checkbox" bind:checked={config.allow_missing} />
			<span>Allow missing columns (fill with nulls)</span>
		</label>
		<span
			class={css({
				marginTop: '2',
				display: 'block',
				fontSize: 'xs',
				color: 'fg.muted',
				lineHeight: 'relaxed'
			})}
		>
			When enabled, missing columns are created with null values to keep all rows.
		</span>
	</div>
</div>

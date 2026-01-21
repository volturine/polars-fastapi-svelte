<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import { analysisStore } from '$lib/stores/analysis.svelte';
	import { datasourceStore } from '$lib/stores/datasource.svelte';
	import { schemaStore } from '$lib/stores/schema.svelte';

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
	let search = $state('');
	let showPicker = $state(false);

	const currentTabDatasource = $derived(analysisStore.activeTab?.datasource_id ?? null);
	const currentDatasource = $derived(
		datasourceStore.datasources.find((ds) => ds.id === currentTabDatasource)
	);
	const datasourceOptions = $derived.by(() => datasourceStore.datasources);
	const filteredOptions = $derived.by(() => {
		const query = search.trim().toLowerCase();
		if (!query) return datasourceOptions;
		return datasourceOptions.filter((ds) => {
			const name = ds.name.toLowerCase();
			const type = ds.source_type.toLowerCase();
			return name.includes(query) || type.includes(query);
		});
	});

	$effect(() => {
		config.sources = selectedSources;
	});

	$effect(() => {
		if (config.allow_missing === undefined) {
			config.allow_missing = true;
		}
	});

	$effect(() => {
		const selected = new Set(selectedSources);
		for (const sourceId of selectedSources) {
			if (!loadedSources.includes(sourceId)) {
				loadUnionSchema(sourceId);
			}
		}
		const removed = loadedSources.filter((id) => !selected.has(id));
		if (removed.length === 0) return;
		for (const sourceId of removed) {
			schemaStore.removeJoinDatasource(sourceId);
		}
		loadedSources = loadedSources.filter((id) => selected.has(id));
	});

	async function loadUnionSchema(datasourceId: string) {
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

	function toggleSource(sourceId: string) {
		const exists = selectedSources.includes(sourceId);
		selectedSources = exists
			? selectedSources.filter((id) => id !== sourceId)
			: [...selectedSources, sourceId];
	}

	function handlePickerFocus() {
		showPicker = true;
	}

	function handlePickerBlur() {
		setTimeout(() => {
			showPicker = false;
		}, 100);
	}

	function selectAll() {
		selectedSources = filteredOptions.map((ds) => ds.id);
	}

	function deselectAll() {
		selectedSources = [];
	}
</script>

<div class="union-config">
	<h3>Union By Name</h3>
	<p class="description">
		Combine rows from multiple datasources using matching column names.
	</p>

	<div class="section">
		<h4>Base Datasource</h4>
		<div class="summary">
			{#if currentDatasource}
				<strong>{currentDatasource.name}</strong>
				<span class="meta">{schema.columns.length} columns</span>
			{:else}
				<span class="muted">No active datasource selected</span>
			{/if}
		</div>
	</div>

	<div class="section">
		<div class="section-header">
			<h4>Union Sources</h4>
			<div class="column-actions">
				<button type="button" class="btn-link" onclick={selectAll}>Select All</button>
				<button type="button" class="btn-link" onclick={deselectAll}>Deselect All</button>
			</div>
		</div>

		<div class="search-picker" role="combobox" aria-expanded={showPicker} aria-controls="union-source-options">
			<span class="sr-only">Search datasources</span>
			<input
				type="text"
				placeholder="Search datasources..."
				bind:value={search}
				onfocus={handlePickerFocus}
				onblur={handlePickerBlur}
			/>
			{#if showPicker}
				<div
					class="picker-list"
					id="union-source-options"
					role="listbox"
					aria-label="Union datasource options"
				>
					{#if datasourceOptions.length === 0}
						<div class="picker-empty">Add another datasource to enable unions.</div>
					{:else if filteredOptions.length === 0}
						<div class="picker-empty">No matching datasources.</div>
					{:else}
						{#each filteredOptions as ds (ds.id)}
							<button
								type="button"
								class="picker-item"
								data-selected={selectedSources.includes(ds.id)}
								onmousedown={() => toggleSource(ds.id)}
							>
								<span class="source-name">{ds.name}</span>
								<span class="meta">{ds.source_type}</span>
							</button>
						{/each}
					{/if}
				</div>
			{/if}
		</div>

		{#if datasourceOptions.length === 0}
			<p class="empty-message">Add another datasource to enable unions.</p>
		{:else if selectedSources.length === 0}
			<p class="empty-message">No sources selected yet.</p>
		{:else}
			<div class="source-list">
				{#each datasourceOptions.filter((ds) => selectedSources.includes(ds.id)) as ds (ds.id)}
					<div class="source-chip">
						<span>{ds.name}</span>
						<button type="button" onclick={() => toggleSource(ds.id)} aria-label={`Remove ${ds.name}`}>
							×
						</button>
					</div>
				{/each}
			</div>
		{/if}

		{#if selectedSources.length === 0}
			<div class="warning">Select at least one datasource to union.</div>
		{/if}
	</div>

	<div class="section">
		<h4>Column Matching</h4>
		<label class="toggle">
			<input type="checkbox" bind:checked={config.allow_missing} />
			<span>Allow missing columns (fill with nulls)</span>
		</label>
		<p class="help-text">
			When enabled, missing columns are created with null values to keep all rows.
			Disable to require identical schemas.
		</p>
	</div>
</div>

<style>
	.union-config {
		padding: 1rem;
		border: 1px solid var(--panel-border);
		border-radius: var(--radius-md);
		background-color: var(--panel-bg);
	}

	h3 {
		margin-top: 0;
		margin-bottom: 0.5rem;
		color: var(--panel-header-fg);
	}

	h4 {
		margin-top: 0;
		margin-bottom: 0.75rem;
		font-size: 1rem;
		color: var(--fg-secondary);
	}

	.description {
		margin: 0 0 1rem;
		color: var(--fg-muted);
		font-size: 0.875rem;
	}

	.section {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background-color: var(--form-section-bg);
		border-radius: var(--radius-md);
		border: 1px solid var(--form-section-border);
	}

	.section-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 1rem;
	}

	.summary {
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		font-size: 0.875rem;
	}

	.meta {
		color: var(--fg-tertiary);
		font-size: 0.75rem;
	}

	.muted {
		color: var(--fg-muted);
	}

	.column-actions {
		display: flex;
		gap: 0.5rem;
	}

	.btn-link {
		background: none;
		border: none;
		color: var(--primary-fg);
		cursor: pointer;
		font-size: 0.75rem;
		padding: 0.25rem;
		text-decoration: underline;
	}

	.source-list {
		display: flex;
		flex-wrap: wrap;
		gap: 0.5rem;
		padding: 0.5rem;
		background-color: var(--panel-bg);
		border-radius: var(--radius-sm);
		border: 1px solid var(--panel-border);
	}

	.source-chip {
		display: inline-flex;
		align-items: center;
		gap: 0.35rem;
		padding: 0.35rem 0.5rem;
		border-radius: 999px;
		background-color: var(--bg-hover);
		font-size: 0.75rem;
	}

	.source-chip button {
		border: none;
		background: none;
		cursor: pointer;
		font-size: 0.875rem;
		line-height: 1;
		color: var(--fg-muted);
		padding: 0;
	}

	.source-chip button:hover {
		color: var(--fg-primary);
	}

	.source-name {
		flex: 1;
	}

	.toggle {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		color: var(--fg-primary);
	}

	.help-text {
		font-size: 0.875rem;
		color: var(--fg-tertiary);
		line-height: 1.5;
		margin: 0.5rem 0 0;
		padding: 0.75rem;
		background-color: var(--form-help-bg);
		border-left: 3px solid var(--form-help-accent);
		border-radius: var(--radius-sm);
		border: 1px solid var(--form-help-border);
	}

	.warning {
		padding: 0.5rem;
		background-color: var(--warning-bg);
		color: var(--warning-fg);
		border-radius: var(--radius-sm);
		font-size: 0.875rem;
		margin-top: 0.5rem;
	}

	.empty-message {
		color: var(--fg-muted);
		font-size: 0.875rem;
		font-style: italic;
		margin: 0.5rem 0;
	}

	.search-picker {
		position: relative;
		margin-bottom: 0.75rem;
	}

	.search-picker input {
		width: 100%;
		padding: 0.5rem 0.75rem;
		border: 1px solid var(--form-control-border);
		border-radius: var(--radius-sm);
		background-color: var(--form-control-bg);
		color: var(--fg-primary);
		font-size: 0.875rem;
	}

	.search-picker input::placeholder {
		color: var(--fg-muted);
	}

	.picker-list {
		position: absolute;
		z-index: 10;
		top: calc(100% + 0.25rem);
		left: 0;
		right: 0;
		display: flex;
		flex-direction: column;
		gap: 0.25rem;
		max-height: 220px;
		overflow-y: auto;
		padding: 0.5rem;
		background-color: var(--panel-bg);
		border-radius: var(--radius-sm);
		border: 1px solid var(--panel-border);
		box-shadow: 0 12px 30px rgba(0, 0, 0, 0.08);
	}

	.picker-item {
		display: flex;
		align-items: center;
		gap: 0.5rem;
		font-size: 0.875rem;
		cursor: pointer;
		padding: 0.4rem 0.5rem;
		border: 1px solid transparent;
		border-radius: var(--radius-sm);
		background-color: transparent;
		color: var(--fg-primary);
		text-align: left;
	}

	.picker-item[data-selected='true'] {
		border-color: var(--accent-primary);
		background-color: var(--bg-hover);
	}

	.picker-item:hover {
		background-color: var(--bg-hover);
	}

	.picker-empty {
		padding: 0.5rem;
		color: var(--fg-muted);
		font-size: 0.875rem;
		font-style: italic;
	}

	.sr-only {
		position: absolute;
		width: 1px;
		height: 1px;
		padding: 0;
		margin: -1px;
		overflow: hidden;
		clip: rect(0, 0, 0, 0);
		white-space: nowrap;
		border: 0;
	}
</style>

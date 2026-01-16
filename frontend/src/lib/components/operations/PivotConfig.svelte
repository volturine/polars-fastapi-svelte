<script lang="ts">
	import type { Schema } from '$lib/types/schema';

	interface PivotConfigData {
		index: string[];
		columns: string;
		values: string;
		aggregate_function: string;
	}

	interface Props {
		schema: Schema;
		config: PivotConfigData;
		onSave: (config: PivotConfigData) => void;
	}

	let { schema, config, onSave }: Props = $props();

	let localConfig = $state<PivotConfigData>({
		index: config?.index ? [...config.index] : [],
		columns: config?.columns || '',
		values: config?.values || '',
		aggregate_function: config?.aggregate_function || 'first'
	});

	const aggregateFunctions = [
		'first',
		'last',
		'sum',
		'mean',
		'median',
		'min',
		'max',
		'count'
	];

	function toggleIndexColumn(columnName: string) {
		const index = localConfig.index.indexOf(columnName);
		if (index > -1) {
			localConfig.index.splice(index, 1);
		} else {
			localConfig.index.push(columnName);
		}
	}

	function handleSave() {
		onSave(localConfig);
	}

	function handleCancel() {
		localConfig = {
			index: config?.index ? [...config.index] : [],
			columns: config?.columns || '',
			values: config?.values || '',
			aggregate_function: config?.aggregate_function || 'first'
		};
	}
</script>

<div class="pivot-config">
	<h3>Pivot Configuration</h3>

	<div class="section">
		<h4>Index Columns</h4>
		<div class="column-list">
			{#each schema.columns as column}
				<label class="column-item">
					<input
						type="checkbox"
						checked={localConfig.index.includes(column.name)}
						onchange={() => toggleIndexColumn(column.name)}
					/>
					<span>{column.name} ({column.dtype})</span>
				</label>
			{/each}
		</div>
		{#if localConfig.index.length > 0}
			<div class="selected-info">Selected: {localConfig.index.join(', ')}</div>
		{/if}
	</div>

	<div class="section">
		<h4>Pivot Column</h4>
		<select bind:value={localConfig.columns}>
			<option value="">Select column...</option>
			{#each schema.columns as column}
				<option value={column.name}>{column.name} ({column.dtype})</option>
			{/each}
		</select>
	</div>

	<div class="section">
		<h4>Values Column</h4>
		<select bind:value={localConfig.values}>
			<option value="">Select column...</option>
			{#each schema.columns as column}
				<option value={column.name}>{column.name} ({column.dtype})</option>
			{/each}
		</select>
	</div>

	<div class="section">
		<h4>Aggregation Function</h4>
		<select bind:value={localConfig.aggregate_function}>
			{#each aggregateFunctions as func}
				<option value={func}>{func}</option>
			{/each}
		</select>
	</div>

	<div class="actions">
		<button
			type="button"
			onclick={handleSave}
			class="save-btn"
			disabled={!localConfig.columns || !localConfig.values || localConfig.index.length === 0}
		>
			Save
		</button>
		<button type="button" onclick={handleCancel} class="cancel-btn">Cancel</button>
	</div>
</div>

<style>
	.pivot-config {
		padding: 1rem;
		border: 1px solid #ddd;
		border-radius: 4px;
	}

	h3 {
		margin-top: 0;
		margin-bottom: 1rem;
	}

	h4 {
		margin-top: 0;
		margin-bottom: 0.5rem;
		font-size: 1rem;
	}

	.section {
		margin-bottom: 1.5rem;
		padding: 1rem;
		background-color: #f8f9fa;
		border-radius: 4px;
	}

	.column-list {
		max-height: 200px;
		overflow-y: auto;
		border: 1px solid #ddd;
		border-radius: 4px;
		padding: 0.5rem;
		background-color: white;
	}

	.column-item {
		display: flex;
		align-items: center;
		padding: 0.5rem;
		cursor: pointer;
		border-radius: 4px;
	}

	.column-item:hover {
		background-color: #f8f9fa;
	}

	.column-item input[type='checkbox'] {
		margin-right: 0.5rem;
		cursor: pointer;
	}

	.selected-info {
		margin-top: 0.5rem;
		padding: 0.5rem;
		background-color: #e7f3ff;
		border-radius: 4px;
		font-size: 0.875rem;
	}

	select {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	.actions {
		display: flex;
		gap: 0.5rem;
	}

	.save-btn {
		padding: 0.5rem 1.5rem;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	.save-btn:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}

	.cancel-btn {
		padding: 0.5rem 1.5rem;
		background-color: #6c757d;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	button:hover:not(:disabled) {
		opacity: 0.9;
	}
</style>

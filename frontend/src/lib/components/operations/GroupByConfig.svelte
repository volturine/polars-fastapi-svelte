<script lang="ts">
	import type { Schema } from '$lib/types/schema';

	interface Aggregation {
		column: string;
		function: string;
		alias: string;
	}

	interface GroupByConfigData {
		groupBy: string[];
		aggregations: Aggregation[];
	}

	interface Props {
		schema: Schema;
		config: GroupByConfigData;
		onSave: (config: GroupByConfigData) => void;
	}

	let { schema, config, onSave }: Props = $props();

	let localConfig = $state<GroupByConfigData>({
		groupBy: config?.groupBy ? [...config.groupBy] : [],
		aggregations: config?.aggregations?.length > 0 ? [...config.aggregations] : []
	});

	let newAggregation = $state<Aggregation>({
		column: '',
		function: 'sum',
		alias: ''
	});

	const aggregationFunctions = [
		'sum',
		'mean',
		'count',
		'min',
		'max',
		'first',
		'last',
		'median',
		'std'
	];

	function toggleGroupByColumn(columnName: string) {
		const index = localConfig.groupBy.indexOf(columnName);
		if (index > -1) {
			localConfig.groupBy.splice(index, 1);
		} else {
			localConfig.groupBy.push(columnName);
		}
	}

	function addAggregation() {
		if (!newAggregation.column) return;

		const alias = newAggregation.alias || `${newAggregation.column}_${newAggregation.function}`;

		localConfig.aggregations.push({
			column: newAggregation.column,
			function: newAggregation.function,
			alias
		});

		newAggregation = {
			column: '',
			function: 'sum',
			alias: ''
		};
	}

	function removeAggregation(index: number) {
		localConfig.aggregations.splice(index, 1);
	}

	function handleSave() {
		onSave(localConfig);
	}

	function handleCancel() {
		localConfig = {
			groupBy: config?.groupBy ? [...config.groupBy] : [],
			aggregations: config?.aggregations?.length > 0 ? [...config.aggregations] : []
		};
	}
</script>

<div class="groupby-config">
	<h3>Group By Configuration</h3>

	<div class="section">
		<h4>Group By Columns</h4>
		<div class="column-list">
			{#each schema.columns as column}
				<label class="column-item">
					<input
						type="checkbox"
						checked={localConfig.groupBy.includes(column.name)}
						onchange={() => toggleGroupByColumn(column.name)}
					/>
					<span>{column.name} ({column.dtype})</span>
				</label>
			{/each}
		</div>
		{#if localConfig.groupBy.length > 0}
			<div class="selected-info">
				Selected: {localConfig.groupBy.join(', ')}
			</div>
		{/if}
	</div>

	<div class="section">
		<h4>Aggregations</h4>

		<div class="add-aggregation">
			<select bind:value={newAggregation.column}>
				<option value="">Select column...</option>
				{#each schema.columns as column}
					<option value={column.name}>{column.name} ({column.dtype})</option>
				{/each}
			</select>

			<select bind:value={newAggregation.function}>
				{#each aggregationFunctions as func}
					<option value={func}>{func}</option>
				{/each}
			</select>

			<input type="text" bind:value={newAggregation.alias} placeholder="Alias (optional)" />

			<button type="button" onclick={addAggregation} disabled={!newAggregation.column}>
				Add
			</button>
		</div>

		{#if localConfig.aggregations.length > 0}
			<div class="aggregations-list">
				{#each localConfig.aggregations as agg, i}
					<div class="aggregation-item">
						<span class="agg-details">
							{agg.function}({agg.column}) as {agg.alias}
						</span>
						<button type="button" onclick={() => removeAggregation(i)}>Remove</button>
					</div>
				{/each}
			</div>
		{/if}
	</div>

	<div class="actions">
		<button type="button" onclick={handleSave} class="save-btn">Save</button>
		<button type="button" onclick={handleCancel} class="cancel-btn">Cancel</button>
	</div>
</div>

<style>
	.groupby-config {
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
		margin-bottom: 0.75rem;
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

	.add-aggregation {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 1rem;
	}

	.add-aggregation select,
	.add-aggregation input {
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	.add-aggregation select:first-child {
		flex: 2;
	}

	.add-aggregation select:nth-child(2) {
		flex: 1;
	}

	.add-aggregation input {
		flex: 2;
	}

	.add-aggregation button {
		padding: 0.5rem 1rem;
		background-color: #28a745;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
	}

	.add-aggregation button:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}

	.aggregations-list {
		display: flex;
		flex-direction: column;
		gap: 0.5rem;
	}

	.aggregation-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background-color: white;
		border: 1px solid #ddd;
		border-radius: 4px;
	}

	.agg-details {
		font-family: monospace;
		font-size: 0.875rem;
	}

	.aggregation-item button {
		padding: 0.25rem 0.75rem;
		background-color: #dc3545;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.875rem;
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

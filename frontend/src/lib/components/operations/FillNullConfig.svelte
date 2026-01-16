<script lang="ts">
	import type { Schema } from '$lib/types/schema';

	interface FillNullConfigData {
		strategy: string;
		columns: string[] | null;
		value?: string | number;
	}

	interface Props {
		schema: Schema;
		config: FillNullConfigData;
		onSave: (config: FillNullConfigData) => void;
	}

	let { schema, config, onSave }: Props = $props();

	let localConfig = $state<FillNullConfigData>({
		strategy: config?.strategy || 'literal',
		columns: config?.columns ? [...config.columns] : null,
		value: config?.value || ''
	});

	const strategies = [
		{ value: 'literal', label: 'Fill with Value', needsValue: true, needsColumns: true },
		{ value: 'forward', label: 'Forward Fill', needsValue: false, needsColumns: true },
		{ value: 'backward', label: 'Backward Fill', needsValue: false, needsColumns: true },
		{ value: 'mean', label: 'Fill with Mean', needsValue: false, needsColumns: true },
		{ value: 'median', label: 'Fill with Median', needsValue: false, needsColumns: true },
		{ value: 'drop_rows', label: 'Drop Rows with Nulls', needsValue: false, needsColumns: true }
	];

	const currentStrategy = $derived(strategies.find((s) => s.value === localConfig.strategy));

	function toggleColumn(columnName: string) {
		if (!localConfig.columns) {
			localConfig.columns = [];
		}
		const index = localConfig.columns.indexOf(columnName);
		if (index > -1) {
			localConfig.columns.splice(index, 1);
		} else {
			localConfig.columns.push(columnName);
		}
	}

	function selectAllColumns() {
		localConfig.columns = schema.columns.map((c) => c.name);
	}

	function deselectAllColumns() {
		localConfig.columns = [];
	}

	function handleSave() {
		const saveConfig: FillNullConfigData = {
			strategy: localConfig.strategy,
			columns: localConfig.columns && localConfig.columns.length > 0 ? localConfig.columns : null
		};

		if (currentStrategy?.needsValue) {
			saveConfig.value = localConfig.value;
		}

		onSave(saveConfig);
	}

	function handleCancel() {
		localConfig = {
			strategy: config?.strategy || 'literal',
			columns: config?.columns ? [...config.columns] : null,
			value: config?.value || ''
		};
	}
</script>

<div class="fill-null-config">
	<h3>Fill Null Configuration</h3>

	<div class="section">
		<h4>Fill Strategy</h4>
		<select bind:value={localConfig.strategy}>
			{#each strategies as strategy}
				<option value={strategy.value}>{strategy.label}</option>
			{/each}
		</select>
	</div>

	{#if currentStrategy?.needsValue}
		<div class="section">
			<h4>Fill Value</h4>
			<input type="text" bind:value={localConfig.value} placeholder="Enter value (e.g., 0, N/A)" />
		</div>
	{/if}

	<div class="section">
		<h4>Target Columns</h4>
		<div class="column-actions">
			<button type="button" onclick={selectAllColumns} class="action-btn">Select All</button>
			<button type="button" onclick={deselectAllColumns} class="action-btn">Deselect All</button>
		</div>

		<div class="column-list">
			{#each schema.columns as column}
				<label class="column-item">
					<input
						type="checkbox"
						checked={localConfig.columns?.includes(column.name) || false}
						onchange={() => toggleColumn(column.name)}
					/>
					<span>{column.name} ({column.dtype})</span>
				</label>
			{/each}
		</div>

		{#if localConfig.columns && localConfig.columns.length > 0}
			<div class="selected-info">
				Selected {localConfig.columns.length} column{localConfig.columns.length !== 1 ? 's' : ''}:
				{localConfig.columns.join(', ')}
			</div>
		{:else}
			<div class="selected-info">No columns selected - will apply to all columns</div>
		{/if}
	</div>

	<div class="actions">
		<button type="button" onclick={handleSave} class="save-btn">Save</button>
		<button type="button" onclick={handleCancel} class="cancel-btn">Cancel</button>
	</div>
</div>

<style>
	.fill-null-config {
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

	select,
	input[type='text'] {
		width: 100%;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	.column-actions {
		display: flex;
		gap: 0.5rem;
		margin-bottom: 0.75rem;
	}

	.action-btn {
		padding: 0.25rem 0.75rem;
		background-color: #6c757d;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.875rem;
	}

	.action-btn:hover {
		opacity: 0.9;
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

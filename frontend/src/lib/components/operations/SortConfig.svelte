<script lang="ts">
	import type { Schema } from '$lib/types/schema';

	interface SortRule {
		column: string;
		descending: boolean;
	}

	interface Props {
		schema: Schema;
		config: SortRule[];
		onSave: (config: SortRule[]) => void;
	}

	let { schema, config, onSave }: Props = $props();

	let sortRules = $state<SortRule[]>(config?.length > 0 ? [...config] : []);

	let newRule = $state<SortRule>({
		column: '',
		descending: false
	});

	function addSortRule() {
		if (!newRule.column) return;

		// Check if column is already in sort rules
		const exists = sortRules.some((rule) => rule.column === newRule.column);
		if (exists) return;

		sortRules.push({
			column: newRule.column,
			descending: newRule.descending
		});

		newRule = {
			column: '',
			descending: false
		};
	}

	function removeSortRule(index: number) {
		sortRules.splice(index, 1);
	}

	function toggleDirection(index: number) {
		sortRules[index].descending = !sortRules[index].descending;
	}

	function moveUp(index: number) {
		if (index === 0) return;
		const temp = sortRules[index];
		sortRules[index] = sortRules[index - 1];
		sortRules[index - 1] = temp;
	}

	function moveDown(index: number) {
		if (index === sortRules.length - 1) return;
		const temp = sortRules[index];
		sortRules[index] = sortRules[index + 1];
		sortRules[index + 1] = temp;
	}

	function handleSave() {
		onSave(sortRules);
	}

	function handleCancel() {
		sortRules = config?.length > 0 ? [...config] : [];
	}

	let availableColumns = $derived(
		schema.columns.filter((col) => !sortRules.some((rule) => rule.column === col.name))
	);
</script>

<div class="sort-config">
	<h3>Sort Configuration</h3>

	<div class="add-rule">
		<select bind:value={newRule.column}>
			<option value="">Select column...</option>
			{#each availableColumns as column}
				<option value={column.name}>{column.name} ({column.dtype})</option>
			{/each}
		</select>

		<label class="direction-toggle">
			<input type="checkbox" bind:checked={newRule.descending} />
			<span>Descending</span>
		</label>

		<button type="button" onclick={addSortRule} disabled={!newRule.column}> Add Sort Rule </button>
	</div>

	{#if sortRules.length > 0}
		<div class="sort-rules">
			<h4>Sort Order (top to bottom)</h4>
			{#each sortRules as rule, i}
				<div class="sort-rule-item">
					<div class="rule-info">
						<span class="rule-column">{rule.column}</span>
						<button type="button" class="direction-btn" onclick={() => toggleDirection(i)}>
							{rule.descending ? '↓ DESC' : '↑ ASC'}
						</button>
					</div>

					<div class="rule-actions">
						<button type="button" onclick={() => moveUp(i)} disabled={i === 0} title="Move up">
							↑
						</button>
						<button
							type="button"
							onclick={() => moveDown(i)}
							disabled={i === sortRules.length - 1}
							title="Move down"
						>
							↓
						</button>
						<button type="button" class="remove-btn" onclick={() => removeSortRule(i)}>
							Remove
						</button>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<p class="empty-state">No sort rules configured. Add a column to sort by.</p>
	{/if}

	<div class="actions">
		<button type="button" onclick={handleSave} class="save-btn">Save</button>
		<button type="button" onclick={handleCancel} class="cancel-btn">Cancel</button>
	</div>
</div>

<style>
	.sort-config {
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
		font-size: 0.875rem;
		color: #6c757d;
		text-transform: uppercase;
	}

	.add-rule {
		display: flex;
		gap: 0.5rem;
		align-items: center;
		margin-bottom: 1.5rem;
	}

	.add-rule select {
		flex: 2;
		padding: 0.5rem;
		border: 1px solid #ccc;
		border-radius: 4px;
	}

	.direction-toggle {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		cursor: pointer;
		white-space: nowrap;
	}

	.direction-toggle input[type='checkbox'] {
		cursor: pointer;
	}

	.add-rule button {
		padding: 0.5rem 1rem;
		background-color: #28a745;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		white-space: nowrap;
	}

	.add-rule button:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}

	.sort-rules {
		padding: 1rem;
		background-color: #f8f9fa;
		border-radius: 4px;
		margin-bottom: 1rem;
	}

	.sort-rule-item {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem;
		background-color: white;
		border: 1px solid #ddd;
		border-radius: 4px;
		margin-bottom: 0.5rem;
	}

	.sort-rule-item:last-child {
		margin-bottom: 0;
	}

	.rule-info {
		display: flex;
		align-items: center;
		gap: 1rem;
	}

	.rule-column {
		font-weight: 500;
		font-size: 0.95rem;
	}

	.direction-btn {
		padding: 0.25rem 0.75rem;
		background-color: #007bff;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.875rem;
		font-family: monospace;
	}

	.rule-actions {
		display: flex;
		gap: 0.25rem;
	}

	.rule-actions button {
		padding: 0.25rem 0.5rem;
		background-color: #6c757d;
		color: white;
		border: none;
		border-radius: 4px;
		cursor: pointer;
		font-size: 0.875rem;
	}

	.rule-actions button:disabled {
		background-color: #ccc;
		cursor: not-allowed;
	}

	.remove-btn {
		background-color: #dc3545 !important;
	}

	.empty-state {
		padding: 2rem;
		text-align: center;
		color: #6c757d;
		background-color: #f8f9fa;
		border-radius: 4px;
		margin-bottom: 1rem;
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

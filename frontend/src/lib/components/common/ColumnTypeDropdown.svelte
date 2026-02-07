<script lang="ts">
	import ColumnTypeBadge from '$lib/components/common/ColumnTypeBadge.svelte';
	import { getAllColumnTypes } from '$lib/utils/columnTypes';
	import { onClickOutside } from 'runed';

	interface Props {
		value: string;
		onChange: (value: string) => void;
		placeholder?: string;
		disabled?: boolean;
	}

	let { value = $bindable(), onChange, placeholder = 'Select type...', disabled = false }: Props = $props();

	let menuOpen = $state(false);
	let menuRef = $state<HTMLElement>();
	let searchQuery = $state('');
	let searchInputRef = $state<HTMLInputElement>();

	const allColumnTypes = getAllColumnTypes();
	let filteredTypes = $derived(
		searchQuery
			? allColumnTypes.filter(
					(t) =>
						t.label.toLowerCase().includes(searchQuery.toLowerCase()) ||
						t.type.toLowerCase().includes(searchQuery.toLowerCase())
				)
			: allColumnTypes
	);
	let selectedType = $derived(allColumnTypes.find((t) => t.type === value));

	function selectType(typeValue: string) {
		onChange(typeValue);
		menuOpen = false;
		searchQuery = '';
	}

	function openMenu() {
		if (disabled) return;
		menuOpen = true;
		setTimeout(() => searchInputRef?.focus(), 0);
	}

	onClickOutside(
		() => menuRef,
		() => {
			if (menuOpen) {
				menuOpen = false;
				searchQuery = '';
			}
		}
	);
</script>

<div class="column-select" bind:this={menuRef}>
	<button 
		type="button" 
		class="column-trigger" 
		class:opacity-60={disabled}
		class:cursor-not-allowed={disabled}
		onclick={openMenu} 
		aria-expanded={menuOpen}
		disabled={disabled}
	>
		{#if selectedType}
			<ColumnTypeBadge columnType={selectedType.type} size="sm" />
		{:else}
			<span class="column-placeholder">{placeholder}</span>
		{/if}
		<span class="chevron">▾</span>
	</button>
	{#if menuOpen}
		<div class="column-menu" role="listbox">
			<div class="column-search">
				<input
					bind:this={searchInputRef}
					bind:value={searchQuery}
					type="text"
					placeholder="Search types..."
					class="column-search-input"
				/>
			</div>
			<div class="column-options">
				{#each filteredTypes as typeConfig (typeConfig.type)}
					<button
						type="button"
						class="column-option type-option"
						class:selected={value === typeConfig.type}
						onclick={() => selectType(typeConfig.type)}
						role="option"
						aria-selected={value === typeConfig.type}
						title={typeConfig.description}
					>
						<ColumnTypeBadge columnType={typeConfig.type} size="sm" />
					</button>
				{:else}
					<div class="no-results">No types found</div>
				{/each}
			</div>
		</div>
	{/if}
</div>

<style>
	.column-select {
		position: relative;
		display: flex;
		flex-direction: column;
	}

	.column-trigger {
		display: flex;
		align-items: center;
		justify-content: space-between;
		gap: var(--space-2);
		padding: var(--space-1) var(--space-2);
		background-color: var(--bg-primary);
		border: 1px solid var(--border-primary);
		border-radius: var(--radius-sm);
		cursor: pointer;
		font-size: var(--font-size-sm);
		transition: border-color var(--transition);
	}

	.column-trigger:hover {
		border-color: var(--border-primary);
	}

	.column-placeholder {
		color: var(--fg-muted);
	}

	.chevron {
		color: var(--fg-muted);
		font-size: 10px;
	}

	.column-menu {
		position: absolute;
		top: 100%;
		left: 0;
		right: 0;
		margin-top: var(--space-1);
		background-color: var(--bg-primary);
		border: 1px solid var(--border-primary);
		border-radius: var(--radius-sm);
		box-shadow: var(--shadow-md);
		z-index: var(--z-dropdown);
		max-height: 200px;
		display: flex;
		flex-direction: column;
	}

	.column-search {
		padding: var(--space-2);
		border-bottom: 1px solid var(--border-primary);
	}

	.column-search-input {
		width: 100%;
		padding: var(--space-1) var(--space-2);
		border: 1px solid var(--border-primary);
		border-radius: var(--radius-sm);
		background-color: var(--bg-primary);
		color: var(--fg-primary);
		font-size: var(--font-size-sm);
	}

	.column-search-input:focus {
		outline: none;
		border-color: var(--info-border);
	}

	.column-options {
		overflow-y: auto;
		padding: var(--space-1);
	}

	.column-option {
		display: flex;
		align-items: center;
		width: 100%;
		padding: var(--space-1) var(--space-2);
		background: none;
		border: none;
		cursor: pointer;
		border-radius: var(--radius-sm);
		transition: background-color var(--transition);
	}

	.column-option:hover {
		background-color: var(--bg-hover);
	}

	.column-option.selected {
		background-color: var(--accent-bg);
	}

	.no-results {
		padding: var(--space-2);
		text-align: center;
		color: var(--fg-muted);
		font-size: var(--font-size-sm);
	}
</style>

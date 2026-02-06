<script lang="ts">
	import { Search, X, Trash2 } from 'lucide-svelte';

	export type SortOption = 'newest' | 'oldest' | 'name-asc' | 'name-desc';

	interface Props {
		searchQuery: string;
		sortOption: SortOption;
		onSearch: (query: string) => void;
		onSort: (option: SortOption) => void;
		selectionCount?: number;
		onSelectAll?: () => void;
		onClearSelection?: () => void;
		onBulkDelete?: () => void;
	}

	let {
		searchQuery,
		sortOption,
		onSearch,
		onSort,
		selectionCount = 0,
		onSelectAll,
		onClearSelection,
		onBulkDelete
	}: Props = $props();
</script>

<div class="mb-7 flex flex-wrap items-center gap-4 max-sm:flex-col max-sm:items-stretch">
	<div class="relative min-w-[220px] max-w-[420px] flex-1 max-sm:max-w-none">
		<Search
			class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2"
			size={16}
			style="color: var(--fg-muted);"
		/>
		<input
			type="text"
			placeholder="Search analyses..."
			value={searchQuery}
			oninput={(e) => onSearch((e.target as HTMLInputElement).value)}
			class="search-input w-full border py-3 pl-10 pr-10 font-mono text-sm transition-all"
			style="border-color: var(--border-primary); color: var(--fg-primary); background-color: var(--bg-primary);"
		/>
		{#if searchQuery}
			<button
				class="clear-btn absolute right-2 top-1/2 flex -translate-y-1/2 cursor-pointer items-center justify-center border-none bg-transparent p-1 transition-all"
				onclick={() => onSearch('')}
				aria-label="Clear search"
				style="color: var(--fg-muted);"
			>
				<X size={14} />
			</button>
		{/if}
	</div>

	<div class="flex items-center gap-2 max-sm:justify-between">
		<label
			for="sort-select"
			class="whitespace-nowrap text-xs font-medium"
			style="color: var(--fg-muted);"
		>
			Sort:
		</label>
		<select
			id="sort-select"
			value={sortOption}
			onchange={(e) => onSort((e.target as HTMLSelectElement).value as SortOption)}
			class="sort-select cursor-pointer appearance-none border bg-no-repeat py-2 pl-3 pr-8 font-mono text-sm transition-colors max-sm:flex-1"
			style="border-color: var(--border-primary); color: var(--fg-primary); background-color: var(--bg-primary); background-image: url(&quot;data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23737373' stroke-width='2'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E&quot;); background-position: right 0.5rem center;"
		>
			<option value="newest">Newest</option>
			<option value="oldest">Oldest</option>
			<option value="name-asc">A-Z</option>
			<option value="name-desc">Z-A</option>
		</select>
	</div>

	{#if selectionCount > 0}
		<div class="ml-auto flex items-center gap-2">
			<button
				class="btn-text flex items-center gap-1 border border-transparent bg-transparent px-3 py-2 text-sm transition-all"
				onclick={onSelectAll}
			>
				Select All
			</button>
			<button
				class="btn-text flex items-center gap-1 border border-transparent bg-transparent px-3 py-2 text-sm transition-all"
				onclick={onClearSelection}
			>
				<X size={14} />
				Clear
			</button>
			<button class="btn-danger flex items-center gap-1" onclick={onBulkDelete}>
				<Trash2 size={14} />
				Delete
			</button>
		</div>
	{/if}
</div>

<style>
	.search-input:focus {
		outline: none;
		border-color: var(--border-focus);
		box-shadow: 0 0 0 2px color-mix(in srgb, var(--border-focus) 20%, transparent);
	}

	.search-input::placeholder {
		color: var(--fg-muted);
	}

	.clear-btn:hover {
		background-color: var(--bg-hover);
		color: var(--fg-primary);
	}

	.sort-select:focus {
		outline: none;
		border-color: var(--border-focus);
	}

	.sort-select:hover {
		border-color: var(--border-tertiary);
	}

	.btn-text {
		color: var(--fg-secondary);
	}

	.btn-text:hover {
		background-color: var(--bg-hover);
		color: var(--fg-primary);
	}
</style>

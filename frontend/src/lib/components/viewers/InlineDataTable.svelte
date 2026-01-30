<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import {
		createTable,
		getCoreRowModel,
		getSortedRowModel,
		type ColumnDef,
		type SortingState,
		type HeaderGroup,
		type Row
	} from '@tanstack/table-core';
	import { previewStepData, type StepPreviewResponse } from '$lib/api/compute';
	import type { TableCellValue } from '$lib/types/api-responses';
	import { schemaStore } from '$lib/stores/schema.svelte';
	import { analysisStore } from '$lib/stores/analysis.svelte';
	import { compress, formatBytes } from '$lib/utils/compression';
	import { hashPipeline } from '$lib/utils/hash';
	import type { CachedPreview } from '$lib/stores/analysis.svelte';

	interface Props {
		analysisId: string;
		datasourceId: string;
		pipeline: Array<{
			id: string;
			type: string;
			config: Record<string, unknown>;
			depends_on?: string[];
		}>;
		stepId: string;
		rowLimit?: number;
		previewVersion?: number;
		tabId: string;
		isStale?: boolean;
		onForceRefresh?: () => void;
	}

	type RowData = Record<string, unknown>;

	let {
		analysisId,
		datasourceId,
		pipeline,
		stepId,
		rowLimit = 1000,
		previewVersion = 0,
		tabId,
		isStale = false,
		onForceRefresh
	}: Props = $props();
	let currentPage = $state(1);
	let sorting = $state<SortingState>([]);
	let cacheError = $state<string | null>(null);

	// Reset page when previewVersion changes (new preview requested)
	let lastPreviewVersion = $state(0);
	$effect(() => {
		if (previewVersion !== lastPreviewVersion) {
			currentPage = 1;
			lastPreviewVersion = previewVersion;
		}
	});

	// Get cached preview from store
	const cachedPreview = $derived(analysisStore.getCachedPreview(tabId));
	const hasCachedPreview = $derived(!!cachedPreview && !isStale);

	// Query with optional initial data from cache
	const query = createQuery(() => {
		const cached = analysisStore.getCachedPreview(tabId);
		let initialData: StepPreviewResponse | undefined;

		// Use cached data if available and not stale
		if (cached && !isStale) {
			// Cached data is already the decompressed StepPreviewResponse
			// We need to access it through the store which will decompress it
			initialData = undefined; // We'll handle this via $effect below
		}

		return {
			queryKey: [
				'step-preview',
				analysisId,
				datasourceId,
				stepId,
				currentPage,
				rowLimit,
				previewVersion
			],
			queryFn: async (): Promise<StepPreviewResponse> => {
				const resourceConfig = analysisStore.resourceConfig as unknown as Record<
					string,
					unknown
				> | null;
				const result = await previewStepData({
					analysis_id: analysisId,
					datasource_id: datasourceId,
					pipeline_steps: pipeline,
					target_step_id: stepId,
					row_limit: rowLimit,
					page: currentPage,
					resource_config: resourceConfig
				});
				if (result.isErr()) {
					throw new Error(result.error.message);
				}

				// Cache the preview data
				const response = result.value;
				try {
					const compressed = await compress(response);
					if (compressed) {
						const originalSize = JSON.stringify(response).length;
						const compressedSize = compressed.length;

						// Skip if compressed size exceeds 50MB (50 * 1024 * 1024 bytes, but base64 is ~33% larger)
						// Base64 encoded string: 50MB * 1.33 = ~66.5MB
						const maxSize = 50 * 1024 * 1024 * 1.33;
						if (compressedSize < maxSize) {
							const cache: CachedPreview = {
								compressed,
								originalSize,
								compressedSize,
								pipelineHash: hashPipeline(pipeline),
								timestamp: Date.now(),
								version: previewVersion || 1
							};
							analysisStore.setCachedPreview(tabId, cache);
						} else {
							console.warn(
								`Preview data too large to cache: ${formatBytes(compressedSize)} compressed (limit: 50MB)`
							);
						}
					}
				} catch (e) {
					console.error('Failed to cache preview:', e);
				}

				return response;
			},
			staleTime: Infinity,
			enabled: !!previewVersion
		};
	});

	const data = $derived(query.data);
	const isLoading = $derived(query.isLoading);
	const error = $derived(query.error);

	// Try to load cached data if query hasn't fetched yet
	let cachedData = $state<StepPreviewResponse | null>(null);
	let loadingCached = $state(false);

	$effect(() => {
		const cached = analysisStore.getCachedPreview(tabId);
		if (cached && !isStale && !data && !isLoading && !loadingCached) {
			loadingCached = true;
			// Dynamically import decompress to avoid issues
			import('$lib/utils/compression').then(async ({ decompress }) => {
				try {
					const decompressed = await decompress<StepPreviewResponse>(cached.compressed);
					if (decompressed) {
						cachedData = decompressed;
						// Update schema store with cached columns
						if (decompressed.columns && decompressed.column_types) {
							schemaStore.setPreviewSchema(stepId, decompressed.columns, decompressed.column_types);
						}
					}
				} catch (e) {
					cacheError = 'Failed to load cached preview';
					console.error('Failed to decompress cached preview:', e);
				} finally {
					loadingCached = false;
				}
			});
		}
	});

	// Use cached data if available, otherwise use query data
	const displayData = $derived(data ?? cachedData);

	// Update schema store with actual columns from preview
	$effect(() => {
		if (data?.columns && data.column_types) {
			schemaStore.setPreviewSchema(stepId, data.columns, data.column_types);
		}
	});

	const totalPages = $derived(displayData ? Math.ceil(displayData.total_rows / rowLimit) : 0);
	const startRow = $derived((currentPage - 1) * rowLimit + 1);
	const endRow = $derived(displayData ? Math.min(currentPage * rowLimit, displayData.total_rows) : 0);

	function formatValue(value: TableCellValue): string {
		if (value === null || value === undefined) return '—';
		if (typeof value === 'number') return value.toLocaleString();
		if (typeof value === 'boolean') return value ? 'true' : 'false';
		if (Array.isArray(value)) {
			return (
				'[' +
				value
					.map((v) => {
						if (typeof v === 'number') return v.toLocaleString();
						if (v === null || v === undefined) return 'null';
						return String(v);
					})
					.join(', ') +
				']'
			);
		}
		return String(value);
	}

	function getColumnType(col: string): string {
		return displayData?.column_types?.[col] || '';
	}

	function isListType(columnType: string): boolean {
		return columnType.includes('List') || columnType === 'list';
	}

	const table = $derived.by(() => {
		const currentData = displayData;
		if (!currentData || !currentData.columns || currentData.columns.length === 0) {
			return null;
		}

		const columnDefs: ColumnDef<RowData>[] = currentData.columns.map((col) => ({
			id: col,
			accessorKey: col,
			header: col
		}));

		return createTable({
			data: currentData.data,
			columns: columnDefs,
			state: {
				sorting,
				columnPinning: { left: [], right: [] },
				columnVisibility: {},
				expanded: {},
				grouping: [],
				rowSelection: {},
				columnOrder: []
			},
			onSortingChange: () => {},
			getCoreRowModel: getCoreRowModel(),
			getSortedRowModel: getSortedRowModel(),
			onStateChange: () => {},
			renderFallbackValue: null
		});
	});

	const headerGroups = $derived<HeaderGroup<RowData>[]>(table ? table.getHeaderGroups() : []);

	const rows = $derived<Row<RowData>[]>(table ? table.getRowModel().rows : []);

	function nextPage() {
		if (currentPage < totalPages) currentPage++;
	}

	function prevPage() {
		if (currentPage > 1) currentPage--;
	}

	function toggleSort(columnId: string) {
		const existing = sorting.find((s: SortingState[number]) => s.id === columnId);
		if (!existing) {
			sorting = [{ id: columnId, desc: false }];
		} else if (!existing.desc) {
			sorting = [{ id: columnId, desc: true }];
		} else {
			sorting = [];
		}
	}

	function getSortDirection(columnId: string): 'asc' | 'desc' | false {
		const sort = sorting.find((s: SortingState[number]) => s.id === columnId);
		if (!sort) return false;
		return sort.desc ? 'desc' : 'asc';
	}

	function handleForceRefresh() {
		// Clear cache for this tab
		analysisStore.clearCachedPreview(tabId);
		cachedData = null;
		// Trigger refresh
		onForceRefresh?.();
	}
</script>

<div class="inline-data-table">
	{#if !previewVersion && !hasCachedPreview}
		<div class="not-loaded-state">
			<p>Click Preview button to load data</p>
		</div>
	{:else if isLoading || loadingCached}
		<div class="loading-overlay">
			<div class="spinner-md"></div>
			<p class="text-tertiary">Loading preview...</p>
		</div>
	{:else if error}
		<div class="error-state">
			<p class="error-title">Failed to load preview</p>
			<p class="error-message">{error.message}</p>
		</div>
	{:else if cacheError}
		<div class="error-state">
			<p class="error-title">Cache Error</p>
			<p class="error-message">{cacheError}</p>
			<button class="refresh-btn" onclick={handleForceRefresh}>Refresh</button>
		</div>
	{:else if headerGroups.length > 0 && displayData}
		<div class="table-info">
			<span>
				Showing {startRow.toLocaleString()}-{endRow.toLocaleString()} of {displayData.total_rows.toLocaleString()}
				rows
			</span>
			{#if cachedData && !data}
				<span class="cache-badge">Cached</span>
			{/if}
		</div>

		<div class="table-wrapper">
			<table>
				<thead>
					{#each headerGroups as headerGroup (headerGroup.id)}
						<tr>
							{#each headerGroup.headers as header (header.id)}
								<th>
									<button class="column-header" onclick={() => toggleSort(header.id)}>
										<span class="column-name">
											{typeof header.column.columnDef.header === 'string'
												? header.column.columnDef.header
												: header.id}
										</span>
										{#if getSortDirection(header.id)}
											<span class="sort-indicator">
												{getSortDirection(header.id) === 'asc' ? '↑' : '↓'}
											</span>
										{/if}
									</button>
									{#if getColumnType(header.id)}
										<span class="column-type" class:is-list={isListType(getColumnType(header.id))}>
											{getColumnType(header.id)}
										</span>
									{/if}
								</th>
							{/each}
						</tr>
					{/each}
				</thead>
				<tbody>
					{#each rows as row (row.id)}
						<tr>
							{#each row.getVisibleCells() as cell (cell.id)}
								<td class:is-list-cell={isListType(getColumnType(cell.column.id))}>
									{formatValue(cell.getValue() as TableCellValue)}
								</td>
							{/each}
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		{#if totalPages > 1}
			<div class="pagination">
				<button onclick={prevPage} disabled={currentPage === 1}>Previous</button>
				<span class="page-info">Page {currentPage} of {totalPages}</span>
				<button onclick={nextPage} disabled={currentPage >= totalPages}>Next</button>
			</div>
		{/if}

		{#if isStale}
			<div class="stale-warning">
				<span>Preview is stale - pipeline has changed</span>
				<button class="refresh-btn" onclick={handleForceRefresh}>Refresh</button>
			</div>
		{/if}
	{:else}
		<div class="empty-state">
			<p>No data available</p>
		</div>
	{/if}
</div>

<style>
	.inline-data-table {
		width: 100%;
		background: var(--panel-bg);
		border: 1px solid var(--panel-border);
		border-radius: var(--radius-md);
		overflow: hidden;
		margin: var(--space-2) 0;
		box-shadow: var(--panel-shadow);
		user-select: text;
	}
	.loading-overlay {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 2rem;
		gap: 0.75rem;
		color: var(--fg-tertiary);
	}
	.loading-overlay p {
		margin: 0;
	}
	.not-loaded-state {
		padding: var(--space-6);
		text-align: center;
		color: var(--fg-muted);
	}
	.not-loaded-state p {
		margin: 0;
	}
	.error-state {
		padding: var(--space-8);
		text-align: center;
	}
	.error-title {
		margin: 0 0 var(--space-2) 0;
		color: var(--error-fg);
		font-weight: var(--font-semibold);
	}
	.error-message {
		margin: 0;
		color: var(--fg-tertiary);
	}
	.empty-state {
		padding: var(--space-8);
		text-align: center;
		color: var(--fg-muted);
	}
	.empty-state p {
		margin: 0;
	}
	.table-info {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		font-size: 0.75rem;
		color: var(--fg-tertiary);
		background: var(--panel-header-bg);
		border-bottom: 1px solid var(--panel-border);
	}
	.cache-badge {
		padding: 0.125rem 0.5rem;
		background: var(--accent-bg);
		color: var(--accent-fg);
		border-radius: var(--radius-sm);
		font-size: 0.625rem;
		font-weight: 500;
		text-transform: uppercase;
	}
	.table-wrapper {
		overflow-x: auto;
		max-height: 400px;
		overflow-y: auto;
	}
	table {
		width: 100%;
		border-collapse: collapse;
	}
	thead {
		position: sticky;
		top: 0;
		background: var(--table-header-bg);
		z-index: 10;
	}
	th {
		padding: 0;
		text-align: left;
		border-bottom: 2px solid var(--table-border);
		font-weight: 600;
		font-size: 0.8125rem;
		text-transform: uppercase;
		letter-spacing: 0.02em;
	}
	.column-header {
		display: flex;
		align-items: center;
		gap: 0.25rem;
		padding: 0.75rem 1rem;
		background: none;
		border: none;
		cursor: pointer;
		font-size: inherit;
		font-weight: inherit;
		color: inherit;
		text-transform: inherit;
		letter-spacing: inherit;
		transition: background-color 0.15s ease;
	}
	.column-header:hover {
		background: var(--bg-hover);
	}
	.column-name {
		font-size: 0.875rem;
	}
	.sort-indicator {
		color: var(--accent-primary);
		font-size: 0.75rem;
	}
	.column-type {
		display: inline-block;
		margin-left: 0.5rem;
		padding: 0.125rem 0.375rem;
		font-size: 0.625rem;
		font-weight: 500;
		text-transform: uppercase;
		letter-spacing: 0.05em;
		border-radius: var(--radius-sm);
		background: var(--bg-tertiary);
		color: var(--fg-muted);
	}
	.column-type.is-list {
		background: var(--accent-bg);
		color: var(--accent-fg);
	}
	td.is-list-cell {
		font-size: 0.75rem;
	}
	tbody tr {
		border-bottom: 1px solid var(--table-border);
		transition: background-color 0.15s ease;
	}
	tbody tr:nth-child(even) {
		background: var(--table-row-alt);
	}
	tbody tr:hover {
		background: var(--table-row-hover);
	}
	tbody tr:last-child {
		border-bottom: none;
	}
	td {
		padding: 0.75rem 1rem;
		color: var(--fg-secondary);
		white-space: nowrap;
		overflow: hidden;
		text-overflow: ellipsis;
		max-width: 250px;
		font-size: 0.8125rem;
		user-select: text;
	}
	.pagination {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: var(--panel-header-bg);
		border-top: 1px solid var(--panel-border);
	}
	.pagination button {
		padding: 0.5rem 1rem;
		border: 1px solid var(--border-primary);
		border-radius: var(--radius-sm);
		background: var(--panel-bg);
		cursor: pointer;
		transition: all 0.15s ease;
	}
	.pagination button:hover:not(:disabled) {
		background: var(--bg-hover);
		border-color: var(--border-secondary);
	}
	.pagination button:disabled {
		opacity: 0.4;
		cursor: not-allowed;
	}
	.page-info {
		font-size: 0.75rem;
		color: var(--fg-tertiary);
	}
	.stale-warning {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 0.75rem 1rem;
		background: var(--warning-bg);
		border-top: 1px solid var(--warning-border);
		color: var(--warning-fg);
		font-size: 0.875rem;
	}
	.refresh-btn {
		padding: 0.25rem 0.75rem;
		background: var(--accent-primary);
		color: white;
		border: none;
		border-radius: var(--radius-sm);
		cursor: pointer;
		font-size: 0.75rem;
		font-weight: 500;
		transition: opacity 0.15s ease;
	}
	.refresh-btn:hover {
		opacity: 0.85;
	}
</style>

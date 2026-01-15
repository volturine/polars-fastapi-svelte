<script lang="ts">
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { listDatasources, deleteDatasource } from '$lib/api/datasource';
	import type { DataSource } from '$lib/types/datasource';

	const queryClient = useQueryClient();

	const query = createQuery(() => ({
		queryKey: ['datasources'],
		queryFn: listDatasources
	}));

	const deleteMutation = createMutation(() => ({
		mutationFn: deleteDatasource,
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['datasources'] });
		}
	}));

	let confirmingDelete = $state<string | null>(null);

	function handleDelete(id: string) {
		confirmingDelete = id;
	}

	function confirmDelete(id: string) {
		deleteMutation.mutate(id);
		confirmingDelete = null;
	}

	function cancelDelete() {
		confirmingDelete = null;
	}

	function getColumnCount(datasource: DataSource): number {
		if (datasource.schema_cache && typeof datasource.schema_cache === 'object') {
			const schema = datasource.schema_cache as { columns?: unknown[] };
			if (Array.isArray(schema.columns)) {
				return schema.columns.length;
			}
		}
		return 0;
	}

	function formatDate(dateString: string): string {
		const date = new Date(dateString);
		return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
	}
</script>

<div class="container">
	<header>
		<h1>Data Sources</h1>
		<a href="/datasources/new" class="button primary">Add Data Source</a>
	</header>

	{#if query.isLoading}
		<div class="loading">Loading data sources...</div>
	{:else if query.isError}
		<div class="error">
			Error loading data sources: {query.error instanceof Error
				? query.error.message
				: 'Unknown error'}
		</div>
	{:else if query.data}
		{#if query.data.length === 0}
			<div class="empty">
				<p>No data sources yet.</p>
				<a href="/datasources/new" class="button">Create your first data source</a>
			</div>
		{:else}
			<table>
				<thead>
					<tr>
						<th>Name</th>
						<th>Type</th>
						<th>Columns</th>
						<th>Created</th>
						<th>Actions</th>
					</tr>
				</thead>
				<tbody>
					{#each query.data as datasource (datasource.id)}
						<tr>
							<td class="name">{datasource.name}</td>
							<td>
								<span class="badge {datasource.source_type}">
									{datasource.source_type}
								</span>
							</td>
							<td>{getColumnCount(datasource)}</td>
							<td class="date">{formatDate(datasource.created_at)}</td>
							<td>
								{#if confirmingDelete === datasource.id}
									<div class="confirm-delete">
										<button
											onclick={() => confirmDelete(datasource.id)}
											class="button danger small"
											disabled={deleteMutation.isPending}
										>
											Confirm
										</button>
										<button onclick={cancelDelete} class="button small">Cancel</button>
									</div>
								{:else}
									<button
										onclick={() => handleDelete(datasource.id)}
										class="button danger small"
										disabled={deleteMutation.isPending}
									>
										Delete
									</button>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		{/if}
	{/if}
</div>

<style>
	.container {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem;
	}

	header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: 2rem;
	}

	h1 {
		font-size: 2rem;
		font-weight: 600;
		margin: 0;
	}

	.button {
		display: inline-block;
		padding: 0.5rem 1rem;
		background: #e5e7eb;
		border: none;
		border-radius: 0.375rem;
		cursor: pointer;
		text-decoration: none;
		color: #1f2937;
		font-size: 0.875rem;
		font-weight: 500;
		transition: background-color 0.15s;
	}

	.button:hover {
		background: #d1d5db;
	}

	.button.primary {
		background: #3b82f6;
		color: white;
	}

	.button.primary:hover {
		background: #2563eb;
	}

	.button.danger {
		background: #ef4444;
		color: white;
	}

	.button.danger:hover {
		background: #dc2626;
	}

	.button.small {
		padding: 0.25rem 0.75rem;
		font-size: 0.813rem;
	}

	.button:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}

	.loading,
	.error {
		padding: 2rem;
		text-align: center;
		border-radius: 0.5rem;
		margin: 2rem 0;
	}

	.loading {
		background: #f3f4f6;
		color: #6b7280;
	}

	.error {
		background: #fee2e2;
		color: #991b1b;
	}

	.empty {
		text-align: center;
		padding: 3rem;
		background: #f9fafb;
		border-radius: 0.5rem;
		border: 2px dashed #d1d5db;
	}

	.empty p {
		margin: 0 0 1rem 0;
		color: #6b7280;
		font-size: 1.125rem;
	}

	table {
		width: 100%;
		border-collapse: collapse;
		background: white;
		border-radius: 0.5rem;
		overflow: hidden;
		box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1);
	}

	thead {
		background: #f9fafb;
	}

	th {
		text-align: left;
		padding: 0.75rem 1rem;
		font-weight: 600;
		font-size: 0.875rem;
		color: #374151;
		border-bottom: 1px solid #e5e7eb;
	}

	td {
		padding: 1rem;
		border-bottom: 1px solid #f3f4f6;
	}

	tr:last-child td {
		border-bottom: none;
	}

	tbody tr:hover {
		background: #f9fafb;
	}

	.name {
		font-weight: 500;
		color: #111827;
	}

	.date {
		color: #6b7280;
		font-size: 0.875rem;
	}

	.badge {
		display: inline-block;
		padding: 0.25rem 0.625rem;
		border-radius: 9999px;
		font-size: 0.75rem;
		font-weight: 500;
		text-transform: capitalize;
	}

	.badge.file {
		background: #dbeafe;
		color: #1e40af;
	}

	.badge.database {
		background: #dcfce7;
		color: #166534;
	}

	.badge.api {
		background: #fef3c7;
		color: #92400e;
	}

	.confirm-delete {
		display: flex;
		gap: 0.5rem;
	}
</style>

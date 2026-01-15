<script lang="ts">
	import { createQuery } from '@tanstack/svelte-query';
	import { useQueryClient } from '@tanstack/svelte-query';
	import { goto } from '$app/navigation';
	import { listAnalyses, deleteAnalysis } from '$lib/api/analysis';
	import { GalleryGrid, EmptyState } from '$lib/components/gallery';

	const queryClient = useQueryClient();

	const query = createQuery(() => ({
		queryKey: ['analyses'],
		queryFn: listAnalyses
	}));

	function createNew() {
		goto('/analysis/new');
	}

	async function handleDelete(id: string) {
		try {
			await deleteAnalysis(id);
			queryClient.invalidateQueries({ queryKey: ['analyses'] });
		} catch (err) {
			console.error('Failed to delete analysis:', err);
			alert('Failed to delete analysis. Please try again.');
		}
	}
</script>

<div class="container">
	<header>
		<div class="header-content">
			<div>
				<h1>Analysis Gallery</h1>
				<p class="subtitle">Browse and manage your data analyses</p>
			</div>
			<button class="btn-new" onclick={createNew}>
				<svg
					xmlns="http://www.w3.org/2000/svg"
					viewBox="0 0 24 24"
					fill="none"
					stroke="currentColor"
				>
					<path d="M12 5v14M5 12h14" stroke-width="2" />
				</svg>
				New Analysis
			</button>
		</div>
	</header>

	<main>
		{#if query.isPending}
			<div class="loading">
				<div class="skeleton-grid">
					{#each Array(6) as _, i (i)}
						<div class="skeleton-card">
							<div class="skeleton-thumbnail"></div>
							<div class="skeleton-content">
								<div class="skeleton-title"></div>
								<div class="skeleton-text"></div>
								<div class="skeleton-text small"></div>
							</div>
						</div>
					{/each}
				</div>
			</div>
		{:else if query.isError}
			<div class="error">
				<div class="error-icon">
					<svg
						xmlns="http://www.w3.org/2000/svg"
						viewBox="0 0 24 24"
						fill="none"
						stroke="currentColor"
					>
						<circle cx="12" cy="12" r="10" stroke-width="2" />
						<path d="M12 8v4M12 16h.01" stroke-width="2" />
					</svg>
				</div>
				<h2>Failed to Load Analyses</h2>
				<p class="error-message">{query.error.message}</p>
				<button class="btn-retry" onclick={() => query.refetch()}> Try Again </button>
			</div>
		{:else if query.data}
			{#if query.data.length === 0}
				<EmptyState />
			{:else}
				<GalleryGrid analyses={query.data} onDelete={handleDelete} />
			{/if}
		{/if}
	</main>
</div>

<style>
	.container {
		max-width: 1400px;
		margin: 0 auto;
		padding: 24px;
	}

	header {
		margin-bottom: 32px;
	}

	.header-content {
		display: flex;
		justify-content: space-between;
		align-items: flex-start;
		gap: 24px;
	}

	h1 {
		margin: 0 0 8px 0;
		font-size: 32px;
		font-weight: 700;
		color: #212121;
	}

	.subtitle {
		margin: 0;
		font-size: 16px;
		color: #757575;
	}

	.btn-new {
		background: #1976d2;
		color: white;
		border: none;
		border-radius: 8px;
		padding: 12px 24px;
		font-size: 16px;
		font-weight: 500;
		cursor: pointer;
		display: inline-flex;
		align-items: center;
		gap: 8px;
		transition: all 0.2s;
		white-space: nowrap;
	}

	.btn-new:hover {
		background: #1565c0;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
	}

	.btn-new svg {
		width: 20px;
		height: 20px;
		stroke-width: 2;
	}

	.loading {
		padding: 24px 0;
	}

	.skeleton-grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 24px;
	}

	.skeleton-card {
		border: 1px solid #e0e0e0;
		border-radius: 8px;
		overflow: hidden;
		background: white;
	}

	.skeleton-thumbnail {
		width: 100%;
		aspect-ratio: 16 / 9;
		background: linear-gradient(90deg, #f5f5f5 25%, #eeeeee 50%, #f5f5f5 75%);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
	}

	.skeleton-content {
		padding: 16px;
	}

	.skeleton-title,
	.skeleton-text {
		height: 16px;
		background: linear-gradient(90deg, #f5f5f5 25%, #eeeeee 50%, #f5f5f5 75%);
		background-size: 200% 100%;
		animation: shimmer 1.5s infinite;
		border-radius: 4px;
		margin-bottom: 12px;
	}

	.skeleton-title {
		height: 20px;
		width: 70%;
	}

	.skeleton-text.small {
		width: 50%;
	}

	@keyframes shimmer {
		0% {
			background-position: 200% 0;
		}
		100% {
			background-position: -200% 0;
		}
	}

	.error {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 80px 24px;
		text-align: center;
		min-height: 400px;
	}

	.error-icon {
		width: 64px;
		height: 64px;
		color: #d32f2f;
		margin-bottom: 24px;
	}

	.error-icon svg {
		width: 100%;
		height: 100%;
	}

	.error h2 {
		margin: 0 0 12px 0;
		font-size: 24px;
		font-weight: 600;
		color: #212121;
	}

	.error-message {
		margin: 0 0 32px 0;
		font-size: 16px;
		color: #757575;
		max-width: 400px;
	}

	.btn-retry {
		background: #1976d2;
		color: white;
		border: none;
		border-radius: 8px;
		padding: 12px 24px;
		font-size: 16px;
		font-weight: 500;
		cursor: pointer;
		transition: all 0.2s;
	}

	.btn-retry:hover {
		background: #1565c0;
	}

	@media (max-width: 768px) {
		.container {
			padding: 16px;
		}

		.header-content {
			flex-direction: column;
			align-items: stretch;
		}

		h1 {
			font-size: 24px;
		}

		.subtitle {
			font-size: 14px;
		}

		.btn-new {
			width: 100%;
			justify-content: center;
		}

		.skeleton-grid {
			grid-template-columns: 1fr;
			gap: 16px;
		}
	}
</style>

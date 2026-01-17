<script lang="ts">
	import type { DataSource } from '$lib/types/datasource';

	interface Props {
		datasource: DataSource | null;
		onChangeDatasource?: () => void;
	}

	let { datasource, onChangeDatasource }: Props = $props();
</script>

<div class="datasource-node">
	<div class="node-content">
		<div class="node-header">
			<span class="node-type">source</span>
			<span class="node-badge">root</span>
		</div>

		{#if datasource}
			<div class="datasource-info">
				<span class="datasource-name">{datasource.name}</span>
				<span class="datasource-type">{datasource.source_type}</span>
			</div>
		{:else}
			<div class="datasource-info empty">
				<span class="datasource-name">No datasource</span>
			</div>
		{/if}

		{#if onChangeDatasource}
			<div class="node-actions">
				<button class="action-btn" onclick={onChangeDatasource} type="button">
					change source
				</button>
			</div>
		{/if}
	</div>

	<div class="connection-point bottom"></div>
</div>

<style>
	.datasource-node {
		position: relative;
		width: min(55%, 640px);
	}

	.node-content {
		background-color: var(--bg-primary);
		border: 2px solid var(--accent-primary);
		border-radius: var(--radius-sm);
		padding: var(--space-4);
		transition: all var(--transition-fast);
		box-shadow: var(--card-shadow);
	}

	.node-header {
		display: flex;
		justify-content: space-between;
		align-items: center;
		margin-bottom: var(--space-3);
	}

	.node-type {
		font-size: var(--text-sm);
		font-weight: 600;
		color: var(--accent-primary);
		font-family: var(--font-mono);
	}

	.node-badge {
		font-size: var(--text-xs);
		color: var(--bg-primary);
		background-color: var(--accent-primary);
		padding: var(--space-1) var(--space-2);
		border-radius: var(--radius-sm);
		font-family: var(--font-mono);
		text-transform: uppercase;
		letter-spacing: 0.05em;
	}

	.datasource-info {
		padding: var(--space-2) var(--space-3);
		background-color: var(--bg-tertiary);
		border-radius: var(--radius-sm);
		margin-bottom: var(--space-3);
	}

	.datasource-info.empty {
		border: 1px dashed var(--border-secondary);
		background-color: transparent;
	}

	.datasource-name {
		display: block;
		font-size: var(--text-sm);
		font-weight: 500;
		color: var(--fg-primary);
	}

	.datasource-type {
		display: block;
		font-size: var(--text-xs);
		color: var(--fg-muted);
		text-transform: uppercase;
		margin-top: var(--space-1);
	}

	.node-actions {
		display: flex;
		gap: var(--space-2);
	}

	.action-btn {
		flex: 1;
		padding: var(--space-2);
		background-color: transparent;
		border: 1px solid var(--border-primary);
		border-radius: var(--radius-sm);
		cursor: pointer;
		font-family: var(--font-mono);
		font-size: var(--text-xs);
		font-weight: 500;
		color: var(--fg-secondary);
		transition: all var(--transition-fast);
	}

	.action-btn:hover {
		background-color: var(--bg-hover);
		color: var(--fg-primary);
		border-color: var(--accent-primary);
	}

	.connection-point {
		position: absolute;
		left: 50%;
		transform: translateX(-50%);
		width: 8px;
		height: 8px;
		background-color: var(--accent-primary);
		border: 2px solid var(--bg-primary);
		border-radius: 50%;
		z-index: 2;
	}

	.connection-point.bottom {
		bottom: -4px;
	}
</style>

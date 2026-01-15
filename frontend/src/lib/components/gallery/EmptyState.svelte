<script lang="ts">
	import { goto } from '$app/navigation';

	function createNew() {
		goto('/analysis/new');
	}
</script>

<div class="empty">
	<div class="icon">
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
			<rect x="3" y="3" width="18" height="18" rx="2" stroke-width="2" />
			<path d="M3 9h18M9 3v18" stroke-width="2" />
		</svg>
	</div>

	<h2>No Analyses Yet</h2>
	<p>Create your first analysis to get started with data exploration</p>

	<button class="btn-create" onclick={createNew}>
		<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor">
			<path d="M12 5v14M5 12h14" stroke-width="2" />
		</svg>
		Create Analysis
	</button>
</div>

<style>
	.empty {
		display: flex;
		flex-direction: column;
		align-items: center;
		justify-content: center;
		padding: 80px 24px;
		text-align: center;
		min-height: 400px;
	}

	.icon {
		width: 80px;
		height: 80px;
		color: #bdbdbd;
		margin-bottom: 24px;
	}

	.icon svg {
		width: 100%;
		height: 100%;
	}

	h2 {
		margin: 0 0 12px 0;
		font-size: 24px;
		font-weight: 600;
		color: #212121;
	}

	p {
		margin: 0 0 32px 0;
		font-size: 16px;
		color: #757575;
		max-width: 400px;
	}

	.btn-create {
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
	}

	.btn-create:hover {
		background: #1565c0;
		transform: translateY(-1px);
		box-shadow: 0 4px 12px rgba(25, 118, 210, 0.3);
	}

	.btn-create svg {
		width: 20px;
		height: 20px;
		stroke-width: 2;
	}
</style>

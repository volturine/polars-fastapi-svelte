<script lang="ts">
	interface Props {
		config?: Record<string, never>;
	}

	let { config = $bindable({}) }: Props = $props();
</script>

<div class="config-panel">
	<h3>Null Count</h3>
	<p class="description">Count null values for each column in the dataset.</p>
	<p class="info-box">
		This operation will return a single row with the count of null values for each column.
	</p>
</div>

<style>
	h3 {
		margin-bottom: var(--space-2);
	}

	.description {
		margin-bottom: var(--space-2);
	}

	.info-box {
		margin: 0;
	}
</style>

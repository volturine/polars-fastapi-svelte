<script lang="ts">
	import type { AnalysisGalleryItem } from '$lib/types/analysis';
	import AnalysisCard from './AnalysisCard.svelte';

	interface Props {
		analyses: AnalysisGalleryItem[];
		onDelete: (id: string) => void;
	}

	let { analyses, onDelete }: Props = $props();
</script>

<div class="grid">
	{#each analyses as analysis (analysis.id)}
		<AnalysisCard {analysis} {onDelete} />
	{/each}
</div>

<style>
	.grid {
		display: grid;
		grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
		gap: 24px;
		width: 100%;
	}

	@media (max-width: 768px) {
		.grid {
			grid-template-columns: 1fr;
			gap: 16px;
		}
	}

	@media (min-width: 769px) and (max-width: 1024px) {
		.grid {
			grid-template-columns: repeat(2, 1fr);
		}
	}

	@media (min-width: 1025px) {
		.grid {
			grid-template-columns: repeat(3, 1fr);
		}
	}

	@media (min-width: 1440px) {
		.grid {
			grid-template-columns: repeat(4, 1fr);
		}
	}
</style>

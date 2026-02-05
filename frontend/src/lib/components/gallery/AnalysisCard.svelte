<script lang="ts">
	import type { AnalysisGalleryItem } from '$lib/types/analysis';
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { ChartBar, Trash2 } from 'lucide-svelte';
	import { formatDateDisplay, getYearDisplay } from '$lib/utils/datetime';

	interface Props {
		analysis: AnalysisGalleryItem;
		selected: boolean;
		anySelected: boolean;
		onDelete: (id: string) => void;
		onToggleSelect: (id: string) => void;
	}

	let { analysis, selected, anySelected, onDelete, onToggleSelect }: Props = $props();

	function handleClick(e: MouseEvent) {
		const target = e.target as HTMLElement;
		if (target.closest('button') || target.closest('input[type=checkbox]')) return;
		goto(resolve(`/analysis/${analysis.id}`), { invalidateAll: true });
	}

	function handleKeyPress(e: KeyboardEvent) {
		if ((e.key === 'Enter' || e.key === ' ') && !(e.target as HTMLElement).closest('button')) {
			e.preventDefault();
			goto(resolve(`/analysis/${analysis.id}`), { invalidateAll: true });
		}
	}

	function formatDate(date: string): string {
		const now = new Date();
		const year = getYearDisplay(date);
		const currentYear = getYearDisplay(now);
		const opts: Intl.DateTimeFormatOptions = { month: 'short', day: 'numeric' };
		if (year !== null && currentYear !== null && year !== currentYear) {
			opts.year = 'numeric';
		}
		return formatDateDisplay(date, opts);
	}
</script>

<div
	class="card group relative cursor-pointer overflow-hidden rounded-sm border transition-all hover:-translate-y-px"
	class:selected
	onclick={handleClick}
	onkeypress={handleKeyPress}
	role="button"
	tabindex="0"
	style="background-color: var(--bg-primary); border-color: var(--border-primary); box-shadow: var(--card-shadow);"
>
	<div
		class="relative flex aspect-video w-full items-center justify-center border-b"
		style="background-color: var(--bg-tertiary); border-color: var(--border-primary);"
	>
		<input
			type="checkbox"
			class="checkbox absolute left-2 top-2 z-[2] m-0 h-[18px] w-[18px] cursor-pointer opacity-0 transition-opacity group-hover:opacity-100"
			class:visible={anySelected}
			checked={selected}
			onchange={(e) => {
				e.stopPropagation();
				onToggleSelect(analysis.id);
			}}
			onclick={(e) => e.stopPropagation()}
			aria-label={`Select ${analysis.name}`}
			style="accent-color: var(--accent-primary);"
		/>
		{#if analysis.thumbnail}
			<img src={analysis.thumbnail} alt={analysis.name} class="h-full w-full object-cover" />
		{:else}
			<div style="color: var(--fg-faint);">
				<ChartBar size={32} strokeWidth={1.5} />
			</div>
		{/if}
	</div>

	<div class="p-4">
		<div class="mb-2 flex items-start justify-between gap-3">
			<h3 class="m-0 min-w-0 flex-1 truncate text-sm font-semibold">{analysis.name}</h3>
			<button
				class="btn-delete flex flex-shrink-0 items-center justify-center rounded-sm border p-1 opacity-0 transition-all group-hover:opacity-100"
				onclick={(e) => {
					e.stopPropagation();
					onDelete(analysis.id);
				}}
				aria-label="Delete analysis"
				style="background-color: transparent; border-color: var(--border-primary); color: var(--fg-muted);"
			>
				<Trash2 size={14} />
			</button>
		</div>

		<div class="text-xs" style="color: var(--fg-muted);">
			<span>{formatDate(analysis.updated_at)}</span>
		</div>
	</div>
</div>

<style>
	.card:hover {
		border-color: var(--border-tertiary);
	}

	.card:focus {
		outline: none;
		border-color: var(--border-focus);
	}

	.card.selected {
		border-color: var(--accent-primary);
	}

	.checkbox.visible {
		opacity: 1;
	}

	.btn-delete:hover {
		background-color: var(--error-bg);
		border-color: var(--error-border);
		color: var(--error-fg);
	}
</style>

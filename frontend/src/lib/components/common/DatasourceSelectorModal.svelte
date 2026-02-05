<script lang="ts">
	import { onClickOutside, Debounced } from 'runed';
	import { X } from 'lucide-svelte';
	import type { DataSource } from '$lib/types/datasource';
	import FileTypeBadge from '$lib/components/common/FileTypeBadge.svelte';

	interface Props {
		show: boolean;
		datasources: DataSource[];
		isLoading?: boolean;
		mode?: 'add' | 'change';
		onSelect: (id: string, name: string) => void;
		onClose: () => void;
	}

	let { show, datasources, isLoading = false, mode = 'add', onSelect, onClose }: Props = $props();

	let searchQuery = $state('');
	let debouncedSearch = new Debounced(() => searchQuery, 200);
	let modalRef = $state<HTMLElement>();
	let searchInput = $state<HTMLInputElement>();

	onClickOutside(
		() => modalRef,
		() => handleClose(),
		{ immediate: true }
	);

	let filteredDatasources = $derived(
		datasources.filter((ds) => {
			const query = debouncedSearch.current.toLowerCase().trim();
			if (!query) return true;
			return ds.name.toLowerCase().includes(query);
		})
	);

	function handleClose() {
		onClose();
		searchQuery = '';
	}

	function handleSelect(datasourceId: string, name: string) {
		onSelect(datasourceId, name);
		handleClose();
	}

	function handleKeydown(event: KeyboardEvent) {
		if (event.key === 'Escape') {
			handleClose();
		}
	}

	function handleBackdropKeydown(event: KeyboardEvent) {
		if (event.key === 'Enter' || event.key === ' ') {
			event.preventDefault();
			handleClose();
		}
	}

	$effect(() => {
		if (show) {
			document.body.style.overflow = 'hidden';
		} else {
			document.body.style.overflow = '';
		}

		return () => {
			document.body.style.overflow = '';
		};
	});

	$effect(() => {
		if (show && searchInput) {
			searchInput.focus();
		}
	});
</script>

<svelte:window onkeydown={handleKeydown} />

{#if show}
	<div
		class="modal-backdrop fixed inset-0 z-[1000] flex items-center justify-center p-4"
		onclick={handleClose}
		onkeydown={handleBackdropKeydown}
		role="button"
		tabindex="0"
		aria-label="Close modal"
		style="background-color: var(--overlay-bg);"
	>
		<div
			class="modal flex max-h-[80vh] w-full max-w-[480px] flex-col rounded-md border focus:outline-none max-sm:max-w-full"
			bind:this={modalRef}
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
			role="dialog"
			aria-modal="true"
			aria-labelledby="modal-title"
			tabindex="-1"
			style="background-color: var(--panel-bg); border-color: var(--panel-border); box-shadow: var(--shadow-lg);"
		>
			<div class="flex items-center justify-between border-b p-4" style="border-color: var(--panel-border);">
				<h2 id="modal-title" class="m-0 text-sm font-semibold" style="color: var(--fg-primary);">{mode === 'change' ? 'Change Datasource' : 'Add Datasource'}</h2>
				<button
					class="modal-close flex cursor-pointer items-center justify-center rounded-sm border-none bg-transparent p-1 transition-all"
					onclick={handleClose}
					aria-label="Close"
					style="color: var(--fg-muted);"
				>
					<X size={20} />
				</button>
			</div>
			<div class="flex flex-col gap-4 overflow-y-auto p-4">
				<input
					class="search-input w-full rounded-sm border px-3 py-3 text-sm transition-all focus:outline-none"
					type="text"
					bind:this={searchInput}
					bind:value={searchQuery}
					placeholder="Search datasources..."
					style="border-color: var(--panel-border); color: var(--fg-primary); background-color: var(--bg-primary);"
				/>
				<div class="flex max-h-[300px] flex-col gap-1 overflow-y-auto">
					{#if isLoading}
						<div class="flex items-center justify-center p-8 text-sm" style="color: var(--fg-muted);">Loading...</div>
					{:else if filteredDatasources.length === 0}
						<div class="flex items-center justify-center p-8 text-sm" style="color: var(--fg-muted);">
							{searchQuery ? 'No matching datasources' : 'No datasources available'}
						</div>
					{:else}
						{#each filteredDatasources as ds (ds.id)}
							<button
								class="datasource-item flex cursor-pointer items-center justify-between rounded-sm border border-transparent bg-transparent p-3 text-left transition-all"
								onclick={() => handleSelect(ds.id, ds.name)}
							>
								<span class="text-sm font-medium" style="color: var(--fg-primary);">{ds.name}</span>
								<span class="flex items-center gap-1" style="color: var(--fg-muted);">
									{#if ds.source_type === 'file'}
										<FileTypeBadge path={ds.config.file_path as string} size="sm" showIcon={true} />
									{:else}
										<FileTypeBadge
											sourceType={ds.source_type as 'database' | 'api' | 'iceberg' | 'duckdb'}
											size="sm"
											showIcon={true}
										/>
									{/if}
								</span>
							</button>
						{/each}
					{/if}
				</div>
			</div>
		</div>
	</div>
{/if}

<style>
	@keyframes fadeIn {
		from { opacity: 0; }
		to { opacity: 1; }
	}

	@keyframes slideIn {
		from { transform: translateY(-10px); opacity: 0; }
		to { transform: translateY(0); opacity: 1; }
	}

	.modal-backdrop {
		animation: fadeIn var(--transition);
	}

	.modal {
		animation: slideIn var(--transition);
	}

	.modal-close:hover {
		background-color: var(--bg-hover);
		color: var(--fg-primary);
	}

	.search-input:focus {
		border-color: var(--accent-primary);
	}

	.datasource-item:hover {
		background-color: var(--bg-hover);
		border-color: var(--panel-border);
	}
</style>

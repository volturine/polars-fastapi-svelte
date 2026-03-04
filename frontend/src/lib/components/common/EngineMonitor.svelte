<script lang="ts">
	import { Cpu, X, ChevronDown, LoaderCircle } from 'lucide-svelte';
	import { onClickOutside } from 'runed';
	import { untrack } from 'svelte';
	import { enginesStore } from '$lib/stores/engines.svelte';
	import { toEpochDisplay } from '$lib/utils/datetime';
	import { css } from '$lib/styles/panda';

	let expanded = $state(false);
	let killing = $state<string | null>(null);

	// Subscription: $derived can't start/stop polling.
	$effect(() => {
		untrack(() => enginesStore.startPolling());
		return () => enginesStore.stopPolling();
	});

	async function handleKill(analysisId: string) {
		killing = analysisId;
		try {
			await enginesStore.shutdownEngine(analysisId);
		} finally {
			killing = null;
		}
	}

	function formatTime(isoString: string | null): string {
		if (!isoString) return 'N/A';
		const dateMs = toEpochDisplay(isoString);
		const nowMs = Date.now();
		const diff = Math.floor((nowMs - dateMs) / 1000);

		if (diff < 60) return `${diff}s ago`;
		if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
		return `${Math.floor(diff / 3600)}h ago`;
	}

	function toggleExpanded() {
		expanded = !expanded;
		if (expanded) {
			enginesStore.fetch();
		}
	}

	let dropdownRef = $state<HTMLElement>();
	onClickOutside(
		() => dropdownRef,
		() => {
			expanded = false;
		},
		{ immediate: true }
	);
</script>

<div class={css({ position: 'relative' })} bind:this={dropdownRef}>
	<button
		class={css({
			display: 'flex',
			cursor: 'pointer',
			alignItems: 'center',
			gap: '2',
			borderWidth: '1px',
			borderStyle: 'solid',
			borderColor: 'transparent',
			paddingX: '3',
			paddingY: '2',
			fontSize: 'xs',
			backgroundColor: expanded ? 'bg.hover' : undefined,
			color: expanded ? 'fg.primary' : enginesStore.count > 0 ? 'fg.secondary' : 'fg.tertiary',
			_hover: { color: 'fg.primary' }
		})}
		onclick={toggleExpanded}
		title="Engine Monitor"
	>
		<Cpu size={16} />
		{#if enginesStore.count > 0}
			<span
				class={css({
					minWidth: '4.5',
					paddingX: '2',
					textAlign: 'center',
					fontSize: 'xs',
					fontWeight: 'semibold',
					backgroundColor: 'accent.primary',
					color: 'bg.primary'
				})}
			>
				{enginesStore.count}
			</span>
		{/if}
		<span class={expanded ? css({ transform: 'rotate(180deg)' }) : ''}>
			<ChevronDown size={12} />
		</span>
	</button>

	{#if expanded}
		<div
			class={css({
				position: 'absolute',
				right: '0',
				top: '100%',
				zIndex: 'engine',
				width: '17.5rem',
				overflow: 'hidden',
				borderWidth: '1px',
				borderStyle: 'solid',
				borderColor: 'border.tertiary',
				backgroundColor: 'bg.primary'
			})}
		>
			<div
				class={css({
					display: 'flex',
					alignItems: 'center',
					justifyContent: 'space-between',
					borderBottomWidth: '1px',
					borderBottomStyle: 'solid',
					borderBottomColor: 'border.tertiary',
					padding: '3',
					backgroundColor: 'bg.secondary'
				})}
			>
				<span class={css({ fontSize: 'sm', fontWeight: 'semibold', color: 'fg.primary' })}>
					Active Engines
				</span>
				<button
					class={css({
						display: 'flex',
						cursor: 'pointer',
						alignItems: 'center',
						justifyContent: 'center',
						border: 'none',
						backgroundColor: 'transparent',
						padding: '1',
						color: 'fg.muted',
						_hover: { backgroundColor: 'bg.hover', color: 'fg.primary' }
					})}
					onclick={() => (expanded = false)}
				>
					<X size={14} />
				</button>
			</div>

			<div class={css({ maxHeight: '18.75rem', overflowY: 'auto' })}>
				{#if enginesStore.count === 0}
					{#if enginesStore.loading}
						<div
							class={css({
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
								gap: '2',
								padding: '6',
								textAlign: 'center',
								fontSize: 'sm',
								color: 'fg.muted'
							})}
						>
							<LoaderCircle size={16} class={css({ animation: 'spin 1s linear infinite' })} />
							<span>Loading...</span>
						</div>
					{:else}
						<div
							class={css({ padding: '6', textAlign: 'center', fontSize: 'sm', color: 'fg.muted' })}
						>
							<span>No active engines</span>
						</div>
					{/if}
				{:else}
					<ul class={css({ margin: '0', listStyle: 'none', padding: '0' })}>
						{#each enginesStore.engines as engine (engine.analysis_id)}
							<li
								class={css({
									display: 'flex',
									alignItems: 'center',
									gap: '3',
									borderBottomWidth: '1px',
									borderBottomStyle: 'solid',
									borderBottomColor: 'border.tertiary',
									padding: '3'
								})}
							>
								<div class={css({ minWidth: '0', flex: '1' })}>
									<div class={css({ display: 'flex', alignItems: 'center', gap: '2' })}>
										<span
											class={css({
												fontFamily: 'var(--font-mono)',
												fontSize: 'xs',
												color: 'fg.primary'
											})}
											title={engine.analysis_id}
										>
											{engine.analysis_id.slice(0, 8)}...
										</span>
										<span
											class={css({
												paddingX: '2',
												paddingY: 'px',
												fontSize: 'xs',
												fontWeight: 'medium',
												textTransform: 'uppercase',
												backgroundColor: engine.status === 'healthy' ? 'accent.bg' : 'bg.tertiary',
												color: engine.status === 'healthy' ? 'accent.primary' : 'fg.muted'
											})}
										>
											{engine.status}
										</span>
									</div>
									<div
										class={css({ marginTop: '1', display: 'flex', alignItems: 'center', gap: '2' })}
									>
										{#if engine.current_job_id}
											<span
												class={css({
													fontFamily: 'var(--font-mono)',
													fontSize: 'xs',
													color: 'accent.primary'
												})}
											>
												Job: {engine.current_job_id.slice(0, 6)}
											</span>
										{/if}
										<span class={css({ fontSize: 'xs', color: 'fg.muted' })}>
											{formatTime(engine.last_activity)}
										</span>
									</div>
								</div>
								<button
									class={css({
										display: 'flex',
										cursor: 'pointer',
										alignItems: 'center',
										justifyContent: 'center',
										borderWidth: '1px',
										borderStyle: 'solid',
										borderColor: 'border.tertiary',
										padding: '1',
										backgroundColor: 'transparent',
										color: 'fg.muted',
										_hover: {
											backgroundColor: 'error',
											borderColor: 'border.error',
											color: 'error.fg'
										},
										_disabled: { cursor: 'not-allowed', opacity: 0.5 }
									})}
									onclick={() => handleKill(engine.analysis_id)}
									disabled={killing === engine.analysis_id}
									title="Shutdown engine"
								>
									{#if killing === engine.analysis_id}
										<LoaderCircle size={12} class={css({ animation: 'spin 1s linear infinite' })} />
									{:else}
										<X size={12} />
									{/if}
								</button>
							</li>
						{/each}
					</ul>
				{/if}
			</div>

			{#if enginesStore.error}
				<div
					class={css({
						borderTopWidth: '1px',
						borderTopStyle: 'solid',
						borderTopColor: 'border.error',
						padding: '2',
						fontSize: 'xs',
						backgroundColor: 'error',
						color: 'error.fg'
					})}
				>
					{enginesStore.error}
				</div>
			{/if}
		</div>
	{/if}
</div>

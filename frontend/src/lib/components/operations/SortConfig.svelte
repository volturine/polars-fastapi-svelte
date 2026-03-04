<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import { X, Plus, ArrowUp, ArrowDown } from 'lucide-svelte';
	import ColumnDropdown from '$lib/components/common/ColumnDropdown.svelte';
	import { css } from '$lib/styles/panda';

	const uid = $props.id();

	interface Props {
		schema: Schema;
		config?: { columns: string[]; descending: boolean[] };
	}

	let { schema, config = $bindable({ columns: [], descending: [] }) }: Props = $props();

	const safeConfig = $derived({
		columns: config?.columns ?? [],
		descending: config?.descending ?? []
	});

	let newColumn = $state('');
	let newDescending = $state(false);

	function addSortRule() {
		if (!newColumn) return;
		if (safeConfig.columns.includes(newColumn)) return;
		config = {
			columns: [...safeConfig.columns, newColumn],
			descending: [...safeConfig.descending, newDescending]
		};
		newColumn = '';
		newDescending = false;
	}

	function removeSortRule(index: number) {
		config = {
			columns: safeConfig.columns.filter((_, i) => i !== index),
			descending: safeConfig.descending.filter((_, i) => i !== index)
		};
	}

	function setDirection(index: number, descending: boolean) {
		config = {
			...safeConfig,
			descending: safeConfig.descending.map((d, i) => (i === index ? descending : d))
		};
	}

	const availableColumns = $derived(
		schema.columns.filter((col) => !safeConfig.columns.includes(col.name))
	);
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Sort configuration"
>
	<div
		class={css({
			display: 'flex',
			gap: '2',
			alignItems: 'center',
			marginBottom: '8',
			flexWrap: 'wrap'
		})}
		role="group"
		aria-label="Add sort rule form"
	>
		<div class={css({ flex: '2', minWidth: '50' })}>
			<span
				class={css({
					position: 'absolute',
					width: '1px',
					height: '1px',
					padding: '0',
					margin: '-1px',
					overflow: 'hidden',
					clip: 'rect(0, 0, 0, 0)',
					whiteSpace: 'nowrap',
					border: '0'
				})}>Select column to sort</span
			>
			<ColumnDropdown
				{schema}
				value={newColumn}
				onChange={(val) => (newColumn = val)}
				placeholder="Select column..."
				filter={(col) => availableColumns.some((c) => c.name === col.name)}
			/>
		</div>

		<div
			class={css({
				display: 'flex',
				gap: '1px',
				backgroundColor: 'border.primary',
				padding: '1px'
			})}
			role="group"
			aria-label="Sort direction"
		>
			<button
				id="{uid}-ascending"
				data-testid="sort-ascending-button"
				type="button"
				class={!newDescending
					? css({
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							width: '8',
							height: '8',
							padding: '0',
							cursor: 'pointer',
							borderWidth: '1px',
							borderStyle: 'solid',
							borderColor: 'border.primary',
							borderRadius: 'sm 0 0 sm',
							backgroundColor: 'accent.bg',
							color: 'accent.primary',
							boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
							position: 'relative',
							zIndex: '1'
						})
					: css({
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							width: '8',
							height: '8',
							padding: '0',
							cursor: 'pointer',
							borderWidth: '1px',
							borderStyle: 'solid',
							borderColor: 'border.primary',
							borderRadius: 'sm 0 0 sm',
							backgroundColor: 'bg.tertiary',
							color: 'fg.secondary',
							_hover: { backgroundColor: 'bg.secondary', color: 'fg.primary' }
						})}
				onclick={() => (newDescending = false)}
				title="Ascending"
				aria-pressed={!newDescending}
				aria-label="Sort ascending"
			>
				<ArrowUp size={14} aria-hidden="true" />
			</button>
			<button
				id="{uid}-descending"
				data-testid="sort-descending-button"
				type="button"
				class={newDescending
					? css({
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							width: '8',
							height: '8',
							padding: '0',
							cursor: 'pointer',
							borderWidth: '1px',
							borderStyle: 'solid',
							borderColor: 'border.primary',
							borderRadius: '0 sm sm 0',
							backgroundColor: 'accent.bg',
							color: 'accent.primary',
							boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
							position: 'relative',
							zIndex: '1'
						})
					: css({
							display: 'flex',
							alignItems: 'center',
							justifyContent: 'center',
							width: '8',
							height: '8',
							padding: '0',
							cursor: 'pointer',
							borderWidth: '1px',
							borderStyle: 'solid',
							borderColor: 'border.primary',
							borderRadius: '0 sm sm 0',
							backgroundColor: 'bg.tertiary',
							color: 'fg.secondary',
							_hover: { backgroundColor: 'bg.secondary', color: 'fg.primary' }
						})}
				onclick={() => (newDescending = true)}
				title="Descending"
				aria-pressed={newDescending}
				aria-label="Sort descending"
			>
				<ArrowDown size={14} aria-hidden="true" />
			</button>
		</div>

		<button
			id="{uid}-add"
			data-testid="sort-add-button"
			type="button"
			class={css({
				display: 'flex',
				alignItems: 'center',
				gap: '1',
				paddingY: '2',
				paddingX: '4',
				border: 'none',
				cursor: 'pointer',
				whiteSpace: 'nowrap',
				backgroundColor: 'accent.bg',
				color: 'accent.primary',
				_disabled: { backgroundColor: 'border.tertiary', cursor: 'not-allowed', color: 'fg.muted' }
			})}
			onclick={addSortRule}
			disabled={!newColumn}
			aria-label="Add sort rule"
		>
			<Plus size={16} aria-hidden="true" />
			Add
		</button>
	</div>

	{#if safeConfig.columns.length > 0}
		<div id="sort-rules-list" role="region" aria-labelledby="sort-order-heading">
			<h4
				id="sort-order-heading"
				class={css({
					marginTop: '0',
					marginBottom: '3',
					fontSize: '0.6875rem',
					fontWeight: '600',
					color: 'fg.muted',
					textTransform: 'uppercase',
					letterSpacing: '0.08em'
				})}
			>
				Sort Order
			</h4>
			{#each safeConfig.columns as column, i (column)}
				<div
					class={css({
						display: 'flex',
						justifyContent: 'space-between',
						alignItems: 'center',
						paddingY: '2',
						borderBottomWidth: '1px',
						borderBottomStyle: 'solid',
						borderBottomColor: 'border.tertiary',
						'&:last-child': { borderBottomWidth: '0' }
					})}
					role="group"
					aria-label={`Sort rule ${i + 1}: ${column}`}
				>
					<span class={css({ fontWeight: 'medium' })}>{column}</span>

					<div
						class={css({
							display: 'flex',
							alignItems: 'center',
							gap: '1px',
							backgroundColor: 'border.primary',
							padding: '1px'
						})}
						role="group"
						aria-label={`Sort direction for ${column}`}
					>
						<button
							id={`sort-btn-asc-${i}`}
							data-testid={`sort-ascending-rule-${i}`}
							type="button"
							class={!safeConfig.descending[i]
								? css({
										display: 'flex',
										alignItems: 'center',
										justifyContent: 'center',
										width: '7',
										height: '7',
										padding: '0',
										cursor: 'pointer',
										borderWidth: '1px',
										borderStyle: 'solid',
										borderColor: 'border.primary',
										borderRadius: 'sm 0 0 sm',
										backgroundColor: 'accent.bg',
										color: 'accent.primary',
										boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
										position: 'relative',
										zIndex: '1'
									})
								: css({
										display: 'flex',
										alignItems: 'center',
										justifyContent: 'center',
										width: '7',
										height: '7',
										padding: '0',
										cursor: 'pointer',
										borderWidth: '1px',
										borderStyle: 'solid',
										borderColor: 'border.primary',
										borderRadius: 'sm 0 0 sm',
										backgroundColor: 'bg.tertiary',
										color: 'fg.secondary',
										_hover: { backgroundColor: 'bg.tertiary', color: 'fg.primary' }
									})}
							onclick={() => setDirection(i, false)}
							title="Ascending"
							aria-pressed={!safeConfig.descending[i]}
							aria-label={`Sort ${column} ascending`}
						>
							<ArrowUp size={12} aria-hidden="true" />
						</button>
						<button
							id={`sort-btn-desc-${i}`}
							data-testid={`sort-descending-rule-${i}`}
							type="button"
							class={safeConfig.descending[i]
								? css({
										display: 'flex',
										alignItems: 'center',
										justifyContent: 'center',
										width: '7',
										height: '7',
										padding: '0',
										cursor: 'pointer',
										borderWidth: '1px',
										borderStyle: 'solid',
										borderColor: 'border.primary',
										borderRadius: '0 sm sm 0',
										backgroundColor: 'accent.bg',
										color: 'accent.primary',
										boxShadow: 'inset 0 0 0 1px var(--accent-primary)',
										position: 'relative',
										zIndex: '1'
									})
								: css({
										display: 'flex',
										alignItems: 'center',
										justifyContent: 'center',
										width: '7',
										height: '7',
										padding: '0',
										cursor: 'pointer',
										borderWidth: '1px',
										borderStyle: 'solid',
										borderColor: 'border.primary',
										borderRadius: '0 sm sm 0',
										backgroundColor: 'bg.tertiary',
										color: 'fg.secondary',
										_hover: { backgroundColor: 'bg.tertiary', color: 'fg.primary' }
									})}
							onclick={() => setDirection(i, true)}
							title="Descending"
							aria-pressed={safeConfig.descending[i]}
							aria-label={`Sort ${column} descending`}
						>
							<ArrowDown size={12} aria-hidden="true" />
						</button>
						<button
							id={`sort-btn-remove-${i}`}
							data-testid={`sort-remove-rule-${i}`}
							type="button"
							class={css({
								display: 'flex',
								alignItems: 'center',
								justifyContent: 'center',
								width: '7',
								height: '7',
								padding: '0',
								backgroundColor: 'transparent',
								cursor: 'pointer',
								color: 'fg.secondary',
								borderWidth: '1px',
								borderStyle: 'solid',
								borderColor: 'border.transparent',
								_hover: {
									backgroundColor: 'error.bg!',
									color: 'error.fg!',
									borderColor: 'error.border!'
								}
							})}
							onclick={() => removeSortRule(i)}
							title="Remove"
							aria-label={`Remove sort rule for ${column}`}
						>
							<X size={14} aria-hidden="true" />
						</button>
					</div>
				</div>
			{/each}
		</div>
	{:else}
		<p
			id="sort-empty-state"
			class={css({ paddingY: '8', textAlign: 'center', fontSize: 'xs', color: 'fg.muted' })}
			role="status"
		>
			No sort rules configured. Add a column to sort by.
		</p>
	{/if}
</div>

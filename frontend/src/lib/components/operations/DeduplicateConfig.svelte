<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import { css, cx } from '$lib/styles/panda';

	interface DeduplicateConfigData {
		subset: string[] | null;
		keep: string;
	}

	interface Props {
		schema: Schema;
		config?: DeduplicateConfigData;
	}

	let { schema, config = $bindable({ subset: null, keep: 'first' }) }: Props = $props();

	const keepStrategies = [
		{ value: 'first', label: 'Keep First' },
		{ value: 'last', label: 'Keep Last' },
		{ value: 'none', label: 'Keep None' }
	];
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Deduplicate configuration"
>
	<div
		class={css({
			marginBottom: '0',
			padding: '0 0 1.25rem 0',
			backgroundColor: 'transparent',
			borderRadius: '0',
			border: 'none'
		})}
		role="radiogroup"
		aria-labelledby="keep-strategy-heading"
	>
		<h4
			id="keep-strategy-heading"
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
			Keep Strategy
		</h4>
		<div class={css({ display: 'flex', flexDirection: 'column', gap: '1' })}>
			{#each keepStrategies as strategy (strategy.value)}
				<label
					class={css({
						display: 'flex',
						cursor: 'pointer',
						alignItems: 'center',
						gap: '3',
						paddingY: '2',
						_hover: { color: 'fg.primary' }
					})}
				>
					<input
						type="radio"
						name="keep-strategy"
						bind:group={config.keep}
						value={strategy.value}
						class={css({ marginRight: '2', cursor: 'pointer' })}
					/>
					<span>{strategy.label}</span>
				</label>
			{/each}
		</div>
	</div>

	<div
		class={cx(
			css({
				marginBottom: '0',
				padding: '0 0 1.25rem 0',
				backgroundColor: 'transparent',
				borderRadius: '0',
				border: 'none'
			}),
			css({ paddingTop: '1.25rem', borderTop: '1px solid var(--color-border-tertiary)' })
		)}
		role="group"
		aria-labelledby="column-subset-heading"
	>
		<h4
			id="column-subset-heading"
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
			Column Subset
		</h4>
		<div
			class={css({
				display: 'block',
				fontSize: '0.6875rem',
				fontWeight: '600',
				color: 'fg.muted',
				marginBottom: '1.5',
				textTransform: 'uppercase',
				letterSpacing: '0.05em'
			})}
		>
			Columns to check for duplicates
		</div>
		<MultiSelectColumnDropdown
			{schema}
			value={config.subset ?? []}
			onChange={(val) => (config.subset = val.length > 0 ? val : null)}
			placeholder="Select columns..."
		/>

		{#if config.subset && config.subset.length > 0}
			<div
				class={css({
					padding: '0.625rem 0.75rem',
					border: 'none',
					borderLeft: '2px solid',
					borderRadius: '0',
					marginTop: '2',
					marginBottom: '0',
					fontSize: '0.75rem',
					lineHeight: '1.5',
					backgroundColor: 'transparent',
					borderLeftColor: 'accent.secondary',
					color: 'fg.tertiary'
				})}
				aria-live="polite"
			>
				Checking {config.subset.length} column{config.subset.length !== 1 ? 's' : ''} for duplicates
			</div>
		{:else}
			<div
				class={css({
					padding: '0.625rem 0.75rem',
					border: 'none',
					borderLeft: '2px solid',
					borderRadius: '0',
					marginTop: '2',
					marginBottom: '0',
					fontSize: '0.75rem',
					lineHeight: '1.5',
					backgroundColor: 'transparent',
					borderLeftColor: 'accent.secondary',
					color: 'fg.tertiary'
				})}
			>
				No columns selected - will check all columns for duplicates
			</div>
		{/if}
	</div>
</div>

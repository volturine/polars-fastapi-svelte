<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import ColumnTypeDropdown from '$lib/components/common/ColumnTypeDropdown.svelte';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import { css, cx } from '$lib/styles/panda';

	interface FillNullConfigData {
		strategy: string;
		columns: string[] | null;
		value?: string | number;
		value_type?: string;
	}

	interface Props {
		schema: Schema;
		config?: FillNullConfigData;
	}

	let {
		schema,
		config = $bindable({ strategy: 'literal', columns: null, value: '', value_type: 'Utf8' })
	}: Props = $props();

	const strategies = [
		{ value: 'literal', label: 'Fill with Value', needsValue: true, needsColumns: true },
		{ value: 'forward', label: 'Forward Fill', needsValue: false, needsColumns: true },
		{ value: 'backward', label: 'Backward Fill', needsValue: false, needsColumns: true },
		{ value: 'mean', label: 'Fill with Mean', needsValue: false, needsColumns: true },
		{ value: 'median', label: 'Fill with Median', needsValue: false, needsColumns: true },
		{ value: 'drop_rows', label: 'Drop Rows with Nulls', needsValue: false, needsColumns: true }
	];

	const currentStrategy = $derived(strategies.find((s) => s.value === config.strategy));
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Fill null configuration"
>
	<div
		class={css({
			marginBottom: '0',
			padding: '0 0 1.25rem 0',
			backgroundColor: 'transparent',
			borderRadius: '0',
			border: 'none'
		})}
		role="group"
		aria-labelledby="fill-strategy-heading"
	>
		<h4
			id="fill-strategy-heading"
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
			Fill Strategy
		</h4>
		<label
			for="fill-select-strategy"
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
			})}>Select fill strategy</label
		>
		<select
			id="fill-select-strategy"
			data-testid="fill-strategy-select"
			bind:value={config.strategy}
			class={css({ marginBottom: '2', width: 'full' })}
		>
			{#each strategies as strategy (strategy.value)}
				<option value={strategy.value}>{strategy.label}</option>
			{/each}
		</select>
	</div>

	{#if currentStrategy?.needsValue}
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
			aria-labelledby="fill-value-heading"
		>
			<h4
				id="fill-value-heading"
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
				Fill Value
			</h4>
			<label
				for="fill-input-value"
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
				})}>Fill value</label
			>
			<input
				id="fill-value"
				type="text"
				bind:value={config.value}
				placeholder="Enter value (e.g., 0, N/A)"
				class={css({ marginBottom: '2', width: 'full' })}
			/>
			<ColumnTypeDropdown
				value={config.value_type ?? 'Utf8'}
				onChange={(val) => (config.value_type = val)}
				placeholder="Select type..."
			/>
		</div>
	{/if}

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
		aria-labelledby="target-columns-heading"
	>
		<h4
			id="target-columns-heading"
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
			Target Columns
		</h4>
		<MultiSelectColumnDropdown
			{schema}
			value={config.columns ?? []}
			onChange={(val) => (config.columns = val)}
			showSelectAll={true}
			placeholder="Select target columns..."
		/>

		{#if !config.columns || config.columns.length === 0}
			<div
				id="fill-no-columns-info"
				class={css({
					padding: '0.625rem 0.75rem',
					border: 'none',
					borderLeft: '2px solid',
					borderRadius: '0',
					marginTop: '0.75rem',
					marginBottom: '0',
					fontSize: '0.75rem',
					lineHeight: '1.5',
					backgroundColor: 'transparent',
					borderLeftColor: 'accent.secondary',
					color: 'fg.tertiary'
				})}
			>
				No columns selected - will apply to all columns
			</div>
		{/if}
	</div>
</div>

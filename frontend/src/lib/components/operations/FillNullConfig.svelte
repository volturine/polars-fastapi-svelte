<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import ColumnTypeDropdown from '$lib/components/common/ColumnTypeDropdown.svelte';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import SectionHeader from '$lib/components/ui/SectionHeader.svelte';
	import Callout from '$lib/components/ui/Callout.svelte';
	import { css, cx, stepConfig, divider } from '$lib/styles/panda';

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

<div class={stepConfig()} role="region" aria-label="Fill null configuration">
	<div
		class={css({
			marginBottom: '0',
			paddingBottom: '5',
			backgroundColor: 'transparent',

			border: 'none'
		})}
		role="group"
		aria-labelledby="fill-strategy-heading"
	>
		<span id="fill-strategy-heading"><SectionHeader>Fill Strategy</SectionHeader></span>
		<label
			for="fill-select-strategy"
			class={css({
				position: 'absolute',
				width: 'px',
				height: 'px',
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
					paddingBottom: '5',
					backgroundColor: 'transparent',

					border: 'none'
				}),
				cx(
					divider,
					css({
						paddingTop: '5'
					})
				)
			)}
			role="group"
			aria-labelledby="fill-value-heading"
		>
			<span id="fill-value-heading"><SectionHeader>Fill Value</SectionHeader></span>
			<label
				for="fill-input-value"
				class={css({
					position: 'absolute',
					width: 'px',
					height: 'px',
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
				paddingBottom: '5',
				backgroundColor: 'transparent',

				border: 'none'
			}),
			cx(
				divider,
				css({
					paddingTop: '5'
				})
			)
		)}
		role="group"
		aria-labelledby="target-columns-heading"
	>
		<span id="target-columns-heading"><SectionHeader>Target Columns</SectionHeader></span>
		<MultiSelectColumnDropdown
			{schema}
			value={config.columns ?? []}
			onChange={(val) => (config.columns = val)}
			showSelectAll={true}
			placeholder="Select target columns..."
		/>

		{#if !config.columns || config.columns.length === 0}
			<Callout>No columns selected - will apply to all columns</Callout>
		{/if}
	</div>
</div>

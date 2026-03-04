<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import ColumnDropdown from '$lib/components/common/ColumnDropdown.svelte';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import SectionHeader from '$lib/components/ui/SectionHeader.svelte';
	import { css } from '$lib/styles/panda';

	const uid = $props.id();

	interface Aggregation {
		column: string;
		function: string;
		alias: string;
	}

	interface GroupByConfigData {
		groupBy: string[];
		aggregations: Aggregation[];
	}

	interface Props {
		schema: Schema;
		config?: GroupByConfigData;
	}

	let { schema, config = $bindable({ groupBy: [], aggregations: [] }) }: Props = $props();

	const safeAggregations = $derived(config.aggregations ?? []);

	let newAggregation = $state<Aggregation>({
		column: '',
		function: 'sum',
		alias: ''
	});

	const aggregationFunctions = [
		'sum',
		'mean',
		'count',
		'min',
		'max',
		'first',
		'last',
		'median',
		'std',
		'collect_list',
		'collect_set'
	];

	function addAggregation() {
		if (!newAggregation.column) return;

		const alias = newAggregation.alias || `${newAggregation.column}_${newAggregation.function}`;

		config.aggregations = [
			...safeAggregations,
			{
				column: newAggregation.column,
				function: newAggregation.function,
				alias
			}
		];

		newAggregation = {
			column: '',
			function: 'sum',
			alias: ''
		};
	}

	function removeAggregation(index: number) {
		config.aggregations = safeAggregations.filter((_, i) => i !== index);
	}
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Group by configuration"
>
	<div
		class={css({
			marginBottom: '0',
			paddingBottom: '5',
			backgroundColor: 'transparent',
			borderRadius: '0',
			border: 'none'
		})}
		role="group"
		aria-labelledby="{uid}-columns-heading"
	>
		<span id="{uid}-columns-heading"><SectionHeader>Group By Columns</SectionHeader></span>
		<MultiSelectColumnDropdown
			{schema}
			value={config.groupBy ?? []}
			onChange={(val) => (config.groupBy = val)}
			showSelectAll={false}
			placeholder="Select group by columns..."
		/>
	</div>

	<div
		class={css({
			marginBottom: '0',
			paddingBottom: '5',
			backgroundColor: 'transparent',
			borderRadius: '0',
			border: 'none',
			paddingTop: '5',
			borderTopWidth: '1',
			borderTopStyle: 'solid',
			borderTopColor: 'border.tertiary'
		})}
		role="group"
		aria-labelledby="{uid}-agg-heading"
	>
		<span id="{uid}-agg-heading"><SectionHeader>Aggregations</SectionHeader></span>

		<div
			class={css({ display: 'flex', flexWrap: 'wrap', gap: '2', marginBottom: '5' })}
			role="group"
			aria-label="Add aggregation form"
		>
			<div class={css({ flex: '2', minWidth: '40' })}>
				<ColumnDropdown
					{schema}
					value={newAggregation.column}
					onChange={(val) => (newAggregation.column = val)}
					placeholder="Select column..."
				/>
			</div>

			<label
				for="{uid}-agg-function"
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
				})}>Aggregation function</label
			>
			<select
				id="{uid}-agg-function"
				data-testid="agg-function-select"
				class={css({ flex: '1', minWidth: '30' })}
				bind:value={newAggregation.function}
			>
				{#each aggregationFunctions as func (func)}
					<option value={func}>{func}</option>
				{/each}
			</select>

			<input
				id="{uid}-agg-alias"
				type="text"
				class={css({ flex: '2', minWidth: '40' })}
				bind:value={newAggregation.alias}
				placeholder="Alias (optional)"
			/>

			<button
				id="{uid}-agg-add"
				data-testid="agg-add-button"
				type="button"
				class={css({
					backgroundColor: 'accent.primary',
					color: 'bg.primary',
					border: '1px solid',
					borderColor: 'accent.secondary',
					paddingX: '4',
					paddingY: '2',
					cursor: 'pointer',
					_hover: { opacity: '0.9' },
					_disabled: {
						backgroundColor: 'bg.muted',
						color: 'fg.muted',
						borderColor: 'border.tertiary',
						cursor: 'not-allowed'
					}
				})}
				onclick={addAggregation}
				disabled={!newAggregation.column}
				aria-label="Add aggregation"
			>
				Add
			</button>
		</div>

		{#if safeAggregations.length > 0}
			<div
				id="aggregations-list"
				class={css({ display: 'flex', flexDirection: 'column', gap: '3' })}
				role="list"
				aria-label="Configured aggregations"
			>
				{#each safeAggregations as agg, i (i)}
					<div
						class={css({
							backgroundColor: 'transparent',
							border: 'none',
							borderBottom: '1px solid',
							borderBottomColor: 'border.tertiary',
							display: 'flex',
							justifyContent: 'space-between',
							alignItems: 'center',
							padding: '3',
							_last: { borderBottom: 'none' }
						})}
						role="listitem"
					>
						<span class={css({ fontSize: 'sm', fontFamily: 'mono', color: 'fg.primary' })}>
							{agg.function}({agg.column}) as {agg.alias}
						</span>
						<button
							id={`agg-btn-remove-${i}`}
							data-testid={`agg-remove-button-${i}`}
							type="button"
							class={css({
								backgroundColor: 'error.bg',
								color: 'error.fg',
								border: '1px solid',
								borderColor: 'error.border'
							})}
							onclick={() => removeAggregation(i)}
							aria-label={`Remove aggregation ${agg.alias}`}
						>
							Remove
						</button>
					</div>
				{/each}
			</div>
		{/if}
	</div>
</div>

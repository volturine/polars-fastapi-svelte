<script lang="ts">
	import ColumnTypeBadge from '$lib/components/common/ColumnTypeBadge.svelte';
	import SearchableDropdown from '$lib/components/ui/SearchableDropdown.svelte';
	import { css, cx } from '$lib/styles/panda';
	import { getAllColumnTypes } from '$lib/utils/columnTypes';

	interface ColumnTypeOption {
		id: string;
		label: string;
		type: string;
		description?: string;
	}

	interface Props {
		value: string;
		onChange: (value: string) => void;
		placeholder?: string;
		disabled?: boolean;
	}

	let {
		value = $bindable(),
		onChange,
		placeholder = 'Select type...',
		disabled = false
	}: Props = $props();

	const allColumnTypes = getAllColumnTypes();
	const options = $derived(
		allColumnTypes.map((entry) => ({
			id: entry.type,
			label: entry.label,
			type: entry.type,
			description: entry.description
		}))
	);
</script>

<SearchableDropdown
	{options}
	{value}
	onChange={(next) => onChange(next as string)}
	{placeholder}
	searchPlaceholder="Search types..."
	{disabled}
	{renderOption}
/>

{#snippet renderOption(payload: {
	option: { id: string; label: string };
	selected: boolean;
	onSelect: () => void;
})}
	{@const item = payload.option as ColumnTypeOption}
	<button
		type="button"
		class={cx(
			css({
				minWidth: '0',
				width: '100%',
				padding: '0.5rem 0.75rem',
				borderWidth: '1px',
				borderStyle: 'solid',
				borderColor: 'transparent',
				background: 'transparent',
				textAlign: 'left',
				display: 'flex',
				alignItems: 'center',
				justifyContent: 'flex-start',
				gap: '2',
				cursor: 'pointer',
				color: 'fg.primary',
				fontSize: 'sm',
				'& span': { minWidth: '0', overflowWrap: 'anywhere' },
				_hover: { backgroundColor: 'bg.hover', borderColor: 'border.primary' }
			}),
			css({ minWidth: 'auto', padding: '2', justifyContent: 'center' }),
			payload.selected && css({ backgroundColor: 'bg.hover', borderColor: 'border.primary' })
		)}
		onclick={payload.onSelect}
		role="option"
		aria-selected={payload.selected}
		title={item.description}
	>
		<ColumnTypeBadge columnType={item.type} size="sm" />
	</button>
{/snippet}

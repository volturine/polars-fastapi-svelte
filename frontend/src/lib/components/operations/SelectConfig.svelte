<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import SectionHeader from '$lib/components/ui/SectionHeader.svelte';
	import Callout from '$lib/components/ui/Callout.svelte';
	import { css } from '$lib/styles/panda';

	interface SelectConfigData {
		columns: string[];
	}

	interface Props {
		schema: Schema;
		config?: SelectConfigData;
	}

	let { schema, config = $bindable({ columns: [] }) }: Props = $props();

	const safeColumns = $derived(Array.isArray(config.columns) ? config.columns : []);
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
	role="region"
	aria-label="Select columns configuration"
>
	<div class={css({ marginBottom: '0', paddingBottom: '5' })}>
		<SectionHeader>Columns to keep</SectionHeader>
		<div class={css({ marginTop: '1.5' })}>
			<MultiSelectColumnDropdown
				{schema}
				value={safeColumns}
				onChange={(val) => (config.columns = val)}
				placeholder="Select columns to keep..."
			/>
		</div>
	</div>

	{#if safeColumns.length > 0}
		<Callout tone="info">
			<strong>Selected {safeColumns.length} column{safeColumns.length !== 1 ? 's' : ''}</strong>
		</Callout>
	{/if}
</div>

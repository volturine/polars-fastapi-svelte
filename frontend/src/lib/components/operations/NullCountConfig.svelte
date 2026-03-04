<script lang="ts">
	import { css } from '$lib/styles/panda';

	interface Props {
		config?: Record<string, never>;
	}

	let { config = $bindable({} as Record<string, never>) }: Props = $props();
	void config;
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
>
	<h3 class={css({ marginBottom: '2' })}>Null Count</h3>
	<p
		class={css({
			marginTop: '0',
			marginBottom: '2',
			color: 'fg.tertiary',
			fontSize: 'xs',
			lineHeight: '1.6'
		})}
	>
		Count null values for each column in the dataset.
	</p>
	<p
		class={css({
			padding: '0.625rem 0.75rem',
			border: 'none',
			borderLeft: '2px solid',
			borderLeftColor: 'accent.secondary',
			borderRadius: '0',
			marginTop: '0.75rem',
			marginBottom: '0',
			fontSize: '0.75rem',
			lineHeight: '1.5',
			backgroundColor: 'transparent',
			color: 'fg.tertiary'
		})}
	>
		This operation will return a single row with the count of null values for each column.
	</p>
</div>

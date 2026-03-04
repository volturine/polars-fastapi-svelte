<script lang="ts">
	import { toggleButton } from '$lib/styles/panda';
	import type { Snippet } from 'svelte';

	interface Props {
		active?: boolean;
		radius?: 'left' | 'right' | 'none';
		onclick: () => void;
		children: Snippet;
		ariaPressed?: boolean;
		ariaLabel?: string;
	}

	let {
		active = false,
		radius = 'none',
		onclick,
		children,
		ariaPressed,
		ariaLabel
	}: Props = $props();
</script>

<button
	type="button"
	class={toggleButton({ active, radius })}
	{onclick}
	aria-pressed={ariaPressed ?? active}
	aria-label={ariaLabel}
>
	{@render children()}
</button>

<script lang="ts">
	import { getColumnTypeConfig } from '$lib/utils/columnTypes';
	import { css } from '$lib/styles/panda';

	interface Props {
		columnType: string;
		size?: 'xs' | 'sm' | 'md';
		showIcon?: boolean;
		showLabel?: boolean;
		variant?: 'default' | 'subtle' | 'compact';
	}

	let {
		columnType,
		size = 'sm',
		showIcon = true,
		showLabel = true,
		variant = 'default'
	}: Props = $props();

	const config = $derived(getColumnTypeConfig(columnType));
	const iconSize = $derived(size === 'xs' ? 11 : size === 'md' ? 14 : 12);
	const labelVisible = $derived(showLabel && variant !== 'compact');

	const sizes: Record<string, Record<string, string>> = {
		xs: { padding: '2px 6px', fontSize: '0.6875rem', gap: '3px' },
		sm: { padding: '3px 8px', fontSize: '0.75rem', gap: '4px' },
		md: { padding: '4px 10px', fontSize: '0.875rem', gap: '5px' }
	};

	const variants: Record<string, Record<string, string>> = {
		default: {},
		subtle: { backgroundColor: 'transparent' },
		compact: { padding: '2px 4px', gap: '0' }
	};
</script>

<span
	class={css({
		display: 'inline-flex',
		alignItems: 'center',
		fontFamily: 'var(--font-mono, monospace)',
		fontWeight: '600',
		whiteSpace: 'nowrap',
		lineHeight: '1',
		userSelect: 'none',
		transitionProperty: 'opacity',
		transitionDuration: '160ms',
		color: 'accent.primary',
		borderWidth: '1px',
		borderStyle: 'solid',
		borderColor: 'accent.secondary',
		backgroundColor: 'accent.bg',
		_hover: { opacity: '0.9' },
		...sizes[size],
		...variants[variant]
	})}
	title={config.description}
>
	{#if showIcon}
		{@const IconComponent = config.icon}
		<IconComponent size={iconSize} strokeWidth={2.5} />
	{/if}
	{#if labelVisible}
		<span>{config.label}</span>
	{/if}
</span>

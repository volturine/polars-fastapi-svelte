<script lang="ts">
	import { getColumnTypeConfig, type ColumnTypeCategory } from '$lib/utils/columnTypes';

	interface Props {
		columnType: string;
		size?: 'xs' | 'sm' | 'md';
		showIcon?: boolean;
		variant?: 'default' | 'subtle';
	}

	let { columnType, size = 'sm', showIcon = true, variant = 'default' }: Props = $props();

	const config = $derived(getColumnTypeConfig(columnType));

	const categoryClass = $derived(getCategoryClass(config.category));
	const sizeClass = $derived(`size-${size}`);
	const variantClass = $derived(`variant-${variant}`);
	const iconSize = $derived(size === 'xs' ? 11 : size === 'md' ? 14 : 12);

	function getCategoryClass(category: ColumnTypeCategory): string {
		return `category-${category}`;
	}
</script>

<span
	class="type-badge {categoryClass} {sizeClass} {variantClass}"
	title={config.description}
>
	{#if showIcon}
		{@const IconComponent = config.icon}
		<IconComponent size={iconSize} strokeWidth={2.5} />
	{/if}
	<span>{config.label}</span>
</span>

<style>
	.type-badge {
		display: inline-flex;
		align-items: center;
		font-family: var(--font-mono, monospace);
		font-weight: 600;
		white-space: nowrap;
		line-height: 1;
		user-select: none;
		transition: all 160ms ease;
	}

	.type-badge:hover {
		opacity: 0.9;
	}

	/* Size classes */
	.size-xs {
		padding: 2px 6px;
		font-size: 0.6875rem;
		gap: 3px;
	}

	.size-sm {
		padding: 3px 8px;
		font-size: 0.75rem;
		gap: 4px;
	}

	.size-md {
		padding: 4px 10px;
		font-size: 0.875rem;
		gap: 5px;
	}

	/* Category colors - default variant */
	.category-string {
		color: var(--type-string-fg);
		border: 1px solid var(--type-string-border);
		background-color: var(--type-string-bg);
	}

	.category-integer {
		color: var(--type-integer-fg);
		border: 1px solid var(--type-integer-border);
		background-color: var(--type-integer-bg);
	}

	.category-float {
		color: var(--type-float-fg);
		border: 1px solid var(--type-float-border);
		background-color: var(--type-float-bg);
	}

	.category-temporal {
		color: var(--type-temporal-fg);
		border: 1px solid var(--type-temporal-border);
		background-color: var(--type-temporal-bg);
	}

	.category-boolean {
		color: var(--type-boolean-fg);
		border: 1px solid var(--type-boolean-border);
		background-color: var(--type-boolean-bg);
	}

	.category-complex {
		color: var(--type-complex-fg);
		border: 1px solid var(--type-complex-border);
		background-color: var(--type-complex-bg);
	}

	.category-other {
		color: var(--type-other-fg);
		border: 1px solid var(--type-other-border);
		background-color: var(--type-other-bg);
	}

	/* Subtle variant overrides */
	.variant-subtle {
		background-color: var(--color-transparent);
	}
</style>

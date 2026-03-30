<script lang="ts">
	import { PanelLeftClose, PanelLeftOpen, PanelRightClose, PanelRightOpen } from 'lucide-svelte';
	import { css } from '$lib/styles/panda';
	import type { Snippet } from 'svelte';

	interface Props {
		title: string;
		width?: string;
		collapsible?: boolean;
		collapsed?: boolean;
		position?: 'left' | 'right';
		children: Snippet;
	}

	let {
		title,
		width = '320px',
		collapsible = true,
		collapsed = $bindable(false),
		position = 'left',
		children
	}: Props = $props();

	const CollapseIcon = $derived(
		position === 'left'
			? collapsed
				? PanelLeftOpen
				: PanelLeftClose
			: collapsed
				? PanelRightOpen
				: PanelRightClose
	);

	const panelClass = $derived(
		css({
			display: 'flex',
			flexDirection: 'column',
			height: '100%',
			backgroundColor: 'bg.panel',
			borderLeftWidth: position === 'right' ? '1' : '0',
			borderRightWidth: position === 'left' ? '1' : '0',
			flexShrink: 0,
			width: collapsed ? '0px' : width,
			minWidth: collapsed ? '0px' : width,
			overflow: 'hidden',
			transitionProperty: 'width, min-width',
			transitionDuration: '200ms',
			transitionTimingFunction: 'ease'
		})
	);

	const headerClass = css({
		display: 'flex',
		alignItems: 'center',
		justifyContent: 'space-between',
		position: 'sticky',
		top: '0',
		zIndex: 'header',
		borderBottomWidth: '1',
		paddingX: '4',
		paddingY: '3',
		backgroundColor: 'bg.panel'
	});
</script>

<div class={panelClass} aria-label="{title} panel">
	{#if !collapsed}
		<div class={headerClass}>
			<h2
				class={css({
					margin: '0',
					fontSize: 'sm',
					fontWeight: 'semibold',
					whiteSpace: 'nowrap',
					overflow: 'hidden',
					textOverflow: 'ellipsis'
				})}
			>
				{title}
			</h2>
			{#if collapsible}
				<button
					class={css({
						display: 'flex',
						alignItems: 'center',
						justifyContent: 'center',
						borderWidth: '0',
						backgroundColor: 'transparent',
						padding: '1',
						color: 'fg.muted',
						_hover: { color: 'fg.primary', backgroundColor: 'bg.hover' }
					})}
					onclick={() => (collapsed = true)}
					title="Collapse panel"
					aria-label="Collapse panel"
					type="button"
				>
					<CollapseIcon size={16} />
				</button>
			{/if}
		</div>

		<div
			class={css({
				flex: '1',
				overflowY: 'auto',
				minHeight: '0'
			})}
		>
			{@render children()}
		</div>
	{/if}
</div>

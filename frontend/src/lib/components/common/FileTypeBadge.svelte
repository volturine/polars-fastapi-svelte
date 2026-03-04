<script lang="ts">
	import {
		detectFileType,
		getFileTypeConfig,
		getSourceTypeConfig,
		type FileType,
		type SourceType
	} from '$lib/utils/fileTypes';
	import { css } from '$lib/styles/panda';

	interface Props {
		fileType?: FileType;
		sourceType?: SourceType;
		path?: string;
		isFolder?: boolean;
		size?: 'sm' | 'md' | 'lg';
		showIcon?: boolean;
		variant?: 'default' | 'minimal' | 'outline';
	}

	let {
		fileType,
		sourceType,
		path,
		isFolder = false,
		size = 'md',
		showIcon = false,
		variant = 'default'
	}: Props = $props();

	const config = $derived.by(() => {
		if (sourceType) return getSourceTypeConfig(sourceType);
		if (fileType) return getFileTypeConfig(fileType);
		if (path) {
			const detected = detectFileType(path, isFolder);
			return getFileTypeConfig(detected);
		}
		return getFileTypeConfig('unknown');
	});
	const Icon = $derived(config.icon);

	const sizes: Record<string, { iconSize: number; fontSize: string; padding: string }> = {
		sm: { iconSize: 12, fontSize: '10px', padding: '2px 6px' },
		md: { iconSize: 14, fontSize: '11px', padding: '2px 8px' },
		lg: { iconSize: 16, fontSize: '12px', padding: '3px 10px' }
	};

	const variants: Record<string, Record<string, string>> = {
		default: {},
		minimal: { border: 'none', padding: '0', backgroundColor: 'transparent' },
		outline: { backgroundColor: 'transparent', borderColor: 'border.primary' }
	};
</script>

<span
	class={css({
		display: 'inline-flex',
		flexShrink: '0',
		alignItems: 'center',
		gap: '0.25rem',
		whiteSpace: 'nowrap',
		borderWidth: '1px',
		borderStyle: 'solid',
		fontWeight: '600',
		textTransform: 'uppercase',
		letterSpacing: '0.08em',
		transitionProperty: 'color, background-color, border-color',
		transitionDuration: '150ms',
		fontFamily: 'var(--font-mono, monospace)',
		color: 'accent.primary',
		borderColor: 'border.primary',
		backgroundColor: 'accent.bg',
		fontSize: sizes[size].fontSize,
		padding: sizes[size].padding,
		...variants[variant]
	})}
	role="img"
	aria-label="{config.label} file type"
	title={config.description}
>
	{#if showIcon}
		<Icon size={sizes[size].iconSize} />
	{/if}
	{config.label}
</span>

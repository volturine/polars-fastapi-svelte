<script lang="ts">
	import { X } from 'lucide-svelte';
	import BaseModal from '$lib/components/ui/BaseModal.svelte';
	import { css } from '$lib/styles/panda';

	interface Props {
		show: boolean;
		title: string;
		message: string;
		confirmText?: string;
		cancelText?: string;
		onConfirm: () => void;
		onCancel: () => void;
	}

	let {
		show,
		title,
		message,
		confirmText = 'Confirm',
		cancelText = 'Cancel',
		onConfirm,
		onCancel
	}: Props = $props();

	function handleKeydown(e: KeyboardEvent) {
		if (!show) return;
		if (e.key === 'Enter') {
			e.preventDefault();
			onConfirm();
		}
	}
</script>

<svelte:window onkeydown={handleKeydown} />

<BaseModal
	open={show}
	onClose={onCancel}
	closeOnEscape={true}
	closeOnBackdrop={true}
	panelClass={css({
		width: 'full',
		maxWidth: '100',
		overflow: 'hidden',
		borderWidth: '1px',
		borderStyle: 'solid',
		borderColor: 'border.tertiary',
		_focus: { outline: 'none' },
		smDown: { maxWidth: 'full' },
		backgroundColor: 'bg.primary',
		animation: 'var(--animate-slide-up)'
	})}
	ariaLabelledby="dialog-title"
	ariaDescribedby="dialog-message"
	{content}
/>

{#snippet content()}
	<div
		class={css({
			display: 'flex',
			alignItems: 'center',
			justifyContent: 'space-between',
			borderBottomWidth: '1px',
			borderBottomStyle: 'solid',
			borderColor: 'border.tertiary',
			padding: '4'
		})}
	>
		<h2
			id="dialog-title"
			class={css({ margin: '0', fontSize: 'md', fontWeight: 'semibold', color: 'fg.primary' })}
		>
			{title}
		</h2>
		<button
			class={css({
				display: 'flex',
				cursor: 'pointer',
				alignItems: 'center',
				justifyContent: 'center',
				borderStyle: 'none',
				backgroundColor: 'transparent',
				padding: '1',
				color: 'fg.muted',
				_hover: { backgroundColor: 'bg.hover', color: 'fg.primary' }
			})}
			onclick={onCancel}
			aria-label="Close dialog"
			type="button"
		>
			<X size={16} />
		</button>
	</div>

	<div class={css({ padding: '6' })}>
		<p
			id="dialog-message"
			class={css({ margin: '0', fontSize: 'sm', lineHeight: 'relaxed', color: 'fg.secondary' })}
		>
			{message}
		</p>
	</div>

	<div
		class={css({
			display: 'flex',
			justifyContent: 'flex-end',
			gap: '3',
			borderTopWidth: '1px',
			borderTopStyle: 'solid',
			borderColor: 'border.tertiary',
			padding: '4',
			smDown: { flexDirection: 'column-reverse' }
		})}
	>
		<button
			class={css({
				cursor: 'pointer',
				borderWidth: '1px',
				borderStyle: 'solid',
				borderColor: 'border.tertiary',
				backgroundColor: 'transparent',
				paddingX: '4',
				paddingY: '2',
				fontFamily: 'var(--font-mono)',
				fontSize: 'sm',
				fontWeight: 'medium',
				_hover: { backgroundColor: 'bg.hover' },
				smDown: { width: 'full' },
				color: 'fg.primary'
			})}
			onclick={onCancel}
			type="button"
		>
			{cancelText}
		</button>
		<button
			class={css({
				cursor: 'pointer',
				borderWidth: '1px',
				borderStyle: 'solid',
				borderColor: 'error.border',
				backgroundColor: 'error.bg',
				paddingX: '4',
				paddingY: '2',
				fontFamily: 'var(--font-mono)',
				fontSize: 'sm',
				fontWeight: 'medium',
				_hover: { opacity: '0.85' },
				smDown: { width: 'full' },
				color: 'error.fg'
			})}
			onclick={onConfirm}
			type="button"
		>
			{confirmText}
		</button>
	</div>
{/snippet}

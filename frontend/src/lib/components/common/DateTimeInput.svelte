<script lang="ts">
	import { X } from 'lucide-svelte';
	import { css } from '$lib/styles/panda';

	interface Props {
		value: string;
		onChange: (value: string) => void;
		id?: string;
	}

	let { value, onChange, id }: Props = $props();

	const dateValue = $derived.by(() => {
		if (!value) return '';
		const match = /^(\d{4}-\d{2}-\d{2})/.exec(value);
		return match ? match[1] : '';
	});

	const timeValue = $derived.by(() => {
		if (!value) return '';
		const match = /T(\d{2}:\d{2})/.exec(value);
		return match ? match[1] : '';
	});

	function handleDateChange(e: Event) {
		const date = (e.target as HTMLInputElement).value;
		if (!date) {
			onChange('');
			return;
		}
		onChange(timeValue ? `${date}T${timeValue}` : date);
	}

	function handleTimeChange(e: Event) {
		const time = (e.target as HTMLInputElement).value;
		if (!dateValue) return;
		onChange(time ? `${dateValue}T${time}` : dateValue);
	}

	function clearTime() {
		if (dateValue) onChange(dateValue);
	}
</script>

<div class={css({ display: 'flex', gap: '1', overflow: 'hidden' })}>
	<input
		type="date"
		id={id ? `${id}-date` : undefined}
		value={dateValue}
		onchange={handleDateChange}
		class={css({ minWidth: '0', flex: '1', paddingX: '1.5', paddingY: '1', fontSize: 'xs' })}
	/>
	<div class={css({ position: 'relative', minWidth: '0', flex: '1' })}>
		<input
			type="time"
			id={id ? `${id}-time` : undefined}
			value={timeValue}
			onchange={handleTimeChange}
			disabled={!dateValue}
			class={css({
				width: '100%',
				paddingX: '1.5',
				paddingY: '1',
				paddingRight: '6',
				fontSize: 'xs',
				_disabled: { cursor: 'not-allowed', opacity: '0.5' }
			})}
		/>
		{#if timeValue}
			<button
				type="button"
				class={css({
					position: 'absolute',
					right: '1',
					top: '50%',
					transform: 'translateY(-50%)',
					display: 'flex',
					height: 'icon',
					width: 'icon',
					cursor: 'pointer',
					alignItems: 'center',
					justifyContent: 'center',
					border: 'none',
					background: 'transparent',
					padding: '0',
					color: 'fg.muted'
				})}
				onclick={clearTime}
				title="Clear time"
			>
				<X size={12} />
			</button>
		{/if}
	</div>
</div>

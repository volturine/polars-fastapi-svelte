<script lang="ts">
	interface Props {
		value: string;
		onChange: (value: string) => void;
		id?: string;
	}

	let { value, onChange, id }: Props = $props();

	// Parse value into date and time parts
	const datePart = $derived(() => {
		if (!value) return '';
		const match = /^(\d{4}-\d{2}-\d{2})/.exec(value);
		return match ? match[1] : '';
	});

	const timePart = $derived(() => {
		if (!value) return '';
		const match = /T(\d{2}:\d{2})/.exec(value);
		return match ? match[1] : '';
	});

	function handleDateChange(e: Event) {
		const date = (e.target as HTMLInputElement).value;
		const time = timePart() || '00:00';
		onChange(date ? `${date}T${time}` : '');
	}

	function handleTimeChange(e: Event) {
		const time = (e.target as HTMLInputElement).value;
		const date = datePart();
		if (date) {
			onChange(`${date}T${time || '00:00'}`);
		}
	}
</script>

<div class="datetime-input">
	<input
		type="date"
		id={id ? `${id}-date` : undefined}
		value={datePart()}
		onchange={handleDateChange}
		class="date-part"
	/>
	<input
		type="time"
		id={id ? `${id}-time` : undefined}
		value={timePart()}
		onchange={handleTimeChange}
		disabled={!datePart()}
		class="time-part"
	/>
</div>

<style>
	.datetime-input {
		display: flex;
		gap: var(--space-2);
	}

	.date-part {
		flex: 1.2;
		min-width: 0;
	}

	.time-part {
		flex: 0.8;
		min-width: 0;
	}

	.time-part:disabled {
		opacity: 0.5;
		cursor: not-allowed;
	}
</style>

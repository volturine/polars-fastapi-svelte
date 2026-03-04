<script lang="ts">
	interface DownloadConfigData {
		format: string;
		filename: string;
	}

	interface Props {
		config?: DownloadConfigData;
	}

	import { css, cx } from '$lib/styles/panda';

	let { config = $bindable({ format: 'csv', filename: 'download' }) }: Props = $props();

	const formats = [
		{ value: 'csv', label: 'CSV' },
		{ value: 'json', label: 'JSON' },
		{ value: 'ndjson', label: 'NDJSON' },
		{ value: 'parquet', label: 'Parquet' },
		{ value: 'excel', label: 'Excel' },
		{ value: 'duckdb', label: 'DuckDB' }
	];
</script>

<div
	class={css({ padding: '0', border: 'none', borderRadius: '0', backgroundColor: 'bg.primary' })}
>
	<div
		class={css({
			marginBottom: '0',
			paddingBottom: '5',
			backgroundColor: 'transparent',
			borderRadius: '0',
			border: 'none'
		})}
	>
		<label
			for="download-filename"
			class={css({ display: 'flex', flexDirection: 'column', gap: '3' })}
		>
			Filename
			<input
				id="download-filename"
				type="text"
				bind:value={config.filename}
				placeholder="download"
			/>
		</label>
		<p
			class={css({
				marginTop: '2',
				marginBottom: '0',
				fontSize: 'sm',
				fontWeight: 'normal',
				color: 'fg.tertiary'
			})}
		>
			Name of the downloaded file (without extension)
		</p>
	</div>
	<div
		class={cx(
			css({
				marginBottom: '0',
				paddingBottom: '5',
				backgroundColor: 'transparent',
				borderRadius: '0',
				border: 'none'
			}),
			css({ paddingTop: '5', borderTop: '1px solid var(--color-border-tertiary)' })
		)}
	>
		<label
			for="download-format"
			class={css({ display: 'flex', flexDirection: 'column', gap: '3' })}
		>
			Format
			<select id="download-format" bind:value={config.format}>
				{#each formats as fmt (fmt.value)}
					<option value={fmt.value}>{fmt.label}</option>
				{/each}
			</select>
		</label>
		<p
			class={css({
				marginTop: '2',
				marginBottom: '0',
				fontSize: 'sm',
				fontWeight: 'normal',
				color: 'fg.tertiary'
			})}
		>
			File format for download
		</p>
	</div>
</div>

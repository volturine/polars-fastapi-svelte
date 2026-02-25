<script lang="ts">
	interface DownloadConfigData {
		format: string;
		filename: string;
	}

	interface Props {
		config?: DownloadConfigData;
	}

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

<div class="config-panel">
	<div class="form-section">
		<label for="download-filename" class="flex flex-col gap-3">
			Filename
			<input
				id="download-filename"
				type="text"
				bind:value={config.filename}
				placeholder="download"
			/>
		</label>
		<p class="mt-2 mb-0 text-sm font-normal text-fg-tertiary">
			Name of the downloaded file (without extension)
		</p>
	</div>
	<div class="form-section">
		<label for="download-format" class="flex flex-col gap-3">
			Format
			<select id="download-format" bind:value={config.format}>
				{#each formats as fmt (fmt.value)}
					<option value={fmt.value}>{fmt.label}</option>
				{/each}
			</select>
		</label>
		<p class="mt-2 mb-0 text-sm font-normal text-fg-tertiary">File format for download</p>
	</div>
</div>

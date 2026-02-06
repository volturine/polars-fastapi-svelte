<script lang="ts">
	import { goto } from '$app/navigation';
	import { resolve } from '$app/paths';
	import { page } from '$app/state';
	import { createQuery, createMutation, useQueryClient } from '@tanstack/svelte-query';
	import { getDatasource, updateDatasource, getDatasourceSchema } from '$lib/api/datasource';
	import { ArrowLeft, Save, Loader, CircleAlert } from 'lucide-svelte';
	import type {
		DataSource,
		SchemaInfo,
		ColumnSchema,
		FileDataSourceConfig,
		IcebergDataSourceConfig
	} from '$lib/types/datasource';
	import FileTypeBadge from '$lib/components/common/FileTypeBadge.svelte';
	import ColumnTypeDropdown from '$lib/components/common/ColumnTypeDropdown.svelte';
	import { formatDateDisplay } from '$lib/utils/datetime';
	import { resolveColumnType } from '$lib/utils/columnTypes';

	const queryClient = useQueryClient();
	const datasourceId = $derived(page.params.id);

	const datasourceQuery = createQuery(() => ({
		queryKey: ['datasource', datasourceId],
		queryFn: async () => {
			if (!datasourceId) throw new Error('No datasource ID provided');
			const result = await getDatasource(datasourceId);
			if (result.isErr()) throw new Error(result.error.message);
			return result.value;
		},
		enabled: !!datasourceId
	}));

	const schemaQuery = createQuery(() => ({
		queryKey: ['datasource-schema', datasourceId],
		queryFn: async () => {
			if (!datasourceId) throw new Error('No datasource ID provided');
			const result = await getDatasourceSchema(datasourceId);
			if (result.isErr()) throw new Error(result.error.message);
			return result.value;
		},
		enabled: !!datasourceId && !!datasourceQuery.data
	}));

	const updateMutation = createMutation(() => ({
		mutationFn: async (update: { name: string; config: Record<string, unknown> }) => {
			if (!datasourceId) throw new Error('No datasource ID provided');
			const result = await updateDatasource(datasourceId, update);
			if (result.isErr()) throw new Error(result.error.message);
			return result.value;
		},
		onSuccess: () => {
			queryClient.invalidateQueries({ queryKey: ['datasource', datasourceId] });
			queryClient.invalidateQueries({ queryKey: ['datasource-schema', datasourceId] });
			queryClient.invalidateQueries({ queryKey: ['datasources'] });
		}
	}));

	let name = $state('');
	let columns = $state<ColumnSchema[]>([]);
	let hasChanges = $state(false);
	let schemaModified = $state(false);
	let activeTab = $state<'general' | 'schema' | 'csv' | 'excel'>('general');
	let initialized = $state(false);
	let parsingOptionsTimer: ReturnType<typeof setTimeout> | null = null;
	let isSavingParsing = $state(false);
	function formatDate(dateString: string): string {
		return formatDateDisplay(dateString);
	}

	$effect(() => {
		if (!datasourceId) return;
		initialized = false;
		hasChanges = false;
		schemaModified = false;
		columns = [];
	});

	$effect(() => {
		const data = datasourceQuery.data;
		if (!data) return;
		if (initialized) return;
		name = data.name;
		const config = data.config as unknown as FileDataSourceConfig;
		if (isCsv(data)) {
			const opts = config.csv_options;
			csvConfig = {
				delimiter: opts?.delimiter ?? ',',
				quote_char: opts?.quote_char ?? '"',
				has_header: opts?.has_header ?? true,
				skip_rows: opts?.skip_rows ?? 0,
				encoding: opts?.encoding ?? 'utf8'
			};
		}
		if (isExcel(data)) {
			excelConfig = {
				sheet_name: config.sheet_name ?? '',
				table_name: config.table_name ?? '',
				named_range: config.named_range ?? '',
				start_row: config.start_row ?? 0,
				start_col: config.start_col ?? 0,
				end_col: config.end_col ?? 0,
				has_header: config.has_header ?? true
			};
		}
		initialized = true;
	});

	$effect(() => {
		if (!schemaQuery.data) return;
		setSchema(schemaQuery.data);
	});

	// CSV-specific state
	let csvConfig = $state<{
		delimiter: string;
		quote_char: string;
		has_header: boolean;
		skip_rows: number;
		encoding: string;
	}>({
		delimiter: ',',
		quote_char: '"',
		has_header: true,
		skip_rows: 0,
		encoding: 'utf8'
	});

	// Excel-specific state
	let excelConfig = $state<{
		sheet_name: string;
		table_name: string;
		named_range: string;
		start_row: number;
		start_col: number;
		end_col: number;
		has_header: boolean;
	}>({
		sheet_name: '',
		table_name: '',
		named_range: '',
		start_row: 0,
		start_col: 0,
		end_col: 0,
		has_header: true
	});

	function setSchema(value: SchemaInfo | null | undefined) {
		if (!value) return;
		if (schemaModified) return;
		if (!value.columns?.length) {
			columns = [];
			return;
		}
		// Normalize dtypes to handle parameterized types like "Datetime(time_unit='us', time_zone=None)"
		columns = value.columns.map((col) => ({
			...col,
			dtype: resolveColumnType(col.dtype)
		}));
	}

	function isCsv(datasource: DataSource): boolean {
		if (datasource.source_type !== 'file') return false;
		const config = datasource.config as unknown as FileDataSourceConfig;
		return config.file_type === 'csv';
	}

	function isExcel(datasource: DataSource): boolean {
		if (datasource.source_type !== 'file') return false;
		const config = datasource.config as unknown as FileDataSourceConfig;
		return config.file_type === 'xlsx';
	}

	function isFile(datasource: DataSource): boolean {
		return datasource.source_type === 'file';
	}

	function isIceberg(datasource: DataSource): boolean {
		return datasource.source_type === 'iceberg';
	}

	function handleNameChange(newName: string) {
		name = newName;
		hasChanges = true;
	}

	function handleColumnNameChange(index: number, newName: string) {
		columns = columns.map((col, i) => (i === index ? { ...col, name: newName } : col));
		hasChanges = true;
		schemaModified = true;
	}

	function handleColumnTypeChange(index: number, newType: string) {
		columns = columns.map((col, i) => (i === index ? { ...col, dtype: newType } : col));
		hasChanges = true;
		schemaModified = true;
	}

	async function handleCsvConfigChange<K extends keyof typeof csvConfig>(
		key: K,
		value: (typeof csvConfig)[K]
	) {
		csvConfig = { ...csvConfig, [key]: value };
		hasChanges = true;

		// Clear existing timer
		if (parsingOptionsTimer) {
			clearTimeout(parsingOptionsTimer);
			parsingOptionsTimer = null;
		}

		// Auto-save when parsing options change (affects schema)
		if (['delimiter', 'skip_rows', 'has_header'].includes(key as string)) {
			// Immediate save for delimiter and has_header (select/checkbox)
			// Debounced save for skip_rows (numeric input)
			if (key === 'skip_rows') {
				parsingOptionsTimer = setTimeout(async () => {
					await saveParsingOptions();
				}, 500);
			} else {
				await saveParsingOptions();
			}
		}
	}

	async function handleExcelConfigChange<K extends keyof typeof excelConfig>(
		key: K,
		value: (typeof excelConfig)[K]
	) {
		excelConfig = { ...excelConfig, [key]: value };
		hasChanges = true;

		// Clear existing timer
		if (parsingOptionsTimer) {
			clearTimeout(parsingOptionsTimer);
			parsingOptionsTimer = null;
		}

		// Auto-save when parsing options change (affects schema)
		if (
			[
				'sheet_name',
				'start_row',
				'start_col',
				'end_col',
				'table_name',
				'named_range',
				'has_header'
			].includes(key as string)
		) {
			// Immediate save for sheet_name, table_name, named_range, has_header (text/checkbox)
			// Debounced save for numeric inputs
			if (['start_row', 'start_col', 'end_col'].includes(key as string)) {
				parsingOptionsTimer = setTimeout(async () => {
					await saveParsingOptions();
				}, 500);
			} else {
				await saveParsingOptions();
			}
		}
	}

	async function saveParsingOptions() {
		if (!datasourceQuery.data) return;

		isSavingParsing = true;
		const update: { name: string; config: Record<string, unknown> } = { name, config: {} };

		if (isCsv(datasourceQuery.data)) {
			update.config = {
				...datasourceQuery.data.config,
				csv_options: {
					delimiter: csvConfig.delimiter,
					quote_char: csvConfig.quote_char,
					has_header: csvConfig.has_header,
					skip_rows: csvConfig.skip_rows,
					encoding: csvConfig.encoding
				}
			};
		} else if (isExcel(datasourceQuery.data)) {
			update.config = {
				...datasourceQuery.data.config,
				sheet_name: excelConfig.sheet_name || null,
				table_name: excelConfig.table_name || null,
				named_range: excelConfig.named_range || null,
				start_row: excelConfig.start_row,
				start_col: excelConfig.start_col,
				end_col: excelConfig.end_col,
				has_header: excelConfig.has_header
			};
		}

		// Save without column_schema - just parsing options
		const save = updateMutation.mutateAsync(update);
		save.finally(() => {
			isSavingParsing = false;
		});
		const saved = await save.then(
			() => true,
			() => false
		);
		if (!saved) return;

		queryClient.removeQueries({ queryKey: ['datasource-schema', datasourceId] });
		columns = [];
		hasChanges = false;
		schemaModified = false;

		if (!datasourceId) return;
		const result = await getDatasourceSchema(datasourceId);
		if (result.isOk()) {
			setSchema(result.value);
		}
	}

	function cellLabel(col: number): string {
		let idx = col + 1;
		let label = '';
		while (idx > 0) {
			const rem = (idx - 1) % 26;
			label = String.fromCharCode(65 + rem) + label;
			idx = Math.floor((idx - 1) / 26);
		}
		return label;
	}

	async function handleSave() {
		if (!datasourceQuery.data) return;

		const update: { name: string; config: Record<string, unknown> } = { name, config: {} };

		if (isCsv(datasourceQuery.data)) {
			update.config = {
				...datasourceQuery.data.config,
				csv_options: {
					delimiter: csvConfig.delimiter,
					quote_char: csvConfig.quote_char,
					has_header: csvConfig.has_header,
					skip_rows: csvConfig.skip_rows,
					encoding: csvConfig.encoding
				}
			};
		} else if (isExcel(datasourceQuery.data)) {
			update.config = {
				...datasourceQuery.data.config,
				sheet_name: excelConfig.sheet_name || null,
				table_name: excelConfig.table_name || null,
				named_range: excelConfig.named_range || null,
				start_row: excelConfig.start_row,
				start_col: excelConfig.start_col,
				end_col: excelConfig.end_col,
				has_header: excelConfig.has_header
			};
		} else if (isFile(datasourceQuery.data)) {
			update.config = { ...datasourceQuery.data.config };
		}

		// Only include column_schema if schema was actually modified
		if (schemaModified && columns.length > 0) {
			update.config.column_schema = columns;
		}

		updateMutation.mutate(update);
		hasChanges = false;
		schemaModified = false;
		initialized = false;
	}

	function handleBack() {
		goto(resolve('/datasources'), { invalidateAll: true });
	}

	async function handleRefreshRows() {
		if (!datasourceId) return;
		await getDatasourceSchema(datasourceId, { refresh: true });
		await schemaQuery.refetch();
	}
</script>

<div class="mx-auto min-h-full max-w-[900px] p-6">
	<header class="mb-6 flex items-center justify-between gap-4 border-b pb-6" style="border-color: var(--border-primary);">
		<div class="flex items-center gap-4">
			<button
				class="btn-back flex h-9 w-9 items-center justify-center rounded-sm border p-0 transition-all"
				style="background: var(--bg-tertiary); border-color: var(--border-primary); color: var(--fg-secondary);"
				onclick={handleBack}
			>
				<ArrowLeft size={20} />
			</button>
			<div>
				<h1 class="m-0 mb-1 text-2xl font-semibold">Edit Data Source</h1>
				{#if datasourceQuery.data}
					<p class="m-0 text-sm" style="color: var(--fg-tertiary);">{datasourceQuery.data.name}</p>
				{/if}
			</div>
		</div>
		<button
			class="btn-primary flex items-center gap-2"
			onclick={handleSave}
			disabled={!hasChanges || updateMutation.isPending}
		>
			{#if updateMutation.isPending}
				<Loader size={16} class="spin" />
				Saving...
			{:else}
				<Save size={16} />
				Save Changes
			{/if}
		</button>
	</header>

	{#if datasourceQuery.isLoading}
		<div class="flex flex-col items-center justify-center gap-4 p-12" style="color: var(--fg-muted);">
			<Loader size={32} class="spin" />
			<p>Loading data source...</p>
		</div>
	{:else if datasourceQuery.isError}
		<div class="error-box mb-4 flex items-start gap-3">
			<CircleAlert size={20} />
			<div class="flex flex-col gap-1">
				<p class="m-0 font-semibold">Error loading data source</p>
				<p class="m-0 text-sm opacity-80">
					{datasourceQuery.error instanceof Error ? datasourceQuery.error.message : 'Unknown error'}
				</p>
			</div>
		</div>
	{:else if datasourceQuery.data}
		{@const datasource = datasourceQuery.data}
		{@const csv = isCsv(datasource)}
		{@const excel = isExcel(datasource)}

		<div class="mb-6 flex gap-2 border-b-2" style="border-color: var(--border-primary);">
			<button
				class="tab -mb-0.5 border-b-2 border-transparent px-5 py-3 text-sm font-medium transition-all"
				class:active={activeTab === 'general'}
				onclick={() => (activeTab = 'general')}
				style="color: var(--fg-muted);"
			>
				General
			</button>
			<button
				class="tab -mb-0.5 border-b-2 border-transparent px-5 py-3 text-sm font-medium transition-all"
				class:active={activeTab === 'schema'}
				onclick={() => (activeTab = 'schema')}
				style="color: var(--fg-muted);"
			>
				Schema
			</button>
			{#if csv}
				<button
					class="tab -mb-0.5 border-b-2 border-transparent px-5 py-3 text-sm font-medium transition-all"
					class:active={activeTab === 'csv'}
					onclick={() => (activeTab = 'csv')}
					style="color: var(--fg-muted);"
				>
					CSV Options
				</button>
			{/if}
			{#if excel}
				<button
					class="tab -mb-0.5 border-b-2 border-transparent px-5 py-3 text-sm font-medium transition-all"
					class:active={activeTab === 'excel'}
					onclick={() => (activeTab = 'excel')}
					style="color: var(--fg-muted);"
				>
					Excel Options
				</button>
			{/if}
		</div>

		{#if updateMutation.isError}
			<div class="error-box mb-4 flex items-start gap-3">
				<CircleAlert size={20} />
				<div class="flex flex-col gap-1">
					<p class="m-0 font-semibold">Error saving changes</p>
					<p class="m-0 text-sm opacity-80">
						{updateMutation.error instanceof Error ? updateMutation.error.message : 'Unknown error'}
					</p>
				</div>
			</div>
		{/if}

		{#if updateMutation.isSuccess}
			<div class="success-box mb-4 flex items-center gap-2 rounded-sm border p-3 text-sm" style="background-color: var(--success-bg); border-color: var(--success-border); color: var(--success-fg);">
				<p class="m-0">Changes saved successfully!</p>
			</div>
		{/if}

		<div class="rounded-md border p-6" style="background-color: var(--bg-primary); border-color: var(--border-primary);">
			{#if activeTab === 'general'}
				<div class="flex flex-col gap-5">
					<div class="flex flex-col gap-2">
						<label for="datasource-name" class="text-sm font-medium" style="color: var(--fg-secondary);">Name</label>
						<input
							id="datasource-name"
							type="text"
							value={name}
							oninput={(e) => handleNameChange(e.currentTarget.value)}
							placeholder="Data source name"
							class="rounded-sm border px-3 py-2 text-sm transition-colors"
							style="border-color: var(--input-border); background-color: var(--input-bg);"
						/>
					</div>

					<div class="mt-4 border-t pt-4" style="border-color: var(--border-primary);">
						<h3 class="m-0 mb-4 text-sm font-semibold" style="color: var(--fg-secondary);">Source Information</h3>
						<div class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
							<div class="flex flex-col gap-1">
								<span class="text-xs uppercase tracking-wide" style="color: var(--fg-muted);">Type</span>
								<span class="text-sm font-medium" style="color: var(--fg-primary);">{datasource.source_type}</span>
							</div>
							{#if isFile(datasource)}
								{@const config = datasource.config as unknown as FileDataSourceConfig}
								<div class="flex flex-col gap-1">
									<span class="text-xs uppercase tracking-wide" style="color: var(--fg-muted);">File Type</span>
									<FileTypeBadge path={config.file_path} size="sm" />
								</div>
							{/if}
							{#if isIceberg(datasource)}
								{@const config = datasource.config as unknown as IcebergDataSourceConfig}
								<div class="flex flex-col gap-1">
									<span class="text-xs uppercase tracking-wide" style="color: var(--fg-muted);">Metadata Path</span>
									<span class="break-all text-xs" style="color: var(--fg-secondary);">{config.metadata_path}</span>
								</div>
							{/if}
							<div class="flex flex-col gap-1">
								<span class="text-xs uppercase tracking-wide" style="color: var(--fg-muted);">Created</span>
								<span class="text-sm font-medium" style="color: var(--fg-primary);">{formatDate(datasource.created_at)}</span>
							</div>
							{#if schemaQuery.data}
								<div class="flex flex-col gap-1">
									<span class="text-xs uppercase tracking-wide" style="color: var(--fg-muted);">Rows</span>
									<span class="text-sm font-medium" style="color: var(--fg-primary);">
										{schemaQuery.data.row_count?.toLocaleString() ?? 'Unknown'}
									</span>
									<button
										class="btn-secondary btn-inline mt-1 self-start px-2.5 py-1 text-xs"
										onclick={handleRefreshRows}
										disabled={schemaQuery.isFetching}
									>
										{schemaQuery.isFetching ? 'Refreshing...' : 'Refresh'}
									</button>
								</div>
								<div class="flex flex-col gap-1">
									<span class="text-xs uppercase tracking-wide" style="color: var(--fg-muted);">Columns</span>
									<span class="text-sm font-medium" style="color: var(--fg-primary);">{schemaQuery.data.columns.length}</span>
								</div>
							{/if}
						</div>
					</div>
				</div>
			{:else if activeTab === 'schema'}
				<div class="flex flex-col gap-4">
					<div>
						<h3 class="m-0 mb-2 text-base font-semibold">Column Schema</h3>
						<p class="m-0 text-xs" style="color: var(--fg-muted);">
							Adjust column names and types. Changes will trigger re-processing of the file.
						</p>
					</div>

					{#if isSavingParsing}
						<div class="flex flex-col items-center justify-center gap-4 p-12" style="color: var(--fg-muted);">
							<Loader size={24} class="spin" />
							<p>Refreshing schema...</p>
						</div>
					{:else if schemaQuery.isLoading}
						<div class="flex flex-col items-center justify-center gap-4 p-12" style="color: var(--fg-muted);">
							<Loader size={24} class="spin" />
							<p>Loading schema...</p>
						</div>
					{:else if schemaQuery.isError}
						<div class="error-box flex items-center gap-2">
							<CircleAlert size={20} />
							<p>Error loading schema</p>
						</div>
					{:else if columns.length > 0}
						<div class="overflow-hidden rounded-sm border" style="border-color: var(--border-primary);">
							<div class="grid grid-cols-[50px_2fr_140px_1fr] items-center gap-3 px-4 py-3 text-xs font-semibold uppercase tracking-wide" style="background-color: var(--bg-tertiary); color: var(--fg-tertiary);">
								<span>#</span>
								<span>Column Name</span>
								<span>Type</span>
								<span>Sample Value</span>
							</div>
							{#each columns as column, index (index)}
								<div class="table-row grid grid-cols-[50px_2fr_140px_1fr] items-center gap-3 border-t px-4 py-3" style="border-color: var(--border-primary);">
									<span class="text-xs" style="color: var(--fg-muted);">{index + 1}</span>
									<input
										type="text"
										class="w-full rounded-sm border px-3 py-2 text-sm"
										style="border-color: var(--input-border); background-color: var(--input-bg);"
										value={column.name}
										oninput={(e) => handleColumnNameChange(index, e.currentTarget.value)}
									/>
									<ColumnTypeDropdown
										value={column.dtype}
										onChange={(val) => handleColumnTypeChange(index, val)}
										placeholder="Select type..."
									/>
									<span class="max-w-[200px] overflow-hidden text-ellipsis whitespace-nowrap text-sm" style="color: var(--fg-muted);" title={column.sample_value ?? ''}>
										{column.sample_value ?? '-'}
									</span>
								</div>
							{/each}
						</div>
					{:else}
						<div class="p-8 text-center" style="color: var(--fg-muted);">
							<p class="m-0">No schema information available.</p>
						</div>
					{/if}
				</div>
			{:else if activeTab === 'csv' && csv}
				<div class="flex flex-col gap-5">
					<h3 class="m-0 text-base font-semibold">CSV Configuration</h3>

					<div class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
						<div class="flex flex-col gap-2">
							<label for="csv-delimiter" class="text-sm font-medium" style="color: var(--fg-secondary);">Delimiter</label>
							<select
								id="csv-delimiter"
								value={csvConfig.delimiter}
								onchange={(e) => handleCsvConfigChange('delimiter', e.currentTarget.value)}
								class="rounded-sm border px-3 py-2 text-sm"
								style="border-color: var(--input-border); background-color: var(--input-bg);"
							>
								<option value=",">Comma (,)</option>
								<option value=";">Semicolon (;)</option>
								<option value="\t">Tab</option>
								<option value="|">Pipe (|)</option>
								<option value=" ">Space</option>
							</select>
						</div>

						<div class="flex flex-col gap-2">
							<label for="csv-quote" class="text-sm font-medium" style="color: var(--fg-secondary);">Quote Character</label>
							<select
								id="csv-quote"
								value={csvConfig.quote_char}
								onchange={(e) => handleCsvConfigChange('quote_char', e.currentTarget.value)}
								class="rounded-sm border px-3 py-2 text-sm"
								style="border-color: var(--input-border); background-color: var(--input-bg);"
							>
								<option value="&quot;">Double Quote (")</option>
								<option value="'">Single Quote (')</option>
								<option value="">None</option>
							</select>
						</div>
					</div>

					<div class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
						<div class="flex flex-col gap-2">
							<label for="csv-encoding" class="text-sm font-medium" style="color: var(--fg-secondary);">Encoding</label>
							<select
								id="csv-encoding"
								value={csvConfig.encoding}
								onchange={(e) => handleCsvConfigChange('encoding', e.currentTarget.value)}
								class="rounded-sm border px-3 py-2 text-sm"
								style="border-color: var(--input-border); background-color: var(--input-bg);"
							>
								<option value="utf8">UTF-8</option>
								<option value="utf8-lossy">UTF-8 (lossy)</option>
								<option value="latin1">Latin-1 (ISO-8859-1)</option>
								<option value="ascii">ASCII</option>
							</select>
						</div>

						<div class="flex flex-col gap-2">
							<label for="csv-skip-rows" class="text-sm font-medium" style="color: var(--fg-secondary);">Skip Rows</label>
							<input
								id="csv-skip-rows"
								type="number"
								min="0"
								value={csvConfig.skip_rows}
								oninput={(e) =>
									handleCsvConfigChange('skip_rows', parseInt(e.currentTarget.value) || 0)}
								class="rounded-sm border px-3 py-2 text-sm"
								style="border-color: var(--input-border); background-color: var(--input-bg);"
							/>
							<span class="m-0 text-xs" style="color: var(--fg-muted);">Number of rows to skip at the start</span>
						</div>
					</div>

					<div class="flex items-center gap-2">
						<input
							id="csv-header"
							type="checkbox"
							checked={csvConfig.has_header}
							onchange={(e) => handleCsvConfigChange('has_header', e.currentTarget.checked)}
							class="h-4 w-4 cursor-pointer"
						/>
						<label for="csv-header" class="m-0 text-sm font-medium" style="color: var(--fg-secondary);">First row is header</label>
					</div>
				</div>
			{:else if activeTab === 'excel' && excel}
				<div class="flex flex-col gap-5">
					<h3 class="m-0 text-base font-semibold">Excel Configuration</h3>

					<div class="grid grid-cols-[repeat(auto-fit,minmax(200px,1fr))] gap-4">
						<div class="flex flex-col gap-2">
							<label for="excel-sheet" class="text-sm font-medium" style="color: var(--fg-secondary);">Sheet Name</label>
							<input
								id="excel-sheet"
								type="text"
								value={excelConfig.sheet_name}
								oninput={(e) => handleExcelConfigChange('sheet_name', e.currentTarget.value)}
								placeholder="Sheet1"
								class="rounded-sm border px-3 py-2 text-sm"
								style="border-color: var(--input-border); background-color: var(--input-bg);"
							/>
						</div>

						<div class="flex flex-col gap-2">
							<label for="excel-table" class="text-sm font-medium" style="color: var(--fg-secondary);">Table Name</label>
							<input
								id="excel-table"
								type="text"
								value={excelConfig.table_name}
								oninput={(e) => handleExcelConfigChange('table_name', e.currentTarget.value)}
								placeholder="Optional"
								class="rounded-sm border px-3 py-2 text-sm"
								style="border-color: var(--input-border); background-color: var(--input-bg);"
							/>
						</div>
					</div>

					<div class="flex flex-col gap-2">
						<label for="excel-range" class="text-sm font-medium" style="color: var(--fg-secondary);">Named Range</label>
						<input
							id="excel-range"
							type="text"
							value={excelConfig.named_range}
							oninput={(e) => handleExcelConfigChange('named_range', e.currentTarget.value)}
							placeholder="Optional"
							class="rounded-sm border px-3 py-2 text-sm"
							style="border-color: var(--input-border); background-color: var(--input-bg);"
						/>
					</div>

					<div class="rounded-sm border p-4" style="background-color: var(--bg-tertiary); border-color: var(--border-primary);">
						<h4 class="m-0 mb-4 text-sm font-semibold" style="color: var(--fg-secondary);">Table Bounds</h4>
						<div class="grid grid-cols-[repeat(auto-fit,minmax(150px,1fr))] gap-4">
							<div class="flex flex-col gap-2">
								<label for="start-row" class="text-sm font-medium" style="color: var(--fg-secondary);">Start Row (0-based)</label>
								<input
									id="start-row"
									type="number"
									min="0"
									value={excelConfig.start_row}
									oninput={(e) =>
										handleExcelConfigChange('start_row', parseInt(e.currentTarget.value) || 0)}
									class="rounded-sm border px-3 py-2 text-sm"
									style="border-color: var(--input-border); background-color: var(--input-bg);"
								/>
								<span class="m-0 text-xs" style="color: var(--fg-muted);">Excel row: {excelConfig.start_row + 1}</span>
							</div>

							<div class="flex flex-col gap-2">
								<label for="start-col" class="text-sm font-medium" style="color: var(--fg-secondary);">Start Column</label>
								<input
									id="start-col"
									type="number"
									min="0"
									value={excelConfig.start_col}
									oninput={(e) =>
										handleExcelConfigChange('start_col', parseInt(e.currentTarget.value) || 0)}
									class="rounded-sm border px-3 py-2 text-sm"
									style="border-color: var(--input-border); background-color: var(--input-bg);"
								/>
								<span class="m-0 text-xs" style="color: var(--fg-muted);">Excel column: {cellLabel(excelConfig.start_col)}</span>
							</div>

							<div class="flex flex-col gap-2">
								<label for="end-col" class="text-sm font-medium" style="color: var(--fg-secondary);">End Column</label>
								<input
									id="end-col"
									type="number"
									min="0"
									value={excelConfig.end_col}
									oninput={(e) =>
										handleExcelConfigChange('end_col', parseInt(e.currentTarget.value) || 0)}
									class="rounded-sm border px-3 py-2 text-sm"
									style="border-color: var(--input-border); background-color: var(--input-bg);"
								/>
								<span class="m-0 text-xs" style="color: var(--fg-muted);">Excel column: {cellLabel(excelConfig.end_col)}</span>
							</div>
						</div>
					</div>

					<div class="flex items-center gap-2">
						<input
							id="excel-header"
							type="checkbox"
							checked={excelConfig.has_header}
							onchange={(e) => handleExcelConfigChange('has_header', e.currentTarget.checked)}
							class="h-4 w-4 cursor-pointer"
						/>
						<label for="excel-header" class="m-0 text-sm font-medium" style="color: var(--fg-secondary);">First row is header</label>
					</div>
				</div>
			{/if}
		</div>
	{/if}
</div>

<style>
	.btn-back:hover {
		background: var(--bg-hover);
		color: var(--fg-primary);
	}

	.tab:hover {
		color: var(--fg-secondary);
	}

	.tab.active {
		color: var(--accent-primary);
		border-bottom-color: var(--accent-primary);
	}

	.table-row:hover {
		background-color: var(--bg-hover);
	}

	input:focus,
	select:focus {
		outline: none;
		border-color: var(--border-focus);
		box-shadow: 0 0 0 3px var(--accent-bg);
	}

	input:disabled,
	select:disabled {
		background: var(--bg-tertiary);
		cursor: not-allowed;
	}

	:global(.spin) {
		animation: spin 1s linear infinite;
	}

	@keyframes spin {
		from {
			transform: rotate(0deg);
		}
		to {
			transform: rotate(360deg);
		}
	}
</style>

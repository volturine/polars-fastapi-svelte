import type { APIRequestContext } from '@playwright/test';

export const API_BASE = 'http://localhost:8000/api/v1';

const SAMPLE_CSV = 'id,name,age,city\n1,Alice,30,London\n2,Bob,25,Paris\n3,Charlie,35,Berlin\n';

const E2E_PREFIX_RE = /^e2e[^a-z]/i;

/**
 * Purge all resources whose names match the e2e prefix.
 * Safe to call before/after a run to ensure a clean slate.
 */
export async function purgeE2eResources(request: APIRequestContext): Promise<void> {
	const [dsResp, aResp, udfResp, schedResp, hcResp] = await Promise.all([
		request.get(`${API_BASE}/datasource`),
		request.get(`${API_BASE}/analysis`),
		request.get(`${API_BASE}/udf`),
		request.get(`${API_BASE}/schedules`),
		request.get(`${API_BASE}/healthchecks`)
	]);

	const deletions: Promise<void>[] = [];

	// Schedules & health checks first (they reference datasources)
	if (schedResp.ok()) {
		const schedules = (await schedResp.json()) as Array<{ id: string; datasource_id?: string }>;
		const dsNames = new Map<string, string>();
		if (dsResp.ok()) {
			for (const ds of (await dsResp.json()) as Array<{ id: string; name: string }>) {
				dsNames.set(ds.id, ds.name);
			}
		}
		for (const s of schedules) {
			const dsName = s.datasource_id ? dsNames.get(s.datasource_id) : undefined;
			if (dsName && E2E_PREFIX_RE.test(dsName)) {
				deletions.push(deleteSchedule(request, s.id).catch(() => undefined));
			}
		}
	}
	if (hcResp.ok()) {
		const checks = (await hcResp.json()) as Array<{ id: string; name: string }>;
		for (const hc of checks) {
			if (E2E_PREFIX_RE.test(hc.name)) {
				deletions.push(deleteHealthCheck(request, hc.id).catch(() => undefined));
			}
		}
	}
	await Promise.all(deletions);

	const deletions2: Promise<void>[] = [];

	// Analyses (reference datasources)
	if (aResp.ok()) {
		const analyses = (await aResp.json()) as Array<{ id: string; name: string }>;
		for (const a of analyses) {
			if (E2E_PREFIX_RE.test(a.name)) {
				deletions2.push(deleteAnalysis(request, a.id).catch(() => undefined));
			}
		}
	}
	// UDFs
	if (udfResp.ok()) {
		const udfs = (await udfResp.json()) as Array<{ id: string; name: string }>;
		for (const u of udfs) {
			if (E2E_PREFIX_RE.test(u.name)) {
				deletions2.push(deleteUdf(request, u.id).catch(() => undefined));
			}
		}
	}
	// Datasources (must come after analyses/schedules/health checks)
	if (dsResp.ok()) {
		const datasources = (await dsResp.json()) as Array<{ id: string; name: string }>;
		for (const ds of datasources) {
			if (E2E_PREFIX_RE.test(ds.name)) {
				deletions2.push(deleteDatasource(request, ds.id).catch(() => undefined));
			}
		}
	}
	await Promise.all(deletions2);
}

// ── Datasource ────────────────────────────────────────────────────────────────

export async function createDatasource(request: APIRequestContext, name: string): Promise<string> {
	const response = await request.post(`${API_BASE}/datasource/upload`, {
		multipart: {
			file: {
				name: `${name}.csv`,
				mimeType: 'text/csv',
				buffer: Buffer.from(SAMPLE_CSV)
			},
			name
		}
	});
	if (!response.ok()) {
		throw new Error(`createDatasource failed: ${response.status()} ${await response.text()}`);
	}
	return ((await response.json()) as { id: string }).id;
}

export async function deleteDatasource(request: APIRequestContext, id: string): Promise<void> {
	await request.delete(`${API_BASE}/datasource/${id}`);
}

// ── Analysis ──────────────────────────────────────────────────────────────────

export async function createAnalysis(
	request: APIRequestContext,
	name: string,
	datasourceId: string
): Promise<string> {
	// Proper UUID v4 is required by the backend (result_id validator)
	const resultId = crypto.randomUUID();

	const response = await request.post(`${API_BASE}/analysis`, {
		data: {
			name,
			description: null,
			tabs: [
				{
					id: crypto.randomUUID(),
					name: 'Source 1',
					parent_id: null,
					datasource: {
						id: datasourceId,
						analysis_tab_id: null,
						config: { branch: 'master' }
					},
					output: {
						result_id: resultId,
						datasource_type: 'iceberg',
						format: 'parquet',
						filename: 'source_1'
					},
					steps: [
						{
							id: crypto.randomUUID(),
							type: 'view',
							config: {},
							depends_on: [],
							is_applied: true
						}
					]
				}
			]
		}
	});
	if (!response.ok()) {
		throw new Error(`createAnalysis failed: ${response.status()} ${await response.text()}`);
	}
	return ((await response.json()) as { id: string }).id;
}

export async function deleteAnalysis(request: APIRequestContext, id: string): Promise<void> {
	await request.delete(`${API_BASE}/analysis/${id}`);
}

// ── UDF ───────────────────────────────────────────────────────────────────────

export async function createUdf(request: APIRequestContext, name: string): Promise<string> {
	const response = await request.post(`${API_BASE}/udf`, {
		data: {
			name,
			description: `Test UDF: ${name}`,
			code: 'def transform(col):\n    return col\n', // backend requires 'code', not 'source'
			tags: ['test'],
			signature: { inputs: [], output: null }
		}
	});
	if (!response.ok()) {
		throw new Error(`createUdf failed: ${response.status()} ${await response.text()}`);
	}
	return ((await response.json()) as { id: string }).id;
}

export async function deleteUdf(request: APIRequestContext, id: string): Promise<void> {
	await request.delete(`${API_BASE}/udf/${id}`);
}

// ── Schedule ──────────────────────────────────────────────────────────────────

export async function createSchedule(
	request: APIRequestContext,
	datasourceId: string,
	cron = '0 9 * * *'
): Promise<string> {
	const response = await request.post(`${API_BASE}/schedules`, {
		data: {
			datasource_id: datasourceId,
			cron_expression: cron,
			enabled: true
		}
	});
	if (!response.ok()) {
		throw new Error(`createSchedule failed: ${response.status()} ${await response.text()}`);
	}
	return ((await response.json()) as { id: string }).id;
}

export async function deleteSchedule(request: APIRequestContext, id: string): Promise<void> {
	await request.delete(`${API_BASE}/schedules/${id}`);
}

// ── Health Check ──────────────────────────────────────────────────────────────

export async function createHealthCheck(
	request: APIRequestContext,
	datasourceId: string,
	name: string
): Promise<string> {
	const response = await request.post(`${API_BASE}/healthchecks`, {
		data: {
			datasource_id: datasourceId,
			name,
			check_type: 'row_count',
			config: { min_rows: 1 },
			enabled: true,
			critical: false
		}
	});
	if (!response.ok()) {
		throw new Error(`createHealthCheck failed: ${response.status()} ${await response.text()}`);
	}
	return ((await response.json()) as { id: string }).id;
}

export async function deleteHealthCheck(request: APIRequestContext, id: string): Promise<void> {
	await request.delete(`${API_BASE}/healthchecks/${id}`);
}

import type {
	ComputeJob,
	ComputeStatus,
	EngineListResponse,
	EngineStatusResponse
} from '$lib/types/compute';
import type { RawComputeJobResponse } from '$lib/types/api-responses';
import { apiRequest } from './client';

export interface PreviewResponse {
	columns: string[];
	data: Record<string, unknown>[];
	total_count: number;
}

export interface StepPreviewRequest {
	datasource_id: string;
	pipeline_steps: Array<{
		id: string;
		type: string;
		config: Record<string, unknown>;
		depends_on?: string[];
	}>;
	target_step_id: string;
	row_limit?: number;
	page?: number;
}

export interface StepPreviewResponse {
	step_id: string;
	columns: string[];
	column_types?: Record<string, string>;
	data: Array<Record<string, unknown>>;
	total_rows: number;
	page: number;
	page_size: number;
}

function isValidComputeStatus(status: unknown): status is ComputeStatus {
	return (
		status === 'pending' || status === 'running' || status === 'completed' || status === 'failed'
	);
}

function normalizeJob(raw: RawComputeJobResponse): ComputeJob {
	const status: ComputeStatus = isValidComputeStatus(raw.status) ? raw.status : 'pending';

	return {
		id: raw.job_id ?? raw.id ?? '',
		status,
		progress: raw.progress ?? 0,
		error: raw.error_message ?? raw.error ?? null,
		result: raw.data ?? raw.result,
		created_at: raw.created_at ?? '',
		updated_at: raw.updated_at ?? ''
	};
}

export async function executeAnalysis(analysisId: string): Promise<ComputeJob> {
	const raw = await apiRequest<RawComputeJobResponse>('/api/v1/compute/execute', {
		method: 'POST',
		body: JSON.stringify({
			analysis_id: analysisId,
			execute_mode: 'full',
			step_id: null
		})
	});
	return normalizeJob(raw);
}

export async function getComputeStatus(jobId: string): Promise<ComputeJob> {
	const raw = await apiRequest<RawComputeJobResponse>(`/api/v1/compute/status/${jobId}`);
	return normalizeJob(raw);
}

export async function previewStep(analysisId: string, stepId: string): Promise<PreviewResponse> {
	return apiRequest<PreviewResponse>('/api/v1/compute/preview', {
		method: 'POST',
		body: JSON.stringify({
			analysis_id: analysisId,
			execute_mode: 'preview',
			step_id: stepId
		})
	});
}

export async function previewStepData(request: StepPreviewRequest): Promise<StepPreviewResponse> {
	return apiRequest<StepPreviewResponse>('/api/v1/compute/preview', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}

export async function cancelJob(jobId: string): Promise<void> {
	await apiRequest<void>(`/api/v1/compute/${jobId}`, {
		method: 'DELETE'
	});
}

export async function cleanupJob(jobId: string): Promise<void> {
	await apiRequest<void>(`/api/v1/compute/${jobId}/cleanup`, {
		method: 'DELETE'
	});
}

// Engine lifecycle functions

export async function spawnEngine(analysisId: string): Promise<EngineStatusResponse> {
	return apiRequest<EngineStatusResponse>(`/api/v1/compute/engine/spawn/${analysisId}`, {
		method: 'POST'
	});
}

export async function sendKeepalive(analysisId: string): Promise<EngineStatusResponse> {
	return apiRequest<EngineStatusResponse>(`/api/v1/compute/engine/keepalive/${analysisId}`, {
		method: 'POST'
	});
}

export async function getEngineStatus(analysisId: string): Promise<EngineStatusResponse> {
	return apiRequest<EngineStatusResponse>(`/api/v1/compute/engine/status/${analysisId}`);
}

export async function shutdownEngine(analysisId: string): Promise<void> {
	await apiRequest<void>(`/api/v1/compute/engine/${analysisId}`, {
		method: 'DELETE'
	});
}

export async function listEngines(): Promise<EngineListResponse> {
	return apiRequest<EngineListResponse>('/api/v1/compute/engines');
}

export interface ExportRequest {
	datasource_id: string;
	pipeline_steps: Array<{
		id: string;
		type: string;
		config: Record<string, unknown>;
		depends_on?: string[];
	}>;
	target_step_id: string;
	format: 'csv' | 'parquet' | 'json' | 'ndjson';
	filename: string;
	destination: 'download' | 'filesystem';
}

export interface ExportResponse {
	success: boolean;
	filename: string;
	format: string;
	destination: string;
	file_path: string | null;
	message: string | null;
}

export async function exportData(request: ExportRequest): Promise<Blob | ExportResponse> {
	const response = await fetch('/api/v1/compute/export', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(request)
	});

	if (!response.ok) {
		const error = await response.json().catch(() => ({ detail: 'Export failed' }));
		throw new Error(error.detail || 'Export failed');
	}

	// For download destination, return blob for browser download
	if (request.destination === 'download') {
		return response.blob();
	}

	// For filesystem destination, return JSON response
	return response.json();
}

export function downloadBlob(blob: Blob, filename: string): void {
	const url = URL.createObjectURL(blob);
	const link = document.createElement('a');
	link.href = url;
	link.download = filename;
	document.body.appendChild(link);
	link.click();
	document.body.removeChild(link);
	URL.revokeObjectURL(url);
}

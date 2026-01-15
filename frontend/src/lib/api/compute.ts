import type { ComputeJob } from '$lib/types/compute';
import { apiRequest } from './client';

export async function executeAnalysis(analysisId: string): Promise<ComputeJob> {
	return apiRequest<ComputeJob>('/api/v1/compute/execute', {
		method: 'POST',
		body: JSON.stringify({
			analysis_id: analysisId,
			execute_mode: 'full'
		})
	});
}

export async function getComputeStatus(jobId: string): Promise<ComputeJob> {
	return apiRequest<ComputeJob>(`/api/v1/compute/status/${jobId}`);
}

export async function previewStep(analysisId: string, stepId: string): Promise<any> {
	return apiRequest('/api/v1/compute/preview', {
		method: 'POST',
		body: JSON.stringify({
			analysis_id: analysisId,
			execute_mode: 'preview',
			step_id: stepId
		})
	});
}

export async function cancelJob(jobId: string): Promise<void> {
	await apiRequest<void>(`/api/v1/compute/${jobId}`, {
		method: 'DELETE'
	});
}

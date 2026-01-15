export type ComputeStatus = 'pending' | 'running' | 'completed' | 'failed';

export interface ComputeJob {
	id: string;
	status: ComputeStatus;
	progress?: number;
	error?: string | null;
	result?: unknown;
	created_at: string;
	updated_at: string;
}

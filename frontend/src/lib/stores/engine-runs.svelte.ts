import { listEngineRuns, type EngineRun, type ListEngineRunsParams } from '$lib/api/engine-runs';

export type EngineRunsStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export class EngineRunsStore {
	runs = $state<EngineRun[]>([]);
	status = $state<EngineRunsStatus>('disconnected');
	error = $state<string | null>(null);

	private abortController: AbortController | null = null;
	private params: ListEngineRunsParams | undefined;

	load(params?: ListEngineRunsParams): void {
		if (
			sameParams(this.params, params) &&
			(this.status === 'connecting' || this.status === 'connected')
		) {
			return;
		}
		this.abortController?.abort();
		this.params = params;
		this.status = 'connecting';
		this.error = null;
		this.fetch();
	}

	refresh(): void {
		if (this.params === undefined && this.status === 'disconnected') return;
		this.abortController?.abort();
		this.status = 'connecting';
		this.error = null;
		this.fetch();
	}

	close(): void {
		this.abortController?.abort();
		this.abortController = null;
	}

	reset(): void {
		this.close();
		this.runs = [];
		this.status = 'disconnected';
		this.error = null;
	}

	private fetch(): void {
		this.abortController?.abort();
		const controller = new AbortController();
		this.abortController = controller;

		listEngineRuns(this.params).match(
			(runs) => {
				if (controller.signal.aborted) return;
				this.runs = runs;
				this.status = 'connected';
				this.error = null;
			},
			(err) => {
				if (controller.signal.aborted) return;
				this.error = err.message;
				this.status = 'error';
			}
		);
	}
}

function sameParams(a?: ListEngineRunsParams, b?: ListEngineRunsParams): boolean {
	if (a === b) return true;
	if (!a || !b) return a === b;
	return (
		a.analysis_id === b.analysis_id &&
		a.datasource_id === b.datasource_id &&
		a.kind === b.kind &&
		a.status === b.status &&
		a.limit === b.limit &&
		a.offset === b.offset
	);
}

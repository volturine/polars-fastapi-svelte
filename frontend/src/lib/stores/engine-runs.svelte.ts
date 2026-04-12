import { listEngineRuns, type EngineRun, type ListEngineRunsParams } from '$lib/api/engine-runs';

export type EngineRunsStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export class EngineRunsStore {
	runs = $state<EngineRun[]>([]);
	status = $state<EngineRunsStatus>('disconnected');
	error = $state<string | null>(null);

	private abortController: AbortController | null = null;
	private params: ListEngineRunsParams | undefined;
	private polling: ReturnType<typeof setInterval> | null = null;
	private pollIntervalMs = 5000;

	start(params?: ListEngineRunsParams): void {
		this.close();
		this.params = params;
		this.status = 'connecting';
		this.error = null;
		this.fetch();
		this.polling = setInterval(() => this.fetch(), this.pollIntervalMs);
	}

	close(): void {
		this.abortController?.abort();
		this.abortController = null;
		if (this.polling) {
			clearInterval(this.polling);
			this.polling = null;
		}
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

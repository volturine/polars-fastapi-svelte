import type { EngineStatusResponse } from '$lib/types/compute';
import { listEngines, shutdownEngine as shutdownEngineApi } from '$lib/api/compute';

const POLL_INTERVAL = 3000; // 3 seconds

class EnginesStore {
	engines = $state<EngineStatusResponse[]>([]);
	loading = $state(false);
	error = $state<string | null>(null);

	private interval: number | null = null;

	get count(): number {
		return this.engines.length;
	}

	get running(): EngineStatusResponse[] {
		return this.engines.filter((e) => e.status === 'running');
	}

	get idle(): EngineStatusResponse[] {
		return this.engines.filter((e) => e.status === 'idle');
	}

	async fetch(): Promise<void> {
		try {
			this.loading = true;
			this.error = null;
			const response = await listEngines();
			this.engines = response.engines;
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to fetch engines';
		} finally {
			this.loading = false;
		}
	}

	async shutdownEngine(analysisId: string): Promise<void> {
		try {
			await shutdownEngineApi(analysisId);
			this.engines = this.engines.filter((e) => e.analysis_id !== analysisId);
		} catch (err) {
			this.error = err instanceof Error ? err.message : 'Failed to shutdown engine';
			throw err;
		}
	}

	startPolling(): void {
		if (this.interval !== null) return;

		// Fetch immediately
		this.fetch();

		this.interval = window.setInterval(() => {
			this.fetch();
		}, POLL_INTERVAL);
	}

	stopPolling(): void {
		if (this.interval === null) return;

		window.clearInterval(this.interval);
		this.interval = null;
	}

	get isPolling(): boolean {
		return this.interval !== null;
	}
}

export const enginesStore = new EnginesStore();

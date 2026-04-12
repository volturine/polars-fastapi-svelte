import type { ActiveBuildSummary, BuildEvent } from '$lib/types/build-stream';
import { connectBuildsListStream } from '$lib/api/build-stream';
import type { StreamHandle } from '$lib/api/websocket';

const RECONNECT_DELAY_MS = 1_000;

export type ActiveBuildsStatus = 'disconnected' | 'connecting' | 'connected' | 'error';

export class ActiveBuildsStore {
	builds = $state<ActiveBuildSummary[]>([]);
	status = $state<ActiveBuildsStatus>('disconnected');
	error = $state<string | null>(null);

	private connection: StreamHandle | null = null;
	private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
	private shouldReconnect = false;

	count = $derived(this.builds.length);

	start(): void {
		this.shouldReconnect = true;
		this.openConnection();
	}

	close(): void {
		this.shouldReconnect = false;
		this.clearReconnectTimer();
		this.connection?.close();
		this.connection = null;
		this.status = 'disconnected';
	}

	reset(): void {
		this.close();
		this.builds = [];
		this.error = null;
	}

	private openConnection(): void {
		if (this.connection) return;
		this.clearReconnectTimer();
		this.error = null;
		this.status = 'connecting';

		this.connection = connectBuildsListStream({
			onSnapshot: (builds) => {
				this.builds = builds;
				this.status = 'connected';
				this.error = null;
			},
			onEvent: (event) => {
				this.applyEvent(event);
			},
			onError: (message) => {
				this.error = message;
				this.status = 'error';
			},
			onClose: () => {
				this.connection = null;
				if (!this.shouldReconnect) {
					this.status = 'disconnected';
					return;
				}
				this.scheduleReconnect();
			}
		});
	}

	private applyEvent(event: BuildEvent): void {
		const idx = this.builds.findIndex((b) => b.build_id === event.build_id);

		if (event.type === 'complete' || event.type === 'failed') {
			if (idx >= 0) {
				this.builds = this.builds.filter((b) => b.build_id !== event.build_id);
			}
			return;
		}

		if (idx < 0) return;

		if (event.type === 'progress') {
			const updated = { ...this.builds[idx] };
			updated.progress = event.progress;
			updated.elapsed_ms = event.elapsed_ms;
			updated.estimated_remaining_ms = event.estimated_remaining_ms;
			updated.current_step = event.current_step;
			updated.current_step_index = event.current_step_index;
			updated.total_steps = event.total_steps;
			const next = [...this.builds];
			next[idx] = updated;
			this.builds = next;
		}
	}

	private scheduleReconnect(): void {
		if (this.reconnectTimer !== null) return;
		this.reconnectTimer = setTimeout(() => {
			this.reconnectTimer = null;
			if (!this.shouldReconnect) return;
			this.openConnection();
		}, RECONNECT_DELAY_MS);
	}

	private clearReconnectTimer(): void {
		if (this.reconnectTimer === null) return;
		clearTimeout(this.reconnectTimer);
		this.reconnectTimer = null;
	}
}

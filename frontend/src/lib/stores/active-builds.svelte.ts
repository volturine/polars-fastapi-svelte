import type { ActiveBuildSummary } from '$lib/types/build-stream';
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

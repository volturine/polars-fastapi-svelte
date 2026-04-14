import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import type { ActiveBuildSummary } from '$lib/types/build-stream';

vi.mock('$lib/stores/clientIdentity.svelte', () => ({
	getClientIdentity: () => ({ clientId: 'client-1', clientSignature: 'signature-1' })
}));

vi.mock('$lib/stores/namespace.svelte', () => ({
	requireNamespace: () => 'default',
	isNamespaceReady: () => true
}));

type Listener = (event?: { data?: string; code?: number; reason?: string }) => void;

class MockWebSocket {
	static instances: MockWebSocket[] = [];

	url: string;
	readyState = 1;
	private listeners = new Map<string, Listener[]>();

	static readonly OPEN = 1;
	static readonly CONNECTING = 0;

	constructor(url: string) {
		this.url = url;
		MockWebSocket.instances.push(this);
	}

	addEventListener(type: string, listener: Listener) {
		this.listeners.set(type, [...(this.listeners.get(type) ?? []), listener]);
	}

	close() {
		this.emit('close', { code: 1000, reason: '' });
	}

	emit(type: string, event?: { data?: string; code?: number; reason?: string }) {
		for (const listener of this.listeners.get(type) ?? []) {
			listener(event);
		}
	}
}

const STARTER = { user_id: null, display_name: null, email: null, triggered_by: null };

function makeSummary(overrides: Partial<ActiveBuildSummary> = {}): ActiveBuildSummary {
	return {
		build_id: 'build-1',
		analysis_id: 'analysis-1',
		analysis_name: 'My Analysis',
		namespace: 'default',
		status: 'running',
		started_at: '2025-01-01T00:00:00Z',
		starter: STARTER,
		resource_config: null,
		progress: 0.3,
		elapsed_ms: 500,
		estimated_remaining_ms: 1000,
		current_step: 'Loading',
		current_step_index: 0,
		total_steps: 3,
		current_kind: 'preview',
		current_datasource_id: 'ds-1',
		current_tab_id: null,
		current_tab_name: null,
		current_output_id: null,
		current_output_name: null,
		current_engine_run_id: null,
		total_tabs: 1,
		cancelled_at: null,
		cancelled_by: null,
		...overrides
	};
}

function snapshot(socket: MockWebSocket, builds: ActiveBuildSummary[]) {
	socket.emit('message', { data: JSON.stringify({ type: 'snapshot', builds }) });
}

const { ActiveBuildsStore } = await import('./active-builds.svelte');

describe('ActiveBuildsStore', () => {
	beforeEach(() => {
		MockWebSocket.instances = [];
		vi.useFakeTimers();
		vi.stubGlobal('WebSocket', MockWebSocket);
	});

	afterEach(() => {
		vi.useRealTimers();
		vi.unstubAllGlobals();
	});

	test('initial state', () => {
		const store = new ActiveBuildsStore();
		expect(store.builds).toEqual([]);
		expect(store.status).toBe('disconnected');
		expect(store.error).toBeNull();
		expect(store.count).toBe(0);
	});

	test('start opens websocket to /v1/compute/ws/builds', () => {
		const store = new ActiveBuildsStore();
		store.start();
		expect(MockWebSocket.instances).toHaveLength(1);
		expect(MockWebSocket.instances[0].url).toContain('/v1/compute/ws/builds');
		expect(store.status).toBe('connecting');
		store.close();
	});

	test('applies snapshot', () => {
		const store = new ActiveBuildsStore();
		store.start();
		const socket = MockWebSocket.instances[0];

		const builds = [makeSummary(), makeSummary({ build_id: 'build-2' })];
		snapshot(socket, builds);

		expect(store.builds).toHaveLength(2);
		expect(store.status).toBe('connected');
		expect(store.error).toBeNull();
		expect(store.count).toBe(2);
		store.close();
	});

	test('snapshot replaces previous builds', () => {
		const store = new ActiveBuildsStore();
		store.start();
		const socket = MockWebSocket.instances[0];

		snapshot(socket, [makeSummary(), makeSummary({ build_id: 'build-2' })]);
		expect(store.builds).toHaveLength(2);

		snapshot(socket, [makeSummary({ build_id: 'build-3' })]);
		expect(store.builds).toHaveLength(1);
		expect(store.builds[0].build_id).toBe('build-3');
		store.close();
	});

	test('close stops connection', () => {
		const store = new ActiveBuildsStore();
		store.start();
		store.close();
		expect(store.status).toBe('disconnected');
	});

	test('reset clears builds and closes', () => {
		const store = new ActiveBuildsStore();
		store.start();
		const socket = MockWebSocket.instances[0];
		snapshot(socket, [makeSummary()]);
		expect(store.builds).toHaveLength(1);

		store.reset();
		expect(store.builds).toEqual([]);
		expect(store.status).toBe('disconnected');
		expect(store.error).toBeNull();
	});

	test('reconnects after unexpected close', () => {
		const store = new ActiveBuildsStore();
		store.start();
		const socket = MockWebSocket.instances[0];
		socket.emit('close', { code: 1006, reason: 'Connection lost' });

		expect(MockWebSocket.instances).toHaveLength(1);
		vi.advanceTimersByTime(1000);
		expect(MockWebSocket.instances).toHaveLength(2);
		store.close();
	});

	test('does not reconnect after explicit close', () => {
		const store = new ActiveBuildsStore();
		store.start();
		store.close();

		vi.advanceTimersByTime(5000);
		expect(MockWebSocket.instances).toHaveLength(1);
	});

	test('error callback sets error state', () => {
		const store = new ActiveBuildsStore();
		store.start();
		const socket = MockWebSocket.instances[0];
		socket.emit('error');

		expect(store.error).toBe('WebSocket connection failed');
		expect(store.status).toBe('error');
		store.close();
	});
});

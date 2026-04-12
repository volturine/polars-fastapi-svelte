import { afterEach, beforeEach, describe, expect, test, vi } from 'vitest';
import { EngineRunsStore } from './engine-runs.svelte';
import type { EngineRun } from '$lib/api/engine-runs';

const mockListEngineRuns = vi.fn();

vi.mock('$lib/api/engine-runs', () => ({
	listEngineRuns: (...args: unknown[]) => mockListEngineRuns(...args)
}));

function makeRun(overrides: Partial<EngineRun> = {}): EngineRun {
	return {
		id: 'run-1',
		analysis_id: null,
		datasource_id: 'ds-1',
		kind: 'datasource_update',
		status: 'success',
		request_json: {},
		result_json: null,
		error_message: null,
		created_at: '2024-06-15T12:00:00Z',
		completed_at: '2024-06-15T12:01:00Z',
		duration_ms: 60000,
		step_timings: {},
		query_plan: null,
		progress: 100,
		current_step: null,
		triggered_by: null,
		execution_entries: [],
		...overrides
	};
}

function mockOk(runs: EngineRun[]) {
	return { match: (onOk: (v: EngineRun[]) => void, _onErr: (e: unknown) => void) => onOk(runs) };
}

function mockErr(message: string) {
	return {
		match: (_onOk: (v: unknown) => void, onErr: (e: { message: string }) => void) =>
			onErr({ message })
	};
}

describe('EngineRunsStore', () => {
	beforeEach(() => {
		vi.useFakeTimers();
		mockListEngineRuns.mockReturnValue(mockOk([]));
	});

	afterEach(() => {
		vi.useRealTimers();
		vi.clearAllMocks();
	});

	test('initial state', () => {
		const store = new EngineRunsStore();
		expect(store.runs).toEqual([]);
		expect(store.status).toBe('disconnected');
		expect(store.error).toBeNull();
	});

	test('start sets status to connecting then connected on success', () => {
		const runs = [makeRun()];
		mockListEngineRuns.mockReturnValue(mockOk(runs));

		const store = new EngineRunsStore();
		store.start({ datasource_id: 'ds-1' });

		expect(store.status).toBe('connected');
		expect(store.runs).toEqual(runs);
		expect(store.error).toBeNull();
		expect(mockListEngineRuns).toHaveBeenCalledWith({ datasource_id: 'ds-1' });
		store.close();
	});

	test('start sets error status on fetch failure', () => {
		mockListEngineRuns.mockReturnValue(mockErr('Network error'));

		const store = new EngineRunsStore();
		store.start();

		expect(store.status).toBe('error');
		expect(store.error).toBe('Network error');
		store.close();
	});

	test('polling fetches at interval', () => {
		const store = new EngineRunsStore();
		store.start();
		expect(mockListEngineRuns).toHaveBeenCalledTimes(1);

		vi.advanceTimersByTime(5000);
		expect(mockListEngineRuns).toHaveBeenCalledTimes(2);

		vi.advanceTimersByTime(5000);
		expect(mockListEngineRuns).toHaveBeenCalledTimes(3);
		store.close();
	});

	test('close stops polling', () => {
		const store = new EngineRunsStore();
		store.start();
		expect(mockListEngineRuns).toHaveBeenCalledTimes(1);

		store.close();
		vi.advanceTimersByTime(15000);
		expect(mockListEngineRuns).toHaveBeenCalledTimes(1);
	});

	test('close when not started is safe', () => {
		const store = new EngineRunsStore();
		expect(() => store.close()).not.toThrow();
	});

	test('reset clears all state and stops polling', () => {
		const runs = [makeRun()];
		mockListEngineRuns.mockReturnValue(mockOk(runs));

		const store = new EngineRunsStore();
		store.start();
		expect(store.runs).toHaveLength(1);

		store.reset();
		expect(store.runs).toEqual([]);
		expect(store.status).toBe('disconnected');
		expect(store.error).toBeNull();

		vi.advanceTimersByTime(15000);
		expect(mockListEngineRuns).toHaveBeenCalledTimes(1);
	});

	test('start closes previous polling and restarts', () => {
		const store = new EngineRunsStore();
		store.start({ datasource_id: 'ds-1' });
		expect(mockListEngineRuns).toHaveBeenCalledTimes(1);

		store.start({ datasource_id: 'ds-2' });
		expect(mockListEngineRuns).toHaveBeenCalledTimes(2);
		expect(mockListEngineRuns).toHaveBeenLastCalledWith({ datasource_id: 'ds-2' });
		store.close();
	});

	test('start clears previous error', () => {
		mockListEngineRuns.mockReturnValue(mockErr('fail'));
		const store = new EngineRunsStore();
		store.start();
		expect(store.error).toBe('fail');

		mockListEngineRuns.mockReturnValue(mockOk([]));
		store.start();
		expect(store.error).toBeNull();
		expect(store.status).toBe('connected');
		store.close();
	});

	test('params are forwarded to listEngineRuns', () => {
		const store = new EngineRunsStore();
		store.start({ datasource_id: 'ds-42', limit: 25 });
		expect(mockListEngineRuns).toHaveBeenCalledWith({ datasource_id: 'ds-42', limit: 25 });
		store.close();
	});

	test('no params calls listEngineRuns with undefined', () => {
		const store = new EngineRunsStore();
		store.start();
		expect(mockListEngineRuns).toHaveBeenCalledWith(undefined);
		store.close();
	});

	test('subsequent poll success updates runs', () => {
		const store = new EngineRunsStore();
		mockListEngineRuns.mockReturnValue(mockOk([makeRun({ id: 'run-1' })]));
		store.start();
		expect(store.runs).toHaveLength(1);

		mockListEngineRuns.mockReturnValue(
			mockOk([makeRun({ id: 'run-1' }), makeRun({ id: 'run-2' })])
		);
		vi.advanceTimersByTime(5000);
		expect(store.runs).toHaveLength(2);
		store.close();
	});

	test('poll error after success sets error status', () => {
		const store = new EngineRunsStore();
		mockListEngineRuns.mockReturnValue(mockOk([makeRun()]));
		store.start();
		expect(store.status).toBe('connected');

		mockListEngineRuns.mockReturnValue(mockErr('Server down'));
		vi.advanceTimersByTime(5000);
		expect(store.status).toBe('error');
		expect(store.error).toBe('Server down');
		store.close();
	});
});

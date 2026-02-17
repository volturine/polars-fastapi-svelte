import { SvelteMap } from 'svelte/reactivity';
import type { EngineRun } from '$lib/api/engine-runs';

type SnapshotRef = { snapshot_id: string; timestamp_ms: number };

export function buildSnapshotMap(
	runs: EngineRun[],
	snapshots: SnapshotRef[]
): SvelteMap<string, string> {
	const sorted = [...snapshots].sort((a, b) => b.timestamp_ms - a.timestamp_ms);
	const map = new SvelteMap<string, string>();
	for (const run of runs) {
		const result = run.result_json ?? {};
		const direct = result.snapshot_id;
		if (typeof direct === 'string' && direct.length > 0) {
			map.set(run.id, direct);
			continue;
		}
		if (typeof direct === 'number') {
			map.set(run.id, String(direct));
			continue;
		}
		const runTime = Date.parse(run.created_at);
		if (Number.isNaN(runTime)) continue;
		const match = sorted.find((snap) => snap.timestamp_ms <= runTime);
		if (match) {
			map.set(run.id, match.snapshot_id);
		}
	}
	return map;
}

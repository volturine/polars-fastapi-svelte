export type {
	ActiveBuildDetail,
	ActiveBuildSummary,
	BuildDetailSnapshot,
	BuildsSnapshot,
	BuildEvent,
	BuildLogLevel,
	EngineRunKind,
	BuildQueryPlanSnapshot,
	BuildStepSnapshot,
	BuildTabStatus,
	BuildWebsocketErrorMessage
} from './build-stream.generated';

export type BuildStatus =
	| 'connecting'
	| 'queued'
	| 'running'
	| 'completed'
	| 'failed'
	| 'cancelled'
	| 'disconnected';

import type {
	BuildLogEntry,
	BuildResourceConfigSummary,
	BuildResourceSnapshot,
	BuildStepState,
	BuildTabResult,
	EngineRunKind
} from './build-stream.generated';

export type StepInfo = {
	buildStepIndex: number;
	stepIndex: number;
	stepId: string;
	name: string;
	stepType: string;
	tabId: string | null;
	tabName: string | null;
	state: BuildStepState;
	duration: number | null;
	rowCount: number | null;
	error: string | null;
};

export type QueryPlan = {
	tabId: string | null;
	tabName: string | null;
	optimized: string;
	unoptimized: string;
};

export type {
	BuildLogEntry,
	BuildResourceConfigSummary,
	BuildResourceSnapshot,
	BuildStepState,
	BuildTabResult
};

const ENGINE_RUN_KINDS = new Set<EngineRunKind>(['build', 'preview', 'row_count', 'download']);

export function readEngineRunKind(value: unknown): EngineRunKind | null {
	return typeof value === 'string' && ENGINE_RUN_KINDS.has(value as EngineRunKind)
		? (value as EngineRunKind)
		: null;
}

export type {
	ActiveBuildDetail,
	ActiveBuildSummary,
	BuildDetailSnapshot,
	BuildEvent,
	BuildLogLevel,
	BuildQueryPlanSnapshot,
	BuildStepSnapshot,
	BuildTabStatus,
	BuildWebsocketErrorMessage,
	BuildsSnapshot
} from './build-stream.generated';

export type BuildStatus =
	| 'connecting'
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
	BuildTabResult
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

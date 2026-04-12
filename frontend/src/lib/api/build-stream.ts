import type { BuildRequest } from './compute';
import { apiRequest } from './client';
import { createStream, type StreamHandle } from './websocket';
import type { BuildEvent, BuildDetailSnapshot, BuildsSnapshot } from '$lib/types/build-stream';
import type { ActiveBuildDetail } from '$lib/types/build-stream';
import type { ResultAsync } from 'neverthrow';
import type { ApiError } from './client';

export type BuildStreamMessage =
	| { type: 'snapshot'; build: BuildDetailSnapshot['build'] }
	| BuildEvent;
export type BuildsListMessage = BuildsSnapshot | BuildEvent;

export interface BuildStreamCallbacks {
	onSnapshot: (build: BuildDetailSnapshot['build']) => void;
	onEvent: (event: BuildEvent) => void;
	onError: (error: string) => void;
	onClose: () => void;
}

export interface BuildsListCallbacks {
	onSnapshot: (builds: BuildsSnapshot['builds']) => void;
	onEvent: (event: BuildEvent) => void;
	onError: (error: string) => void;
	onClose: () => void;
}

function parseBuildMessage(data: string): BuildStreamMessage | null {
	try {
		return JSON.parse(data) as BuildStreamMessage;
	} catch {
		return null;
	}
}

function parseBuildsMessage(data: string): BuildsListMessage | null {
	try {
		return JSON.parse(data) as BuildsListMessage;
	} catch {
		return null;
	}
}

export function startActiveBuild(request: BuildRequest): ResultAsync<ActiveBuildDetail, ApiError> {
	return apiRequest<ActiveBuildDetail>('/v1/compute/builds/active', {
		method: 'POST',
		body: JSON.stringify(request)
	});
}

export function connectBuildsListStream(callbacks: BuildsListCallbacks): StreamHandle {
	return createStream<BuildsSnapshot['builds'], BuildEvent>('/v1/compute/ws/builds', {
		parse: parseBuildsMessage,
		isSnapshot: (msg) => msg.type === 'snapshot',
		extractSnapshot: (msg) => (msg as BuildsSnapshot).builds,
		extractEvent: (msg) => msg as unknown as BuildEvent,
		callbacks
	});
}

export function connectBuildDetailStream(
	buildId: string,
	callbacks: BuildStreamCallbacks
): StreamHandle {
	return createStream<BuildDetailSnapshot['build'], BuildEvent>(
		`/v1/compute/ws/builds/${buildId}`,
		{
			parse: parseBuildMessage,
			isSnapshot: (msg) => msg.type === 'snapshot',
			extractSnapshot: (msg) => (msg as BuildDetailSnapshot).build,
			extractEvent: (msg) => msg as unknown as BuildEvent,
			callbacks
		}
	);
}

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
export type BuildsListMessage = BuildsSnapshot;

export interface BuildStreamCallbacks {
	onSnapshot: (build: BuildDetailSnapshot['build']) => void;
	onEvent: (event: BuildEvent) => void;
	onError: (error: string) => void;
	onClose: () => void;
}

export interface BuildsListCallbacks {
	onSnapshot: (builds: BuildsSnapshot['builds']) => void;
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

function isBuildsSnapshot(msg: BuildsListMessage): msg is BuildsSnapshot {
	return msg.type === 'snapshot';
}

function isBuildDetailSnapshot(msg: BuildStreamMessage): msg is BuildDetailSnapshot {
	return msg.type === 'snapshot';
}

function toBuildDetailEvent(msg: BuildStreamMessage): BuildEvent {
	if (isBuildDetailSnapshot(msg)) {
		throw new Error('Expected build event');
	}
	return msg;
}

function getBuildsSnapshot(msg: BuildsListMessage): BuildsSnapshot['builds'] {
	if (!isBuildsSnapshot(msg)) {
		throw new Error('Expected builds snapshot');
	}
	return msg.builds;
}

function getBuildDetailSnapshot(msg: BuildStreamMessage): BuildDetailSnapshot['build'] {
	if (!isBuildDetailSnapshot(msg)) {
		throw new Error('Expected build snapshot');
	}
	return msg.build;
}

export function connectBuildsListStream(callbacks: BuildsListCallbacks): StreamHandle {
	return createStream<BuildsSnapshot['builds'], never, BuildsListMessage>('/v1/compute/ws/builds', {
		parse: parseBuildsMessage,
		isSnapshot: isBuildsSnapshot,
		extractSnapshot: getBuildsSnapshot,
		callbacks
	});
}

export function connectBuildDetailStream(
	buildId: string,
	callbacks: BuildStreamCallbacks
): StreamHandle {
	return createStream<BuildDetailSnapshot['build'], BuildEvent, BuildStreamMessage>(
		`/v1/compute/ws/builds/${buildId}`,
		{
			parse: parseBuildMessage,
			isSnapshot: isBuildDetailSnapshot,
			extractSnapshot: getBuildDetailSnapshot,
			extractEvent: toBuildDetailEvent,
			callbacks
		}
	);
}

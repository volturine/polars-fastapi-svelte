import { buildWebsocketUrl } from './websocket';
import type { BuildEvent, BuildDetailSnapshot, BuildsSnapshot } from '$lib/types/build-stream';

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

export function connectBuildStream(
	request: Record<string, unknown>,
	callbacks: BuildStreamCallbacks
): { close: () => void } {
	const url = buildWebsocketUrl('/v1/compute/ws/build');
	const socket = new WebSocket(url);

	socket.addEventListener('open', () => {
		socket.send(JSON.stringify(request));
	});

	socket.addEventListener('message', (event) => {
		const msg = parseBuildMessage(event.data as string);
		if (!msg) return;
		if (msg.type === 'snapshot') {
			callbacks.onSnapshot((msg as BuildDetailSnapshot).build);
			return;
		}
		callbacks.onEvent(msg as BuildEvent);
	});

	socket.addEventListener('error', () => {
		callbacks.onError('WebSocket connection failed');
	});

	socket.addEventListener('close', (event) => {
		if (event.code !== 1000 && event.code !== 1005) {
			callbacks.onError(event.reason || `Connection closed (code ${event.code})`);
		}
		callbacks.onClose();
	});

	return {
		close() {
			if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
				socket.close(1000);
			}
		}
	};
}

export function connectBuildsListStream(callbacks: BuildsListCallbacks): { close: () => void } {
	const url = buildWebsocketUrl('/v1/compute/ws/builds');
	const socket = new WebSocket(url);

	socket.addEventListener('message', (event) => {
		const msg = parseBuildsMessage(event.data as string);
		if (!msg) return;
		if (msg.type === 'snapshot') {
			callbacks.onSnapshot((msg as BuildsSnapshot).builds);
			return;
		}
		callbacks.onEvent(msg as BuildEvent);
	});

	socket.addEventListener('error', () => {
		callbacks.onError('WebSocket connection failed');
	});

	socket.addEventListener('close', (event) => {
		if (event.code !== 1000 && event.code !== 1005) {
			callbacks.onError(event.reason || `Connection closed (code ${event.code})`);
		}
		callbacks.onClose();
	});

	return {
		close() {
			if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
				socket.close(1000);
			}
		}
	};
}

export function connectBuildDetailStream(
	buildId: string,
	callbacks: BuildStreamCallbacks
): { close: () => void } {
	const url = buildWebsocketUrl(`/v1/compute/ws/builds/${buildId}`);
	const socket = new WebSocket(url);

	socket.addEventListener('message', (event) => {
		const msg = parseBuildMessage(event.data as string);
		if (!msg) return;
		if (msg.type === 'snapshot') {
			callbacks.onSnapshot((msg as BuildDetailSnapshot).build);
			return;
		}
		callbacks.onEvent(msg as BuildEvent);
	});

	socket.addEventListener('error', () => {
		callbacks.onError('WebSocket connection failed');
	});

	socket.addEventListener('close', (event) => {
		if (event.code !== 1000 && event.code !== 1005) {
			callbacks.onError(event.reason || `Connection closed (code ${event.code})`);
		}
		callbacks.onClose();
	});

	return {
		close() {
			if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
				socket.close(1000);
			}
		}
	};
}

import { apiRequest } from './client';

export interface UserPublic {
	id: string;
	email: string;
	display_name: string;
	avatar_url: string | null;
	status: string;
	email_verified: boolean;
	has_password: boolean;
	preferences: Record<string, unknown>;
	providers: string[];
	created_at: string;
}

interface RegisterPayload {
	email: string;
	password: string;
	display_name: string;
}

interface LoginPayload {
	email: string;
	password: string;
}

interface UpdateProfilePayload {
	display_name?: string;
	avatar_url?: string | null;
	preferences?: Record<string, unknown>;
}

interface ChangePasswordPayload {
	current_password: string;
	new_password: string;
}

export function register(payload: RegisterPayload) {
	return apiRequest<UserPublic>('/v1/auth/register', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function login(payload: LoginPayload) {
	return apiRequest<UserPublic>('/v1/auth/login', {
		method: 'POST',
		body: JSON.stringify(payload)
	});
}

export function logout() {
	return apiRequest<{ success: boolean }>('/v1/auth/logout', {
		method: 'POST'
	});
}

export function getMe() {
	return apiRequest<UserPublic>('/v1/auth/me');
}

export function updateProfile(payload: UpdateProfilePayload) {
	return apiRequest<UserPublic>('/v1/auth/profile', {
		method: 'PUT',
		body: JSON.stringify(payload)
	});
}

export function changePassword(payload: ChangePasswordPayload) {
	return apiRequest<{ success: boolean }>('/v1/auth/password', {
		method: 'PUT',
		body: JSON.stringify(payload)
	});
}

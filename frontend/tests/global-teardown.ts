import { request } from '@playwright/test';
import { purgeE2eResources } from './utils/api.js';

export default async function globalTeardown() {
	const ctx = await request.newContext();
	await purgeE2eResources(ctx);
	await ctx.dispose();
}

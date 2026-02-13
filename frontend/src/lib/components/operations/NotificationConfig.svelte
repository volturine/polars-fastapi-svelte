<script lang="ts">
	type NotificationConfigData = {
		method: 'email' | 'telegram';
		recipient: string;
		subject_template: string;
		body_template: string;
		attach_result: boolean;
		attach_error: boolean;
		webhook_url?: string | null;
		timeout_seconds?: number;
		retries?: number;
	};

	interface Props {
		config?: Record<string, unknown>;
		configFlags?: { smtpEnabled: boolean; telegramEnabled: boolean };
	}

	const defaultConfig: NotificationConfigData = {
		method: 'email',
		recipient: '',
		subject_template: 'Build Complete: {{analysis_name}}',
		body_template:
			'Analysis: {{analysis_name}}\nStatus: {{status}}\nDuration: {{duration_ms}}ms\nRows: {{row_count}}',
		attach_result: false,
		attach_error: true,
		webhook_url: null,
		timeout_seconds: 20,
		retries: 0
	};

	let {
		config = $bindable(defaultConfig),
		configFlags = { smtpEnabled: true, telegramEnabled: true }
	}: Props = $props();
	let notifyConfig = $derived.by(() => config as NotificationConfigData);

	const canEmail = $derived(configFlags.smtpEnabled);
	const canTelegram = $derived(configFlags.telegramEnabled);
	const isReady = $derived(
		(notifyConfig.method === 'email' && canEmail) ||
			(notifyConfig.method === 'telegram' && canTelegram)
	);
</script>

<div class="config-panel" role="region" aria-label="Notification configuration">
	<h3>Notification</h3>

	{#if !isReady}
		<div class="rounded-sm border border-tertiary bg-bg-secondary p-3 text-sm text-fg-tertiary">
			Notifications are disabled until SMTP or Telegram settings are configured on the server.
		</div>
	{/if}

	<div class="form-group mb-4">
		<label for="notify-method">Method</label>
		<select id="notify-method" bind:value={notifyConfig.method}>
			<option value="email" disabled={!canEmail}>Email (SMTP)</option>
			<option value="telegram" disabled={!canTelegram}>Telegram</option>
		</select>
	</div>

	<div class="form-group mb-4">
		<label for="notify-recipient">
			{notifyConfig.method === 'email' ? 'Email Address' : 'Telegram Chat ID'}
		</label>
		<input
			id="notify-recipient"
			type="text"
			bind:value={notifyConfig.recipient}
			placeholder={notifyConfig.method === 'email' ? 'user@example.com' : '123456789'}
		/>
	</div>

	<div class="form-group mb-4">
		<label for="notify-subject">Subject Template</label>
		<input id="notify-subject" type="text" bind:value={notifyConfig.subject_template} />
	</div>

	<div class="form-group mb-4">
		<label for="notify-body">Body Template</label>
		<textarea id="notify-body" rows="6" bind:value={notifyConfig.body_template}></textarea>
		<span class="hint mt-1 block text-xs text-fg-muted">
			Use {'{{analysis_name}}'}, {'{{status}}'}, {'{{duration_ms}}'}, {'{{row_count}}'} in templates
		</span>
	</div>

	<div class="form-group mb-4">
		<label for="notify-webhook">Webhook URL (optional)</label>
		<input
			id="notify-webhook"
			type="text"
			bind:value={notifyConfig.webhook_url}
			placeholder="https://hooks.example.com/notify"
		/>
	</div>

	<div class="form-group mb-4">
		<label for="notify-timeout">Timeout (seconds)</label>
		<input id="notify-timeout" type="number" min="1" bind:value={notifyConfig.timeout_seconds} />
	</div>

	<div class="form-group mb-4">
		<label for="notify-retries">Retries</label>
		<input id="notify-retries" type="number" min="0" max="5" bind:value={notifyConfig.retries} />
	</div>

	<div class="form-group mb-0">
		<label class="flex cursor-pointer items-center gap-2">
			<input type="checkbox" bind:checked={notifyConfig.attach_error} />
			<span>Attach error details on failure</span>
		</label>
	</div>
</div>

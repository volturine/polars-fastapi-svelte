<script lang="ts">
	import type { Schema } from '$lib/types/schema';
	import type { Subscriber } from '$lib/api/settings';
	import type { NotificationConfigData } from '$lib/utils/step-config-defaults';
	import { getSubscribers } from '$lib/api/settings';
	import { createQuery } from '@tanstack/svelte-query';
	import MultiSelectColumnDropdown from '$lib/components/common/MultiSelectColumnDropdown.svelte';
	import { Search } from 'lucide-svelte';

	interface Props {
		config?: NotificationConfigData;
		schema: Schema;
		configFlags?: { smtpEnabled: boolean; telegramEnabled: boolean };
	}

	const defaultConfig: NotificationConfigData = {
		method: 'email',
		recipient: '',
		subscriber_ids: [],
		bot_token: '',
		input_columns: [],
		output_column: 'notification_status',
		message_template: '{{message}}',
		subject_template: 'Notification',
		batch_size: 10,
		timeout_seconds: 20
	};

	let {
		config = $bindable(defaultConfig),
		schema,
		configFlags = { smtpEnabled: true, telegramEnabled: true }
	}: Props = $props();

	const canEmail = $derived(configFlags.smtpEnabled);
	const canTelegram = $derived(configFlags.telegramEnabled);
	const method = $derived(config?.method ?? 'email');
	const inputColumns = $derived.by(() =>
		Array.isArray(config?.input_columns) ? config.input_columns : []
	);
	const subscriberIds = $derived.by(() =>
		Array.isArray(config?.subscriber_ids) ? config.subscriber_ids : []
	);
	const isReady = $derived(
		(method === 'email' && canEmail) || (method === 'telegram' && canTelegram)
	);
	let search = $state('');

	const subscribersQuery = createQuery(() => ({
		queryKey: ['telegram-subscribers'],
		queryFn: async () => {
			const result = await getSubscribers();
			if (result.isErr()) throw new Error(result.error.message);
			return result.value;
		},
		staleTime: 30_000,
		enabled: canTelegram
	}));

	const activeSubscribers = $derived(
		(subscribersQuery.data ?? []).filter((s: Subscriber) => s.is_active)
	);

	const filtered = $derived.by(() => {
		const q = search.toLowerCase().trim();
		if (!q) return activeSubscribers;
		return activeSubscribers.filter(
			(s: Subscriber) => s.title.toLowerCase().includes(q) || s.chat_id.toLowerCase().includes(q)
		);
	});

	function handleColumnsChange(columns: string[]) {
		config.input_columns = columns;
	}

	function toggleSubscriber(chatId: string) {
		const next = [...subscriberIds];
		const idx = next.indexOf(chatId);
		if (idx >= 0) {
			next.splice(idx, 1);
		} else {
			next.push(chatId);
		}
		config.subscriber_ids = next;
		if (config.method === 'telegram') {
			config.recipient = next.join(',');
		}
	}

	function isSelected(chatId: string): boolean {
		return subscriberIds.includes(chatId);
	}

	const placeholderHint = $derived.by(() => {
		if (inputColumns.length === 0) return 'Select column(s), then use {{column_name}} in template';
		if (inputColumns.length === 1)
			return `Use {{${inputColumns[0]}}} to reference the column value`;
		return `Use {{${inputColumns.join('}}, {{')}}} in template`;
	});
</script>

<div class="config-panel" role="region" aria-label="Notification configuration">
	<h3>Notification (UDF)</h3>

	{#if !isReady}
		<div class="rounded-sm border border-tertiary bg-bg-secondary p-3 text-sm text-fg-tertiary">
			Configure SMTP or Telegram in global settings first.
		</div>
	{/if}

	<div class="form-group mb-4">
		<label for="notify-method">Method</label>
		<select id="notify-method" bind:value={config.method}>
			<option value="email" disabled={!canEmail}>Email (SMTP)</option>
			<option value="telegram" disabled={!canTelegram}>Telegram</option>
		</select>
	</div>

	<div class="form-group mb-4">
		<label for="notify-recipient">
			{method === 'email' ? 'Email Address' : 'Recipients'}
		</label>
		{#if method === 'email'}
			<input
				id="notify-recipient"
				type="text"
				bind:value={config.recipient}
				placeholder="user@example.com"
			/>
		{:else}
			<div class="flex flex-col gap-2">
				<div class="relative">
					<Search
						size={12}
						class="pointer-events-none absolute left-2 top-1/2 -translate-y-1/2 text-fg-muted"
					/>
					<input
						class="resource-input w-full border border-tertiary bg-secondary py-1 pl-7 pr-2 text-xs text-fg-primary"
						placeholder="Search subscribers..."
						value={search}
						oninput={(e) => (search = e.currentTarget.value)}
					/>
				</div>
				<div class="max-h-32 overflow-y-auto border border-tertiary bg-secondary">
					{#if subscribersQuery.isPending}
						<div class="p-2 text-center text-[10px] text-fg-muted">Loading...</div>
					{:else if subscribersQuery.isError}
						<div class="p-2 text-center text-[10px] text-error">Failed to load subscribers</div>
					{:else if activeSubscribers.length === 0}
						<div class="p-2 text-center text-[10px] text-fg-muted">
							No subscribers. Users can subscribe via /subscribe in Telegram.
						</div>
					{:else if filtered.length === 0}
						<div class="p-2 text-center text-[10px] text-fg-muted">No matches</div>
					{:else}
						{#each filtered as sub (sub.id)}
							<label
								class="flex cursor-pointer items-center gap-2 border-b border-tertiary px-2 py-1.5 last:border-b-0 hover:bg-tertiary"
							>
								<input
									type="checkbox"
									checked={isSelected(sub.chat_id)}
									onchange={() => toggleSubscriber(sub.chat_id)}
								/>
								<span class="truncate text-xs text-fg-primary">{sub.title}</span>
								<span class="ml-auto shrink-0 text-[10px] text-fg-muted">
									{sub.chat_id}
								</span>
							</label>
						{/each}
					{/if}
				</div>
			</div>
		{/if}
	</div>

	<!-- svelte-ignore a11y_label_has_associated_control -->
	<div class="form-group mb-4">
		<label>Input Column(s)</label>
		<MultiSelectColumnDropdown
			{schema}
			value={inputColumns}
			onChange={handleColumnsChange}
			placeholder="Select column(s)..."
			showSelectAll={false}
		/>
	</div>

	<div class="form-group mb-4">
		<label for="notify-output">Output Column</label>
		<input
			id="notify-output"
			type="text"
			bind:value={config.output_column}
			placeholder="notification_status"
		/>
	</div>

	{#if config.method === 'email'}
		<div class="form-group mb-4">
			<label for="notify-subject">Subject Template</label>
			<input id="notify-subject" type="text" bind:value={config.subject_template} />
		</div>
	{/if}

	<div class="form-group mb-0">
		<label for="notify-message">Message Template</label>
		<textarea id="notify-message" rows="4" bind:value={config.message_template}></textarea>
		<span class="hint mt-1 block text-xs text-fg-muted">
			{placeholderHint}
		</span>
	</div>
</div>

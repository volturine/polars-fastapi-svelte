<script lang="ts">
	type AIConfigData = {
		provider: 'ollama' | 'openai';
		model: string;
		input_column: string;
		output_column: string;
		prompt_template: string;
		batch_size: number;
		endpoint_url?: string | null;
		api_key?: string | null;
		request_options?: string | null;
	};

	interface Props {
		config?: Record<string, unknown>;
	}

	const defaultConfig: AIConfigData = {
		provider: 'ollama',
		model: 'llama2',
		input_column: '',
		output_column: 'ai_result',
		prompt_template: 'Classify this text: {{text}}',
		batch_size: 10,
		endpoint_url: null,
		api_key: null,
		request_options: null
	};

	let { config = $bindable(defaultConfig) }: Props = $props();
	let aiConfig = $derived.by(() => config as AIConfigData);

	const ollamaModels = ['llama2', 'codellama', 'mistral', 'neural-chat'];
	const openaiModels = ['gpt-4o', 'gpt-4-turbo', 'gpt-3.5-turbo'];

	const availableModels = $derived(aiConfig.provider === 'ollama' ? ollamaModels : openaiModels);
</script>

<div class="config-panel" role="region" aria-label="AI configuration">
	<h3>AI</h3>

	<div class="form-group mb-4">
		<label for="ai-provider">Provider</label>
		<select id="ai-provider" bind:value={aiConfig.provider}>
			<option value="ollama">Ollama (Local)</option>
			<option value="openai">OpenAI (Cloud)</option>
		</select>
	</div>

	<div class="form-group mb-4">
		<label for="ai-model">Model</label>
		<select id="ai-model" bind:value={aiConfig.model}>
			{#each availableModels as model (model)}
				<option value={model}>{model}</option>
			{/each}
		</select>
	</div>

	<div class="form-group mb-4">
		<label for="ai-endpoint">Endpoint URL</label>
		<input
			id="ai-endpoint"
			type="text"
			bind:value={aiConfig.endpoint_url}
			placeholder={aiConfig.provider === 'openai'
				? 'https://api.openai.com'
				: 'http://localhost:11434'}
		/>
	</div>

	<div class="form-group mb-4">
		<label for="ai-api-key">API Key (optional)</label>
		<input id="ai-api-key" type="password" bind:value={aiConfig.api_key} placeholder="sk-..." />
	</div>

	<div class="form-group mb-4">
		<label for="ai-input">Input Column (Text)</label>
		<input id="ai-input" type="text" bind:value={aiConfig.input_column} placeholder="Column name" />
		<span class="hint mt-1 block text-xs text-fg-muted"> Use a text column in your dataset </span>
	</div>

	<div class="form-group mb-4">
		<label for="ai-output">Output Column</label>
		<input id="ai-output" type="text" bind:value={aiConfig.output_column} placeholder="ai_result" />
	</div>

	<div class="form-group mb-4">
		<label for="ai-prompt">Prompt Template</label>
		<textarea id="ai-prompt" rows="4" bind:value={aiConfig.prompt_template}></textarea>
		<span class="hint mt-1 block text-xs text-fg-muted">
			Use {'{{text}}'} to reference the input column
		</span>
	</div>

	<div class="form-group mb-4">
		<label for="ai-options">Request Options (JSON)</label>
		<textarea id="ai-options" rows="3" bind:value={aiConfig.request_options}></textarea>
		<span class="hint mt-1 block text-xs text-fg-muted">
			Example: {`{"temperature": 0.2}`}
		</span>
	</div>

	<div class="form-group mb-0">
		<label for="ai-batch">Batch Size</label>
		<input id="ai-batch" type="number" min="1" max="100" bind:value={aiConfig.batch_size} />
	</div>
</div>

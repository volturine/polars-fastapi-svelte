<script lang="ts">
	let health: { status: string; version: string } | null = $state(null);
	let error: string | null = $state(null);

	$effect(() => {
		fetch('http://127.0.0.1:8000/api/v1/health')
			.then((res) => res.json())
			.then((data) => {
				health = data;
			})
			.catch((err) => {
				error = 'Failed to connect to backend';
				console.error(err);
			});
	});
</script>

<main style="font-family: sans-serif; text-align: center; margin-top: 50px;">
	<h1>Svelte 5 + FastAPI Template</h1>

	{#if health}
		<p style="color: green;">
			Backend Status: <strong>{health.status}</strong> (v{health.version})
		</p>
	{:else if error}
		<p style="color: red;">{error}</p>
	{:else}
		<p>Connecting to backend...</p>
	{/if}

	<p>
		Edit <code>frontend/src/routes/+page.svelte</code> to change this page.
	</p>
</main>

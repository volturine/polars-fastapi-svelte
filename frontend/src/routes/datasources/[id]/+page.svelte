<script lang="ts">
	import { goto } from '$app/navigation';
	import { page } from '$app/state';
	
	const id = page.params.id;
	if (id) {
		goto(`/datasources?id=${id}`, { replaceState: true });
	}
</script>

<div class="p-8 text-center">
	<p>Redirecting...</p>
</div>

# SvelteKit Structure

Documentation for the SvelteKit application structure and routing.

## Overview

The frontend uses SvelteKit 2 with file-based routing. Pages are organized under `src/routes/` with shared code in `src/lib/`.

## Directory Structure

```
frontend/src/
├── routes/                      # File-based routing
│   ├── +layout.svelte          # Root layout (global)
│   ├── +layout.ts              # Layout load function
│   ├── +page.svelte            # Home page (Gallery)
│   │
│   ├── analysis/
│   │   ├── new/
│   │   │   └── +page.svelte    # Create analysis wizard
│   │   └── [id]/
│   │       ├── +page.svelte    # Pipeline editor
│   │       └── +page.ts        # Page load function
│   │
│   └── datasources/
│       ├── +page.svelte        # Datasource list
│       └── new/
│           └── +page.svelte    # Add datasource form
│
├── lib/                         # Shared code ($lib alias)
│   ├── api/                    # HTTP client layer
│   ├── components/             # Svelte components
│   ├── stores/                 # Reactive state
│   ├── types/                  # TypeScript types
│   └── utils/                  # Utilities
│
├── app.d.ts                    # App-level type declarations
└── app.html                    # HTML template
```

## Routing

### File-Based Routes

| File | URL | Description |
|------|-----|-------------|
| `routes/+page.svelte` | `/` | Home (Gallery) |
| `routes/analysis/new/+page.svelte` | `/analysis/new` | Create wizard |
| `routes/analysis/[id]/+page.svelte` | `/analysis/:id` | Pipeline editor |
| `routes/datasources/+page.svelte` | `/datasources` | Datasource list |
| `routes/datasources/new/+page.svelte` | `/datasources/new` | Add datasource |

### Dynamic Routes

The `[id]` folder creates a dynamic segment:

```
/analysis/abc-123  →  routes/analysis/[id]/+page.svelte
/analysis/xyz-789  →  routes/analysis/[id]/+page.svelte
```

Access the parameter in the page:

```typescript
// +page.ts
export const load = ({ params }) => {
    return { analysisId: params.id };
};
```

```svelte
<!-- +page.svelte -->
<script lang="ts">
    let { data } = $props();
    // data.analysisId = 'abc-123'
</script>
```

## Layout System

### Root Layout

```svelte
<!-- routes/+layout.svelte -->
<script lang="ts">
    import { QueryClientProvider } from '@tanstack/svelte-query';
    import { queryClient } from '$lib/api/client';

    let { children } = $props();
</script>

<QueryClientProvider client={queryClient}>
    <div class="app">
        <nav><!-- Navigation --></nav>
        <main>
            {@render children()}
        </main>
    </div>
</QueryClientProvider>
```

### Layout Load Function

```typescript
// routes/+layout.ts
export const ssr = false;  // Disable SSR for SPA mode
export const prerender = false;
```

## Page Load Functions

### Client-Side Loading

```typescript
// routes/analysis/[id]/+page.ts
import type { PageLoad } from './$types';

export const load: PageLoad = ({ params }) => {
    return {
        analysisId: params.id
    };
};
```

### Using Load Data

```svelte
<!-- routes/analysis/[id]/+page.svelte -->
<script lang="ts">
    import type { PageData } from './$types';

    let { data }: { data: PageData } = $props();

    // Load analysis using the ID
    $effect(() => {
        analysisStore.loadAnalysis(data.analysisId);
    });
</script>
```

## Navigation

### Programmatic Navigation

```typescript
import { goto } from '$app/navigation';

// Navigate to analysis
goto(`/analysis/${id}`);

// Navigate with invalidation
goto('/datasources', { invalidateAll: true });
```

### Link Navigation

```svelte
<a href="/analysis/new">Create Analysis</a>

<!-- With SvelteKit reload -->
<a href="/datasources" data-sveltekit-reload>Datasources</a>
```

## The $lib Alias

The `$lib` alias points to `src/lib/`:

```typescript
// These are equivalent:
import { apiRequest } from '$lib/api/client';
import { apiRequest } from '../../../lib/api/client';
```

Configure in `svelte.config.js`:

```javascript
kit: {
    alias: {
        $lib: 'src/lib'
    }
}
```

## Configuration Files

### svelte.config.js

```javascript
import adapter from '@sveltejs/adapter-node';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

export default {
    preprocess: vitePreprocess(),
    kit: {
        adapter: adapter(),
        alias: {
            $lib: 'src/lib'
        }
    }
};
```

### vite.config.ts

```typescript
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
    plugins: [sveltekit()],
    server: {
        port: 3000,
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true
            }
        }
    }
});
```

## SPA Mode

The app runs as a Single Page Application:

```typescript
// routes/+layout.ts
export const ssr = false;    // No server-side rendering
export const prerender = false;  // No static generation
```

**Why SPA mode?**
- Client-side state management
- No Node.js server needed in production
- Simpler deployment (static files + API)

## Type Safety

### Generated Types

SvelteKit generates types for routes:

```typescript
// Auto-generated in .svelte-kit/types/
import type { PageLoad } from './$types';
import type { PageData } from './$types';
```

### App-Level Types

```typescript
// src/app.d.ts
declare global {
    namespace App {
        interface Error {
            message: string;
            code?: string;
        }
        interface Locals {}
        interface PageData {}
        interface Platform {}
    }
}

export {};
```

## Best Practices

### Route Organization

```
routes/
├── (marketing)/           # Route group (no URL segment)
│   ├── about/
│   └── pricing/
├── (app)/                 # Another route group
│   ├── analysis/
│   └── datasources/
└── api/                   # API routes (if needed)
```

### Loading States

```svelte
<script lang="ts">
    import { page } from '$app/stores';

    let loading = $state(false);

    $effect(() => {
        // React to route changes
        loading = true;
        loadData($page.params.id).finally(() => {
            loading = false;
        });
    });
</script>

{#if loading}
    <LoadingSpinner />
{:else}
    <Content />
{/if}
```

### Error Handling

```svelte
<!-- routes/+error.svelte -->
<script lang="ts">
    import { page } from '$app/stores';
</script>

<h1>{$page.status}: {$page.error?.message}</h1>
<a href="/">Go home</a>
```

## See Also

- [Components](./components/README.md) - Component documentation
- [State Management](./state-management/README.md) - Stores and reactivity
- [API Client](./api-client/README.md) - HTTP client layer

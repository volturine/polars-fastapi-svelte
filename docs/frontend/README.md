# Frontend Documentation

Comprehensive documentation for the SvelteKit frontend of the Polars-FastAPI-Svelte Analysis Platform.

## Overview

The frontend is a **SvelteKit** application using **Svelte 5** with runes for reactive state management. It provides a visual pipeline builder interface for constructing data transformations.

## Technology Stack

| Component | Technology | Version |
|-----------|------------|---------|
| Framework | SvelteKit | ^2.49.1 |
| UI Library | Svelte | ^5.45.6 |
| Build Tool | Vite | ^7.2.6 |
| Language | TypeScript | ^5.9.3 |
| Data Fetching | TanStack Query | ^6.0.15 |
| UI Primitives | Melt UI | ^0.42.0 |
| Testing | Vitest | ^3.0.0 |

## Contents

| Document | Description |
|----------|-------------|
| [SvelteKit Structure](./sveltekit-structure.md) | Routing and app structure |
| [Styling](./styling.md) | Design system and CSS |
| [Components](./components/README.md) | Component documentation |
| [State Management](./state-management/README.md) | Stores and reactivity |
| [API Client](./api-client/README.md) | HTTP client layer |

## Project Structure

```
frontend/src/
├── routes/                    # SvelteKit pages
│   ├── +layout.svelte        # Root layout
│   ├── +page.svelte          # Gallery (home)
│   ├── analysis/
│   │   ├── new/+page.svelte  # Create wizard
│   │   └── [id]/+page.svelte # Pipeline editor
│   └── datasources/
│       └── +page.svelte      # Data sources list
│
└── lib/                       # Shared code
    ├── api/                   # HTTP client
    │   ├── client.ts         # Base client
    │   ├── analysis.ts       # Analysis API
    │   ├── compute.ts        # Compute API
    │   ├── datasource.ts     # DataSource API
    │   └── health.ts         # Health API
    ├── components/            # Svelte components
    │   ├── pipeline/         # Pipeline editor (6)
    │   ├── operations/       # Operation configs (20+)
    │   ├── viewers/          # Data viewers (4)
    │   └── gallery/          # Gallery components (4)
    ├── stores/                # Reactive state
    │   ├── analysis.svelte.ts
    │   ├── datasource.svelte.ts
    │   ├── compute.svelte.ts
    │   └── drag.svelte.ts
    ├── types/                 # TypeScript types
    │   ├── analysis.ts
    │   ├── datasource.ts
    │   ├── compute.ts
    │   └── operation-config.ts
    └── utils/                 # Utilities
        └── schema/           # Schema calculator
```

## Key Features

### Visual Pipeline Builder

- Drag-and-drop interface for adding operations
- Visual connections between steps
- Real-time schema preview
- Auto-save with debouncing

### Svelte 5 Runes

Modern reactive state management:

```typescript
class Store {
  data = $state<Data | null>(null);
  loading = $state(false);

  derived = $derived(this.data?.items ?? []);

  async load() {
    this.loading = true;
    this.data = await fetchData();
    this.loading = false;
  }
}
```

### Client-Side Schema Calculation

Predicts output schema without API calls:

```typescript
const calculator = new SchemaCalculator();
const outputSchema = calculator.calculatePipelineSchema(
  baseSchema,
  pipelineSteps
);
```

## Quick Start

```bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Access application
open http://localhost:3000
```

## Development Commands

| Command | Description |
|---------|-------------|
| `npm run dev` | Start dev server (port 3000) |
| `npm run build` | Build for production |
| `npm run preview` | Preview production build |
| `npm run check` | Type check |
| `npm run lint` | Lint code |
| `npm run test` | Run tests |
| `npm run test:watch` | Run tests in watch mode |

## Configuration Files

| File | Purpose |
|------|---------|
| `svelte.config.js` | SvelteKit configuration |
| `vite.config.ts` | Vite build configuration |
| `tsconfig.json` | TypeScript configuration |
| `.prettierrc` | Code formatting |
| `eslint.config.js` | Linting rules |

## See Also

- [SvelteKit Structure](./sveltekit-structure.md)
- [Components](./components/README.md)
- [State Management](./state-management/README.md)
- [Styling](./styling.md)

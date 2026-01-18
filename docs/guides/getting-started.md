# Getting Started

Step-by-step guide to installing and running your first analysis.

## Prerequisites

- **Python 3.13+** with UV package manager
- **Node.js 18+** with npm
- **Git**

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd polars-fastapi-svelte
```

### 2. Install Backend Dependencies

```bash
cd backend
uv sync --extra dev
```

### 3. Install Frontend Dependencies

```bash
cd ../frontend
npm install
```

### 4. Initialize Database

```bash
cd ../backend
uv run alembic upgrade head
```

## Running the Application

### Option A: Using Just (Recommended)

If you have [just](https://github.com/casey/just) installed:

```bash
just dev
```

This starts both backend and frontend simultaneously.

### Option B: Manual Start

**Terminal 1 - Backend**:
```bash
cd backend
uv run main.py
```

**Terminal 2 - Frontend**:
```bash
cd frontend
npm run dev
```

## Accessing the Application

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

## Your First Analysis

### Step 1: Upload Data

1. Open http://localhost:3000
2. Click **"Data Sources"** in the navigation
3. Click **"Add Data Source"**
4. Select the **File Upload** tab
5. Choose a CSV file and give it a name
6. Click **Upload**

### Step 2: Create an Analysis

1. Go to the home page (Gallery)
2. Click **"New Analysis"**
3. Enter a name (e.g., "My First Analysis")
4. Select the datasource you uploaded
5. Click **Create**

### Step 3: Build a Pipeline

You're now in the Pipeline Editor:

1. **Step Library** (left panel) - Available operations
2. **Canvas** (center) - Your pipeline
3. **Config Panel** (right) - Step configuration

**Add your first operation**:
1. Drag **"Filter"** from the Step Library onto the canvas
2. Configure the filter in the right panel:
   - Select a column
   - Choose an operator (e.g., `>`)
   - Enter a value
3. Click **Save**

### Step 4: Execute the Pipeline

1. Click the **"Run"** button in the toolbar
2. Watch the progress indicator
3. View results in the preview panel

### Step 5: Export Results

1. Click **"Export"** after execution completes
2. Choose format (CSV, Parquet, or JSON)
3. Download the file

## Project Structure

```
polars-fastapi-svelte/
├── backend/           # FastAPI application
│   ├── modules/       # Feature modules
│   ├── core/          # Configuration, database
│   └── database/      # Migrations
├── frontend/          # SvelteKit application
│   └── src/
│       ├── routes/    # Pages
│       └── lib/       # Shared code
├── docs/              # Documentation
└── justfile           # Task runner
```

## Common Commands

### Backend

```bash
cd backend

# Start server
uv run main.py

# Run tests
uv run pytest

# Format code
uv run ruff format . && uv run ruff check --fix .

# Run migrations
uv run alembic upgrade head
```

### Frontend

```bash
cd frontend

# Start dev server
npm run dev

# Run tests
npm run test

# Type check
npm run check

# Build for production
npm run build
```

## Troubleshooting

### Backend won't start

1. Check Python version: `python --version` (needs 3.13+)
2. Ensure dependencies installed: `uv sync --extra dev`
3. Check port 8000 is available

### Frontend won't start

1. Check Node version: `node --version` (needs 18+)
2. Ensure dependencies installed: `npm install`
3. Check port 3000 is available

### Database errors

1. Run migrations: `cd backend && uv run alembic upgrade head`
2. If corrupted, delete `backend/database/app.db` and re-run migrations

### CORS errors

Ensure backend is running on port 8000 and frontend on port 3000.

## Next Steps

- [Creating Datasources](./creating-datasources.md) - Learn about different data sources
- [Building Pipelines](./building-pipelines.md) - Master the pipeline editor
- [Development Workflow](./development-workflow.md) - For contributors

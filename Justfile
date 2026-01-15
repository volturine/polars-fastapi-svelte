# Justfile for Svelte-FastAPI Template

# Default goal
default: dev

# Install all dependencies
install:
    @echo "Installing backend dependencies..."
    cd backend && uv sync
    @echo "Installing frontend dependencies..."
    cd frontend && npm install

# Run development servers concurrently
dev:
    @echo "Starting servers..."
    (cd backend && uv run uvicorn main:app --reload --port 8000) & (cd frontend && npm run dev) & wait

# Lint everything
lint:
    @echo "Linting backend..."
    cd backend && uv run ruff check .
    @echo "Linting frontend..."
    cd frontend && npm run lint

# Format code
format:
    @echo "Formatting backend..."
    cd backend && uv run ruff format .
    @echo "Formatting frontend..."
    cd frontend && npm run format

# Build for production
build:
    @echo "Building frontend..."
    cd frontend && npm run build

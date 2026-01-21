# Dockerization & Deployment Improvements Plan

## 🎯 Goals

1. **Single Docker Image**: Combine frontend and backend into one deployable unit
2. **Environment-Based Configuration**: All important settings via environment variables
3. **Production Ready**: Proper resource management, health checks, and monitoring
4. **Developer Friendly**: Easy local development with Docker Compose
5. **Resource Control**: Configurable Polars engine cores and memory limits

## 📋 Detailed Implementation Plan

### 1. Frontend Static Build

**Objective**: Build SvelteKit as static site and serve from FastAPI

**Changes Needed**:
- [ ] Install and configure `@sveltejs/adapter-static`
- [ ] Update `svelte.config.js` to use static adapter
- [ ] Configure build output directory
- [ ] Handle SPA routing (fallback to index.html)
- [ ] Build API URL from environment variable at build time

**Files to Modify**:
- `frontend/package.json` - Add adapter-static dependency
- `frontend/svelte.config.js` - Configure static adapter
- `frontend/src/lib/api/client.ts` - Use env var for API URL
- `frontend/.env.example` - Document PUBLIC_API_URL

**Build Process**:
```bash
cd frontend
npm run build
# Output: frontend/build/ (static files)
```

### 2. FastAPI Static File Serving

**Objective**: Serve built frontend from FastAPI

**Changes Needed**:
- [ ] Add StaticFiles middleware to FastAPI
- [ ] Mount frontend build directory at root
- [ ] Add catch-all route for SPA routing
- [ ] Ensure API routes take precedence over static files

**Files to Modify**:
- `backend/main.py` - Add static file serving
- `backend/core/config.py` - Add frontend_dir setting

**Code Pattern**:
```python
from fastapi.staticfiles import StaticFiles

# Mount API routes first
app.include_router(router, prefix="/api", tags=["api"])

# Then mount static files
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")
```

### 3. Polars Engine Resource Configuration

**Objective**: Control compute resources via environment variables

**Settings to Add**:
- [ ] `POLARS_MAX_THREADS` - Maximum threads per engine (default: num_cores)
- [ ] `POLARS_MAX_MEMORY_MB` - Memory limit per engine (default: unlimited)
- [ ] `POLARS_STREAMING_CHUNK_SIZE` - Streaming chunk size (default: auto)
- [ ] `MAX_CONCURRENT_ENGINES` - Max simultaneous engines (default: 10)
- [ ] `ENGINE_MEMORY_LIMIT_MB` - Overall engine memory limit (default: unlimited)

**Files to Modify**:
- `backend/core/config.py` - Add new settings
- `backend/modules/compute/engine.py` - Apply settings to Polars
- `backend/modules/compute/manager.py` - Enforce engine limits
- `backend/.env.example` - Document new settings

**Implementation**:
```python
class Settings(BaseSettings):
    # Polars Engine Configuration
    polars_max_threads: int = Field(default=0, alias='POLARS_MAX_THREADS')  # 0 = auto
    polars_max_memory_mb: int = Field(default=0, alias='POLARS_MAX_MEMORY_MB')  # 0 = unlimited
    max_concurrent_engines: int = Field(default=10, alias='MAX_CONCURRENT_ENGINES')

# In engine startup:
if settings.polars_max_threads > 0:
    os.environ['POLARS_MAX_THREADS'] = str(settings.polars_max_threads)
```

### 4. Uvicorn/Gunicorn Worker Configuration

**Objective**: Production-ready ASGI server configuration

**Settings to Add**:
- [ ] `WORKERS` - Number of Uvicorn workers (default: 1)
- [ ] `WORKER_CONNECTIONS` - Max connections per worker (default: 1000)
- [ ] `TIMEOUT` - Worker timeout in seconds (default: 30)
- [ ] `KEEPALIVE` - Keep-alive timeout (default: 5)
- [ ] `GRACEFUL_TIMEOUT` - Graceful shutdown timeout (default: 10)

**Files to Create**:
- `backend/gunicorn.conf.py` - Gunicorn configuration
- `backend/start.sh` - Production startup script

**Gunicorn Configuration**:
```python
# gunicorn.conf.py
import os
import multiprocessing

workers = int(os.getenv("WORKERS", "1"))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = int(os.getenv("WORKER_CONNECTIONS", "1000"))
timeout = int(os.getenv("TIMEOUT", "30"))
keepalive = int(os.getenv("KEEPALIVE", "5"))
graceful_timeout = int(os.getenv("GRACEFUL_TIMEOUT", "10"))

# Logging
accesslog = "-"
errorlog = "-"
loglevel = os.getenv("LOG_LEVEL", "info")
```

### 5. Health Check Endpoints

**Objective**: Proper health monitoring for containers

**Endpoints to Add**:
- [ ] `GET /health` - Basic liveness check
- [ ] `GET /health/ready` - Readiness check (DB, engines)
- [ ] `GET /health/startup` - Startup probe
- [ ] `GET /metrics` - Prometheus metrics (optional)

**Files to Modify**:
- `backend/main.py` - Add health check routes

**Health Check Implementation**:
```python
@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.get("/health/ready")
async def readiness():
    # Check database
    # Check engine manager
    # Check filesystem
    return {"status": "ready", "checks": {...}}
```

### 6. Docker Setup

#### Backend Dockerfile (Multi-stage)

```dockerfile
# Stage 1: Build stage
FROM python:3.13-slim as builder

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Stage 2: Runtime stage
FROM python:3.13-slim

WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY . .

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start command
CMD ["gunicorn", "main:app", "-c", "gunicorn.conf.py"]
```

#### Frontend Dockerfile (Build only)

```dockerfile
FROM node:20-slim as builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source
COPY . .

# Build static site
RUN npm run build

# Output will be in /app/build
```

#### Combined Dockerfile (Frontend + Backend)

```dockerfile
# Stage 1: Build frontend
FROM node:20-slim as frontend-builder

WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Stage 2: Build backend dependencies
FROM python:3.13-slim as backend-builder

WORKDIR /app/backend

RUN pip install uv

COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev

# Stage 3: Runtime
FROM python:3.13-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy backend
COPY --from=backend-builder /app/backend/.venv /app/.venv
COPY backend/ /app/backend/

# Copy frontend build
COPY --from=frontend-builder /app/frontend/build /app/frontend/build

# Environment
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

# Create directories
RUN mkdir -p /app/data/uploads /app/data/results /app/data/exports

# Non-root user
RUN useradd -m -u 1000 appuser && \
    chown -R appuser:appuser /app
USER appuser

WORKDIR /app/backend

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["gunicorn", "main:app", "-c", "gunicorn.conf.py", "-b", "0.0.0.0:8000"]
```

### 7. Docker Compose - Development

```yaml
# docker-compose.dev.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    environment:
      - DEBUG=true
      - DATABASE_URL=sqlite+aiosqlite:///./database/app.db
    volumes:
      - ./backend:/app/backend:ro
      - ./data:/app/data
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    ports:
      - "5173:5173"
    environment:
      - PUBLIC_API_URL=http://localhost:8000
    volumes:
      - ./frontend:/app:ro
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0
```

### 8. Docker Compose - Production

```yaml
# docker-compose.yml
version: '3.8'

services:
  app:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "${PORT:-8000}:8000"
    environment:
      # Application
      - APP_NAME=${APP_NAME:-Polars Analysis Platform}
      - DEBUG=${DEBUG:-false}

      # Database
      - DATABASE_URL=${DATABASE_URL:-sqlite+aiosqlite:///./database/app.db}

      # Polars Engine
      - POLARS_MAX_THREADS=${POLARS_MAX_THREADS:-0}
      - POLARS_MAX_MEMORY_MB=${POLARS_MAX_MEMORY_MB:-0}
      - MAX_CONCURRENT_ENGINES=${MAX_CONCURRENT_ENGINES:-10}

      # Workers
      - WORKERS=${WORKERS:-2}
      - WORKER_CONNECTIONS=${WORKER_CONNECTIONS:-1000}

      # Timeouts
      - ENGINE_IDLE_TIMEOUT=${ENGINE_IDLE_TIMEOUT:-300}
      - JOB_TIMEOUT=${JOB_TIMEOUT:-300}
      - JOB_TTL=${JOB_TTL:-1800}

    volumes:
      - data:/app/data
      - database:/app/backend/database
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 3s
      retries: 3
      start_period: 10s

volumes:
  data:
  database:
```

### 9. Environment Variable Documentation

Create comprehensive `.env.example` at project root:

```bash
# Application Configuration
APP_NAME="Polars-FastAPI-Svelte Analysis Platform"
APP_VERSION="1.0.0"
DEBUG=false
PORT=8000

# CORS Configuration
CORS_ORIGINS="http://localhost:3000,http://127.0.0.1:3000"

# Database
DATABASE_URL="sqlite+aiosqlite:///./database/app.db"

# File Storage
UPLOAD_DIR="./data/uploads"
RESULTS_DIR="./data/results"
EXPORTS_DIR="./data/exports"
MAX_UPLOAD_SIZE=10737418240

# Polars Engine Configuration
# Maximum threads per engine (0 = auto-detect)
POLARS_MAX_THREADS=0
# Memory limit per engine in MB (0 = unlimited)
POLARS_MAX_MEMORY_MB=0
# Maximum number of concurrent engines
MAX_CONCURRENT_ENGINES=10

# Worker Configuration
# Number of Uvicorn workers (recommend: 2 * num_cores + 1)
WORKERS=2
# Maximum connections per worker
WORKER_CONNECTIONS=1000
# Worker timeout in seconds
TIMEOUT=30
# Keep-alive timeout
KEEPALIVE=5
# Graceful shutdown timeout
GRACEFUL_TIMEOUT=10

# Engine Lifecycle
ENGINE_IDLE_TIMEOUT=300
ENGINE_CLEANUP_INTERVAL=30
PROCESS_SHUTDOWN_TIMEOUT=5
PROCESS_TERMINATE_TIMEOUT=2

# Job Management
JOB_TIMEOUT=300
JOB_TTL=1800
MAX_JOBS_IN_MEMORY=1000

# Logging
LOG_LEVEL=info
```

### 10. Deployment Scripts

Create `scripts/` directory with helper scripts:

**scripts/build.sh**:
```bash
#!/bin/bash
set -e

echo "Building Docker image..."
docker build -t polars-analysis:latest .

echo "Build complete!"
docker images | grep polars-analysis
```

**scripts/deploy.sh**:
```bash
#!/bin/bash
set -e

echo "Deploying application..."

# Pull latest code
git pull

# Build new image
docker-compose build

# Stop old containers
docker-compose down

# Start new containers
docker-compose up -d

# Show status
docker-compose ps

echo "Deployment complete!"
```

**scripts/dev.sh**:
```bash
#!/bin/bash
set -e

echo "Starting development environment..."
docker-compose -f docker-compose.dev.yml up
```

## 📊 Configuration Matrix

### Resource Recommendations by Environment

| Environment | Workers | Threads/Engine | Memory/Engine | Max Engines |
|-------------|---------|----------------|---------------|-------------|
| **Development** | 1 | 4 | 2GB | 5 |
| **Small (2 cores, 4GB)** | 2 | 2 | 1GB | 3 |
| **Medium (4 cores, 8GB)** | 4 | 4 | 2GB | 5 |
| **Large (8 cores, 16GB)** | 8 | 8 | 4GB | 10 |
| **XL (16+ cores, 32GB+)** | 16 | 16 | 8GB | 15 |

### Environment Variable Examples

**Development**:
```bash
WORKERS=1
POLARS_MAX_THREADS=4
POLARS_MAX_MEMORY_MB=2048
MAX_CONCURRENT_ENGINES=5
DEBUG=true
```

**Production (Medium Server)**:
```bash
WORKERS=4
POLARS_MAX_THREADS=4
POLARS_MAX_MEMORY_MB=2048
MAX_CONCURRENT_ENGINES=5
DEBUG=false
```

## 🧪 Testing Strategy

1. **Local Docker Build Test**:
   ```bash
   docker build -t polars-analysis:test .
   docker run -p 8000:8000 polars-analysis:test
   ```

2. **Health Check Test**:
   ```bash
   curl http://localhost:8000/health
   curl http://localhost:8000/health/ready
   ```

3. **Resource Limit Test**:
   - Set low memory limit
   - Run large data analysis
   - Verify engine respects limits

4. **Multi-Worker Test**:
   - Set WORKERS=4
   - Run concurrent requests
   - Verify load distribution

## 📝 Documentation Updates

1. **README.md**: Add Docker deployment section
2. **DEPLOYMENT.md**: Create comprehensive deployment guide
3. **CONFIGURATION.md**: Document all environment variables
4. **ARCHITECTURE.md**: Update with Docker architecture

## 🚀 Implementation Order

1. ✅ **Phase 1: Configuration** (Est: 2 hours)
   - Add Polars resource settings
   - Add worker configuration
   - Update .env.example

2. ✅ **Phase 2: Frontend Static Build** (Est: 1 hour)
   - Configure adapter-static
   - Test static build
   - Update API URL handling

3. ✅ **Phase 3: Backend Static Serving** (Est: 1 hour)
   - Add StaticFiles middleware
   - Configure routing priority
   - Test SPA routing

4. ✅ **Phase 4: Health Checks** (Est: 1 hour)
   - Add health endpoints
   - Implement readiness checks
   - Test health monitoring

5. ✅ **Phase 5: Docker Setup** (Est: 3 hours)
   - Create Dockerfiles
   - Test multi-stage builds
   - Optimize image size

6. ✅ **Phase 6: Docker Compose** (Est: 2 hours)
   - Create dev compose file
   - Create prod compose file
   - Test both configurations

7. ✅ **Phase 7: Scripts & Documentation** (Est: 2 hours)
   - Create deployment scripts
   - Write deployment guide
   - Update all documentation

**Total Estimated Time: 12 hours**

## ✨ Benefits

1. **Single Deployment Unit**: One Docker image, easy to deploy anywhere
2. **Production Ready**: Proper workers, health checks, resource limits
3. **Environment Flexibility**: Easy to configure for different server sizes
4. **Developer Friendly**: Simple `docker-compose up` for development
5. **Resource Control**: Prevent runaway Polars processes
6. **Monitoring Ready**: Health checks for container orchestration
7. **Scalable**: Can add load balancer and scale horizontally

## 🎯 Success Criteria

- ✅ Single Docker image contains frontend + backend
- ✅ Frontend is statically built and served by FastAPI
- ✅ All critical settings configurable via environment
- ✅ Health checks working in Docker
- ✅ Resource limits respected by Polars engines
- ✅ Development experience with hot reload
- ✅ Production-ready with multiple workers
- ✅ Comprehensive documentation

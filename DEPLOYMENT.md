# Deployment Guide

Complete guide for deploying the Polars-FastAPI-Svelte Analysis Platform using Docker.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Configuration](#configuration)
- [Production Deployment](#production-deployment)
- [Development Setup](#development-setup)
- [Resource Planning](#resource-planning)
- [Monitoring & Health Checks](#monitoring--health-checks)
- [Troubleshooting](#troubleshooting)
- [Scaling](#scaling)

## Prerequisites

### Required

- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Minimum Resources**:
  - 2 CPU cores
  - 4GB RAM
  - 10GB disk space

### Recommended

- **4+ CPU cores**
- **8+ GB RAM**
- **20+ GB disk space** (for data storage)

### Verify Installation

```bash
docker --version
docker-compose --version
```

## Quick Start

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd polars-fastapi-svelte

# Copy environment template
cp .env.example .env

# Edit configuration (see Configuration section)
nano .env
```

### 2. Deploy

```bash
# Build and start the application
./scripts/deploy.sh

# Or manually:
docker-compose up -d
```

### 3. Verify Deployment

```bash
# Check health
./scripts/health-check.sh

# View logs
docker-compose logs -f

# Access the application
open http://localhost:8000
```

## Configuration

### Environment Variables

The `.env` file contains all configuration options. Key settings:

#### Application Settings

```bash
APP_NAME="Polars-FastAPI-Svelte Analysis Platform"
PORT=8000
DEBUG=false
LOG_LEVEL=info
```

#### Resource Limits

```bash
# Polars Engine Configuration
POLARS_MAX_THREADS=0              # 0 = auto-detect
POLARS_MAX_MEMORY_MB=0            # 0 = unlimited
MAX_CONCURRENT_ENGINES=10         # Max simultaneous analyses

# Worker Configuration
WORKERS=2                         # Gunicorn workers (0 = auto)
WORKER_CONNECTIONS=1000
TIMEOUT=30
```

#### Lifecycle Settings

```bash
# Engine Management
ENGINE_IDLE_TIMEOUT=300           # 5 minutes
ENGINE_CLEANUP_INTERVAL=30        # 30 seconds

# Job Management
JOB_TIMEOUT=300                   # 5 minutes
JOB_TTL=1800                      # 30 minutes
MAX_JOBS_IN_MEMORY=1000
```

### Configuration Recommendations by Server Size

#### Small Server (2 cores, 4GB RAM)

```bash
WORKERS=2
POLARS_MAX_THREADS=1
POLARS_MAX_MEMORY_MB=1024
MAX_CONCURRENT_ENGINES=3
```

#### Medium Server (4 cores, 8GB RAM)

```bash
WORKERS=4
POLARS_MAX_THREADS=2
POLARS_MAX_MEMORY_MB=2048
MAX_CONCURRENT_ENGINES=5
```

#### Large Server (8+ cores, 16+ GB RAM)

```bash
WORKERS=8
POLARS_MAX_THREADS=4
POLARS_MAX_MEMORY_MB=4096
MAX_CONCURRENT_ENGINES=10
```

## Production Deployment

### Standard Deployment

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env with your production values

# 2. Deploy
./scripts/deploy.sh

# 3. Verify
curl http://localhost:8000/health
```

### Behind a Reverse Proxy (Nginx)

Example Nginx configuration:

```nginx
upstream polars_backend {
    server localhost:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    # Increase timeouts for long-running analyses
    proxy_read_timeout 600s;
    proxy_connect_timeout 600s;
    proxy_send_timeout 600s;

    location / {
        proxy_pass http://polars_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Increase max upload size
    client_max_body_size 10G;
}
```

### With SSL/TLS

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # ... rest of configuration
}
```

### Using Different Ports

```bash
# Change port in .env
PORT=3000

# Or override in docker-compose
PORT=3000 docker-compose up -d
```

## Development Setup

### Hot-Reload Development

```bash
# Start development environment
./scripts/dev.sh

# Or manually:
docker-compose -f docker-compose.dev.yml up
```

Access:
- **Frontend**: http://localhost:5173 (with hot-reload)
- **Backend**: http://localhost:8000 (with hot-reload)

### Local Development (without Docker)

```bash
# Backend
cd backend
uv sync
source .venv/bin/activate
uvicorn main:app --reload

# Frontend (in another terminal)
cd frontend
npm install
npm run dev
```

## Resource Planning

### CPU Allocation

**Formula**: `Total Workers + (MAX_CONCURRENT_ENGINES × POLARS_MAX_THREADS)`

Example for 8-core server:
- Workers: 4 (50% of cores)
- Max Engines: 5
- Threads per Engine: 1-2
- Total: 4 + (5 × 2) = 14 threads (some over-subscription is OK)

### Memory Allocation

**Formula**: `System (2GB) + Workers (500MB each) + (Engines × Engine Memory)`

Example for 16GB server:
- System: 2GB
- Workers (4): 2GB
- Engines (5 × 2GB): 10GB
- Total: 14GB (leaving 2GB buffer)

### Disk Space

- **Application**: ~500MB
- **Database**: 100MB - 10GB (depends on usage)
- **Data Files**: Variable (uploaded files + results)
- **Recommended**: 20GB minimum, 100GB+ for production

## Monitoring & Health Checks

### Health Endpoints

```bash
# Liveness - Is the app running?
curl http://localhost:8000/health

# Readiness - Can it handle requests?
curl http://localhost:8000/health/ready

# Startup - Is it initialized?
curl http://localhost:8000/health/startup
```

### Docker Health Check

```bash
# Check container health
docker ps

# View health check logs
docker inspect polars-analysis | grep -A 10 Health
```

### Monitoring Logs

```bash
# All logs
docker-compose logs -f

# Specific service logs
docker logs -f polars-analysis

# Last 100 lines
docker-compose logs --tail=100
```

### Resource Usage

```bash
# Container stats
docker stats polars-analysis

# Resource limits
docker inspect polars-analysis | grep -A 20 Resources
```

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs

# Check if port is in use
lsof -i :8000

# Verify environment
docker-compose config
```

### Memory Issues

```bash
# Reduce concurrent engines
MAX_CONCURRENT_ENGINES=3 docker-compose up -d

# Limit engine memory
POLARS_MAX_MEMORY_MB=1024 docker-compose up -d

# Check memory usage
docker stats
```

### Performance Issues

1. **Too many workers**: Reduce `WORKERS`
2. **Engine contention**: Reduce `MAX_CONCURRENT_ENGINES`
3. **Memory swapping**: Reduce `POLARS_MAX_MEMORY_MB`
4. **I/O bottleneck**: Use faster storage (SSD)

### Database Locked

```bash
# Stop all containers
docker-compose down

# Remove old locks
rm -f data/database/*.db-*

# Restart
docker-compose up -d
```

### Container Keeps Restarting

```bash
# Check health check status
docker inspect polars-analysis | grep -A 10 Health

# Check if directories are writable
docker exec polars-analysis ls -la /app/data

# Review recent logs
docker logs --tail=50 polars-analysis
```

## Scaling

### Vertical Scaling (Single Server)

1. **Increase CPU**: Adjust `WORKERS` and `MAX_CONCURRENT_ENGINES`
2. **Increase RAM**: Adjust `POLARS_MAX_MEMORY_MB`
3. **Add Storage**: Mount additional volumes

```yaml
# docker-compose.yml
volumes:
  - data:/app/data
  - /mnt/large-storage:/app/data/uploads  # Additional storage
```

### Horizontal Scaling (Multiple Servers)

The application can be scaled horizontally with some modifications:

1. **Shared Database**: Use PostgreSQL instead of SQLite
2. **Shared Storage**: Use NFS or object storage
3. **Load Balancer**: Nginx or HAProxy
4. **Session Affinity**: Sticky sessions for engine management

Example with PostgreSQL:

```bash
# .env
DATABASE_URL=postgresql+asyncpg://user:password@postgres:5432/polars_db
```

```yaml
# docker-compose.yml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: polars_db
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

### Load Balancing Configuration

Nginx load balancer example:

```nginx
upstream polars_cluster {
    least_conn;
    server server1:8000;
    server server2:8000;
    server server3:8000;
}

server {
    listen 80;

    location / {
        proxy_pass http://polars_cluster;
    }
}
```

## Backup & Recovery

### Backup Data

```bash
# Backup volumes
docker run --rm \
  -v polars-analysis_data:/data \
  -v $(pwd)/backups:/backup \
  busybox tar czf /backup/data-backup-$(date +%Y%m%d).tar.gz /data

# Backup database
docker run --rm \
  -v polars-analysis_database:/db \
  -v $(pwd)/backups:/backup \
  busybox tar czf /backup/db-backup-$(date +%Y%m%d).tar.gz /db
```

### Restore Data

```bash
# Restore volumes
docker run --rm \
  -v polars-analysis_data:/data \
  -v $(pwd)/backups:/backup \
  busybox tar xzf /backup/data-backup-20240121.tar.gz -C /
```

## Security Considerations

1. **Non-root User**: Application runs as `appuser` (UID 1000)
2. **No Secrets in Image**: Use environment variables
3. **Network Isolation**: Use Docker networks
4. **Resource Limits**: Prevent DoS via resource exhaustion
5. **File Permissions**: Data directories owned by appuser
6. **CORS Configuration**: Restrict `CORS_ORIGINS` in production
7. **SSL/TLS**: Use reverse proxy for HTTPS
8. **Firewall**: Only expose necessary ports

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and deploy
./scripts/deploy.sh
```

### Clean Up

```bash
# Remove stopped containers
docker-compose down

# Remove unused images
docker image prune -a

# Remove unused volumes (careful!)
docker volume prune
```

### View Resource Usage History

```bash
# Install ctop for real-time monitoring
docker run --rm -ti \
  -v /var/run/docker.sock:/var/run/docker.sock \
  quay.io/vektorlab/ctop:latest
```

## Support

For issues and questions:

- **GitHub Issues**: <repository-url>/issues
- **Documentation**: See `DOCKERIZATION_PLAN.md` for technical details
- **Health Checks**: Use `./scripts/health-check.sh` for diagnostics

## Next Steps

After successful deployment:

1. Configure automated backups
2. Set up monitoring (Prometheus/Grafana)
3. Configure log aggregation
4. Set up automated restarts
5. Document your specific deployment

---

Last updated: 2024-01-21

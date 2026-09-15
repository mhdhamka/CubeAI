# Phase 10: Docker Containerization

Comprehensive Docker setup for CubeAI application stack.

## Table of Contents

1. [Overview](#overview)
2. [Services](#services)
3. [Configuration](#configuration)
4. [Development Setup](#development-setup)
5. [Production Deployment](#production-deployment)
6. [Docker Architecture](#docker-architecture)
7. [CLI Reference](#cli-reference)
8. [Troubleshooting](#troubleshooting)

## Overview

Phase 10 containerizes all CubeAI components:
- **PostgreSQL 14**: Persistent data storage
- **FastAPI**: Python backend with 9 phases of features
- **Next.js**: React frontend with 3D rendering
- **Docker Compose**: Service orchestration and networking

### Benefits

- **Consistency**: Same environment across dev, test, production
- **Isolation**: Services run in separate containers
- **Scalability**: Easy to replicate and distribute
- **Deployment**: Single command to start entire stack
- **Monitoring**: Built-in health checks and auto-restart
- **Development**: Volume mounts enable live reloading

## Services

### 1. PostgreSQL Database

**Image**: `postgres:14-alpine`

**Container Configuration**:
```yaml
postgres:
  image: postgres:14-alpine
  container_name: cube-ai-postgres
  environment:
    POSTGRES_USER: ${DB_USER:-cubeai}
    POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme123}
    POSTGRES_DB: ${DB_NAME:-cube_ai_db}
  ports:
    - "5432:5432"
  volumes:
    - postgres-data:/var/lib/postgresql/data
    - ./database/schema:/docker-entrypoint-initdb.d
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${DB_USER:-cubeai}"]
    interval: 10s
    timeout: 5s
    retries: 5
```

**Features**:
- Alpine Linux base (40MB base image)
- Automatic initialization from SQL files
- Persistent volume for data
- Health check every 10 seconds
- Auto-restart on failure
- Exposed on port 5432

**Usage**:
```bash
# Connect to database
docker-compose exec postgres psql -U cubeai -d cube_ai_db

# List tables
\dt

# Run SQL query
SELECT * FROM profiles;

# Exit
\q
```

### 2. FastAPI Backend

**Dockerfile**:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 PIP_NO_CACHE_DIR=1
RUN apt-get update && apt-get install -y gcc postgresql-client
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY apps/api/ ./
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Container Configuration**:
```yaml
api:
  build:
    context: .
    dockerfile: Dockerfile
  container_name: cube-ai-api
  environment:
    DATABASE_URL: postgresql://cubeai:password@postgres:5432/cube_ai_db
    CORS_ORIGINS: http://localhost:3000
    DEBUG: false
    LOG_LEVEL: INFO
  ports:
    - "8000:8000"
  depends_on:
    postgres:
      condition: service_healthy
  volumes:
    - ./apps/api:/app
  healthcheck:
    test: ["CMD", "python", "-c", "import requests; requests.get('http://localhost:8000/api/health')"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Features**:
- Python 3.11 slim image
- All Phase 1-9 endpoints included
- FastAPI with Uvicorn ASGI server
- SQLAlchemy ORM with connection pooling
- WebSocket support for real-time scanning
- Pydantic validation for all requests
- OpenAPI documentation at `/docs`
- Non-root user for security
- Health check via `/api/health`
- Auto-reload in development mode

**Endpoints Summary**:
- `GET /api/health` - Service health
- `POST /api/solve` - Solver engine
- `POST /api/validate` - Move validator
- `POST /api/scan/image` - Vision processing
- `WS /api/scan/session` - Real-time scanning
- `POST /api/coaching` - Coaching service
- `GET/POST /api/profiles` - Profile management
- `GET/POST /api/solves` - Solve records
- `GET /api/statistics` - Statistics engine
- `GET /docs` - API documentation (Swagger UI)

**Usage**:
```bash
# View logs
docker-compose logs -f api

# Execute Python script
docker-compose exec api python script.py

# Install additional package
docker-compose exec api pip install package-name

# Run tests
docker-compose exec api pytest tests/
```

### 3. Next.js Frontend

**Dockerfile** (Multi-stage build):
```dockerfile
# Builder stage
FROM node:18-alpine AS builder
WORKDIR /app
COPY package.json package-lock.json ./
COPY packages/cube-api/ ./packages/cube-api/
COPY apps/web/ ./apps/web/
RUN npm ci && npm run build --workspace=@cube-ai/cube-api && npm run build --workspace=apps/web

# Runtime stage
FROM node:18-alpine
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --production
COPY --from=builder /app/apps/web/.next ./apps/web/.next
COPY --from=builder /app/apps/web/public ./apps/web/public
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001
USER nextjs
EXPOSE 3000
CMD ["npm", "run", "start", "--workspace=apps/web"]
```

**Container Configuration**:
```yaml
web:
  build:
    context: .
    dockerfile: Dockerfile.web
    args:
      NEXT_PUBLIC_API_URL: http://localhost:8000
      NEXT_PUBLIC_WS_URL: ws://localhost:8000
  container_name: cube-ai-web
  environment:
    NODE_ENV: production
    NEXT_PUBLIC_API_URL: http://localhost:8000
    NEXT_PUBLIC_WS_URL: ws://localhost:8000
  ports:
    - "3000:3000"
  depends_on:
    - api
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:3000"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Features**:
- Node.js 18 Alpine image
- Multi-stage build (reduces final size ~50%)
- Production-optimized Next.js build
- React with Three.js 3D rendering
- TypeScript for type safety
- Real-time WebSocket integration
- Health check via HTTP GET
- Non-root user (nextjs)
- Environment-based API URLs

**Build Arguments**:
- `NEXT_PUBLIC_API_URL`: Backend URL (default: http://localhost:8000)
- `NEXT_PUBLIC_WS_URL`: WebSocket URL (default: ws://localhost:8000)

**Usage**:
```bash
# View logs
docker-compose logs -f web

# Run commands in container
docker-compose exec web npm list

# Rebuild app
docker-compose exec web npm run build

# Run tests
docker-compose exec web npm test
```

## Configuration

### Environment Variables

#### Database Variables
```env
DB_USER=cubeai                    # PostgreSQL user
DB_PASSWORD=changeme123           # Strong password for production
DB_NAME=cube_ai_db                # Database name
```

#### API Variables
```env
SERVICE_NAME=CubeAI API           # Service identifier
SERVICE_VERSION=0.1.0             # API version
DEBUG=false                        # Debug mode (true for dev)
API_HOST=0.0.0.0                  # Bind address
API_PORT=8000                     # Listen port
DATABASE_URL=...                  # Auto-generated from above
CORS_ORIGINS=http://localhost:3000  # Allowed origins
LOG_LEVEL=INFO                    # INFO, DEBUG, WARNING, ERROR
```

#### Frontend Variables
```env
NODE_ENV=production               # development or production
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Volume Configuration

**Named Volumes**:
```yaml
volumes:
  postgres-data:
    driver: local
```

Purpose: Persistent database storage across container restarts.

**Bind Mounts** (Development):
```yaml
volumes:
  - ./apps/api:/app              # API hot reload
  - ./apps/web:/app              # Web hot reload
  - /app/.next                   # Next.js cache (Docker-only)
```

Purpose: Enable live code reloading during development.

### Network Configuration

**Bridge Network**: `cube-ai-network`

```
External                    Internal
localhost:3000      ←→      web:3000
localhost:8000      ←→      api:8000
localhost:5432      ←→      postgres:5432

web ←→ api:8000 (internal hostname)
api ←→ postgres:5432 (internal hostname)
```

All containers can reference each other by service name.

## Development Setup

### Prerequisites
- Docker Desktop (Windows/Mac) or Docker + Docker Compose (Linux)
- 4GB+ available RAM
- 5GB+ disk space

### Initial Setup

```bash
# 1. Clone repository
git clone https://github.com/yourusername/cube-ai.git
cd cube-ai

# 2. Copy environment template
cp .env.example .env.docker

# 3. Edit environment variables (optional)
nano .env.docker

# 4. Build and start services
docker-compose up --build

# 5. Wait for all services to be healthy
docker-compose ps
# STATUS should show "Up (healthy)" for all services
```

### Verify Services

```bash
# Check all services running
docker-compose ps

# Test API
curl http://localhost:8000/api/health

# Test Frontend
curl http://localhost:3000

# Test Database
docker-compose exec postgres psql -U cubeai -d cube_ai_db -c "SELECT 1"
```

### Development Workflow

#### 1. Make code changes
```bash
# Edit API code
nano apps/api/routes/solve.py

# Edit frontend code
nano apps/web/app/page.tsx
```

Changes are automatically reloaded (hot reload enabled via volume mounts).

#### 2. View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f web

# Follow API logs with timestamps
docker-compose logs -f --timestamps api
```

#### 3. Run commands in containers
```bash
# Python commands
docker-compose exec api python script.py
docker-compose exec api pytest tests/

# Node commands
docker-compose exec web npm test
docker-compose exec web npm run build

# Database queries
docker-compose exec postgres psql -U cubeai -d cube_ai_db
```

#### 4. Restart services
```bash
# Restart one service
docker-compose restart api

# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up --build -d api
```

#### 5. Database operations
```bash
# Initialize database
docker-compose exec api python -c "from db import init_db; init_db()"

# Backup
docker-compose exec postgres pg_dump -U cubeai cube_ai_db > backup.sql

# Restore
docker-compose exec -T postgres psql -U cubeai cube_ai_db < backup.sql

# Reset database
docker-compose down -v
docker-compose up
```

### Debugging

#### View service status
```bash
# Detailed status
docker-compose ps

# Specific container
docker inspect cube-ai-api
```

#### Check health
```bash
# Health status
docker-compose ps

# Detailed health info
docker inspect cube-ai-api --format='{{json .State.Health}}'
```

#### View container logs
```bash
# Last 50 lines
docker-compose logs --tail=50 api

# Follow logs with timestamps
docker-compose logs -f --timestamps api
```

#### Execute interactive commands
```bash
# Bash shell in API
docker-compose exec api bash

# Python REPL
docker-compose exec api python

# PostgreSQL client
docker-compose exec postgres psql -U cubeai -d cube_ai_db
```

## Production Deployment

### Pre-deployment Checklist

- [ ] Update `.env.prod` with strong passwords
- [ ] Set `DEBUG=false`
- [ ] Set `LOG_LEVEL=WARNING`
- [ ] Configure `CORS_ORIGINS` with actual domain
- [ ] Update API URLs to production domain
- [ ] Configure SSL/TLS certificates
- [ ] Remove bind mounts (use volumes instead)
- [ ] Configure health checks properly
- [ ] Set resource limits (CPU, memory)
- [ ] Configure log aggregation
- [ ] Set up monitoring and alerts
- [ ] Plan backup strategy

### Environment (`.env.prod`)

```env
# Database - Use strong password!
DB_USER=cubeai_prod
DB_PASSWORD=<STRONG_PASSWORD_HERE>
DB_NAME=cube_ai_production

# API - Production settings
SERVICE_NAME=CubeAI API
SERVICE_VERSION=1.0.0
DEBUG=false
LOG_LEVEL=WARNING
CORS_ORIGINS=https://cubeai.example.com,https://app.cubeai.example.com

# Frontend
NODE_ENV=production
NEXT_PUBLIC_API_URL=https://api.cubeai.example.com
NEXT_PUBLIC_WS_URL=wss://api.cubeai.example.com
```

### Build and Push Images

```bash
# Build images
docker-compose build

# Tag images
docker tag cube-ai-api:latest myregistry/cube-ai-api:1.0.0
docker tag cube-ai-web:latest myregistry/cube-ai-web:1.0.0

# Push to registry
docker push myregistry/cube-ai-api:1.0.0
docker push myregistry/cube-ai-web:1.0.0
```

### Production Deployment File

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:14-alpine
    environment:
      POSTGRES_USER: ${DB_USER}
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: ${DB_NAME}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${DB_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: always

  api:
    image: myregistry/cube-ai-api:1.0.0
    environment:
      DATABASE_URL: postgresql://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
      DEBUG: false
      LOG_LEVEL: WARNING
      CORS_ORIGINS: ${CORS_ORIGINS}
    depends_on:
      postgres:
        condition: service_healthy
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M

  web:
    image: myregistry/cube-ai-web:1.0.0
    environment:
      NODE_ENV: production
      NEXT_PUBLIC_API_URL: ${NEXT_PUBLIC_API_URL}
      NEXT_PUBLIC_WS_URL: ${NEXT_PUBLIC_WS_URL}
    depends_on:
      - api
    restart: always
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M

volumes:
  postgres-data:
    driver: local
```

### Deploy to Production

```bash
# Pull latest images
docker-compose -f docker-compose.prod.yml pull

# Start services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Reverse Proxy (nginx)

```nginx
upstream cube_api {
    server api:8000;
}

upstream cube_web {
    server web:3000;
}

server {
    listen 443 ssl http2;
    server_name api.cubeai.example.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    # API endpoints
    location /api {
        proxy_pass http://cube_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 60s;
    }

    # WebSocket
    location /api/scan/session {
        proxy_pass http://cube_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_read_timeout 300s;
    }
}

server {
    listen 443 ssl http2;
    server_name cubeai.example.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    location / {
        proxy_pass http://cube_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Docker Architecture

### Image Layers

**API Image**:
```
python:3.11-slim (120MB)
├─ apt packages (50MB)
├─ pip packages (200MB)
├─ app code (5MB)
└─ Total: ~375MB
```

**Web Image** (Multi-stage):
```
Builder Stage:
├─ node:18-alpine (40MB)
├─ npm packages (500MB)
└─ build output (50MB)

Runtime Stage:
├─ node:18-alpine (40MB)
├─ production npm packages (100MB)
└─ app bundle (50MB)
└─ Total: ~190MB
```

### Container Lifecycle

```
┌─────────┐
│ Created │
└────┬────┘
     │
     ▼
┌──────────────────┐
│ Health Check     │
│ Starts (10s)     │
└────┬─────────────┘
     │
     ▼
┌────────────────────────┐
│ Running & Healthy      │
│ (Ready for requests)   │
└────┬───────────────────┘
     │
     ▼
┌──────────────┐
│ Unhealthy    │ (retries exceeded)
└────┬─────────┘
     │
     ▼
┌──────────────────────┐
│ Restart Automatically│
│ (up to 3 times)      │
└──────────────────────┘
```

## CLI Reference

### Basic Commands

```bash
# Start services
docker-compose up

# Start in background
docker-compose up -d

# Stop services
docker-compose stop

# Remove containers
docker-compose rm

# View status
docker-compose ps

# View logs
docker-compose logs -f
```

### Build Commands

```bash
# Build images
docker-compose build

# Build specific service
docker-compose build api

# Build without cache
docker-compose build --no-cache
```

### Execution Commands

```bash
# Execute command
docker-compose exec SERVICE COMMAND

# Interactive bash
docker-compose exec api bash

# Run one-off command
docker-compose run api python script.py
```

### Database Commands

```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U cubeai -d cube_ai_db

# Backup database
docker-compose exec postgres pg_dump -U cubeai cube_ai_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U cubeai cube_ai_db < backup.sql
```

### Cleanup Commands

```bash
# Stop and remove containers
docker-compose down

# Remove containers and volumes
docker-compose down -v

# Remove unused images
docker image prune

# Remove all unused resources
docker system prune -a
```

## Troubleshooting

### Services Won't Start

**Symptom**: `docker-compose up` fails or services immediately restart

**Diagnosis**:
```bash
# Check logs
docker-compose logs

# Check service status
docker-compose ps

# Inspect container
docker inspect cube-ai-api
```

**Solutions**:
1. Check port conflicts: `lsof -i :3000`, `lsof -i :8000`
2. Free up disk space: `docker system df`
3. Rebuild images: `docker-compose down -v && docker-compose up --build`
4. Check Docker resources: Ensure 4GB+ RAM allocated

### Database Connection Error

**Symptom**: `psycopg2.OperationalError: could not connect to server`

**Diagnosis**:
```bash
# Check if PostgreSQL is running
docker-compose exec postgres pg_isready

# Check connection string
docker-compose exec api echo $DATABASE_URL

# Test connection
docker-compose exec api psql $DATABASE_URL -c "SELECT 1"
```

**Solutions**:
1. Ensure `postgres` service is healthy: `docker-compose ps postgres`
2. Check `depends_on` condition
3. Wait longer for PostgreSQL to initialize
4. Check DATABASE_URL environment variable
5. Verify credentials in environment

### API Returns 500 Errors

**Symptom**: `POST /api/solve` returns 500 status

**Diagnosis**:
```bash
# Check logs
docker-compose logs -f api

# Check database
docker-compose exec postgres psql -U cubeai -d cube_ai_db -c "SELECT * FROM profiles"

# Check health
docker-compose exec api python -c "import requests; print(requests.get('http://localhost:8000/api/health').json())"
```

**Solutions**:
1. Initialize database: `docker-compose exec api python -c "from db import init_db; init_db()"`
2. Check database tables exist
3. Review API logs for error details
4. Verify environment variables
5. Restart API service: `docker-compose restart api`

### Frontend Can't Reach API

**Symptom**: Browser console shows CORS errors or API connection fails

**Diagnosis**:
```bash
# Test connectivity
docker-compose exec web curl http://api:8000/api/health

# Check environment
docker-compose exec web env | grep NEXT_PUBLIC

# Check CORS settings
docker-compose exec api echo $CORS_ORIGINS
```

**Solutions**:
1. Verify `NEXT_PUBLIC_API_URL` is correct
2. Check `CORS_ORIGINS` includes frontend URL
3. Ensure API service is running: `docker-compose ps api`
4. Test with curl: `curl -i http://localhost:8000/api/health`
5. Check browser network tab for exact error

### WebSocket Connection Fails

**Symptom**: WebSocket connection hangs or closes immediately

**Diagnosis**:
```bash
# Test WebSocket endpoint
docker-compose exec web curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://api:8000/api/scan/session

# Check logs
docker-compose logs -f api | grep "websocket\|WebSocket\|ws"
```

**Solutions**:
1. Verify `NEXT_PUBLIC_WS_URL` is correct
2. Ensure `api` service is running and healthy
3. Check firewall/routing: `docker-compose exec web ping -c 1 api`
4. Test with simple WebSocket client
5. Check API logs for WebSocket handler errors

### Performance Issues

**Symptom**: Services slow or unresponsive

**Diagnosis**:
```bash
# Check resource usage
docker stats

# Check disk space
docker system df

# Check logs for errors
docker-compose logs | grep -i error
```

**Solutions**:
1. Increase Docker memory/CPU allocation
2. Clean up unused images: `docker system prune -a`
3. Enable logging driver optimization
4. Configure connection pooling
5. Implement caching strategies

### Health Check Failures

**Symptom**: Services marked "unhealthy" in `docker-compose ps`

**Diagnosis**:
```bash
# Check health status
docker-compose ps

# Detailed health info
docker inspect cube-ai-api --format='{{json .State.Health}}'

# View health logs
docker inspect cube-ai-api | jq '.State.Health.Log'
```

**Solutions**:
1. Check service logs for errors
2. Increase health check timeout
3. Verify health check endpoint works
4. Restart service: `docker-compose restart api`
5. Review resource constraints

---

**Next Phase**: Phase 11 - Cross-layer Testing with unit, integration, and E2E tests.

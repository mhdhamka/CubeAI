# Phase 10: Docker Compose Setup

Complete containerization and orchestration of CubeAI services.

## Overview

Phase 10 implements Docker containerization for all services:
- PostgreSQL 14 database
- FastAPI Python backend
- Next.js React frontend
- Network and volume management
- Health checks and auto-restart
- Development and production configurations

## Files Created/Modified

### Docker Configuration Files

**`Dockerfile`** (35 lines)
- Python 3.11 base image
- FastAPI/Uvicorn configuration
- System dependencies (gcc, postgresql-client)
- Non-root user for security
- Health check via `/api/health`
- Port 8000 exposure

**`Dockerfile.web`** (45 lines)
- Multi-stage build (builder + runtime)
- Node.js 18 base image
- Next.js build optimization
- Production dependency installation
- Non-root user (nextjs)
- Health check via HTTP GET
- Port 3000 exposure

**`docker-compose.yml`** (90 lines)
- 3 services: postgres, api, web
- Service dependencies and orchestration
- Environment variable configuration
- Volume management (postgres-data, bind mounts)
- Health checks on all services
- Bridge network (cube-ai-network)
- Auto-restart policy

**`.dockerignore`** (60 lines)
- Excludes unnecessary files from builds
- Reduces image size
- Improves build performance
- Excludes: node_modules, __pycache__, .git, .env, etc.

**`.env.example`** (35 lines)
- Example environment configuration
- Database credentials
- API service settings
- Frontend environment variables
- CORS and URL configuration

### Documentation

**`docs/DOCKER-DEPLOYMENT.md`** (500+ lines)
- Quick start guide
- Service overview and configuration
- Common docker-compose commands
- Database operations
- Health check monitoring
- Production deployment checklist
- Resource limits configuration
- Reverse proxy setup (nginx)
- Troubleshooting guide
- Performance tuning
- Backup and recovery procedures
- Security notes

## Services Architecture

### PostgreSQL Database
```
Container: cube-ai-postgres
Image: postgres:14-alpine
Port: 5432
Volume: postgres-data (named)
Env: DB_USER, DB_PASSWORD, DB_NAME
Health: pg_isready check
```

Features:
- Alpine Linux base (lightweight)
- Persistent data storage
- Auto-initialization from database/schema/
- Health check every 10 seconds
- Connection pooling ready
- Backup compatible

### FastAPI Backend
```
Container: cube-ai-api
Build: Dockerfile
Port: 8000
Volume: ./apps/api:/app (development)
Env: SERVICE_NAME, DEBUG, DATABASE_URL, CORS_ORIGINS, etc.
Health: GET /api/health
Dependencies: postgres (must be healthy)
```

Features:
- Python 3.11 runtime
- Auto-reload in development
- Health checks on startup/runtime
- Security: non-root user
- Full logging support
- All Phase 1-9 endpoints included

Endpoints:
- Health: `GET /api/health`
- Solve: `POST /api/solve`
- Validate: `POST /api/validate`
- Vision: `POST /api/scan/image`
- WebSocket: `WS /api/scan/session`
- Coaching: `POST /api/coaching`
- Profiles: `GET/POST /api/profiles`
- Solves: `GET/POST /api/solves`
- Statistics: `GET /api/statistics`
- OpenAPI Docs: `GET /api/docs`

### Next.js Frontend
```
Container: cube-ai-web
Build: Dockerfile.web (multi-stage)
Port: 3000
Volume: ./apps/web:/app (development)
Env: NODE_ENV, NEXT_PUBLIC_API_URL, NEXT_PUBLIC_WS_URL
Health: HTTP GET http://localhost:3000
Dependencies: api (must be running)
```

Features:
- Multi-stage build (optimized size)
- Hot reload in development
- Production-ready build output
- Security: non-root user (nextjs)
- Environmental build args
- Health check after 30 second delay

## Configuration

### Environment Variables

**Database Variables:**
```
DB_USER=cubeai                    # PostgreSQL user
DB_PASSWORD=changeme123           # Database password
DB_NAME=cube_ai_db                # Database name
```

**API Variables:**
```
SERVICE_NAME=CubeAI API
SERVICE_VERSION=0.1.0
DEBUG=false                        # Enable debug mode
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=postgresql://user:pass@postgres:5432/db
CORS_ORIGINS=http://localhost:3000
LOG_LEVEL=INFO                     # INFO, DEBUG, WARNING, ERROR
```

**Frontend Variables:**
```
NODE_ENV=production                # development or production
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Network Configuration

All services run on bridge network `cube-ai-network`:

```
┌─────────────────┐
│  cube-ai-web    │
│  :3000          │
└────────┬────────┘
         │
    Internal: api:8000
    External: localhost:3000
         │
┌────────▼────────┐
│  cube-ai-api    │
│  :8000          │
└────────┬────────┘
         │
    Internal: postgres:5432
    External: localhost:8000
         │
┌────────▼────────────────┐
│  cube-ai-postgres       │
│  :5432                  │
└─────────────────────────┘
External: localhost:5432
```

### Volume Management

**postgres-data** (Named Volume)
- Persistent database storage
- Survives container restarts
- Managed by Docker
- Mount: `/var/lib/postgresql/data`

**Development Bind Mounts**
- API: `./apps/api:/app`
- Web: `./apps/web:/app`
- Enable live code reloading
- Remove for production

## Quick Start

### 1. Setup
```bash
# Clone repository
git clone <repo-url>
cd cube-ai

# Copy environment
cp .env.example .env.docker
# Edit .env.docker if needed
```

### 2. Start Services
```bash
# Build and start all services
docker-compose up --build

# Or start in background
docker-compose up -d

# Check status
docker-compose ps
```

### 3. Access Services
```
Frontend: http://localhost:3000
API:      http://localhost:8000
API Docs: http://localhost:8000/docs
Database: postgresql://localhost:5432/cube_ai_db
```

### 4. Initialize Database (if needed)
```bash
docker-compose exec api python -c "from db import init_db; init_db()"
```

### 5. View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
```

## Development Workflow

### Make code changes
```bash
# Edit source files
nano apps/api/main.py
nano apps/web/app/page.tsx
```

Changes are automatically reflected (hot reload enabled).

### Run tests
```bash
# API tests
docker-compose exec api pytest tests/

# Frontend tests
docker-compose exec web npm test
```

### Database queries
```bash
# Connect to PostgreSQL
docker-compose exec postgres psql -U cubeai -d cube_ai_db

# Execute query
SELECT * FROM profiles;
```

### View API documentation
Visit: http://localhost:8000/docs

## Production Deployment

### Pre-deployment
1. Update `.env.prod` with production values
   - Strong database password
   - Production API URLs
   - Restricted CORS origins
   - Disabled debug mode

2. Build images
```bash
docker-compose -f docker-compose.yml build
```

3. Push to registry
```bash
docker tag cube-ai-api:latest myregistry/cube-ai-api:1.0.0
docker push myregistry/cube-ai-api:1.0.0
```

### Deploy to production
```bash
# Pull latest images
docker pull myregistry/cube-ai-api:1.0.0
docker pull myregistry/cube-ai-web:1.0.0

# Start services
docker-compose -f docker-compose.prod.yml up -d
```

### Monitoring
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f

# Check resource usage
docker stats
```

### Backups
```bash
# Backup database
docker-compose exec postgres pg_dump -U cubeai cube_ai_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U cubeai cube_ai_db < backup.sql
```

## Health Checks

All services include health checks:

**PostgreSQL**
- Check: `pg_isready`
- Interval: 10 seconds
- Timeout: 5 seconds
- Retries: 5
- Status: Container restarts if unhealthy

**FastAPI**
- Check: `GET /api/health`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 10 seconds
- Status: Returns JSON {"status": "healthy"}

**Next.js**
- Check: `GET http://localhost:3000`
- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 30 seconds

### Check health status
```bash
# View all health statuses
docker-compose ps

# Detailed health check info
docker inspect cube-ai-api --format='{{json .State.Health}}' | jq
```

## Common Issues

**Services won't start**
```bash
# Check error messages
docker-compose logs

# Rebuild images
docker-compose down -v
docker-compose up --build
```

**Database connection error**
```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready

# Check DATABASE_URL
docker-compose exec api echo $DATABASE_URL

# Test connection
docker-compose exec api psql $DATABASE_URL -c "SELECT 1"
```

**API returns 500 errors**
```bash
# Check logs
docker-compose logs -f api

# Verify database initialized
docker-compose exec api python -c "from db import init_db; init_db()"
```

**Frontend can't reach API**
```bash
# Test connectivity
docker-compose exec web curl http://api:8000/api/health

# Check CORS settings
docker-compose exec api echo $CORS_ORIGINS
```

## Cleanup

```bash
# Stop services (keep data)
docker-compose stop

# Remove containers (keep data)
docker-compose rm

# Remove everything (delete all data!)
docker-compose down -v
docker system prune
```

## Performance Optimization

### Database tuning
```sql
-- Connection pooling
max_connections=200

-- Memory allocation
shared_buffers=256MB
effective_cache_size=1GB
work_mem=16MB
```

### FastAPI optimization
- Use uvicorn with multiple workers: `--workers 4`
- Set connection pool limits
- Enable gzip compression
- Configure timeouts

### Frontend optimization
- Multi-stage build reduces image size
- Next.js production build includes optimizations
- Caching headers configured
- Assets minified and compressed

## Security Considerations

1. **Passwords**: Use strong, unique passwords
2. **Secrets**: Don't commit `.env` files
3. **Users**: All services run as non-root
4. **CORS**: Restrict to specific origins
5. **SSL/TLS**: Use HTTPS in production
6. **Database**: Use strong authentication
7. **Updates**: Keep base images updated

## Next Phase: Phase 11 - Cross-layer Testing

Testing strategy covering:
- Unit tests for services
- Integration tests for API endpoints
- Frontend component tests
- E2E tests for complete workflows
- Coverage targets (80% service, 70% routes)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Compose Network                    │
│                    cube-ai-network                           │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Frontend (Next.js)                                  │   │
│  │  cube-ai-web:3000                                   │   │
│  │  ├─ Health Check: GET http://localhost:3000        │   │
│  │  ├─ Volume: ./apps/web:/app (dev)                  │   │
│  │  └─ Depends on: api                                 │   │
│  └──────────┬───────────────────────────────────────────┘   │
│             │                                                 │
│             │ api:8000 (internal)                           │
│             │ localhost:8000 (external)                      │
│             ▼                                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Backend (FastAPI)                                   │   │
│  │  cube-ai-api:8000                                   │   │
│  │  ├─ Health Check: GET /api/health                  │   │
│  │  ├─ Volume: ./apps/api:/app (dev)                  │   │
│  │  ├─ WebSocket: /api/scan/session                  │   │
│  │  └─ Depends on: postgres (healthy)                 │   │
│  └──────────┬───────────────────────────────────────────┘   │
│             │                                                 │
│             │ postgres:5432 (internal)                       │
│             │ localhost:5432 (external)                      │
│             ▼                                                 │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Database (PostgreSQL)                               │   │
│  │  cube-ai-postgres:5432                              │   │
│  │  ├─ Health Check: pg_isready                        │   │
│  │  ├─ Volume: postgres-data (named, persistent)       │   │
│  │  └─ Auto-init: database/schema/                     │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## File Structure

```
cube-ai/
├── Dockerfile                    # API container
├── Dockerfile.web                # Web container
├── docker-compose.yml            # Service orchestration
├── .dockerignore                 # Build exclusions
├── .env.example                  # Environment template
├── requirements.txt              # Python dependencies
├── docs/
│   ├── DOCKER-DEPLOYMENT.md      # Detailed deployment guide
│   └── phases/
│       └── phase-10-docker.md    # Phase documentation
├── apps/
│   ├── api/
│   │   ├── main.py               # FastAPI app
│   │   ├── requirements.txt      # Python deps
│   │   ├── routes/               # API endpoints
│   │   ├── services/             # Business logic
│   │   └── db/                   # Database layer
│   └── web/
│       ├── package.json          # Node deps
│       ├── next.config.ts        # Next.js config
│       └── app/                  # React pages
└── database/
    └── schema/                   # SQL initialization
```

## Deployment Checklist

- [ ] Copy `.env.example` to `.env.docker`
- [ ] Update environment variables
- [ ] Build Docker images
- [ ] Test locally with docker-compose
- [ ] Push images to registry
- [ ] Deploy to production environment
- [ ] Verify all services healthy
- [ ] Run health checks
- [ ] Test API endpoints
- [ ] Test WebSocket connection
- [ ] Verify database connectivity
- [ ] Configure backups
- [ ] Set up monitoring
- [ ] Configure log aggregation

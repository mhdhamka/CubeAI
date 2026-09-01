# CubeAI Docker Quick Start

Get the entire CubeAI stack running in 4 commands.

## Prerequisites

- Docker Desktop (Windows/Mac) or Docker + Docker Compose (Linux)
- 4GB+ RAM allocated to Docker
- 5GB+ disk space

## Quick Start

### 1. Copy environment configuration
```bash
cp .env.example .env.docker
```

### 2. Build and start all services
```bash
docker-compose up --build
```

### 3. Wait for all services to be healthy
```bash
# In another terminal, monitor status
docker-compose ps
```

Expected output:
```
NAME              STATUS
cube-ai-web       Up (healthy)
cube-ai-api       Up (healthy)
cube-ai-postgres  Up (healthy)
```

### 4. Access services

| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | CubeAI application |
| API | http://localhost:8000 | Backend API |
| API Docs | http://localhost:8000/docs | Swagger documentation |
| Database | localhost:5432 | PostgreSQL (user: cubeai) |

## Verify Installation

```bash
# Test API health
curl http://localhost:8000/api/health

# Test Frontend
curl http://localhost:3000

# Test Database
docker-compose exec postgres psql -U cubeai -d cube_ai_db -c "SELECT 1"
```

## Common Commands

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f web
```

### Stop services
```bash
docker-compose stop
```

### Restart services
```bash
docker-compose restart
```

### Remove everything (data loss!)
```bash
docker-compose down -v
```

### Execute commands
```bash
# Run tests
docker-compose exec api pytest tests/
docker-compose exec web npm test

# Database query
docker-compose exec postgres psql -U cubeai -d cube_ai_db

# Interactive shell
docker-compose exec api bash
docker-compose exec web sh
```

## Development Workflow

Code changes in `apps/api/` and `apps/web/` are automatically reloaded thanks to volume mounts.

### Edit and save files
Changes appear immediately in running containers without restart.

### View live logs
```bash
docker-compose logs -f api    # Follow API changes
docker-compose logs -f web    # Follow frontend changes
```

## Production Deployment

See `docs/DOCKER-DEPLOYMENT.md` and `docs/phases/phase-10-docker.md` for:
- Production environment setup
- Resource limits configuration
- Reverse proxy configuration (nginx)
- Backup and recovery procedures
- Monitoring and alerting setup

## Troubleshooting

### Services won't start
```bash
docker-compose logs
docker-compose down -v
docker-compose up --build
```

### Port already in use
```bash
# Change ports in docker-compose.yml
# Or stop conflicting services:
lsof -i :3000    # Find process on port 3000
kill -9 <PID>    # Kill the process
```

### Database connection error
```bash
# Check PostgreSQL health
docker-compose exec postgres pg_isready

# Verify DATABASE_URL
docker-compose exec api echo $DATABASE_URL

# Restart PostgreSQL
docker-compose restart postgres
```

### API returns 500 errors
```bash
# Check logs
docker-compose logs api

# Initialize database if needed
docker-compose exec api python -c "from db import init_db; init_db()"
```

## Architecture

```
┌─────────────────────────────────────────────────┐
│          Docker Compose Network                  │
│                                                  │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  Next.js     │  │  FastAPI     │  ┌────────┐ │
│  │  :3000       │→→│  :8000       │→→│ PgSQL  │ │
│  │  (web)       │  │  (api)       │  │ :5432  │ │
│  └──────────────┘  └──────────────┘  └────────┘ │
│       │                   │               │      │
└───────┼───────────────────┼───────────────┼──────┘
        │                   │               │
   localhost:3000      localhost:8000  localhost:5432
```

## Next Steps

1. **Run the application**: `docker-compose up`
2. **Visit frontend**: http://localhost:3000
3. **Browse API docs**: http://localhost:8000/docs
4. **View logs**: `docker-compose logs -f`
5. **Read full guide**: See `docs/DOCKER-DEPLOYMENT.md`

## Support

For detailed documentation, see:
- `docs/DOCKER-DEPLOYMENT.md` - Complete deployment guide
- `docs/phases/phase-10-docker.md` - Detailed technical documentation
- `docs/phases/PHASE-10-README.md` - Phase 10 overview

---

**Phase 10 Complete**: Docker Compose infrastructure ready for Phases 11-12 (Testing & Production Polish)

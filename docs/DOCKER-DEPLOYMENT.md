# Docker Deployment Guide

Complete Docker setup for CubeAI with PostgreSQL database, FastAPI backend, and Next.js frontend.

## Quick Start

### 1. Set up environment
```bash
cp .env.example .env.docker
# Edit .env.docker with your configuration
```

### 2. Build and start services
```bash
docker-compose up --build
```

### 3. Access services
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Database: postgresql://localhost:5432/cube_ai_db

### 4. Initialize database (first run)
```bash
docker-compose exec api python -c "from db import init_db; init_db()"
```

## Services Overview

### PostgreSQL (postgres)
- Image: `postgres:14-alpine`
- Port: `5432`
- Volumes: `postgres-data` (persistent)
- Health Check: Every 10 seconds
- Auto-initialization from `database/schema/`

**Environment Variables:**
- `DB_USER`: Database user (default: `cubeai`)
- `DB_PASSWORD`: Database password (default: `changeme123`)
- `DB_NAME`: Database name (default: `cube_ai_db`)

### FastAPI Backend (api)
- Build: `Dockerfile`
- Port: `8000`
- Dependencies: PostgreSQL must be healthy
- Volumes: `./apps/api:/app` (dev mode)
- Health Check: Every 30 seconds

**Environment Variables:**
- `SERVICE_NAME`: Service identifier
- `SERVICE_VERSION`: API version
- `DEBUG`: Debug mode (false for production)
- `DATABASE_URL`: PostgreSQL connection string
- `CORS_ORIGINS`: Allowed origins (comma-separated)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

**API Endpoints:**
- `GET /api/health` - Health check
- `POST /api/solve` - Solver endpoint
- `POST /api/validate` - Validator endpoint
- `POST /api/scan/image` - Vision endpoint
- `POST /api/coaching` - Coaching endpoint
- `WS /api/scan/session` - WebSocket scanning
- `GET/POST /api/profiles` - Profile management
- `GET/POST /api/solves` - Solve record management
- `GET /api/statistics` - Statistics endpoints

### Next.js Frontend (web)
- Build: `Dockerfile.web`
- Port: `3000`
- Dependencies: FastAPI service
- Multi-stage build: Builder + Runtime
- Health Check: Every 30 seconds

**Build Arguments:**
- `NEXT_PUBLIC_API_URL`: Backend API URL
- `NEXT_PUBLIC_WS_URL`: WebSocket URL

**Environment Variables:**
- `NODE_ENV`: Environment (development/production)
- `NEXT_PUBLIC_API_URL`: Backend URL (http://localhost:8000)
- `NEXT_PUBLIC_WS_URL`: WebSocket URL (ws://localhost:8000)

## Configuration

### Environment Files

**Development (.env.docker):**
```env
DEBUG=true
LOG_LEVEL=DEBUG
DB_PASSWORD=dev-password
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

**Production (.env.prod):**
```env
DEBUG=false
LOG_LEVEL=WARNING
DB_PASSWORD=<strong-password>
CORS_ORIGINS=https://cubeai.example.com
```

### Network Configuration

All services run on `cube-ai-network` bridge network:
- Services communicate by container name
- `api` connects to `postgres:5432` internally
- `web` connects to `api:8000` internally
- External access via published ports

### Volume Configuration

**postgres-data**: Named volume for database persistence
- Mount: `/var/lib/postgresql/data`
- Driver: `local`
- Persists across container restarts

**api**: Bind mount for development
- Mount: `./apps/api:/app`
- Enables live code reloading
- Remove in production builds

**web**: Bind mount for development
- Mount: `./apps/web:/app`
- Mount: `/app/.next` (Docker-only directory)

## Common Commands

### Start services
```bash
# Start in foreground
docker-compose up

# Start in background
docker-compose up -d

# Start with rebuild
docker-compose up --build

# Start specific service
docker-compose up postgres api
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api

# Last 100 lines
docker-compose logs --tail=100 web
```

### Execute commands
```bash
# Execute in api container
docker-compose exec api python -c "print('Hello')"

# Interactive bash
docker-compose exec api bash

# Run migrations
docker-compose exec api flask db upgrade
```

### Stop and remove
```bash
# Stop services (keep data)
docker-compose stop

# Remove containers (keep data)
docker-compose rm

# Remove everything (data loss!)
docker-compose down -v
```

### Database operations
```bash
# Connect to database
docker-compose exec postgres psql -U cubeai -d cube_ai_db

# Backup database
docker-compose exec postgres pg_dump -U cubeai cube_ai_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U cubeai cube_ai_db < backup.sql

# Reset database
docker-compose exec postgres psql -U cubeai -d cube_ai_db -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

## Health Checks

All services include health checks:

**PostgreSQL**: `pg_isready` (10s interval, 5s timeout, 5 retries)
- If unhealthy: Container restarts
- Indicates: Database connectivity issue

**FastAPI**: HTTP GET `/api/health` (30s interval, 10s timeout, 3 retries)
- If unhealthy: Container restarts
- Indicates: API server issue

**Next.js**: HTTP GET `http://localhost:3000` (30s interval, 10s timeout, 3 retries)
- If unhealthy: Container restarts
- Indicates: Frontend server issue

### Check service health
```bash
# View health status
docker-compose ps

# Check specific service
docker inspect cube-ai-api --format='{{.State.Health}}'

# View health logs
docker inspect cube-ai-postgres --format='{{json .State.Health.Log}}' | jq
```

## Production Deployment

### Pre-deployment checklist
- [ ] Set strong database password in `.env.prod`
- [ ] Set `DEBUG=false`
- [ ] Set `LOG_LEVEL=WARNING` or `ERROR`
- [ ] Configure `CORS_ORIGINS` with your domain
- [ ] Update `NEXT_PUBLIC_API_URL` to production URL
- [ ] Update `NEXT_PUBLIC_WS_URL` to production WebSocket URL
- [ ] Configure reverse proxy (nginx) in front
- [ ] Set up SSL/TLS certificates
- [ ] Configure database backups
- [ ] Set resource limits (memory, CPU)

### Resource Limits
```yaml
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
  
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 1G
        reservations:
          cpus: '1'
          memory: 512M
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
    listen 443 ssl;
    server_name cubeai.example.com;
    
    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    
    location /api {
        proxy_pass http://cube_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    location /api/scan/session {
        proxy_pass http://cube_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    location / {
        proxy_pass http://cube_web;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Troubleshooting

### Services won't start
```bash
# Check logs
docker-compose logs

# Rebuild images
docker-compose down -v
docker-compose up --build

# Check disk space
docker system df
docker system prune
```

### Database connection errors
```bash
# Verify PostgreSQL is running
docker-compose exec postgres pg_isready

# Check connection string
docker-compose exec api echo $DATABASE_URL

# Test connection
docker-compose exec api psql $DATABASE_URL -c "SELECT 1"
```

### API returns 500 errors
```bash
# Check API logs
docker-compose logs -f api

# Check database status
docker-compose ps postgres

# Verify database initialization
docker-compose exec api python -c "from db import init_db; init_db()"
```

### Frontend can't reach API
```bash
# Check network connectivity
docker-compose exec web curl http://api:8000/api/health

# Verify CORS settings
docker-compose exec api echo $CORS_ORIGINS

# Check environment variables
docker-compose exec web env | grep NEXT_PUBLIC
```

### WebSocket connection fails
```bash
# Check WebSocket endpoint
docker-compose exec web curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" http://api:8000/api/scan/session

# Verify WebSocket URL
docker-compose exec web env | grep WS_URL

# Check firewall/routing
docker-compose exec web ping -c 1 api
```

## Performance Tuning

### PostgreSQL
```sql
-- Connection pooling (set in docker-compose.env)
max_connections=200

-- Memory settings
shared_buffers=256MB
effective_cache_size=1GB
work_mem=16MB

-- WAL for replication
wal_level=replica
```

### FastAPI
```
--workers 4
--worker-class uvicorn.workers.UvicornWorker
--worker-connections 1000
--backlog 2048
```

### Next.js
```bash
NODE_OPTIONS=--max-old-space-size=2048
```

## Backup and Recovery

### Automated backups
```bash
#!/bin/bash
# backup.sh
docker-compose exec -T postgres pg_dump -U cubeai cube_ai_db | \
  gzip > backups/cube_ai_$(date +%Y%m%d_%H%M%S).sql.gz
```

### Restore from backup
```bash
gunzip < backups/cube_ai_20240115_120000.sql.gz | \
  docker-compose exec -T postgres psql -U cubeai cube_ai_db
```

## Monitoring

### Container stats
```bash
docker stats cube-ai-api cube-ai-web cube-ai-postgres
```

### Log aggregation
```bash
docker-compose logs --timestamps -f
```

### Health monitoring
```bash
docker-compose ps
```

## Security Notes

1. **Passwords**: Use strong, unique passwords in production
2. **Environment Variables**: Don't commit `.env` files to version control
3. **Database**: Use PostgreSQL user instead of postgres user
4. **Permissions**: Use non-root user in containers
5. **SSL/TLS**: Always use HTTPS in production
6. **CORS**: Restrict to specific origins
7. **Rate Limiting**: Implement API rate limiting
8. **Secrets**: Use Docker secrets for sensitive data

## Next Steps

1. Configure production environment variables
2. Set up automated backups
3. Configure monitoring and alerts
4. Set up CI/CD pipeline for deployments
5. Configure log aggregation (ELK, Splunk, etc.)
6. Set up auto-scaling if needed
7. Configure load balancing for high availability

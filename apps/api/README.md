# CubeAI API

FastAPI service for the CubeAI platform. Provides REST and WebSocket endpoints for cube state validation, solving, vision-based scanning, and user management.

## Features

- **Health Checks**: Liveness, readiness, and health status endpoints
- **Cube Validation**: Validate cube states and detect solvability
- **Solver Integration**: Bridge to Python Kociemba and IDA* solvers
- **Vision Pipeline**: Image upload and camera scanning for cube state detection
- **Persistence**: PostgreSQL-backed user profiles, solve history, and statistics
- **WebSocket Sessions**: Real-time camera scanning and scan progress
- **Coaching API**: Contextual explanations and algorithm guidance
- **Error Handling**: Structured error responses with diagnostic details
- **CORS Support**: Configured for Next.js frontend integration
- **Logging**: JSON and text logging with configurable levels

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 14+ (for persistence)
- Virtual environment

### Setup

1. **Create virtual environment**:
   ```bash
   cd apps/api
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Run development server**:
   ```bash
   python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access API**:
   - Interactive docs: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health: http://localhost:8000/api/health

## API Endpoints (Phase 1)

### Health & Status

- `GET /api/health` - Service health check
- `GET /api/health/ready` - Readiness check
- `GET /api/health/live` - Liveness check

## Project Structure

```
apps/api/
├── main.py           # FastAPI application instance, middleware, exception handlers
├── config.py         # Configuration management (pydantic-settings)
├── errors.py         # Exception definitions and error codes
├── models.py         # Pydantic data models (request/response schemas)
├── requirements.txt  # Python dependencies
├── .env.example      # Configuration template
├── routes/
│   ├── __init__.py
│   ├── health.py     # Health check endpoints
│   ├── solve.py      # Solve endpoints (Phase 2)
│   ├── validate.py   # Validation endpoints (Phase 2)
│   ├── scan.py       # Vision scanning endpoints (Phase 4)
│   ├── profile.py    # User profile endpoints (Phase 7)
│   ├── stats.py      # Statistics endpoints (Phase 8)
│   ├── coaching.py   # Coaching endpoints (Phase 6)
│   └── ws.py         # WebSocket endpoints (Phase 9)
├── services/         # Business logic (Phase 2+)
├── db/               # Database models and utilities (Phase 7)
└── tests/            # Test suite (Phase 11)
```

## Development Phases

- **Phase 1** ✅ API Foundation - FastAPI, config, error handling, health checks
- **Phase 2** 🔄 Engine API - `/solve` and `/validate` endpoints
- **Phase 3** 🔄 Frontend Client - TypeScript API client
- **Phase 4** 🔄 Vision API - Image scanning endpoint
- **Phase 5** 🔄 Full Pipeline - End-to-end integration
- **Phase 6** 🔄 Coaching API - Coaching endpoint
- **Phase 7** 🔄 Persistence - Database integration
- **Phase 8** 🔄 Statistics - Aggregates (Ao5/12/100)
- **Phase 9** 🔄 WebSocket - Real-time scanning
- **Phase 10** 🔄 Docker - Containerization
- **Phase 11** 🔄 Testing - Unit, integration, E2E tests
- **Phase 12** 🔄 Production - Tailwind, hardening

## Configuration

See `.env.example` for all configuration options. Key variables:

- `DEBUG` - Enable debug mode and detailed error messages
- `CORS_ORIGINS` - Frontend URLs allowed to access API
- `DATABASE_URL` - PostgreSQL connection string
- `VISION_CONFIDENCE_THRESHOLD` - Minimum confidence for scan results
- `SOLVER_TIMEOUT` - Maximum time for solve operations
- `COACHING_PROVIDER` - Use "deterministic" or "external" coaching

## Error Handling

API returns structured error responses:

```json
{
  "code": "INVALID_CUBE_STATE",
  "message": "Cube state has invalid corner orientation",
  "details": {
    "corner_index": 2,
    "orientation": 3,
    "valid_range": [0, 2]
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

See `errors.py` for complete error code reference.

## Logging

Logs are configured via `LOG_LEVEL` and `LOG_FORMAT`:

- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Formats**: "json" (structured) or "text" (human-readable)

Example JSON log:
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "level": "INFO",
  "logger": "cube_ai.api",
  "message": "Solve request processed",
  "request_id": "abc123",
  "solving_time_ms": 150,
  "num_moves": 18
}
```

## Contributing

1. Create a new route module in `routes/`
2. Define models in `models.py` (or create `models/domain.py`)
3. Implement services in `services/`
4. Add comprehensive error handling
5. Write tests in `tests/`
6. Update this README

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [CubeAI Main README](../../README.md)

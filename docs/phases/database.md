# Phase 7: Database Persistence

User profiles, solve records, and coaching history storage.

## Overview

Phase 7 implements persistent storage for user data, enabling features like statistics tracking, solve history, coaching records, and multi-profile support.

## Database Schema

### Tables

#### Users
```sql
- id (PK)
- username (unique)
- email (unique)
- hashed_password
- created_at, updated_at
```

#### Profiles
```sql
- id (PK)
- user_id (FK → users)
- name
- cube_size (default: 3)
- solving_method (cfop, roux, petrus, zz)
- preferred_focus (cross, f2l, oll, pll, overall)
- created_at, updated_at
```

#### SolveRecords
```sql
- id (PK)
- profile_id (FK → profiles)
- time_ms (solve time)
- num_moves (move count)
- scramble (initial state)
- solution (move sequence)
- solver_used (manual, kociemba, human, algorithm)
- confidence (0.0-1.0)
- is_dnf, is_dns (Did Not Finish/Start)
- notes (user notes)
- metadata (JSON)
- created_at (indexed for sorting)
```

#### ScanSessions
```sql
- id (PK)
- profile_id (FK → profiles)
- session_key (UUID, unique)
- status (active, completed, cancelled)
- detected_cube_state (JSON)
- confidence
- num_frames_processed
- created_at, completed_at
```

#### CoachingRecords
```sql
- id (PK)
- solve_record_id (FK → solve_records)
- focus_area
- explanation
- key_points (JSON list)
- suggested_algorithms (JSON list)
- difficulty_level
- user_rating (1-5, nullable)
- created_at
```

## API Endpoints

### Profiles

**GET /api/profiles/{profile_id}**
- Retrieve a profile by ID
- Returns ProfileModel with metadata

**POST /api/profiles**
- Create a new profile
- Request: { user_id, name, cube_size, solving_method, preferred_focus }
- Response: ProfileModel with ID and timestamps

**PUT /api/profiles/{profile_id}**
- Update profile settings
- Partial updates supported

**DELETE /api/profiles/{profile_id}**
- Delete profile and associated solves
- WARNING: Irreversible!

### Solves

**GET /api/profiles/{profile_id}/solves**
- List all solve records for a profile
- Query params: limit (1-1000, default 100), offset (default 0)
- Returns: SolveRecordModel[]
- Excludes DNF/DNS by default

**GET /api/solves/{solve_id}**
- Retrieve specific solve by ID
- Returns: SolveRecordModel

**POST /api/solves**
- Record a new solve attempt
- Request: SolveRecordModel
- Response: (201) SolveRecordModel with ID and created_at

**DELETE /api/solves/{solve_id}**
- Delete a solve record
- Response: (204) No Content

## Database Configuration

### Connection String

Set `DATABASE_URL` in .env:

**PostgreSQL (Production)**
```
DATABASE_URL=postgresql://user:password@localhost:5432/cubeai
```

**SQLite (Development)**
```
DATABASE_URL=sqlite:///./cubeai.db
```

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/cubeai
# Or for SQLite:
# DATABASE_URL=sqlite:///./cubeai.db
```

## Implementation Details

### Files Created

- `apps/api/db/models.py` - SQLAlchemy models (User, Profile, SolveRecord, ScanSession, CoachingRecord)
- `apps/api/db/database.py` - Connection management and session factory
- `apps/api/db/__init__.py` - Module exports
- `apps/api/services/profile.py` - ProfileService CRUD operations
- `apps/api/services/solve.py` - SolveService CRUD operations
- `apps/api/routes/profiles.py` - Profile endpoints
- `apps/api/routes/solves.py` - Solve record endpoints

### Features

- ✅ SQLAlchemy ORM for type-safe database access
- ✅ Connection pooling (pool_size=10, max_overflow=20)
- ✅ Foreign key constraints and relationships
- ✅ Dependency injection with FastAPI (get_db())
- ✅ Automatic schema initialization on startup
- ✅ SQLite foreign key support
- ✅ PostgreSQL ready (production)
- ✅ Pagination support (limit/offset)
- ✅ Query filtering and ordering
- ✅ JSON field support for metadata

### Database Initialization

Automatically runs on application startup:

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()  # Creates tables if not exist
    yield
    # Shutdown
```

## Usage Examples

### Create Profile

```python
from api.db import SessionLocal
from api.services.profile import ProfileService

db = SessionLocal()
profile = ProfileService.create_profile(db, {
    "user_id": 1,
    "name": "3x3 CFOP",
    "cube_size": 3,
    "solving_method": "cfop",
    "preferred_focus": "f2l",
})
```

### Record Solve

```python
from api.services.solve import SolveService

solve = SolveService.create_solve(db, {
    "profile_id": 1,
    "time_ms": 45320,
    "num_moves": 52,
    "scramble": "R U R' U'",
    "solution": "R U R' U'",
    "solver_used": "manual",
    "confidence": 1.0,
})
```

### Query Solves

```python
from api.services.solve import SolveService

# Get 10 most recent solves
solves = SolveService.get_profile_solves(
    db,
    profile_id=1,
    limit=10,
    offset=0,
)

# Count total solves
count = SolveService.count_profile_solves(db, profile_id=1)
```

## React Integration

```typescript
import { apiClient } from '@cube-ai/cube-api';

// Create profile
const profile = await apiClient.createProfile({
  user_id: 1,
  name: "My 3x3",
  cube_size: 3,
  solving_method: "cfop",
  preferred_focus: "f2l",
});

// Get solves
const solves = await apiClient.getSolves(profile.id);

// Record solve
const solve = await apiClient.createSolve({
  profile_id: profile.id,
  time_ms: 45320,
  num_moves: 52,
  scramble: "R U R' U'",
  solution: "R U R' U'",
  solver_used: "manual",
  confidence: 1.0,
});
```

## Migration Strategy (Phase 7+)

For production migrations, use Alembic:

```bash
# Initialize migrations directory
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Add new table"

# Apply migration
alembic upgrade head
```

## Next Phase

Phase 8: Statistics
- Ao5, Ao12, Ao100 calculations
- Best/worst solve tracking
- Trend analysis
- Dashboard queries

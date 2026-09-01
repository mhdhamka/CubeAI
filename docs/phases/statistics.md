# Phase 8: Statistics (Ao5/12/100)

Performance tracking and achievement metrics for speedcubing.

## Overview

Phase 8 implements comprehensive statistics calculation for cubing profiles, including:
- Average of 5 (Ao5) - Most common metric
- Average of 12 (Ao12) - Longer-term trend
- Average of 100 (Ao100) - Long-term improvement tracking
- Personal records (best/worst times)
- Improvement trend analysis
- Milestone achievements

## API Endpoints

### Statistics

**GET /api/profiles/{profile_id}/statistics**
- Retrieve comprehensive statistics
- Calculates all averages automatically
- Returns: StatisticsModel

**GET /api/profiles/{profile_id}/statistics/improvement**
- Analyze improvement trends
- Compares recent performance with historical
- Returns trend: improving | declining | stable

**GET /api/profiles/{profile_id}/statistics/milestones**
- Track achievement milestones
- Sub-30, Sub-20, Sub-10 tracking
- Personal best history

## Database Queries

No schema changes needed - uses existing SolveRecord table.

### Query Optimization

Queries filter and order by:
- profile_id (indexed)
- is_dnf, is_dns (filter out invalid times)
- created_at DESC (most recent first)

## Statistics Calculations

### Average of 5 (Ao5)
```
Ao5 = average(last 5 solves)
```

**Most important metric for speedcubing**
- Used in official competitions
- Represents consistent performance on any given day
- Improves fastest when practicing efficiently

### Average of 12 (Ao12)
```
Ao12 = average(last 12 solves)
```

**Week-to-week consistency**
- Smooths out daily variance
- Shows training progress
- Better indicator of overall skill level

### Average of 100 (Ao100)
```
Ao100 = average(last 100 solves)
```

**Long-term trend analysis**
- Tracks overall improvement
- Ignores practice plateaus
- Shows actual skill progression

### Personal Records
```
PB (Personal Best) = min(all valid solve times)
Worst = max(all valid solve times)
```

## React Integration

### Hook: useStatistics

```typescript
import { useStatistics, formatSolveTime } from '@cube-ai/cube-api';

export function StatsDisplay({ profileId }: { profileId: number }) {
  const stats = useStatistics();

  useEffect(() => {
    stats.execute(profileId);
  }, [profileId]);

  if (stats.loading) return <div>Loading...</div>;
  if (stats.error) return <div>Error: {stats.error.message}</div>;

  return (
    <div>
      <h2>Statistics</h2>
      <p>Total Solves: {stats.data?.total_solves}</p>
      <p>Ao5: {formatSolveTime(stats.data?.average_ao5_ms || 0)}</p>
      <p>Ao12: {formatSolveTime(stats.data?.average_ao12_ms || 0)}</p>
      <p>Ao100: {formatSolveTime(stats.data?.average_ao100_ms || 0)}</p>
      <p>Best: {formatSolveTime(stats.data?.best_time_ms || 0)}</p>
    </div>
  );
}
```

### Component: StatisticsDisplay

Pre-built statistics display component:

```typescript
import { StatisticsDisplay } from '@cube-ai/cube-api';

export function Dashboard() {
  return <StatisticsDisplay statistics={stats} />;
}
```

## Trend Analysis

### Improvement Detection
- Recent Ao5 vs Previous Ao5
- Calculates delta in ms and %
- Categorizes: improving | stable | declining

### Minimum Thresholds
- Needs 5 solves minimum for Ao5
- Needs 12 solves minimum for Ao12
- Needs 100 solves minimum for Ao100

## Time Formatting

Solves are stored in milliseconds but displayed as MM:SS.ms format:

```
28450 ms  → 28.450
32100 ms  → 32.100
125340 ms → 2:05.340
```

## Implementation Details

### Files Created

- `apps/api/services/statistics.py` - StatisticsService with calculation methods
- `apps/api/routes/statistics.py` - Three statistics endpoints
- `packages/cube-api/hooks-statistics.ts` - React hooks for statistics
- `docs/phases/phase-8-statistics.md` - This documentation

### Features

- ✅ Ao5, Ao12, Ao100 calculations
- ✅ Personal records tracking
- ✅ Improvement trend analysis
- ✅ Milestone achievements
- ✅ Proper time formatting
- ✅ React hooks for integration
- ✅ Pre-built statistics components
- ✅ DNF/DNS filtering

### Performance

Query complexity: O(n) where n is profile's solve count
- Index on profile_id enables fast filtering
- No aggregation database queries needed
- In-memory calculation keeps logic simple and testable

## Speedcubing Benchmarks

| Skill Level | Ao5 | Status |
|-------------|-----|--------|
| Complete Beginner | 2-5 minutes | Just started |
| Learning CFOP | 60-90 seconds | Understanding method |
| Competent Solver | 30-60 seconds | Consistent solves |
| Sub-30 | < 30 seconds | Intermediate milestone |
| Sub-20 | < 20 seconds | Advanced milestone |
| Sub-10 | < 10 seconds | Expert speedcuber |
| Sub-5 | < 5 seconds | Elite/World class |

## Next Phase

Phase 9: WebSocket Real-time Communication
- Live scan session feedback
- Real-time face detection progress
- WebSocket events for scanning workflow
- Camera stream integration

## Examples

### Getting Statistics

```python
# Python backend
stats = StatisticsService.get_statistics(db, profile_id=1)
print(f"Ao5: {stats.average_ao5_ms}ms")
print(f"Ao12: {stats.average_ao12_ms}ms")
print(f"PB: {stats.best_time_ms}ms")
```

### Frontend Display

```tsx
const { data: stats } = useStatistics();

return (
  <div className="stats-grid">
    <div>Ao5: {formatSolveTime(stats?.average_ao5_ms || 0)}</div>
    <div>Ao12: {formatSolveTime(stats?.average_ao12_ms || 0)}</div>
    <div>Ao100: {formatSolveTime(stats?.average_ao100_ms || 0)}</div>
    <div>PB: {formatSolveTime(stats?.best_time_ms || 0)}</div>
  </div>
);
```

## Testing Strategies

### Unit Tests
- Calculate Ao5 with 5 solves
- Calculate Ao12 with 12 solves
- Filter DNF/DNS correctly
- Order by created_at DESC
- Handle null times gracefully

### Integration Tests
- GET /api/profiles/{id}/statistics returns correct averages
- GET improvement endpoint with trend detection
- GET milestones endpoint with achievements
- Verify time formatting correctness

### Edge Cases
- Profile with 0 solves
- Profile with 1-4 solves (Ao5 unavailable)
- Profile with mixed DNF/DNS/valid
- Very fast solves (< 1 second)
- Very slow solves (> 10 minutes)

# Phase 6: Coaching Service API

AI-powered coaching and guidance for cubing solutions.

## Overview

The Coaching Service provides personalized explanations and guidance for cube solutions, helping users understand techniques, learn algorithms, and improve their solving skills.

## Features

- **Solution Explanation**: Detailed breakdown of solving techniques used
- **Algorithm Suggestions**: Recommended algorithms for specific phases
- **Focus Areas**: Targeted coaching for different solving phases (Cross, F2L, OLL, PLL)
- **Difficulty Assessment**: Tracks solution efficiency and provides improvement suggestions
- **Deterministic Fallback**: Works without external AI service (Phase 6), with bridging to external reasoning in Phase 7+

## Coaching Focus Areas

### Cross
- Foundation of CFOP method
- Edge placement strategy
- Efficiency and rotations
- Key: Plan before executing

### F2L (First Two Layers)
- Most important phase for speedcubing
- 41 cases to master
- Corner-edge pairing
- Key: Rotationless solutions

### OLL (Orient Last Layer)
- 57 total cases
- 2-look method alternative (9 cases)
- Yellow stickers orientation
- Key: Quick case recognition

### PLL (Permute Last Layer)
- 21 total cases
- Yellow stickers placement
- AUF (Alignment Up Face) optimization
- Key: Fast algorithm execution

### Overall
- General efficiency analysis
- Cross-phase perspective
- Improvement suggestions
- Tracking progress

## API Endpoint

### POST /api/coaching

**Request:**
```json
{
  "cube_state": {
    "corners": [0, 1, 2, 3, 4, 5, 6, 7],
    "corner_orientations": [0, 0, 0, 0, 0, 0, 0, 0],
    "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "edge_orientations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  },
  "solution_moves": [
    {"face": "R", "times": 1},
    {"face": "U", "times": 1},
    {"face": "R", "times": 3}
  ],
  "focus": "f2l"
}
```

**Response:**
```json
{
  "explanation": "F2L (First 2 Layers) combines the white cross with the first layer corners...",
  "key_points": [
    "Pair corners with their edge partners",
    "Use cube rotations as setup moves",
    "Practice the 41 F2L cases"
  ],
  "suggested_algorithms": [
    "R U R' U'",
    "y' R U' R'",
    "U R U' R' U R U' R'"
  ],
  "difficulty_level": "intermediate"
}
```

## React Hook Usage

```typescript
import { useCoaching } from '@cube-ai/cube-api';

function CoachingComponent() {
  const coaching = useCoaching();
  const [focusArea, setFocusArea] = useState('overall');

  const getCoaching = async (cubeState, solution) => {
    try {
      const response = await coaching.execute({
        cube_state: cubeState,
        solution_moves: solution,
        focus: focusArea,
      });
      
      console.log('Explanation:', response.explanation);
      console.log('Key Points:', response.key_points);
      console.log('Suggested Algorithms:', response.suggested_algorithms);
    } catch (error) {
      console.error('Coaching failed:', error);
    }
  };

  return (
    <div>
      <select value={focusArea} onChange={(e) => setFocusArea(e.target.value)}>
        <option value="cross">Cross</option>
        <option value="f2l">F2L</option>
        <option value="oll">OLL</option>
        <option value="pll">PLL</option>
        <option value="overall">Overall</option>
      </select>

      <button 
        onClick={() => getCoaching(cubeState, solution)} 
        disabled={coaching.loading}
      >
        {coaching.loading ? 'Getting Coaching...' : 'Get Coaching'}
      </button>

      {coaching.data && (
        <div>
          <h3>Coaching</h3>
          <p>{coaching.data.explanation}</p>
          <ul>
            {coaching.data.key_points.map((point) => (
              <li key={point}>{point}</li>
            ))}
          </ul>
          <div>
            <strong>Suggested Algorithms:</strong>
            {coaching.data.suggested_algorithms.map((algo) => (
              <code key={algo}>{algo}</code>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
```

## Implementation Details

### Files Created/Modified

- `apps/api/services/coaching.py` - Coaching service with deterministic logic
- `apps/api/routes/coaching.py` - POST /api/coaching endpoint
- `packages/cube-api/hooks.ts` - useCoaching React hook
- `apps/api/main.py` - Registered coaching router

### Service Logic

**CoachingService.get_coaching()**
1. Receives coaching request with cube state, solution, focus area
2. Determines difficulty level based on move count
3. Generates appropriate guidance based on focus area
4. Returns structured response with explanation, key points, and algorithms

### Difficulty Levels

- **Beginner**: ≤ 8 moves (very efficient)
- **Intermediate**: 8-15 moves (good technique)
- **Advanced**: > 15 moves (needs practice)

## Todo Phase 6

- ✅ Create CoachingService with deterministic logic
- ✅ Implement POST /api/coaching endpoint
- ✅ Create useCoaching React hook
- ✅ Add comprehensive docstring with examples
- ⏳ Bridge to Python ai/coach/coach.py for advanced reasoning
- ⏳ Support external AI reasoning service integration
- ⏳ Cache common coaching responses
- ⏳ Track user learning progress

## Future Enhancements

### Phase 7+
- External AI reasoning service for personalized coaching
- Learning progress tracking per user
- Personalized algorithm recommendations
- Difficulty-appropriate explanations

### Analytics
- Track most common mistakes
- Identify learning gaps
- Suggest practice priorities
- Compare against other users

## Algorithm Notation Reference

### Basic Moves
- **U, D, F, B, L, R** - Face clockwise 90°
- **U', D', F', B', L', R'** - Face counter-clockwise 90°
- **U2, D2, F2, B2, L2, R2** - Face 180°

### Slice Moves
- **M** - Middle layer clockwise (looking from R side)
- **E** - Equatorial layer clockwise (looking from D side)
- **S** - Standing layer clockwise (looking from F side)

### Cube Rotations
- **x** - Rotate on R-L axis (like R)
- **y** - Rotate on U-D axis (like U)
- **z** - Rotate on F-B axis (like F)

### Lowercase/Wide Moves
- **Rw, Uw, Fw** - Two-layer wide moves
- **Rw2, Uw2, Fw2** - Two-layer 180°

## Next Phase

Phase 7: Database Persistence
- User profiles and solve history
- Statistics calculation (Ao5, Ao12, Ao100)
- Persistent coaching records

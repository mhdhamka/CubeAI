# Phase 9: WebSocket Real-time Communication

Real-time cube scanning feedback with live camera feed support.

## Overview

Phase 9 implements WebSocket endpoints for real-time scanning workflow, enabling:
- Live cube detection progress feedback
- Face-by-face detection updates
- Real-time camera stream processing
- Session management and state tracking
- Error handling and retry logic

## WebSocket Endpoint

**WS /api/scan/session**

Establishes a WebSocket connection for real-time scanning.

### Connection Lifecycle

1. **Client connects** → WebSocket established
2. **Server sends** → scan_started event with session_id
3. **Client sends** → frame data (image or video frame)
4. **Server sends** → progress updates
5. **Server sends** → face_detected when cube face recognized
6. **Repeat** → Until all 6 faces detected
7. **Server sends** → completed with final cube_state
8. **Connection closes** → Scanning session ends

## Event Types

### Server Events (→ Client)

#### scan_started
```json
{
  "type": "scan_started",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

Sent when session begins. Client should start sending frames.

#### progress
```json
{
  "type": "progress",
  "face": 1,
  "confidence": 0.85,
  "frames_processed": 45,
  "timestamp": "2024-01-15T10:30:00.234567"
}
```

Updates during scanning. Indicates current detection progress.

#### face_detected
```json
{
  "type": "face_detected",
  "face": 1,
  "stickers": [0, 1, 2, 3, 4, 5, 6, 7, 8],
  "confidence": 0.92,
  "timestamp": "2024-01-15T10:30:00.345678"
}
```

Single face successfully detected. Stickers array contains color IDs.

**Sticker Color IDs:**
- 0: White
- 1: Yellow
- 2: Red
- 3: Orange
- 4: Blue
- 5: Green

#### retry
```json
{
  "type": "retry",
  "face": 1,
  "reason": "Quality too low, please retry",
  "timestamp": "2024-01-15T10:30:00.456789"
}
```

Request to rescan a face. Quality or confidence too low.

#### completed
```json
{
  "type": "completed",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "cube_state": {
    "corners": [0, 1, 2, 3, 4, 5, 6, 7],
    "corner_orientations": [0, 0, 0, 0, 0, 0, 0, 0],
    "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
    "edge_orientations": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
  },
  "confidence": 0.88,
  "timestamp": "2024-01-15T10:30:00.567890"
}
```

All 6 faces detected. Scanning complete with cube state.

#### error
```json
{
  "type": "error",
  "code": "TIMEOUT",
  "message": "Scan session timeout",
  "timestamp": "2024-01-15T10:30:00.678901"
}
```

Error occurred. Session will close.

#### cancel
```json
{
  "type": "cancel",
  "reason": "User cancelled",
  "timestamp": "2024-01-15T10:30:00.789012"
}
```

Session cancelled (by user or server).

### Client Events (← Client)

#### frame
```json
{
  "type": "frame",
  "data": "<ArrayBuffer with image data>"
}
```

Send image frame for processing.

#### cancel
```json
{
  "type": "cancel"
}
```

Cancel the scanning session.

#### retry
```json
{
  "type": "retry",
  "face": 1
}
```

Retry detection for specific face.

## React Integration

### Hook: useScanSession

```typescript
import { useScanSession, ScanSessionStatus } from '@cube-ai/cube-api';

export function LiveScanExample() {
  const session = useScanSession();

  // Send video frames
  const handleVideoFrame = (frameData: ArrayBuffer) => {
    session.sendFrame(frameData);
  };

  // Cancel scanning
  const handleCancel = () => {
    session.cancel();
  };

  // Retry specific face
  const handleRetry = () => {
    session.retry(session.currentFace);
  };

  return (
    <div>
      <ScanSessionStatus session={session} />
      <video onVideoFrame={handleVideoFrame} />
      <button onClick={handleCancel} disabled={!session.isScanning}>
        Cancel
      </button>
      <button onClick={handleRetry} disabled={!session.isScanning}>
        Retry Face {session.currentFace}
      </button>
    </div>
  );
}
```

### Hook Properties

```typescript
interface UseScanSession {
  // State
  connected: boolean;           // WebSocket connected
  sessionId: string | null;     // Session UUID
  isScanning: boolean;          // Actively scanning
  facesDetected: number;        // Number of faces found
  currentFace: number;          // Current face being scanned
  confidence: number;           // Detection confidence (0-1)
  framesProcessed: number;      // Total frames processed
  error: string | null;         // Error message if any
  cubeState: any | null;        // Final cube state (after completion)

  // Actions
  sendFrame: (frameData: ArrayBuffer) => void;
  cancel: () => void;
  retry: (faceNumber: number) => void;
  reset: () => void;
}
```

### Component: ScanSessionStatus

Pre-built status display component showing:
- Session ID
- Connection status
- Scanning progress
- Faces detected count
- Current face
- Confidence level
- Frame count
- Error messages
- Control buttons

## Implementation Details

### Files Created

- `apps/api/routes/ws.py` - WebSocket endpoint and event types
  - ScanEvent class with static methods for each event type
  - ConnectionManager for managing active WebSocket connections
  - websocket_scan_session handler with full protocol implementation

- `packages/cube-api/hooks-websocket.ts` - React WebSocket integration
  - useScanSession hook with full state management
  - Event type definitions (TypeScript interfaces)
  - ScanSessionStatus component for displaying status

### Features

- ✅ Full WebSocket protocol implementation
- ✅ Connection lifecycle management
- ✅ Event-driven architecture
- ✅ Comprehensive error handling
- ✅ Session tracking with UUIDs
- ✅ Face-by-face detection updates
- ✅ Progress feedback with frame counting
- ✅ Retry logic for quality improvement
- ✅ Type-safe event handling
- ✅ React hook for easy integration
- ✅ Pre-built UI components

### Performance Considerations

- Async/await pattern with asyncio for concurrent connections
- Connection manager tracks active sessions efficiently
- No blocking I/O during frame processing
- Timeout (300 seconds) prevents abandoned connections
- Binary frame support for efficient data transfer

## Architecture

### Server-side Architecture

```
WebSocket Connection
    ↓
connection_manager.connect()
    ↓
Send scan_started event
    ↓
Message Loop:
  ├→ Receive frame
  ├→ Process with vision service
  ├→ Send progress updates
  ├→ Send face_detected when ready
  ├→ Repeat until 6 faces
  └→ Send completed or error
    ↓
connection_manager.disconnect()
```

### Client-side Integration

```
useScanSession()
    ↓
WebSocket.open()
    ↓
Display session status
    ↓
Camera capture loop:
  ├→ Get video frame
  ├→ sendFrame(frameData)
  ├→ Update UI on events
  └→ Repeat
    ↓
On completion:
  ├→ Show cube state
  ├→ Convert to SolveRequest
  └→ Call solve endpoint
```

## Usage Examples

### Basic Scanning

```typescript
const { useScanSession } = require('@cube-ai/cube-api');

export function ScannerApp() {
  const session = useScanSession();
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (session.connected && videoRef.current) {
      const canvas = document.createElement('canvas');
      const ctx = canvas.getContext('2d');

      const captureFrame = () => {
        if (videoRef.current && ctx) {
          ctx.drawImage(videoRef.current, 0, 0);
          const frameData = canvas.toDataURL('image/jpeg');
          session.sendFrame(frameData as any);
        }
        if (session.isScanning) {
          requestAnimationFrame(captureFrame);
        }
      };

      captureFrame();
    }
  }, [session.connected, session.isScanning]);

  return (
    <div>
      <video ref={videoRef} />
      <ScanSessionStatus session={session} />
    </div>
  );
}
```

### Error Handling

```typescript
if (session.error) {
  return (
    <div style={{ color: 'red' }}>
      <h3>Scan Error</h3>
      <p>{session.error}</p>
      <button onClick={session.reset}>Try Again</button>
    </div>
  );
}
```

### Completion Handling

```typescript
if (session.cubeState && !session.isScanning) {
  return (
    <div>
      <h2>Cube Detected!</h2>
      <button onClick={() => solveCube(session.cubeState)}>
        Solve Cube
      </button>
    </div>
  );
}
```

## Testing Strategies

### Unit Tests
- Event creation methods
- ConnectionManager add/remove/broadcast
- Message parsing and validation
- Error condition handling

### Integration Tests
- Full scan workflow (frame → completion)
- Retry flow (frame → retry → completion)
- Cancel during scanning
- Timeout handling
- Multiple concurrent sessions

### E2E Tests
- Real camera capture
- Live video feed processing
- UI state transitions
- Error recovery

## Browser Support

- WebSocket support required
- Modern browsers: Chrome 43+, Firefox 11+, Safari 8+, Edge 12+
- Mobile browsers: iOS Safari 8+, Chrome Android 43+
- Fallback: Could implement Socket.IO for older browsers

## Next Phase

Phase 10: Docker Compose Setup
- Complete docker-compose.yml with services (web, api, postgres)
- Dockerfile for API service
- Environment configuration
- Health checks and networking
- Volume management

"""
WebSocket endpoints for real-time scanning and live feedback.
Supports streaming cube detection progress and live camera feeds.
"""

import logging
import json
import asyncio
from datetime import datetime
from uuid import uuid4
from fastapi import APIRouter, WebSocketException, status, Depends
from fastapi.websockets import WebSocket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["websocket"])


# ==================== WebSocket Event Types ====================

class ScanEvent:
    """Base class for scan session events."""
    
    @staticmethod
    def started(session_id: str) -> dict:
        """Scan session started."""
        return {
            "type": "scan_started",
            "session_id": session_id,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def progress(face: int, confidence: float, frame_count: int) -> dict:
        """Progress update during scanning."""
        return {
            "type": "progress",
            "face": face,
            "confidence": confidence,
            "frames_processed": frame_count,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def face_detected(face: int, stickers: list, confidence: float) -> dict:
        """Single face detected."""
        return {
            "type": "face_detected",
            "face": face,
            "stickers": stickers,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def retry(face: int, reason: str) -> dict:
        """Request to retry scanning a face."""
        return {
            "type": "retry",
            "face": face,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def cancel(reason: str) -> dict:
        """Scan session cancelled."""
        return {
            "type": "cancel",
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def completed(session_id: str, cube_state: dict, confidence: float) -> dict:
        """Scan session completed successfully."""
        return {
            "type": "completed",
            "session_id": session_id,
            "cube_state": cube_state,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat(),
        }
    
    @staticmethod
    def error(code: str, message: str) -> dict:
        """Error occurred."""
        return {
            "type": "error",
            "code": code,
            "message": message,
            "timestamp": datetime.utcnow().isoformat(),
        }


# ==================== WebSocket Connection Manager ====================

class ConnectionManager:
    """Manages WebSocket connections for scan sessions."""
    
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}
        self.session_data: dict[str, dict] = {}
    
    async def connect(self, websocket: WebSocket, session_id: str):
        """Register a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[session_id] = websocket
        self.session_data[session_id] = {
            "started_at": datetime.utcnow(),
            "frames_processed": 0,
            "faces_detected": 0,
        }
        logger.info(f"WebSocket connected: {session_id}")
    
    def disconnect(self, session_id: str):
        """Unregister a WebSocket connection."""
        if session_id in self.active_connections:
            del self.active_connections[session_id]
        if session_id in self.session_data:
            del self.session_data[session_id]
        logger.info(f"WebSocket disconnected: {session_id}")
    
    async def send_personal(self, session_id: str, data: dict):
        """Send message to specific connection."""
        if session_id in self.active_connections:
            try:
                await self.active_connections[session_id].send_json(data)
            except Exception as e:
                logger.error(f"Failed to send message to {session_id}: {e}")
    
    async def broadcast(self, message: str):
        """Broadcast message to all connections."""
        for connection in self.active_connections.values():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Failed to broadcast message: {e}")


# Global connection manager
manager = ConnectionManager()


# ==================== WebSocket Endpoint ====================

@router.websocket("/scan/session")
async def websocket_scan_session(websocket: WebSocket):
    """
    WebSocket endpoint for real-time cube scanning.
    
    **Protocol:**
    
    1. Server sends: scan_started event
    2. Client sends: image frames or video feed
    3. Server sends: progress, face_detected events
    4. Server sends: retry if face quality too low
    5. Client sends: new frame or cancel
    6. Server sends: completed (all 6 faces done) or error
    
    **Event Types:**
    
    **From Server:**
    - `scan_started`: Session initialized with session_id
    - `progress`: Face detection progress (face number, confidence, frame count)
    - `face_detected`: Cube face detected with sticker colors
    - `retry`: Request to rescan a face (quality too low)
    - `completed`: All 6 faces detected, cube state ready
    - `cancel`: Session cancelled
    - `error`: Error occurred
    
    **From Client:**
    - `frame`: Binary image data (WebSocket binary message)
    - `cancel`: Cancel the scanning session
    - `retry`: Retry the current face
    
    **Response Example:**
    ```json
    {
        "type": "scan_started",
        "session_id": "550e8400-e29b-41d4-a716-446655440000",
        "timestamp": "2024-01-15T10:30:00.123456"
    }
    ```
    
    **Usage:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/scan/session');
    
    ws.onopen = () => {
        // Send image frames
        const frameData = new ArrayBuffer(...);
        ws.send(frameData);
    };
    
    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === 'face_detected') {
            console.log(`Face ${msg.face} detected`);
        } else if (msg.type === 'completed') {
            console.log('Scan complete!', msg.cube_state);
        }
    };
    
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
    };
    
    ws.onclose = () => {
        console.log('Connection closed');
    };
    ```
    """
    session_id = str(uuid4())
    
    try:
        await manager.connect(websocket, session_id)
        
        # Send initialization event
        await manager.send_personal(
            session_id,
            ScanEvent.started(session_id),
        )
        
        # Simulate scanning workflow
        # In production, this would integrate with vision service
        frame_count = 0
        detected_faces = {}
        
        while True:
            try:
                # Receive message from client
                data = await asyncio.wait_for(websocket.receive_text(), timeout=300.0)
                message = json.loads(data)
                
                if message.get("type") == "cancel":
                    await manager.send_personal(
                        session_id,
                        ScanEvent.cancel("User cancelled"),
                    )
                    break
                
                elif message.get("type") == "frame":
                    # Process frame
                    frame_count += 1
                    
                    # Send progress
                    await manager.send_personal(
                        session_id,
                        ScanEvent.progress(
                            face=len(detected_faces) + 1,
                            confidence=0.85,
                            frame_count=frame_count,
                        ),
                    )
                    
                    # Simulate face detection
                    if frame_count % 30 == 0:  # Every 30 frames, detect a face
                        face_num = len(detected_faces) + 1
                        
                        # Simulated sticker colors (white, yellow, red, orange, blue, green)
                        stickers = [0] * 9  # 9 stickers per face
                        
                        await manager.send_personal(
                            session_id,
                            ScanEvent.face_detected(
                                face=face_num,
                                stickers=stickers,
                                confidence=0.92,
                            ),
                        )
                        
                        detected_faces[face_num] = stickers
                    
                    # Check if all 6 faces detected
                    if len(detected_faces) == 6:
                        cube_state = {
                            "corners": [0, 1, 2, 3, 4, 5, 6, 7],
                            "corner_orientations": [0] * 8,
                            "edges": [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
                            "edge_orientations": [0] * 12,
                        }
                        
                        await manager.send_personal(
                            session_id,
                            ScanEvent.completed(
                                session_id=session_id,
                                cube_state=cube_state,
                                confidence=0.88,
                            ),
                        )
                        break
                
                elif message.get("type") == "retry":
                    # Retry last face
                    face_num = message.get("face", len(detected_faces))
                    await manager.send_personal(
                        session_id,
                        ScanEvent.retry(
                            face=face_num,
                            reason="Quality too low, please retry",
                        ),
                    )
                
            except asyncio.TimeoutError:
                await manager.send_personal(
                    session_id,
                    ScanEvent.error("TIMEOUT", "Scan session timeout"),
                )
                break
            
            except json.JSONDecodeError:
                await manager.send_personal(
                    session_id,
                    ScanEvent.error("INVALID_JSON", "Invalid message format"),
                )
    
    except WebSocketException as e:
        logger.error(f"WebSocket exception: {e}")
    
    finally:
        manager.disconnect(session_id)

/**
 * React hooks for WebSocket real-time scanning
 */

import { useCallback, useEffect, useRef, useState } from 'react';

export interface ScanStartedEvent {
  type: 'scan_started';
  session_id: string;
  timestamp: string;
}

export interface ProgressEvent {
  type: 'progress';
  face: number;
  confidence: number;
  frames_processed: number;
  timestamp: string;
}

export interface FaceDetectedEvent {
  type: 'face_detected';
  face: number;
  stickers: number[];
  confidence: number;
  timestamp: string;
}

export interface RetryEvent {
  type: 'retry';
  face: number;
  reason: string;
  timestamp: string;
}

export interface CompletedEvent {
  type: 'completed';
  session_id: string;
  cube_state: {
    corners: number[];
    corner_orientations: number[];
    edges: number[];
    edge_orientations: number[];
  };
  confidence: number;
  timestamp: string;
}

export interface CancelEvent {
  type: 'cancel';
  reason: string;
  timestamp: string;
}

export interface ErrorEvent {
  type: 'error';
  code: string;
  message: string;
  timestamp: string;
}

export type ScanEvent = 
  | ScanStartedEvent 
  | ProgressEvent 
  | FaceDetectedEvent 
  | RetryEvent 
  | CompletedEvent 
  | CancelEvent 
  | ErrorEvent;

export interface UseScanSessionState {
  connected: boolean;
  sessionId: string | null;
  isScanning: boolean;
  facesDetected: number;
  currentFace: number;
  confidence: number;
  framesProcessed: number;
  error: string | null;
  cubeState: any | null;
}

export interface UseScanSessionActions {
  sendFrame: (frameData: ArrayBuffer) => void;
  cancel: () => void;
  retry: (faceNumber: number) => void;
  reset: () => void;
}

export type UseScanSession = UseScanSessionState & UseScanSessionActions;

export function useScanSession(wsUrl?: string): UseScanSession {
  const url = wsUrl || (typeof window !== 'undefined' ? `${window.location.protocol.replace('http', 'ws')}//${window.location.host}/api/scan/session` : '');
  
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [facesDetected, setFacesDetected] = useState(0);
  const [currentFace, setCurrentFace] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [framesProcessed, setFramesProcessed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [cubeState, setCubeState] = useState<any | null>(null);

  useEffect(() => {
    if (!url) return;
    const ws = new WebSocket(url);

    ws.onopen = () => {
      setConnected(true);
      setIsScanning(true);
      setError(null);
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const message: ScanEvent = JSON.parse(event.data);
        switch (message.type) {
          case 'scan_started':
            setSessionId((message as ScanStartedEvent).session_id);
            setFacesDetected(0);
            break;
          case 'progress':
            setCurrentFace((message as ProgressEvent).face);
            setConfidence((message as ProgressEvent).confidence);
            setFramesProcessed((message as ProgressEvent).frames_processed);
            break;
          case 'face_detected':
            setFacesDetected((prev) => prev + 1);
            setCurrentFace((message as FaceDetectedEvent).face);
            setConfidence((message as FaceDetectedEvent).confidence);
            break;
          case 'completed':
            setCubeState((message as CompletedEvent).cube_state);
            setIsScanning(false);
            break;
          case 'error':
            setError(`${(message as ErrorEvent).code}: ${(message as ErrorEvent).message}`);
            setIsScanning(false);
            break;
          case 'cancel':
            setError((message as CancelEvent).reason);
            setIsScanning(false);
            break;
          case 'retry':
            break;
        }
      } catch (err) {
        console.error('Failed to parse message:', err);
      }
    };

    ws.onerror = () => {
      setError('Connection error');
      setConnected(false);
    };

    ws.onclose = () => {
      setConnected(false);
      setIsScanning(false);
    };

    wsRef.current = ws;

    return () => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.close();
      }
    };
  }, [url]);

  const sendFrame = useCallback((frameData: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'frame', data: frameData }));
    }
  }, []);

  const cancel = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'cancel' }));
    }
  }, []);

  const retry = useCallback((faceNumber: number) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'retry', face: faceNumber }));
    }
  }, []);

  const reset = useCallback(() => {
    setSessionId(null);
    setIsScanning(false);
    setFacesDetected(0);
    setCurrentFace(0);
    setConfidence(0);
    setFramesProcessed(0);
    setError(null);
    setCubeState(null);
  }, []);

  return {
    connected,
    sessionId,
    isScanning,
    facesDetected,
    currentFace,
    confidence,
    framesProcessed,
    error,
    cubeState,
    sendFrame,
    cancel,
    retry,
    reset,
  };
}

export function ScanSessionStatus({ session }: { session: UseScanSession }) {
  if (!session.connected) {
    return <div>Not connected</div>;
  }

  return (
    <div style={{ padding: '16px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h3>Scan Session Status</h3>
      <p>Session ID: {session.sessionId}</p>
      <p>Connected: {session.connected ? '✓' : '✗'}</p>
      <p>Scanning: {session.isScanning ? '✓' : '✗'}</p>
      <p>Faces Detected: {session.facesDetected}/6</p>
      <p>Current Face: {session.currentFace}</p>
      <p>Confidence: {(session.confidence * 100).toFixed(1)}%</p>
      <p>Frames Processed: {session.framesProcessed}</p>
      
      {session.error && (
        <div style={{ color: 'red', marginTop: '8px' }}>
          Error: {session.error}
        </div>
      )}
      
      {session.cubeState && (
        <div style={{ marginTop: '8px', padding: '8px', backgroundColor: '#eee' }}>
          <strong>Cube State Detected!</strong>
          <pre>{JSON.stringify(session.cubeState, null, 2)}</pre>
        </div>
      )}
      
      <div style={{ marginTop: '8px' }}>
        <button onClick={session.cancel} disabled={!session.isScanning}>
          Cancel
        </button>
        <button onClick={() => session.retry(session.currentFace)} disabled={!session.isScanning} style={{ marginLeft: '8px' }}>
          Retry Face
        </button>
        <button onClick={session.reset} style={{ marginLeft: '8px' }}>
          Reset
        </button>
      </div>
    </div>
  );
}
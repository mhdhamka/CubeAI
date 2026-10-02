/**
 * React hooks for WebSocket real-time scanning
 */

import { useCallback, useEffect, useRef, useState } from 'react';
import type { CubeState, StickerCubeState } from './types';

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
  requested_face?: string;
  timestamp: string;
}

export interface FaceDetectedEvent {
  type: 'face_detected';
  face: string;
  stickers: string[];
  confidence: number;
  timestamp: string;
}

export interface RetryEvent {
  type: 'retry';
  face: string;
  reason: string;
  timestamp: string;
}

export interface CompletedEvent {
  type: 'completed';
  session_id: string;
  cube_state: CubeState;
  confidence: number;
  timestamp: string;
  faces?: StickerCubeState['faces'];
  validation?: {
    valid: boolean;
    errors: { field: string; error: string }[];
    is_solved: boolean;
    scramble_distance: number | null;
  };
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
  requestedFace: string | null;
  faces: StickerCubeState['faces'] | null;
  error: string | null;
  cubeState: CubeState | null;
}

export interface UseScanSessionActions {
  sendFrame: (frameData: ArrayBuffer) => void;
  cancel: () => void;
  retry: (faceName: string) => void;
  reset: () => void;
}

export type UseScanSession = UseScanSessionState & UseScanSessionActions;

export function useScanSession(wsUrl?: string, enabled = true): UseScanSession {
  const url =
    wsUrl ||
    (typeof window !== 'undefined'
      ? `${window.location.protocol.replace('http', 'ws')}//${window.location.host}/api/scan/session`
      : '');

  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [facesDetected, setFacesDetected] = useState(0);
  const [currentFace, setCurrentFace] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [framesProcessed, setFramesProcessed] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [requestedFace, setRequestedFace] = useState<string | null>(null);
  const [faces, setFaces] = useState<StickerCubeState['faces'] | null>(null);
  const [cubeState, setCubeState] = useState<CubeState | null>(null);

  useEffect(() => {
    if (!url || !enabled) return;
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
            setError(null);
            break;
          case 'progress':
            setCurrentFace((message as ProgressEvent).face);
            setConfidence((message as ProgressEvent).confidence);
            setFramesProcessed((message as ProgressEvent).frames_processed);
            setRequestedFace((message as ProgressEvent).requested_face ?? null);
            setError(null);
            break;
          case 'face_detected':
            setFacesDetected((prev) => prev + 1);
            setConfidence((message as FaceDetectedEvent).confidence);
            break;
          case 'completed':
            setCubeState((message as CompletedEvent).cube_state);
            setFaces((message as CompletedEvent).faces ?? null);
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
            setError((message as RetryEvent).reason);
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
  }, [url, enabled]);

  const sendFrame = useCallback((frameData: ArrayBuffer) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(frameData);
    }
  }, []);

  const cancel = useCallback(() => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'cancel' }));
    }
  }, []);

  const retry = useCallback((faceName: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'retry', face: faceName }));
    }
  }, []);

  const reset = useCallback(() => {
    setSessionId(null);
    setIsScanning(false);
    setFacesDetected(0);
    setCurrentFace(0);
    setConfidence(0);
    setFramesProcessed(0);
    setRequestedFace(null);
    setError(null);
    setCubeState(null);
    setFaces(null);
  }, []);

  return {
    connected,
    sessionId,
    isScanning,
    facesDetected,
    currentFace,
    confidence,
    framesProcessed,
    requestedFace,
    error,
    cubeState,
    faces,
    sendFrame,
    cancel,
    retry,
    reset,
  };
}
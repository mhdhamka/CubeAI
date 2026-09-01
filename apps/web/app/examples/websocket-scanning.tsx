/**
 * WebSocket real-time scanning example
 * Demonstrates camera capture and live cube detection
 */

'use client';

import React, { useRef, useEffect, useState } from 'react';
import {
  useScanSession,
  ScanSessionStatus,
  type UseScanSession,
} from '@cube-ai/cube-api';

/**
 * Camera-based real-time scanning
 */
export function RealtimeScannerExample() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const session = useScanSession();
  const [cameraReady, setCameraReady] = useState(false);

  // Initialize camera
  useEffect(() => {
    const initCamera = async () => {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: 'environment' },
        });

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          streamRef.current = stream;
          setCameraReady(true);
        }
      } catch (error) {
        console.error('Failed to access camera:', error);
      }
    };

    initCamera();

    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
  }, []);

  // Capture and send frames
  useEffect(() => {
    if (
      !session.connected ||
      !session.isScanning ||
      !cameraReady ||
      !videoRef.current ||
      !canvasRef.current
    ) {
      return;
    }

    const video = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    if (!ctx) return;

    const captureFrame = () => {
      // Draw video frame to canvas
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Convert to JPEG and send
      canvas.toBlob((blob) => {
        if (blob) {
          blob.arrayBuffer().then((buffer) => {
            session.sendFrame(buffer);
          });
        }
      }, 'image/jpeg', 0.9);

      if (session.isScanning) {
        requestAnimationFrame(captureFrame);
      }
    };

    // Start frame capture
    captureFrame();
  }, [session.connected, session.isScanning, cameraReady]);

  if (!cameraReady) {
    return <div>Initializing camera...</div>;
  }

  return (
    <div style={{ padding: '16px' }}>
      <h2>Real-time Cube Scanner</h2>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
        {/* Video Preview */}
        <div>
          <h3>Camera Feed</h3>
          <video
            ref={videoRef}
            autoPlay
            playsInline
            style={{ width: '100%', backgroundColor: '#000' }}
          />
          <canvas
            ref={canvasRef}
            width={320}
            height={240}
            style={{ display: 'none' }}
          />
        </div>

        {/* Scan Status */}
        <div>
          <ScanSessionStatus session={session} />
        </div>
      </div>

      {/* Controls */}
      <div style={{ marginTop: '16px', display: 'flex', gap: '8px' }}>
        <button
          onClick={session.cancel}
          disabled={!session.isScanning}
          style={{
            padding: '8px 16px',
            backgroundColor: '#ff6b6b',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: session.isScanning ? 'pointer' : 'not-allowed',
          }}
        >
          Cancel
        </button>

        <button
          onClick={() => session.retry(session.currentFace)}
          disabled={!session.isScanning}
          style={{
            padding: '8px 16px',
            backgroundColor: '#ffd93d',
            color: '#333',
            border: 'none',
            borderRadius: '4px',
            cursor: session.isScanning ? 'pointer' : 'not-allowed',
          }}
        >
          Retry Face
        </button>

        <button
          onClick={session.reset}
          style={{
            padding: '8px 16px',
            backgroundColor: '#6bcf7f',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Reset
        </button>
      </div>

      {/* Result */}
      {session.cubeState && !session.isScanning && (
        <div
          style={{
            marginTop: '16px',
            padding: '16px',
            backgroundColor: '#d4edda',
            border: '1px solid #c3e6cb',
            borderRadius: '4px',
          }}
        >
          <h3>✓ Cube Detected!</h3>
          <p>Ready to solve. The cube state has been captured.</p>
          <details>
            <summary>View Cube State</summary>
            <pre style={{ marginTop: '8px', fontSize: '12px' }}>
              {JSON.stringify(session.cubeState, null, 2)}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}

/**
 * Batch image scanner (multiple images)
 */
export function BatchScannerExample() {
  const session = useScanSession();
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedImages, setSelectedImages] = useState<File[]>([]);

  const handleImageSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setSelectedImages(Array.from(e.target.files));
    }
  };

  const handleStartScan = async () => {
    for (const image of selectedImages) {
      if (!session.isScanning) {
        return;
      }

      const arrayBuffer = await image.arrayBuffer();
      session.sendFrame(arrayBuffer);

      // Wait for detection
      await new Promise((resolve) => setTimeout(resolve, 500));
    }
  };

  return (
    <div style={{ padding: '16px', border: '1px solid #ddd', borderRadius: '8px' }}>
      <h2>Batch Image Scanner</h2>

      <input
        ref={inputRef}
        type="file"
        multiple
        accept="image/*"
        onChange={handleImageSelect}
        style={{ marginBottom: '16px' }}
      />

      <p>Selected: {selectedImages.length} images</p>

      <button
        onClick={handleStartScan}
        disabled={session.isScanning || selectedImages.length === 0}
        style={{
          padding: '8px 16px',
          backgroundColor: '#4CAF50',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
        }}
      >
        Start Scan
      </button>

      <ScanSessionStatus session={session} />
    </div>
  );
}

/**
 * WebSocket state monitor
 */
export function ScanStateMonitor({ session }: { session: UseScanSession }) {
  return (
    <div
      style={{
        padding: '16px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        fontFamily: 'monospace',
        fontSize: '12px',
      }}
    >
      <h3>Connection State</h3>
      <div style={{ display: 'grid', gap: '4px' }}>
        <div>
          <strong>Connected:</strong> {session.connected ? '✓' : '✗'}
        </div>
        <div>
          <strong>Session ID:</strong> {session.sessionId || 'N/A'}
        </div>
        <div>
          <strong>Scanning:</strong> {session.isScanning ? '✓' : '✗'}
        </div>
        <div>
          <strong>Faces Detected:</strong> {session.facesDetected}/6
        </div>
        <div>
          <strong>Current Face:</strong> {session.currentFace}
        </div>
        <div>
          <strong>Confidence:</strong> {(session.confidence * 100).toFixed(1)}%
        </div>
        <div>
          <strong>Frames Processed:</strong> {session.framesProcessed}
        </div>
        {session.error && (
          <div style={{ color: 'red' }}>
            <strong>Error:</strong> {session.error}
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Combined WebSocket scanning demo
 */
export function WebSocketScanningDemo() {
  const [mode, setMode] = useState<'realtime' | 'batch' | 'state'>('realtime');

  return (
    <div style={{ padding: '24px', maxWidth: '1200px', margin: '0 auto' }}>
      <h1>WebSocket Real-time Scanning Demo</h1>

      <div style={{ marginBottom: '16px' }}>
        <button
          onClick={() => setMode('realtime')}
          style={{
            padding: '8px 16px',
            marginRight: '8px',
            backgroundColor: mode === 'realtime' ? '#2196F3' : '#ccc',
            color: mode === 'realtime' ? 'white' : 'black',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Real-time Camera
        </button>

        <button
          onClick={() => setMode('batch')}
          style={{
            padding: '8px 16px',
            marginRight: '8px',
            backgroundColor: mode === 'batch' ? '#2196F3' : '#ccc',
            color: mode === 'batch' ? 'white' : 'black',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Batch Images
        </button>

        <button
          onClick={() => setMode('state')}
          style={{
            padding: '8px 16px',
            backgroundColor: mode === 'state' ? '#2196F3' : '#ccc',
            color: mode === 'state' ? 'white' : 'black',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          State Monitor
        </button>
      </div>

      <div style={{ border: '1px solid #ddd', borderRadius: '8px', padding: '16px' }}>
        {mode === 'realtime' && <RealtimeScannerExample />}
        {mode === 'batch' && <BatchScannerExample />}
        {mode === 'state' && <ScannerApp />}
      </div>
    </div>
  );
}

/**
 * Simple scanner app component
 */
function ScannerApp() {
  const session = useScanSession();
  return <ScanStateMonitor session={session} />;
}

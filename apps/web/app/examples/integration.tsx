/**
 * Example: Full End-to-End Pipeline Integration
 * 
 * This example shows how to integrate the CubeAI API with the Next.js frontend
 * for the complete solve workflow.
 */

'use client';

import React, { useState, useRef } from 'react';
import { useSolveWorkflow, useScanToSolveWorkflow, useScanImage } from '@cube-ai/cube-api';
import type { CubeState, SolveResponse } from '@cube-ai/cube-api';

/**
 * Example 1: Manual Cube Input + Solve
 */
export function ManualSolveExample() {
  const workflow = useSolveWorkflow();
  const [solution, setSolution] = useState<SolveResponse | null>(null);

  const handleSolve = async () => {
    try {
      // Example solved cube state
      const cubeState: CubeState = {
        corners: [0, 1, 2, 3, 4, 5, 6, 7],
        corner_orientations: [0, 0, 0, 0, 0, 0, 0, 0],
        edges: [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        edge_orientations: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
      };

      const result = await workflow.execute(cubeState);
      setSolution(result);
    } catch (error) {
      console.error('Solve failed:', error);
    }
  };

  return (
    <div>
      <h2>Manual Solve Example</h2>
      <button onClick={handleSolve} disabled={workflow.loading}>
        {workflow.loading ? 'Solving...' : 'Solve Cube'}
      </button>

      {workflow.error && (
        <div style={{ color: 'red' }}>
          Error: {workflow.error.message}
        </div>
      )}

      {solution && (
        <div>
          <h3>Solution ({solution.num_moves} moves)</h3>
          <p>
            Moves: {solution.moves.map(m => `${m.face}${m.times === 1 ? '' : m.times === 3 ? "'" : '2'}`).join(' ')}
          </p>
          <p>Solving time: {solution.solving_time_ms}ms</p>
          <p>Algorithm: {solution.solver_used}</p>
        </div>
      )}
    </div>
  );
}

/**
 * Example 2: Image Upload + Scan + Solve
 */
export function ImageScanSolveExample() {
  const workflow = useScanToSolveWorkflow();
  const [result, setResult] = useState<any | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    try {
      const scanResult = await workflow.execute(file);
      setResult(scanResult);
    } catch (error) {
      console.error('Scan and solve failed:', error);
    }
  };

  return (
    <div>
      <h2>Image Scan & Solve Example</h2>
      
      <input
        ref={fileInputRef}
        type="file"
        accept="image/jpeg,image/png"
        onChange={handleFileSelect}
        disabled={workflow.loading}
      />

      {workflow.loading && <p>Processing...</p>}

      {workflow.error && (
        <div style={{ color: 'red' }}>
          Error: {workflow.error.message}
          {workflow.error.details && (
            <pre>{JSON.stringify(workflow.error.details, null, 2)}</pre>
          )}
        </div>
      )}

      {result && (
        <div>
          <h3>Scan Results</h3>
          <p>
            Confidence: {(result.scan.metadata.confidence * 100).toFixed(1)}%
          </p>
          <p>
            Detected Faces: {result.scan.metadata.detected_faces}/6
          </p>
          <p>
            Processing Time: {result.scan.metadata.processing_time_ms}ms
          </p>

          {result.scan.validation.valid ? (
            <>
              <h4>Cube Valid ✓</h4>
              <p>Is Solved: {result.scan.validation.is_solved ? 'Yes' : 'No'}</p>
              <p>
                Estimated Moves to Solve: {result.scan.validation.scramble_distance}
              </p>

              <h4>Solution ({result.solution.num_moves} moves)</h4>
              <p>
                Moves: {result.solution.moves
                  .map(m => `${m.face}${m.times === 1 ? '' : m.times === 3 ? "'" : '2'}`)
                  .join(' ')}
              </p>
            </>
          ) : (
            <>
              <h4>❌ Cube Invalid</h4>
              <ul>
                {result.scan.validation.errors.map((err: any, i: number) => (
                  <li key={i}>{err.field}: {err.error}</li>
                ))}
              </ul>
            </>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Example 3: Camera Stream Scanning (placeholder for Phase 9)
 */
export function CameraScanExample() {
  const scanImage = useScanImage();
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const startCamera = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error('Camera access denied:', error);
    }
  };

  const captureAndScan = async () => {
    if (!videoRef.current || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Draw current video frame to canvas
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    // Convert canvas to blob and scan
    canvas.toBlob(async (blob) => {
      if (!blob) return;
      const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' });

      try {
        const result = await scanImage.execute(file);
        console.log('Scan result:', result);
      } catch (error) {
        console.error('Scan failed:', error);
      }
    }, 'image/jpeg', 0.95);
  };

  return (
    <div>
      <h2>Live Camera Scan (Phase 9 - Future)</h2>
      <video ref={videoRef} autoPlay playsInline style={{ width: '100%' }} />
      <canvas ref={canvasRef} style={{ display: 'none' }} width={640} height={480} />

      <button onClick={startCamera}>Start Camera</button>
      <button onClick={captureAndScan} disabled={scanImage.loading}>
        {scanImage.loading ? 'Scanning...' : 'Capture & Scan'}
      </button>

      {scanImage.error && (
        <p style={{ color: 'red' }}>Error: {scanImage.error.message}</p>
      )}
    </div>
  );
}

/**
 * Combined Application Component
 */
export function CubeAIIntegrationDemo() {
  const [activeTab, setActiveTab] = useState<'manual' | 'image' | 'camera'>('manual');

  return (
    <div style={{ padding: '20px' }}>
      <h1>CubeAI End-to-End Integration</h1>

      <div style={{ marginBottom: '20px' }}>
        <button onClick={() => setActiveTab('manual')} style={{ marginRight: '10px' }}>
          Manual Input
        </button>
        <button onClick={() => setActiveTab('image')} style={{ marginRight: '10px' }}>
          Image Upload
        </button>
        <button onClick={() => setActiveTab('camera')}>
          Live Camera (Coming Soon)
        </button>
      </div>

      {activeTab === 'manual' && <ManualSolveExample />}
      {activeTab === 'image' && <ImageScanSolveExample />}
      {activeTab === 'camera' && <CameraScanExample />}
    </div>
  );
}

export default CubeAIIntegrationDemo;

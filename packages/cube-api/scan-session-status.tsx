/**
 * Display component for scan session status
 */

import type { UseScanSession } from './hooks-websocket';

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
        <button
          onClick={() => session.retry(session.currentFace)}
          disabled={!session.isScanning}
          style={{ marginLeft: '8px' }}
        >
          Retry Face
        </button>
        <button onClick={session.reset} style={{ marginLeft: '8px' }}>
          Reset
        </button>
      </div>
    </div>
  );
}
/**
 * cube-api package
 * TypeScript client for CubeAI FastAPI backend.
 */

export { CubeAIClient, APIError, apiClient } from './client';
export type {
  CubeState,
  Move,
  SolveRequest,
  SolveResponse,
  ValidateRequest,
  ValidateResponse,
  HealthResponse,
  ErrorDetail,
  ScanResponse,
  ScanMetadata,
  Profile,
  SolveRecord,
  Statistics,
  CoachingRequest,
  CoachingResponse,
} from './types';

// React hooks
export {
  useSolve,
  useValidate,
  useScanImage,
  useHealth,
  useCoaching,
  useSolveWorkflow,
  useScanToSolveWorkflow,
} from './hooks';

export {
  useScanSession,
  ScanSessionStatus,
} from './hooks-websocket';

export type {
  UseAPI,
  UseAPIState,
  UseAPIActions,
} from './hooks';

export type {
  UseScanSession,
  ScanEvent,
  ScanStartedEvent,
  ProgressEvent,
  FaceDetectedEvent,
  RetryEvent,
  CompletedEvent,
  CancelEvent,
  ErrorEvent,
} from './hooks-websocket';

/**
 * API models and types for CubeAI backend communication.
 * Typed contracts for REST endpoints.
 */

export interface CubeState {
  corners: number[];
  corner_orientations: number[];
  edges: number[];
  edge_orientations: number[];
}

export interface Move {
  face: 'U' | 'D' | 'F' | 'B' | 'L' | 'R';
  times: 1 | 2 | 3;
}

export interface SolveRequest {
  cube_state: CubeState;
  max_moves?: number;
}

export interface SolveResponse {
  moves: Move[];
  num_moves: number;
  confidence: number;
  solving_time_ms: number;
  solver_used: string;
}

export interface ValidateRequest {
  cube_state: CubeState;
}

export interface ValidationError {
  field: string;
  error: string;
}

export interface ValidateResponse {
  valid: boolean;
  errors: ValidationError[];
  is_solved: boolean;
  scramble_distance: number | null;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded';
  service: string;
  version: string;
  timestamp: string;
}

export interface ErrorDetail {
  code: string;
  message: string;
  details?: Record<string, any>;
  timestamp?: string;
}

// Scan types (Phase 4+)
export interface ScanMetadata {
  confidence: number;
  detected_faces: number;
  processing_time_ms: number;
  model_version: string;
}

export interface ScanResponse {
  cube_state: CubeState;
  metadata: ScanMetadata;
  validation: ValidateResponse;
}

// Profile types (Phase 7+)
export interface Profile {
  id?: number;
  user_id: number;
  name: string;
  cube_size?: number;
  solving_method?: string;
  preferred_focus?: string;
  created_at?: string;
  updated_at?: string;
}

export interface SolveRecord {
  id?: number;
  profile_id: number;
  time_ms: number;
  num_moves: number;
  scramble: string;
  solution: string;
  solver_used?: string;
  confidence?: number;
  is_dnf?: boolean;
  is_dns?: boolean;
  notes?: string;
  metadata?: Record<string, any>;
  created_at?: string;
}

export interface Statistics {
  profile_id: number;
  total_solves: number;
  best_time_ms?: number;
  worst_time_ms?: number;
  average_ao5_ms?: number;
  average_ao12_ms?: number;
  average_ao100_ms?: number;
  average_overall_ms?: number;
}

// Coaching types (Phase 6+)
export interface CoachingRequest {
  cube_state: CubeState;
  solution_moves: Move[];
  focus?: 'cross' | 'f2l' | 'oll' | 'pll' | 'overall';
}

export interface CoachingResponse {
  explanation: string;
  key_points: string[];
  suggested_algorithms: string[];
  difficulty_level: 'beginner' | 'intermediate' | 'advanced';
}

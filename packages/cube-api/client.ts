/**
 * CubeAI API Client
 * Typed client for communicating with the CubeAI FastAPI backend.
 * Handles requests, responses, and error handling.
 */

import type {
  CubeState,
  CubeStateInput,
  Move,
  SolveRequest,
  SolveResponse,
  ValidateRequest,
  ValidateResponse,
  HealthResponse,
  ErrorDetail,
  ScanResponse,
  Profile,
  SolveRecord,
  Statistics,
  CoachingRequest,
  CoachingResponse,
  TrainingAttempt,
} from './types';

function describeError(errorData: ErrorDetail | null, status: number): string {
  if (errorData?.message) return errorData.message;
  if (typeof errorData?.detail === 'string') return errorData.detail;
  if (Array.isArray(errorData?.detail)) {
    return errorData.detail
      .map((item) => {
        const location = item.loc?.join('.') || 'request';
        return `${location}: ${item.msg || 'invalid value'}`;
      })
      .join('; ');
  }
  return `HTTP ${status}`;
}

export interface ClientConfig {
  baseUrl?: string;
  timeout?: number;
}

export class APIError extends Error {
  constructor(
    public code: string,
    public message: string,
    public statusCode: number,
    public details?: Record<string, any>,
  ) {
    super(message);
    this.name = 'APIError';
  }
}

export class CubeAIClient {
  private baseUrl: string;
  private timeout: number;

  constructor(config: ClientConfig = {}) {
    this.baseUrl = config.baseUrl || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    this.timeout = config.timeout || 30000;
  }

  /**
   * Make a typed HTTP request to the API.
   */
  private async request<T>(
    method: string,
    path: string,
    body?: unknown,
    headers: Record<string, string> = {},
  ): Promise<T> {
    const url = `${this.baseUrl}${path}`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          ...headers,
        },
        body: body ? JSON.stringify(body) : undefined,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: ErrorDetail | null = null;
        try {
          errorData = (await response.json()) as ErrorDetail;
        } catch {
          // If response is not JSON, create a basic error
        }

        throw new APIError(
          errorData?.code || 'API_ERROR',
          describeError(errorData, response.status),
          response.status,
          errorData?.details,
        );
      }

      return (await response.json()) as T;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof APIError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new APIError(
            'TIMEOUT',
            `Request timeout after ${this.timeout}ms`,
            408,
          );
        }
        throw new APIError(
          'NETWORK_ERROR',
          error.message,
          0,
        );
      }

      throw new APIError(
        'UNKNOWN_ERROR',
        'An unknown error occurred',
        0,
      );
    }
  }

  // ==================== Health Endpoints ====================

  /**
   * Check API health status.
   */
  async health(): Promise<HealthResponse> {
    return this.request<HealthResponse>('GET', '/api/health');
  }

  /**
   * Check API readiness.
   */
  async ready(): Promise<{ ready: boolean; timestamp: string }> {
    return this.request<{ ready: boolean; timestamp: string }>('GET', '/api/health/ready');
  }

  /**
   * Check API liveness.
   */
  async live(): Promise<{ alive: boolean; timestamp: string }> {
    return this.request<{ alive: boolean; timestamp: string }>('GET', '/api/health/live');
  }

  // ==================== Engine Endpoints ====================

  /**
   * Solve a cube state.
   * Returns an optimal or near-optimal solution.
   */
  async solve(request: SolveRequest): Promise<SolveResponse> {
    return this.request<SolveResponse>('POST', '/api/solve', request);
  }

  /**
   * Validate a cube state.
   * Checks for physical possibility and solvability.
   */
  async validate(request: ValidateRequest): Promise<ValidateResponse> {
    return this.request<ValidateResponse>('POST', '/api/validate', request);
  }

  // ==================== Vision Endpoints (Phase 4+) ====================

  /**
   * Scan an image for cube state.
   * Uploads image and returns detected cube state with confidence.
   */
  async scanImage(imageFiles: File | File[]): Promise<ScanResponse> {
    const formData = new FormData();
    const files = Array.isArray(imageFiles) ? imageFiles : [imageFiles];
    for (const imageFile of files) {
      formData.append(files.length === 1 ? 'file' : 'files', imageFile);
    }

    const url = `${this.baseUrl}/api/scan/image`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        let errorData: ErrorDetail | null = null;
        try {
          errorData = (await response.json()) as ErrorDetail;
        } catch {
          // Ignore parse errors
        }

        throw new APIError(
          errorData?.code || 'API_ERROR',
          describeError(errorData, response.status),
          response.status,
          errorData?.details,
        );
      }

      return (await response.json()) as ScanResponse;
    } catch (error) {
      clearTimeout(timeoutId);

      if (error instanceof APIError) {
        throw error;
      }

      if (error instanceof Error) {
        if (error.name === 'AbortError') {
          throw new APIError(
            'TIMEOUT',
            `Request timeout after ${this.timeout}ms`,
            408,
          );
        }
        throw new APIError('NETWORK_ERROR', error.message, 0);
      }

      throw new APIError('UNKNOWN_ERROR', 'An unknown error occurred', 0);
    }
  }

  // ==================== Profile Endpoints (Phase 7+) ====================

  /**
   * Get user profile.
   */
  async getProfile(profileId: number): Promise<Profile> {
    return this.request<Profile>('GET', `/api/profiles/${profileId}`);
  }

  /**
   * Create a new profile.
   */
  async createProfile(profile: Omit<Profile, 'id' | 'created_at' | 'updated_at'>): Promise<Profile> {
    return this.request<Profile>('POST', '/api/profiles', profile);
  }

  async getOrCreateGuestProfile(): Promise<Profile> {
    return this.request<Profile>('POST', '/api/profiles/guest');
  }

  // ==================== Solve Record Endpoints (Phase 7+) ====================

  /**
   * Get all solve records for a profile.
   */
  async getSolves(profileId: number): Promise<SolveRecord[]> {
    return this.request<SolveRecord[]>('GET', `/api/solves?profile_id=${profileId}`);
  }

  /**
   * Create a new solve record.
   */
  async createSolve(record: Omit<SolveRecord, 'id' | 'created_at'>): Promise<SolveRecord> {
    return this.request<SolveRecord>('POST', '/api/solves', record);
  }

  // ==================== Statistics Endpoints (Phase 8+) ====================

  /**
   * Get solve statistics for a profile.
   */
  async getStatistics(profileId: number): Promise<Statistics> {
    return this.request<Statistics>('GET', `/api/profiles/${profileId}/statistics`);
  }

  async getTrainingAttempts(profileId: number): Promise<TrainingAttempt[]> {
    return this.request<TrainingAttempt[]>(
      'GET',
      `/api/profiles/${profileId}/training`,
    );
  }

  async createTrainingAttempt(
    attempt: Omit<TrainingAttempt, 'id' | 'created_at'>,
  ): Promise<TrainingAttempt> {
    return this.request<TrainingAttempt>('POST', '/api/training', attempt);
  }

  // ==================== Coaching Endpoints (Phase 6+) ====================

  /**
   * Get coaching explanation for a solution.
   */
  async getCoaching(request: CoachingRequest): Promise<CoachingResponse> {
    return this.request<CoachingResponse>('POST', '/api/coaching', request);
  }

  // ==================== WebSocket Endpoints (Phase 9+) ====================

  /**
   * Create a WebSocket connection for real-time scanning.
   * Returns a WebSocket instance ready for event listening.
   */
  createScanSession(): WebSocket {
    const protocol = this.baseUrl.startsWith('https') ? 'wss' : 'ws';
    const wsUrl = this.baseUrl.replace(/^https?/, protocol);
    return new WebSocket(`${wsUrl}/api/scan/session`);
  }
}

// Export singleton instance
export const apiClient = new CubeAIClient();

// Re-export types
export type { CubeState, CubeStateInput, Move, SolveRequest, SolveResponse, ValidateRequest, ValidateResponse };

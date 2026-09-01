/**
 * CubeAI API Client
 * Typed client for communicating with the CubeAI FastAPI backend.
 * Handles requests, responses, and error handling.
 */

import type {
  CubeState,
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
} from './types';

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
    this.baseUrl = config.baseUrl || 'http://localhost:8000';
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
          errorData?.message || `HTTP ${response.status}`,
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
  async scanImage(imageFile: File): Promise<ScanResponse> {
    const formData = new FormData();
    formData.append('file', imageFile);

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
          errorData?.message || `HTTP ${response.status}`,
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

  // ==================== Solve Record Endpoints (Phase 7+) ====================

  /**
   * Get all solve records for a profile.
   */
  async getSolves(profileId: number): Promise<SolveRecord[]> {
    return this.request<SolveRecord[]>('GET', `/api/profiles/${profileId}/solves`);
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
export type { CubeState, Move, SolveRequest, SolveResponse, ValidateRequest, ValidateResponse };

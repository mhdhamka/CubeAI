/**
 * React hook for CubeAI API integration
 * Provides easy access to API client with loading and error states
 */

import { useState, useCallback } from 'react';
import {
  CubeAIClient,
  APIError,
  type CubeState,
  type SolveRequest,
  type SolveResponse,
  type ValidateRequest,
  type ValidateResponse,
  type ScanResponse,
  type HealthResponse,
  type CoachingRequest,
  type CoachingResponse,
} from '@cube-ai/cube-api';

export interface UseAPIState<T> {
  data: T | null;
  loading: boolean;
  error: APIError | null;
}

export interface UseAPIActions<T> {
  execute: (...args: any[]) => Promise<T>;
  reset: () => void;
}

export type UseAPI<T> = UseAPIState<T> & UseAPIActions<T>;

/**
 * Hook factory for API operations
 */
function useAPIOperation<Args extends any[], T>(
  operation: (...args: Args) => Promise<T>,
): UseAPI<T> {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | null>(null);

  const execute = useCallback(
    async (...args: Args): Promise<T> => {
      setLoading(true);
      setError(null);
      try {
        const result = await operation(...args);
        setData(result);
        return result;
      } catch (err) {
        const apiError = err instanceof APIError ? err : new APIError(
          'UNKNOWN',
          err instanceof Error ? err.message : 'Unknown error',
          0,
        );
        setError(apiError);
        throw apiError;
      } finally {
        setLoading(false);
      }
    },
    [operation],
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}

/**
 * Hook for solving a cube state
 */
export function useSolve(client?: CubeAIClient): UseAPI<SolveResponse> {
  const apiClient = client || new CubeAIClient();
  return useAPIOperation((request: SolveRequest) => apiClient.solve(request));
}

/**
 * Hook for validating a cube state
 */
export function useValidate(client?: CubeAIClient): UseAPI<ValidateResponse> {
  const apiClient = client || new CubeAIClient();
  return useAPIOperation((request: ValidateRequest) => apiClient.validate(request));
}

/**
 * Hook for scanning an image
 */
export function useScanImage(client?: CubeAIClient): UseAPI<ScanResponse> {
  const apiClient = client || new CubeAIClient();
  return useAPIOperation((file: File) => apiClient.scanImage(file));
}

/**
 * Hook for health check
 */
export function useHealth(client?: CubeAIClient): UseAPI<HealthResponse> {
  const apiClient = client || new CubeAIClient();
  return useAPIOperation(() => apiClient.health());
}

/**
 * Hook for getting coaching
 */
export function useCoaching(client?: CubeAIClient): UseAPI<CoachingResponse> {
  const apiClient = client || new CubeAIClient();
  return useAPIOperation((request: CoachingRequest) => apiClient.getCoaching(request));
}

/**
 * Combined hook for the full solve workflow
 */
export function useSolveWorkflow(client?: CubeAIClient) {
  const apiClient = client || new CubeAIClient();
  const validate = useValidate(apiClient);
  const solve = useSolve(apiClient);

  const executeWorkflow = useCallback(
    async (cubeState: CubeState, maxMoves?: number) => {
      // Step 1: Validate cube state
      const validation = await validate.execute({ cube_state: cubeState });
      if (!validation.valid) {
        throw new Error(`Invalid cube state: ${validation.errors[0]?.error}`);
      }

      // Step 2: Solve the cube
      const solution = await solve.execute({
        cube_state: cubeState,
        max_moves: maxMoves,
      });

      return solution;
    },
    [validate, solve],
  );

  return {
    execute: executeWorkflow,
    loading: validate.loading || solve.loading,
    error: validate.error || solve.error,
    reset: () => {
      validate.reset();
      solve.reset();
    },
  };
}

/**
 * Combined hook for the full scan-to-solve workflow
 */
export function useScanToSolveWorkflow(client?: CubeAIClient) {
  const apiClient = client || new CubeAIClient();
  const scanImage = useScanImage(apiClient);
  const solve = useSolve(apiClient);

  const executeWorkflow = useCallback(
    async (imageFile: File, maxMoves?: number) => {
      // Step 1: Scan image to get cube state
      const scanResult = await scanImage.execute(imageFile);
      
      if (!scanResult.validation.valid) {
        throw new Error(`Invalid cube detected: ${scanResult.validation.errors[0]?.error}`);
      }

      // Step 2: Solve the detected cube state
      const solution = await solve.execute({
        cube_state: scanResult.cube_state,
        max_moves: maxMoves,
      });

      return {
        scan: scanResult,
        solution,
      };
    },
    [scanImage, solve],
  );

  return {
    execute: executeWorkflow,
    loading: scanImage.loading || solve.loading,
    error: scanImage.error || solve.error,
    reset: () => {
      scanImage.reset();
      solve.reset();
    },
  };
}

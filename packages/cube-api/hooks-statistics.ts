/**
 * React hooks for statistics and performance tracking
 */

import { useState, useCallback } from 'react';
import { CubeAIClient, APIError } from '@cube-ai/cube-api';
import type { Statistics } from '@cube-ai/cube-api';

export interface UseStatisticsState {
  data: Statistics | null;
  loading: boolean;
  error: APIError | null;
}

export interface UseStatisticsActions {
  execute: (profileId: number) => Promise<Statistics>;
  reset: () => void;
}

export type UseStatistics = UseStatisticsState & UseStatisticsActions;

/**
 * Hook for fetching profile statistics
 */
export function useStatistics(client?: CubeAIClient): UseStatistics {
  const apiClient = client || new CubeAIClient();
  const [data, setData] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<APIError | null>(null);

  const execute = useCallback(
    async (profileId: number): Promise<Statistics> => {
      setLoading(true);
      setError(null);
      try {
        const result = await apiClient.getStatistics(profileId);
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
    [apiClient],
  );

  const reset = useCallback(() => {
    setData(null);
    setError(null);
    setLoading(false);
  }, []);

  return { data, loading, error, execute, reset };
}

/**
 * Format time in milliseconds to readable format (MM:SS.ms or SS.ms)
 */
export function formatSolveTime(timeMs: number): string {
  const totalSeconds = timeMs / 1000;
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = totalSeconds % 60;

  if (minutes > 0) {
    return `${minutes}:${seconds.toFixed(2).padStart(6, '0')}`;
  } else {
    return seconds.toFixed(3);
  }
}

/**
 * Component for displaying statistics
 */
export function StatisticsDisplay({ statistics }: { statistics: Statistics | null }) {
  if (!statistics) {
    return <div>No statistics available</div>;
  }

  const {
    total_solves,
    best_time_ms,
    worst_time_ms,
    average_ao5_ms,
    average_ao12_ms,
    average_ao100_ms,
    average_overall_ms,
  } = statistics;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
      <StatCard label="Total Solves" value={total_solves?.toString() || '—'} />

      {best_time_ms && (
        <StatCard label="Personal Best" value={formatSolveTime(best_time_ms)} />
      )}

      {worst_time_ms && (
        <StatCard label="Worst Time" value={formatSolveTime(worst_time_ms)} />
      )}

      {average_ao5_ms && (
        <StatCard
          label="Ao5"
          value={formatSolveTime(average_ao5_ms)}
          subtext="Last 5 solves"
        />
      )}

      {average_ao12_ms && (
        <StatCard
          label="Ao12"
          value={formatSolveTime(average_ao12_ms)}
          subtext="Last 12 solves"
        />
      )}

      {average_ao100_ms && (
        <StatCard
          label="Ao100"
          value={formatSolveTime(average_ao100_ms)}
          subtext="Last 100 solves"
        />
      )}

      {average_overall_ms && (
        <StatCard
          label="Overall Average"
          value={formatSolveTime(average_overall_ms)}
          subtext="All time"
        />
      )}
    </div>
  );
}

/**
 * Individual statistic card component
 */
function StatCard({
  label,
  value,
  subtext,
}: {
  label: string;
  value: string;
  subtext?: string;
}) {
  return (
    <div
      style={{
        padding: '16px',
        border: '1px solid #ddd',
        borderRadius: '8px',
        textAlign: 'center',
      }}
    >
      <div style={{ fontSize: '12px', color: '#666' }}>{label}</div>
      <div style={{ fontSize: '24px', fontWeight: 'bold', marginTop: '8px' }}>
        {value}
      </div>
      {subtext && (
        <div style={{ fontSize: '11px', color: '#999', marginTop: '4px' }}>
          {subtext}
        </div>
      )}
    </div>
  );
}

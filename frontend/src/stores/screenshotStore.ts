/**
 * ✅ Phase 2: Zustand Screenshot Store
 * Replaces ScreenshotContext with better performance
 */

import { create } from 'zustand';

interface ScreenshotResult {
  url: string;
  status: string;
  screenshot_path?: string | null;
  screenshot_paths?: string[] | null;
  segment_count?: number | null;
  error?: string | null;
  quality_score?: number | null;
  quality_issues?: string[] | null;
  timestamp: string;
}

interface ProgressState {
  current: number;
  total: number;
}

interface ScreenshotState {
  // Results
  results: ScreenshotResult[];
  setResults: (results: ScreenshotResult[]) => void;
  addResult: (result: ScreenshotResult) => void;
  clearResults: () => void;

  // Loading State
  loading: boolean;
  setLoading: (loading: boolean) => void;

  // Progress
  progress: ProgressState;
  setProgress: (progress: ProgressState) => void;
  updateProgress: (current: number, total: number) => void;
}

export const useScreenshotStore = create<ScreenshotState>((set) => ({
  // Results
  results: [],
  setResults: (results) => set({ results }),
  addResult: (result) => set((state) => ({ results: [...state.results, result] })),
  clearResults: () => set({ results: [] }),

  // Loading State
  loading: false,
  setLoading: (loading) => set({ loading }),

  // Progress
  progress: { current: 0, total: 0 },
  setProgress: (progress) => set({ progress }),
  updateProgress: (current, total) => set({ progress: { current, total } }),
}));

// Selectors
export const selectResults = (state: ScreenshotState) => state.results;
export const selectLoading = (state: ScreenshotState) => state.loading;
export const selectProgress = (state: ScreenshotState) => state.progress;
export const selectIsCapturing = (state: ScreenshotState) => state.loading && state.progress.total > 0;


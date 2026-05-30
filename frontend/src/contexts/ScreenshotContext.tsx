/**
 * ✅ FIXED (Bug #14): Screenshot-specific state context
 * 
 * Manages screenshot results, loading state, and progress.
 */

import React, { createContext, useContext, useState, ReactNode } from 'react';

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

interface ScreenshotContextType {
  results: ScreenshotResult[];
  setResults: (results: ScreenshotResult[]) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
  progress: ProgressState;
  setProgress: (progress: ProgressState) => void;
}

const ScreenshotContext = createContext<ScreenshotContextType | undefined>(undefined);

export const ScreenshotProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [results, setResults] = useState<ScreenshotResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<ProgressState>({ current: 0, total: 0 });

  const value: ScreenshotContextType = {
    results,
    setResults,
    loading,
    setLoading,
    progress,
    setProgress,
  };

  return <ScreenshotContext.Provider value={value}>{children}</ScreenshotContext.Provider>;
};

export const useScreenshotContext = () => {
  const context = useContext(ScreenshotContext);
  if (!context) {
    throw new Error('useScreenshotContext must be used within ScreenshotProvider');
  }
  return context;
};


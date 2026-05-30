/**
 * ✅ FIXED (Bug #14): Extract screenshot capture logic from App.tsx
 * 
 * This hook encapsulates all screenshot capture logic, reducing App.tsx complexity.
 */

import { useState, useCallback } from 'react';
import config from '../config';
import log from '../utils/logger';

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

interface CaptureOptions {
  urls: string[];
  viewportWidth: number;
  viewportHeight: number;
  useRealBrowser: boolean;
  useStealth: boolean;
  autoExpandDropdowns: boolean;
  maxParallelUrls: number;
  baseUrl?: string;
  wordsToRemove?: string;
  nonScrollableUrls?: string;
}

export function useScreenshotCapture() {
  const [results, setResults] = useState<ScreenshotResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });

  const captureScreenshots = useCallback(async (options: CaptureOptions) => {
    const {
      urls,
      viewportWidth,
      viewportHeight,
      useRealBrowser,
      useStealth,
      autoExpandDropdowns,
      maxParallelUrls,
      baseUrl,
      wordsToRemove,
      nonScrollableUrls,
    } = options;

    setLoading(true);
    setProgress({ current: 0, total: urls.length });
    setResults([]);

    try {
      log.info('Starting screenshot capture', { urlCount: urls.length });

      const response = await fetch(`${config.apiBaseUrl}/api/screenshots/capture`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          urls,
          viewport_width: viewportWidth,
          viewport_height: viewportHeight,
          use_real_browser: useRealBrowser,
          use_stealth: useStealth,
          auto_expand_dropdowns: autoExpandDropdowns,
          max_parallel_urls: maxParallelUrls,
          base_url: baseUrl || '',
          words_to_remove: wordsToRemove || '',
          non_scrollable_urls: nonScrollableUrls || '',
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setResults(data.results || []);
      
      log.info('Screenshot capture completed', {
        total: data.results?.length || 0,
        successful: data.results?.filter((r: ScreenshotResult) => r.status === 'success').length || 0,
      });

      return data.results;
    } catch (error) {
      log.error('Screenshot capture failed', { error });
      throw error;
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0 });
    }
  }, []);

  const cancelCapture = useCallback(async () => {
    try {
      await fetch(`${config.apiBaseUrl}/api/screenshots/cancel`, {
        method: 'POST',
      });
      log.info('Screenshot capture cancelled');
    } catch (error) {
      log.error('Failed to cancel capture', { error });
    }
  }, []);

  return {
    results,
    setResults,
    loading,
    progress,
    setProgress,
    captureScreenshots,
    cancelCapture,
  };
}


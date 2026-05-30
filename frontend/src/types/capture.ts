/**
 * 📸 Capture Type Definitions
 * 
 * Type definitions for screenshot capture functionality.
 * 
 * @module types/capture
 * @author AI Assistant
 * @date 2025-11-03
 */

/**
 * Screenshot capture mode
 * - viewport: Capture visible viewport only
 * - fullpage: Capture entire page (scrolling)
 * - segmented: Capture page in segments with overlap
 */
export type CaptureMode = 'viewport' | 'fullpage' | 'segmented';

/**
 * Browser engine selection
 * - playwright: Standard Playwright (Patchright with stealth)
 * - camoufox: Maximum stealth Firefox-based browser
 */
export type BrowserEngine = 'playwright' | 'camoufox';

/**
 * Screenshot result from backend API
 */
export interface ScreenshotResult {
  /** Original URL that was captured */
  url: string;
  
  /** Capture status */
  status: 'success' | 'failed' | 'pending';
  
  /** Path to single screenshot (viewport/fullpage mode) */
  screenshot_path?: string | null;
  
  /** Paths to multiple screenshots (segmented mode) */
  screenshot_paths?: string[] | null;
  
  /** Number of segments captured (segmented mode) */
  segment_count?: number | null;
  
  /** Error message if capture failed */
  error?: string | null;
  
  /** Quality score (0-100) */
  quality_score?: number | null;
  
  /** List of quality issues detected */
  quality_issues?: string[] | null;
  
  /** Timestamp of capture */
  timestamp: string;
}

/**
 * Capture progress information
 */
export interface CaptureProgress {
  /** Current URL being processed */
  current: number;
  
  /** Total URLs to process */
  total: number;
  
  /** Current URL string */
  currentUrl?: string;
  
  /** Percentage complete (0-100) */
  percentage?: number;
}

/**
 * Capture settings for screenshot operations
 */
export interface CaptureSettings {
  /** Capture mode */
  mode: CaptureMode;
  
  /** Enable stealth mode (anti-bot detection) */
  useStealth: boolean;
  
  /** Use real browser fingerprints */
  useRealBrowser: boolean;
  
  /** Browser engine to use */
  browserEngine: BrowserEngine;
  
  /** Segmented capture settings */
  segmented?: SegmentedCaptureSettings;
}

/**
 * Settings specific to segmented capture mode
 */
export interface SegmentedCaptureSettings {
  /** Overlap percentage between segments (0-100) */
  overlap: number;
  
  /** Delay between scroll actions (milliseconds) */
  scrollDelay: number;
  
  /** Maximum number of segments to capture */
  maxSegments: number;
  
  /** Skip duplicate segments */
  skipDuplicates: boolean;
  
  /** Smart lazy-load detection */
  smartLazyLoad: boolean;
}

/**
 * File naming settings
 */
export interface NamingSettings {
  /** Base URL to remove from filenames */
  baseUrl: string;
  
  /** Words to remove from filenames */
  wordsToRemove: string[];
}

/**
 * Default capture settings
 */
export const DEFAULT_CAPTURE_SETTINGS: CaptureSettings = {
  mode: 'viewport',
  useStealth: false,
  useRealBrowser: false,
  browserEngine: 'playwright',
  segmented: {
    overlap: 20,
    scrollDelay: 1000,
    maxSegments: 50,
    skipDuplicates: true,
    smartLazyLoad: true,
  },
};

/**
 * Default naming settings
 */
export const DEFAULT_NAMING_SETTINGS: NamingSettings = {
  baseUrl: '',
  wordsToRemove: [],
};


// ========================================
// 🌐 GLOBAL TYPE DECLARATIONS
// ========================================
declare global {
  interface Window {
    screenshotsDirTimeout?: NodeJS.Timeout;
  }
}

import React, { lazy, Suspense } from "react";
import { useState, useEffect, useRef, useCallback, useMemo } from "react";
import "./styles.css";
import {
  useLocalStorage,
  useLocalStorageWithSerializer,
} from "./hooks/useLocalStorage";
import { useDebouncedLocalStorage } from "./hooks/useDebouncedLocalStorage";
import { ask, open } from "@tauri-apps/plugin-dialog";
import { listen } from "@tauri-apps/api/event";
import config, { apiUrl } from "./config"; // ✅ FIXED: Centralized configuration
import { useNotifications } from "./hooks/useNotifications"; // 🔔 Toast notifications
import { useWebSocket } from "./hooks/useWebSocket"; // 🔌 WebSocket connection
import ToastContainer from "./components/shared/ToastContainer"; // 🍞 Toast container
import { ConfirmDialog } from "./components/shared/ConfirmDialog"; // 🔔 Confirm dialog
import type { WebSocketMessage } from "./types/notification"; // 📦 WebSocket message types
import { NetworkTab } from "./components/NetworkTab"; // 🌐 Network tab
import log from "./utils/logger"; // 📝 Centralized logging
// ✅ Phase 2: Migrated from Context API to Zustand
import { useAppStore } from "./stores/appStore";
import { useScreenshotStore } from "./stores/screenshotStore";
import { useSessionStore } from "./stores/sessionStore";
import { useSettingsStore } from "./stores/settingsStore";
import { useSystemMonitoring } from "./hooks/useSystemMonitoring"; // ✅ Bug #14 & #15: System monitoring
import { useWordEditor } from "./hooks/useWordEditor"; // ✅ Bug #14: Word editor
import { useCookieManagement } from "./hooks/useCookieManagement"; // ✅ Bug #14: Cookie management
import { useAuthFlow } from "./hooks/useAuthFlow"; // ✅ Bug #14: Auth flow
import { useUrlConfig } from "./hooks/useUrlConfig"; // ✅ Bug #14: URL config
import { ErrorBoundary } from 'react-error-boundary'; // ✅ Error boundaries
import { ErrorFallback } from './components/shared/ErrorFallback'; // ✅ Main error fallback
import { FeatureErrorFallback } from './components/shared/FeatureErrorFallback'; // ✅ Feature error fallback
import { InfoButton } from './components/shared/InfoButton'; // ✅ Accessible info tooltip buttons
import { TextBoxGroup } from './components/TextBoxGroup'; // ✅ Extracted text box component
import { WaffleButton, LauncherPanel } from './components/AppLauncher'; // ✅ App launcher components
import { useAppLauncherStore } from './stores/appLauncherStore'; // ✅ App launcher state
import { BusinessApps } from './components/BusinessApps'; // ✅ Business Apps (Parts, Service, Accounting, CRM)
import { DEFAULT_TEXT_BOXES } from './constants/defaultTextBoxes'; // ✅ FIX 2.3: Shared text box defaults

// ✅ Code Splitting: Lazy load tab components
const LogsTab = lazy(() => import("./components/tabs/LogsTab").then(m => ({ default: m.LogsTab })));
const SessionsTab = lazy(() => import("./components/tabs/SessionsTab").then(m => ({ default: m.SessionsTab })));
const UrlsTab = lazy(() => import("./components/tabs/UrlsTab").then(m => ({ default: m.UrlsTab })));

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

interface SystemUsageState {
  backend_rss_mb?: number | null;
  backend_cpu_percent?: number | null;
  system_ram_total_mb?: number | null;
  system_ram_used_mb?: number | null;
  system_ram_percent?: number | null;
  system_cpu_percent?: number | null;
  browser_rss_mb?: number | null;
  browser_cpu_percent?: number | null;
  status?: string;
  message?: string;
  timestamp?: string;
}

// ========================================
// 🛠️ HELPER FUNCTIONS
// ========================================

/**
 * Safely extracts error message from unknown error type
 * @param error - Unknown error from catch block
 * @returns Human-readable error message
 */
function getErrorMessage(error: unknown): string {
  if (error instanceof Error) return error.message;
  if (typeof error === 'string') return error;
  return 'An unknown error occurred';
}

/**
 * Safely extracts error stack from unknown error type
 * @param error - Unknown error from catch block
 * @returns Error stack trace if available
 */
// eslint-disable-next-line @typescript-eslint/no-unused-vars
function getErrorStack(error: unknown): string | undefined {
  if (error instanceof Error) return error.stack;
  return undefined;
}

// ========================================
// 🔒 ASYNC MUTEX (Concurrency Control)
// ========================================

/**
 * Async Mutex for preventing concurrent operations.
 *
 * ✅ RACE CONDITION FIX: Prevents multiple async operations from running simultaneously.
 * Use case: Prevent concurrent Word document generation for multiple text boxes.
 *
 * Example:
 *   const mutex = new AsyncMutex();
 *   await mutex.runExclusive(async () => {
 *     // Critical section - only one execution at a time
 *     await generateWordDocument();
 *   });
 */
class AsyncMutex {
  private locked = false;
  private queue: Array<() => void> = [];

  async acquire(): Promise<void> {
    if (!this.locked) {
      this.locked = true;
      return;
    }

    // Wait in queue
    return new Promise<void>((resolve) => {
      this.queue.push(resolve);
    });
  }

  release(): void {
    const nextInQueue = this.queue.shift();
    if (nextInQueue) {
      nextInQueue();
    } else {
      this.locked = false;
    }
  }

  async runExclusive<T>(fn: () => Promise<T>): Promise<T> {
    await this.acquire();
    try {
      return await fn();
    } finally {
      this.release();
    }
  }
}

// Serializer helpers for persistent complex UI state
const serializeStringSet = (value: Set<string>): string => {
  return JSON.stringify(Array.from(value));
};

const deserializeStringSet = (stored: string): Set<string> => {
  try {
    const parsed = JSON.parse(stored);
    if (Array.isArray(parsed)) {
      return new Set<string>(parsed);
    }
    return new Set<string>();
  } catch {
    return new Set<string>();
  }
};

function App() {
  // ✅ App Launcher: Track current app (null = home, 'screenshots' = in app)
  const currentApp = useAppLauncherStore((state) => state.currentApp);
  const setCurrentApp = useAppLauncherStore((state) => state.setCurrentApp);
  const goHome = useAppLauncherStore((state) => state.goHome);

  // ✅ Phase 2: Use Zustand stores for state management
  const urls = useAppStore((state) => state.urls);
  const setUrls = useAppStore((state) => state.setUrls);
  const viewportWidth = useAppStore((state) => state.viewportWidth);
  const setViewportWidth = useAppStore((state) => state.setViewportWidth);
  const viewportHeight = useAppStore((state) => state.viewportHeight);
  const setViewportHeight = useAppStore((state) => state.setViewportHeight);
  const useRealBrowser = useAppStore((state) => state.useRealBrowser);
  const setUseRealBrowserContext = useAppStore((state) => state.setUseRealBrowser);
  const useStealth = useAppStore((state) => state.useStealth);
  const setUseStealthContext = useAppStore((state) => state.setUseStealth);
  const headless = useAppStore((state) => state.headless);
  const setHeadlessContext = useAppStore((state) => state.setHeadless);
  const browserEngine = useAppStore((state) => state.browserEngine);
  const setBrowserEngineContext = useAppStore((state) => state.setBrowserEngine);
  const captureMode = useAppStore((state) => state.captureMode);
  const setCaptureModeContext = useAppStore((state) => state.setCaptureMode);
  const autoExpandDropdowns = useAppStore((state) => state.autoExpandDropdowns);
  const setAutoExpandDropdownsContext = useAppStore((state) => state.setAutoExpandDropdowns);
  const trackNetwork = useAppStore((state) => state.trackNetwork);
  const setTrackNetworkContext = useAppStore((state) => state.setTrackNetwork);
  const activeTab = useAppStore((state) => state.activeTab);
  const setActiveTab = useAppStore((state) => state.setActiveTab);

  const results = useScreenshotStore((state) => state.results);
  const setResults = useScreenshotStore((state) => state.setResults);
  const loading = useScreenshotStore((state) => state.loading);
  const setLoading = useScreenshotStore((state) => state.setLoading);
  const progress = useScreenshotStore((state) => state.progress);
  const setProgress = useScreenshotStore((state) => state.setProgress);

  const sessions = useSessionStore((state) => state.sessions);
  const setSessions = useSessionStore((state) => state.setSessions);
  const selectedSessions = useSessionStore((state) => state.selectedSessions);
  const setSelectedSessions = useSessionStore((state) => state.setSelectedSessions);
	  // Track when we are generating Word documents from existing sessions (Sessions tab)
	  const [isGeneratingSessionDocs, setIsGeneratingSessionDocs] = useState(false);

  // ✅ Phase 2: Use Zustand SettingsStore
  const enableMultipleTextBoxes = useSettingsStore((state) => state.enableMultipleTextBoxes);
  const setEnableMultipleTextBoxes = useSettingsStore((state) => state.setEnableMultipleTextBoxes);
  const enableParallelTextBoxes = useSettingsStore((state) => state.enableParallelTextBoxes);
  const setEnableParallelTextBoxes = useSettingsStore((state) => state.setEnableParallelTextBoxes);
  const maxParallelUrls = useSettingsStore((state) => state.maxParallelUrls);
  const setMaxParallelUrls = useSettingsStore((state) => state.setMaxParallelUrls);
  const wordDocFolderName = useSettingsStore((state) => state.wordDocFolderName);
  const setWordDocFolderName = useSettingsStore((state) => state.setWordDocFolderName);
  const screenshotsDir = useSettingsStore((state) => state.screenshotsDir);
  const setScreenshotsDir = useSettingsStore((state) => state.setScreenshotsDir);
  const wordDocsBaseDir = useSettingsStore((state) => state.wordDocsBaseDir);
  const setWordDocsBaseDir = useSettingsStore((state) => state.setWordDocsBaseDir);
  const baseUrl = useSettingsStore((state) => state.baseUrl);
  const setBaseUrl = useSettingsStore((state) => state.setBaseUrl);
  const nonScrollableUrls = useSettingsStore((state) => state.nonScrollableUrls);
  const setNonScrollableUrls = useSettingsStore((state) => state.setNonScrollableUrls);
  const wordsToRemove = useSettingsStore((state) => state.wordsToRemove);
  const setWordsToRemove = useSettingsStore((state) => state.setWordsToRemove);
  const selectedBrowser = useSettingsStore((state) => state.selectedBrowser);
  const setSelectedBrowser = useSettingsStore((state) => state.setSelectedBrowser);
  const cookieDomains = useSettingsStore((state) => state.cookieDomains);
  const setCookieDomains = useSettingsStore((state) => state.setCookieDomains);
  const cookies = useSettingsStore((state) => state.cookies);
  const setCookies = useSettingsStore((state) => state.setCookies);
  const localStorageData = useSettingsStore((state) => state.localStorageData);
  const setLocalStorageData = useSettingsStore((state) => state.setLocalStorageData);
  const expandedAuthMethod = useSettingsStore((state) => state.expandedAuthMethod);
  const setExpandedAuthMethod = useSettingsStore((state) => state.setExpandedAuthMethod);
  const showCookieAnalysis = useSettingsStore((state) => state.showCookieAnalysis);
  const setShowCookieAnalysis = useSettingsStore((state) => state.setShowCookieAnalysis);
  const analysisDomainFilter = useSettingsStore((state) => state.analysisDomainFilter);
  const setAnalysisDomainFilter = useSettingsStore((state) => state.setAnalysisDomainFilter);
  const showAuthCookiesOnly = useSettingsStore((state) => state.showAuthCookiesOnly);
  const setShowAuthCookiesOnly = useSettingsStore((state) => state.setShowAuthCookiesOnly);

  // ✅ FIXED (Bug #14): Use custom hooks for feature-specific state
  const {
    wordInput,
    setWordInput,
    showWordEditor,
    setShowWordEditor,
    editingWordIndex,
    setEditingWordIndex,
    editorWord,
    setEditorWord,
    editorReplacement,
    setEditorReplacement,
    editorType,
    setEditorType,
  } = useWordEditor();
  const {
    cookieImportStatus,
    setCookieImportStatus,
    _availableBrowsers,
    _setAvailableBrowsers,
    isExtractingCookies,
    setIsExtractingCookies,
    cookieAnalysis,
    setCookieAnalysis,
    isAnalyzingCookies,
    setIsAnalyzingCookies,
    showCookieEditor,
    setShowCookieEditor,
    editingCookie,
    setEditingCookie,
    showExportModal,
    setShowExportModal,
    exportType,
    setExportType,
  } = useCookieManagement();
  const {
    authStateStatus,
    setAuthStateStatus,
    isLoginInProgress: _isLoginInProgressFromHook,
    showLoginModal,
    setShowLoginModal,
    loginUrl,
    setLoginUrl,
    customDialog,
    setCustomDialog,
  } = useAuthFlow();
  const {
    urlConfigs,
    setUrlConfigs,
    showUrlConfigEditor,
    setShowUrlConfigEditor,
    editingUrlConfigId,
    setEditingUrlConfigId,
    urlConfigForm,
    setUrlConfigForm,
  } = useUrlConfig();

  // ✅ FIXED (Bug #14 & #15): Use custom hook for system monitoring
  const { systemUsage, startMonitoring } = useSystemMonitoring(5000);

  // Local UI state (component-specific, not shared)
  const [displayedPercent, setDisplayedPercent] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);
  const [renderError, setRenderError] = useState<string | null>(null);

  // ✅ NEW (Phase 3): Rolling parallelization progress tracking
  interface ActiveUrlInfo {
    url: string;
    startTime: number;
    textBoxName: string;
  }
  const [activeUrls, setActiveUrls] = useState<ActiveUrlInfo[]>([]);
  const [completedUrls, setCompletedUrls] = useState<string[]>([]);
  const [failedUrls, setFailedUrls] = useState<string[]>([]);
  const [rollingModeStats, setRollingModeStats] = useState({
    totalUrls: 0,
    completed: 0,
    failed: 0,
    active: 0,
    avgTimePerUrl: 0,
    estimatedTimeRemaining: 0,
  });

  // ✅ NEW (Phase 4): Advanced URL status tracking
  interface UrlStatus {
    url: string;
    status: 'pending' | 'active' | 'completed' | 'failed';
    startTime?: number;
    endTime?: number;
    duration?: number;
    screenshotCount?: number;
    error?: string;
    textBoxName: string;
  }
  const [urlStatuses, setUrlStatuses] = useState<Map<string, UrlStatus>>(new Map());
  const [performanceMetrics, setPerformanceMetrics] = useState({
    throughput: 0, // URLs per minute
    successRate: 0, // Percentage
    avgScreenshotsPerUrl: 0,
    totalScreenshots: 0,
    peakConcurrency: 0,
    startTime: 0,
    elapsedTime: 0,
  });

  // 🔢 Animate a smooth percentage from 0 → 100 while capturing
  useEffect(() => {
    // If we're not capturing or we don't know the total, reset and stop animating
    if (!loading || !progress.total) {
      setDisplayedPercent(0);
      return;
    }

    const target = Math.round((progress.current / progress.total) * 100);
    const stepMs = 80; // "normal" speed: ~0.08s per 1% step

    // If we've already reached or passed the target, nothing to animate
    if (displayedPercent >= target) {
      return;
    }

    const id = setInterval(() => {
      setDisplayedPercent((prev) => {
        if (prev >= target) {
          return prev;
        }
        return Math.min(prev + 1, target);
      });
    }, stepMs);

    return () => clearInterval(id);
  }, [loading, progress.current, progress.total, displayedPercent]);

  // 🔢 Keep the window/tab title in sync with the animated percentage
  useEffect(() => {
    const baseTitle = "ssai";

    // When not capturing or we don't know the total, show only the base title
    if (!loading || !progress.total) {
      document.title = baseTitle;
      return;
    }

    const clamped = Math.max(0, Math.min(displayedPercent, 100));
    document.title = `${baseTitle} ${clamped}%`;
  }, [loading, progress.total, displayedPercent]);

  // ✅ NEW FEATURE: Multiple text boxes for batch processing
  interface TextBox {
    id: string;
    sessionName: string;
    urls: string;
    batchTimeout?: number; // ✅ Internal: always stored in seconds
    batchTimeoutUnit?: string; // ✅ Display: "seconds" | "minutes" | "hours" (UI preference)
    selected?: boolean; // ✅ NEW: Checkbox selection state (default: true)
  }

  // ✅ FIX 2.3: DEFAULT_TEXT_BOXES now imported from shared constants (see top of file)
  // This prevents duplication with useScreenshotEngineForShell.ts

  // ✅ FIXED (Bug #14): These are now in SettingsContext (removed duplicates)
  // enableMultipleTextBoxes, enableParallelTextBoxes, maxParallelUrls
  // wordDocFolderName, screenshotsDir

  // ✅ FIXED (Bug #14): wordDocsBaseDir now in SettingsContext

  const [textBoxes, setTextBoxes] = useDebouncedLocalStorage<TextBox[]>(
    "screenshot-textboxes",
    DEFAULT_TEXT_BOXES, // ✅ Use defaults instead of empty boxes
    500
  );

  // ✅ ENSURE DEFAULTS: Merge defaults with localStorage to ensure first 3 boxes always exist
  useEffect(() => {
    if (textBoxes.length < 3) {
      // If localStorage has fewer than 3 boxes, restore defaults
      setTextBoxes(DEFAULT_TEXT_BOXES);
    } else {
      // Ensure first 3 boxes have default structure (merge user data with defaults)
      const merged = [...textBoxes];
      DEFAULT_TEXT_BOXES.forEach((defaultBox, index) => {
        if (index < merged.length) {
          // Preserve user's URLs and sessionName if they exist, but ensure defaults exist
          // ✅ ALWAYS use default timeout (900s) - don't preserve old values
          merged[index] = {
            ...defaultBox,
            urls: merged[index].urls || defaultBox.urls,
            sessionName: merged[index].sessionName || defaultBox.sessionName,
            batchTimeout: defaultBox.batchTimeout, // ✅ Force default (900s)
            batchTimeoutUnit: defaultBox.batchTimeoutUnit, // ✅ Force default (seconds)
            selected: merged[index].selected ?? defaultBox.selected,
          };
        }
      });

      // Only update if there were changes
      if (JSON.stringify(merged) !== JSON.stringify(textBoxes)) {
        setTextBoxes(merged);
      }
    }
  }, []); // Run only on mount

  // Persist collapse/expand state for each text box across sessions
  const [collapsedTextBoxes, setCollapsedTextBoxes] = useLocalStorage<
    Record<string, boolean>
  >("screenshot-collapsed-textboxes", {});

  // ✅ FIX: Track inline validation errors for batch timeout per text box
  const [timeoutErrors, setTimeoutErrors] = useState<Map<string, string>>(
    new Map()
  );

  // ✅ MIGRATION: Add batchTimeout, batchTimeoutUnit, and selected to old text boxes that don't have them
  useEffect(() => {
    const needsMigration = textBoxes.some(
      (tb) =>
        tb.batchTimeout === undefined ||
        tb.batchTimeoutUnit === undefined ||
        tb.selected === undefined
    );
    if (needsMigration) {
      const migratedTextBoxes = textBoxes.map((tb) => ({
        ...tb,
        batchTimeout: tb.batchTimeout || 90, // Default to 90s if missing
        batchTimeoutUnit: tb.batchTimeoutUnit || "seconds", // Default to seconds if missing
        selected: tb.selected !== undefined ? tb.selected : true, // ✅ NEW: Default to checked if missing
      }));
      setTextBoxes(migratedTextBoxes);
    }
  }, []); // Run once on mount

  // ✅ FIXED (Bug #14 & #15): Start system monitoring on mount
  // Now handled by useSystemMonitoring hook with proper cleanup
  useEffect(() => {
    startMonitoring();
  }, [startMonitoring]);

  // ✅ FIXED (Bug #14): These are now in AppContext (removed duplicate declarations)
  // captureMode, useStealth, useRealBrowser, headless, trackNetwork, autoExpandDropdowns

  // Simple CDP status indicator for a chosen port ("unknown" | "up" | "down")
  const [cdpStatus, setCdpStatus] = useState<"unknown" | "up" | "down">("unknown");
  const [cdpPort, setCdpPort] = useState<number>(9223);
  const [cdpBrowser, setCdpBrowser] = useState<"chrome" | "safari">("chrome");
  const [copyCookies, setCopyCookies] = useState<boolean>(true);
  const [cookieText, setCookieText] = useState<string>("");

  // ✅ FIXED (Bug #14): These are now in SettingsContext
  // nonScrollableUrls, baseUrl, wordsToRemove

  // Current input for adding new word transformation
  // ✅ FIXED (Bug #14): Word editor state now in useWordEditor hook
  // wordInput, showWordEditor, editingWordIndex, editorWord, editorReplacement, editorType

  // ✅ NEW: URL-specific click configurations
  interface UrlClickAction {
    type: "click";
    text: string;
    wait_after_ms: number;
    description?: string;
  }

  interface UrlClickConfig {
    id: string;
    name: string;
    url_pattern: string;
    match_type: "exact" | "contains" | "startswith" | "regex";
    actions: UrlClickAction[];
    enabled: boolean;
    created_at?: string;
	    notes?: string;
	    // Optional per-URL flag to auto-expand dropdowns AFTER URL click actions
	    auto_expand_dropdowns?: boolean;
  }

  // ✅ FIXED (Bug #14): URL config state now in useUrlConfig hook
  // urlConfigs, showUrlConfigEditor, editingUrlConfigId, urlConfigForm

  // ✅ FIXED (Bug #14): Cookies and localStorage now in SettingsContext
  // cookies, localStorageData

  // ✅ FIXED (Bug #14): Auth state now in useAuthFlow hook
  // authStateStatus, isLoginInProgress, showLoginModal, loginUrl, _showAuthPreview, customDialog

  // ✅ FIX: Track WebSocket connection notification to prevent duplicates
  const hasShownConnectionNotificationRef = useRef(false);

  // 🔒 RACE CONDITION FIX: Mutex for preventing concurrent Word document generation
  const documentGenerationMutexRef = useRef(new AsyncMutex());

  // 🔔 Toast notification system
  const {
    notifications,
    history: _history, // Reserved for future use
    addNotification,
    removeNotification,
    clearAll: _clearAll, // Reserved for future use
    clearHistory: _clearHistory, // Reserved for future use
  } = useNotifications();
  // ✅ Removed misleading log - this runs on every render, not just mount

  // 🔔 Confirm dialog state
  const [confirmDialog, setConfirmDialog] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    onConfirm: () => void;
    type?: "danger" | "warning" | "info";
  }>({
    isOpen: false,
    title: "",
    message: "",
    onConfirm: () => {},
    type: "warning",
  });

  // 🔌 WebSocket connection for real-time updates
  const { isConnected: wsConnected, lastMessage: _wsLastMessage } = useWebSocket( // lastMessage reserved for future use
    {
      onMessage: (message: WebSocketMessage) => {
        log.debug(`🔌 App: WebSocket message received: ${message.type}`);

        // Handle different message types
        if (message.type === "progress") {
          const progressMsg = message as any;
          log.debug(
            `🔌 App: Progress update - ${progressMsg.current}/${progressMsg.total} - ${progressMsg.url}`
          );
          addNotification({
            type: "info",
            title: "📸 Screenshot Progress",
            message: `Capturing ${progressMsg.current}/${
              progressMsg.total
            }: ${progressMsg.url?.substring(0, 50)}...`,
            duration: 3000,
          });
        } else if (message.type === "url_config_detected") {
          const configMsg = message as any;
          log.debug(`🔌 App: URL config detected - ${configMsg.config_name}`);
          addNotification({
            type: "info",
            title: "⚙️ URL Configuration Detected",
            message: `Found saved configuration: ${configMsg.config_name}`,
            duration: 5000,
          });
        } else if (message.type === "url_config_action") {
          const actionMsg = message as any;
          log.debug(
            `🔌 App: URL config action - ${actionMsg.action_index}/${actionMsg.total_actions}`
          );
          addNotification({
            type: "info",
            title: "🎯 Executing Action",
            message: `Action ${actionMsg.action_index}/${actionMsg.total_actions}: ${actionMsg.description}`,
            duration: 4000,
          });
        } else if (message.type === "form_processing") {
          const formMsg = message as any;
          log.debug(
            `🔌 App: Form processing - ${formMsg.form_index}/${formMsg.total_forms}`
          );
          addNotification({
            type: "info",
            title: "📋 Processing Form",
            message: `Form ${formMsg.form_index}/${formMsg.total_forms}: ${formMsg.form_name}`,
            duration: 3000,
          });
        } else if (message.type === "segment_progress") {
          const segmentMsg = message as any;
          log.debug(
            `🔌 App: Segment progress - ${segmentMsg.segment_index}/${segmentMsg.total_segments}`
          );
          // Only show segment progress for multi-segment captures
          if (segmentMsg.total_segments > 1) {
            addNotification({
              type: "info",
              title: "📸 Capturing Segments",
              message: `Segment ${segmentMsg.segment_index}/${segmentMsg.total_segments}`,
              duration: 2000,
            });
          }
        } else if (message.type === "url_status_change") {
          // ✅ NEW: Handle real-time URL status updates for rolling parallelization
          const statusMsg = message as any;
          log.debug(
            `🔌 App: URL status change - ${statusMsg.url} → ${statusMsg.status}`
          );

          // Update URL status in real-time (only for rolling mode)
          if (enableParallelTextBoxes) {
            if (statusMsg.status === "active") {
              updateUrlStatus(statusMsg.url, 'active', {
                startTime: Date.now(),
              });
            } else if (statusMsg.status === "completed") {
              updateUrlStatus(statusMsg.url, 'completed', {
                endTime: Date.now(),
                duration: statusMsg.duration,
                screenshotCount: statusMsg.screenshots,
              });

              // ✅ OPTION 4: Real-time log for rolling mode completions
              const shortUrl = statusMsg.url.length > 60
                ? statusMsg.url.substring(0, 57) + '...'
                : statusMsg.url;
              const screenshotCount = statusMsg.screenshots || 0;
              const duration = statusMsg.duration ? statusMsg.duration.toFixed(1) : 'N/A';
              addLog(`   ✅ ${shortUrl} (${duration}s, ${screenshotCount} screenshot${screenshotCount !== 1 ? 's' : ''})`);

            } else if (statusMsg.status === "failed" || statusMsg.status === "cancelled") {
              updateUrlStatus(statusMsg.url, 'failed', {
                endTime: Date.now(),
                duration: statusMsg.duration,
                error: statusMsg.error,
              });

              // ✅ OPTION 4: Real-time log for failures
              const shortUrl = statusMsg.url.length > 60
                ? statusMsg.url.substring(0, 57) + '...'
                : statusMsg.url;
              const errorMsg = statusMsg.error || 'Unknown error';
              const shortError = errorMsg.length > 50
                ? errorMsg.substring(0, 47) + '...'
                : errorMsg;
              addLog(`   ❌ ${shortUrl} - ${shortError}`);
            }

            // Update performance metrics in real-time
            updatePerformanceMetrics();
          }
        } else if (message.type === "result") {
          const resultMsg = message as any;
          log.debug(
            `🔌 App: Screenshot result - ${resultMsg.status} - ${resultMsg.url}`
          );
          if (resultMsg.status === "success") {
            addNotification({
              type: "success",
              title: "✅ Screenshot Captured",
              message: `Successfully captured: ${resultMsg.url?.substring(
                0,
                50
              )}...`,
              duration: 4000,
            });
          } else if (resultMsg.status === "error") {
            addNotification({
              type: "error",
              title: "❌ Screenshot Failed",
              message: `Failed to capture: ${resultMsg.url?.substring(
                0,
                50
              )}...`,
              duration: 6000,
            });
          }
        }
      },
      onOpen: () => {
        log.info("🔌 App: WebSocket connected");
        // ✅ FIX: Only show notification once per session
        if (!hasShownConnectionNotificationRef.current) {
          hasShownConnectionNotificationRef.current = true;
          addNotification({
            type: "success",
            title: "🔌 Connected",
            message: "Real-time updates enabled",
            duration: 3000,
          });
        } else {
          log.debug("🔌 App: Skipping duplicate connection notification (reconnect)");
        }
      },
      onClose: () => {
        log.info("🔌 App: WebSocket disconnected");
      },
      onError: (error) => {
        log.error("🔌 App: WebSocket error:", error);
      },
    }
  );

  // ✅ Removed misleading log - this runs on every render, not just when connection changes

  // ✅ FIXED (Bug #14): Cookie management state now in useCookieManagement hook
  // cookieImportStatus, _availableBrowsers, isExtractingCookies, cookieAnalysis
  // isAnalyzingCookies, _selectedCookie

  // ✅ Cookie editor and export modals already destructured from useCookieManagement() hook (lines 215-222)
  // Removed duplicate declarations

  // Auth flow state (local to App.tsx)
  const [isLoginInProgress, setIsLoginInProgress] = useState(false);

  // ✅ FIXED (Bug #14): Cookie settings now in SettingsContext
  // selectedBrowser, cookieDomains, analysisDomainFilter, showAuthCookiesOnly
  // showCookieAnalysis, expandedAuthMethod
  const [exportOptions, setExportOptions] = useState({
    includeHeaders: true,
    includeMethod: true,
    includeUrl: true,
    url: "",
    method: "GET",
    prettyPrint: true,
    includeComments: false,
    explainEverything: false,
  });
  const [exportCode, setExportCode] = useState("");
  const [showSecurityAudit, setShowSecurityAudit] = useState(false);
  const [securityReport, setSecurityReport] = useState<any>(null);
  const [showFormatExport, setShowFormatExport] = useState(false);
  const [exportFormat, setExportFormat] = useState<string>("json");
  const [showFormatImport, setShowFormatImport] = useState(false);
  const [importFormat, setImportFormat] = useState<string>("json");

  // Regenerate export code when options change
  useEffect(() => {
    if (showExportModal) {
      const code =
        exportType === "curl"
          ? generateCurlCommand()
          : generatePlaywrightCode();
      setExportCode(code);
    }
  }, [exportOptions, showExportModal, exportType]);

  // ❌ DISABLED: Auth and cookie features not needed for screenshot tool
  // Check auth state status on mount
  // useEffect(() => {
  //   checkAuthStatus();
  //   checkCookieStatus();
  //   detectBrowsers();
  // }, []);

  // ✅ Migrate old string[] format to new WordTransformation[] format (backward compatibility)
  useEffect(() => {
    const stored = localStorage.getItem("screenshot-words-to-remove");
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        // Check if it's old format (array of strings)
        if (
          Array.isArray(parsed) &&
          parsed.length > 0 &&
          typeof parsed[0] === "string"
        ) {
          log.info(
            "🔄 Migrating old word format to new transformation format..."
          );
          const migrated: WordTransformation[] = parsed.map((word: string) => ({
            word,
            replacement: " ",
            type: "space" as const,
          }));
          setWordsToRemove(migrated);
          log.info(`✅ Migrated ${migrated.length} words to new format`);
        }
      } catch (e) {
        log.error("Failed to migrate word transformations:", e);
      }
    }
  }, []); // Run once on mount

  const checkAuthStatus = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8001/api/auth/status");
      const data = await response.json();
      setAuthStateStatus(data);
    } catch (error) {
      log.error("Failed to check auth status:", error);
    }
  };

  // ✅ FIX: Custom dialog helpers (replace browser alert/confirm)
  const showCustomAlert = (title: string, message: string) => {
    return new Promise<void>((resolve) => {
      setCustomDialog({
        show: true,
        title,
        message,
        type: "alert",
        onConfirm: () => {
          setCustomDialog({
            show: false,
            title: "",
            message: "",
            type: "alert",
          });
          resolve();
        },
      });
    });
  };

  const showCustomConfirm = (title: string, message: string) => {
    return new Promise<boolean>((resolve) => {
      setCustomDialog({
        show: true,
        title,
        message,
        type: "confirm",
        onConfirm: () => {
          setCustomDialog({
            show: false,
            title: "",
            message: "",
            type: "alert",
          });
          resolve(true);
        },
        onCancel: () => {
          setCustomDialog({
            show: false,
            title: "",
            message: "",
            type: "alert",
          });
          resolve(false);
        },
      });
    });
  };

  // ✅ NEW: Unified notification system (replaces browser alert() and Notification API)
  // This function automatically detects the message type and shows appropriate toast notification
  const notify = (
    message: string,
    options?: {
      title?: string;
      type?: "success" | "error" | "warning" | "info";
      duration?: number;
    }
  ) => {
    log.debug(`🔔 notify() called: ${message.substring(0, 100)}...`);

    // Use toast notification system
    addNotification({
      message,
      title: options?.title,
      type: options?.type,
      duration: options?.duration,
    });
  };

  // ✅ NEW: Custom alert wrapper (replaces browser alert())
  // Automatically uses notify() for all alert() calls
  const alert = (message: string) => {
    log.debug(`🔔 alert() called: ${message.substring(0, 100)}...`);
    return notify(message);
  };

  const openLoginModal = () => {
    setShowLoginModal(true);
  };

  const startLogin = async () => {
    setShowLoginModal(false);
    if (!loginUrl.trim()) {
      alert("Please enter a URL");
      return;
    }

    setIsLoginInProgress(true);
    addLog("🔓 Opening browser for manual login...");
    addLog(`📍 Navigate to: ${loginUrl}`);
    addLog(
      `🌐 Browser engine: ${
        browserEngine === "camoufox"
          ? "🦊 Camoufox (with persistent profile)"
          : "🎭 Playwright"
      }`
    );
    addLog("⏳ Please log in and wait...");

    try {
      const response = await fetch(
        "http://127.0.0.1:8001/api/auth/start-login",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: loginUrl,
            browser_engine: browserEngine, // Send browser engine from settings
          }),
        }
      );

      if (response.ok) {
        const _data = await response.json(); // Response data reserved for future use
        addLog("✅ Auth state saved successfully!");
        addLog(`📊 Cookies: ${authStateStatus.cookie_count || 0}`);
        addLog(`📊 localStorage: ${authStateStatus.localStorage_count || 0}`);
        alert(
          "✅ Login successful!\n\nYour auth state has been saved.\nFuture captures will automatically use this saved state."
        );
        await checkAuthStatus();
      } else {
        const error = await response.json();
        addLog(`❌ Failed to save auth state: ${error.detail}`);
        alert(`❌ Failed to save auth state:\n${error.detail}`);
      }
    } catch (error) {
      addLog(`❌ Error: ${getErrorMessage(error)}`);
      alert(`❌ Error:\n${getErrorMessage(error)}`);
    } finally {
      setIsLoginInProgress(false);
    }
  };

  // Alias for the new button-based UI
  const openLoginBrowser = () => {
    openLoginModal();
  };

  const clearAuthState = async () => {
    const confirmed = await ask(
      "Are you sure you want to clear the saved auth state?",
      { title: "Clear Auth State" }
    );
    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8001/api/auth/clear", {
        method: "DELETE",
      });

      if (response.ok) {
        addLog("✅ Auth state cleared");
        alert("✅ Auth state cleared successfully!");
        await checkAuthStatus();
      } else {
        const error = await response.json();
        addLog(`❌ Failed to clear auth state: ${error.detail}`);
        alert(`❌ Failed to clear auth state:\n${error.detail}`);
      }
    } catch (error) {
      addLog(`❌ Error: ${getErrorMessage(error)}`);
      alert(`❌ Error:\n${getErrorMessage(error)}`);
    }
  };

  // 🍪 Cookie management functions
  const checkCookieStatus = async () => {
    try {
      const response = await fetch("http://127.0.0.1:8001/api/cookies/status");
      const data = await response.json();
      setCookieImportStatus(data);
    } catch (error) {
      log.error("Failed to check cookie status:", error);
    }
  };

  const detectBrowsers = async () => {
    try {
      const response = await fetch(
        "http://127.0.0.1:8001/api/cookies/browsers"
      );
      const data = await response.json();
      _setAvailableBrowsers(data.available || []);
    } catch (error) {
      log.error("Failed to detect browsers:", error);
    }
  };

  const extractCookies = async () => {
    setIsExtractingCookies(true);
    addLog("🍪 Extracting cookies from browser...");
    addLog(`   Browser: ${selectedBrowser}`);
    addLog(`   Engine: ${browserEngine}`);
    if (cookieDomains) {
      addLog(`   Domains: ${cookieDomains}`);
    }

    try {
      const domains = cookieDomains
        ? cookieDomains
            .split(",")
            .map((d) => d.trim())
            .filter((d) => d)
        : null;

      const response = await fetch(
        "http://127.0.0.1:8001/api/cookies/extract",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            domains,
            browser: selectedBrowser,
            engine: browserEngine,
          }),
        }
      );

      const result = await response.json();

      if (result.success) {
        addLog(`✅ Cookies extracted successfully!`);
        addLog(`   Source: ${result.source_browser}`);
        addLog(`   Count: ${result.cookie_count}`);
        if (result.domains && result.domains.length > 0) {
          addLog(`   Domains: ${result.domains.join(", ")}`);
        }
        alert(
          `✅ Cookies extracted successfully!\n\n` +
            `Source: ${result.source_browser}\n` +
            `Count: ${result.cookie_count}\n` +
            `Engine: ${browserEngine}\n\n` +
            `Future captures will automatically use these cookies!`
        );
        await checkCookieStatus();
      } else {
        addLog(`❌ Failed to extract cookies: ${result.error}`);
        alert(`❌ Failed to extract cookies:\n${result.error}`);
      }
    } catch (error) {
      addLog(`❌ Error: ${getErrorMessage(error)}`);
      alert(`❌ Error:\n${getErrorMessage(error)}`);
    } finally {
      setIsExtractingCookies(false);
    }
  };

  const clearCookies = async () => {
    const confirmed = await ask(
      "Are you sure you want to clear imported cookies?",
      { title: "Clear Cookies" }
    );
    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch(
        `http://127.0.0.1:8001/api/cookies/clear?engine=${browserEngine}`,
        { method: "DELETE" }
      );

      const result = await response.json();

      if (result.success) {
        addLog(`✅ Cookies cleared for ${browserEngine}`);
        alert(`✅ Cookies cleared successfully!`);
        await checkCookieStatus();
      } else {
        addLog(`❌ Failed to clear cookies`);
        alert(`❌ Failed to clear cookies`);
      }
    } catch (error) {
      addLog(`❌ Error: ${getErrorMessage(error)}`);
      alert(`❌ Error:\n${getErrorMessage(error)}`);
    }
  };

  const analyzeCookies = async () => {
    setIsAnalyzingCookies(true);
    addLog("🔍 Analyzing cookies...");

    try {
      const params = new URLSearchParams();
      if (analysisDomainFilter) {
        params.append("domain", analysisDomainFilter);
      }
      if (showAuthCookiesOnly) {
        params.append("auth_only", "true");
      }

      const response = await fetch(
        `http://127.0.0.1:8001/api/cookies/analyze?${params}`
      );
      const result = await response.json();

      if (result.success) {
        setCookieAnalysis(result);
        setShowCookieAnalysis(true);
        addLog(`✅ Analysis complete: ${result.total} cookies analyzed`);
      } else {
        addLog(`❌ ${result.error}`);
        alert(result.error);
      }
    } catch (error) {
      addLog(`❌ Error: ${getErrorMessage(error)}`);
      alert(`❌ Error:\n${getErrorMessage(error)}`);
    } finally {
      setIsAnalyzingCookies(false);
    }
  };

  // 🍪 Cookie Management Functions
  const viewCookie = (cookie: any) => {
    _setSelectedCookie(cookie);
    setEditingCookie({ ...cookie });
    setShowCookieEditor(true);
  };

  const updateCookie = async () => {
    if (!editingCookie) return;

    try {
      const response = await fetch("http://127.0.0.1:8001/api/cookies/update", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editingCookie),
      });

      if (response.ok) {
        addLog(`✅ Cookie updated: ${editingCookie.name}`);
        setShowCookieEditor(false);
        await analyzeCookies(); // Refresh the analysis
        await checkCookieStatus(); // Refresh cookie status
      } else {
        const error = await response.json();
        addLog(`❌ Failed to update cookie: ${error.detail}`);
        alert(`❌ Failed to update cookie:\n${error.detail}`);
      }
    } catch (error) {
      addLog(`❌ Error: ${getErrorMessage(error)}`);
      alert(`❌ Error:\n${getErrorMessage(error)}`);
    }
  };

  const deleteCookie = async (cookie: any) => {
    log.debug(`🍪 deleteCookie: Requesting confirmation for ${cookie.name}`);
    // ✅ Use custom confirm dialog
    const confirmed = await showCustomConfirm(
      "🗑️ Delete Cookie",
      `Delete cookie "${cookie.name}" from ${cookie.domain}?`
    );

    if (!confirmed) {
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:8001/api/cookies/delete", {
        method: "DELETE",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: cookie.name,
          domain: cookie.domain,
        }),
      });

      if (response.ok) {
        addLog(`✅ Cookie deleted: ${cookie.name}`);
        setShowCookieEditor(false);
        await analyzeCookies(); // Refresh the analysis
        await checkCookieStatus(); // Refresh cookie status
      } else {
        const error = await response.json();
        addLog(`❌ Failed to delete cookie: ${error.detail}`);
        alert(`❌ Failed to delete cookie:\n${error.detail}`);
      }
    } catch (error) {
      addLog(`❌ Error: ${getErrorMessage(error)}`);
      alert(`❌ Error:\n${getErrorMessage(error)}`);
    }
  };

  const generateCurlCommand = () => {
    const cookie = editingCookie;
    const opts = exportOptions;

    let cmd = "";

    if (opts.explainEverything) {
      cmd +=
        "# ═══════════════════════════════════════════════════════════════\n";
      cmd += "# cURL Command - HTTP Request with Cookie Authentication\n";
      cmd +=
        "# ═══════════════════════════════════════════════════════════════\n\n";

      cmd += "# COOKIE DETAILS:\n";
      cmd += `# Name: ${cookie.name}\n`;
      cmd += `#   └─ Cookie identifier (case-sensitive)\n`;
      cmd += `# Value: ${cookie.value}\n`;
      cmd += `#   └─ Cookie data (session token, user ID, etc.)\n`;
      cmd += `# Domain: ${cookie.domain}\n`;
      cmd += `#   └─ ${
        cookie.domain.startsWith(".")
          ? "Subdomain cookie (works on all subdomains)"
          : "Exact domain only"
      }\n`;
      cmd += `# Path: ${cookie.path || "/"}\n`;
      cmd += `#   └─ Cookie sent only for URLs starting with this path\n`;
      cmd += `# Expires: ${
        cookie.expires === -1 || !cookie.expires
          ? "Session (deleted when browser closes)"
          : new Date(cookie.expires * 1000).toLocaleString()
      }\n`;
      cmd += `#   └─ ${
        cookie.expires === -1 || !cookie.expires
          ? "Temporary cookie"
          : "Persistent cookie (survives browser restart)"
      }\n`;
      cmd += `# Secure: ${
        cookie.secure ? "Yes (HTTPS only)" : "No (HTTP allowed - INSECURE!)"
      }\n`;
      cmd += `#   └─ ${
        cookie.secure
          ? "Cookie only sent over encrypted connections"
          : "WARNING: Cookie can be intercepted over HTTP!"
      }\n`;
      cmd += `# HttpOnly: ${
        cookie.httpOnly
          ? "Yes (JavaScript blocked)"
          : "No (JavaScript accessible)"
      }\n`;
      cmd += `#   └─ ${
        cookie.httpOnly
          ? "Protects against XSS attacks"
          : "WARNING: Vulnerable to XSS attacks!"
      }\n`;
      cmd += `# SameSite: ${cookie.sameSite || "None"}\n`;
      cmd += `#   └─ ${
        cookie.sameSite === "Strict"
          ? "Strict - Only same-site requests (most secure)"
          : cookie.sameSite === "Lax"
          ? "Lax - Top-level navigation allowed (default)"
          : "None - Allows third-party requests (requires Secure)"
      }\n`;
      if (cookie.partitioned) {
        cmd += `# Partitioned: Yes (CHIPS enabled)\n`;
        cmd += `#   └─ Separate cookie jar per top-level site (Chrome 114+)\n`;
      }
      cmd += `# Size: ${
        (cookie.name?.length || 0) + (cookie.value?.length || 0)
      } bytes\n`;
      cmd += `#   └─ ${
        (cookie.name?.length || 0) + (cookie.value?.length || 0) > 4096
          ? "WARNING: Exceeds 4096 byte limit!"
          : "Within RFC 6265bis size limit"
      }\n\n`;

      cmd += "# COMMAND BREAKDOWN:\n";
      cmd +=
        "# curl          - Command-line tool for transferring data with URLs\n";
      if (opts.includeMethod && opts.method !== "GET") {
        cmd += `# -X ${opts.method}        - HTTP method (${
          opts.method === "POST"
            ? "submit data"
            : opts.method === "PUT"
            ? "update resource"
            : opts.method === "DELETE"
            ? "delete resource"
            : opts.method === "PATCH"
            ? "partial update"
            : "custom method"
        })\n`;
      }
      cmd += `# -H \"Cookie:\"  - HTTP header containing cookie data\n`;
      cmd += `#   └─ Format: \"Cookie: name=value\"\n`;
      cmd += `#   └─ Sent with every matching request\n`;
      if (opts.includeUrl) {
        const url = opts.url || `https://${cookie.domain}${cookie.path || "/"}`;
        cmd += `# \"${url}\" - Target URL\n`;
        cmd += `#   └─ ${
          url.startsWith("https://")
            ? "Secure HTTPS connection"
            : "WARNING: Insecure HTTP connection!"
        }\n`;
      }
      cmd += "\n# ACTUAL COMMAND:\n";
    } else if (opts.includeComments) {
      cmd += `# Cookie: ${cookie.name} (${
        cookie.secure ? "Secure" : "Insecure"
      }, ${cookie.sameSite || "No SameSite"})\n`;
    }

    cmd += "curl";

    if (opts.includeMethod && opts.method !== "GET") {
      cmd += ` -X ${opts.method}`;
    }

    if (opts.includeHeaders) {
      cmd += ` -H "Cookie: ${cookie.name}=${cookie.value}"`;
    }

    if (opts.includeUrl) {
      const url = opts.url || `https://${cookie.domain}${cookie.path || "/"}`;
      cmd += ` "${url}"`;
    }

    return cmd;
  };

  const generatePlaywrightCode = () => {
    const cookie = editingCookie;
    const opts = exportOptions;

    let code = "";

    if (opts.explainEverything) {
      code +=
        "// ═══════════════════════════════════════════════════════════════\n";
      code += "// Playwright Cookie Injection - Browser Automation\n";
      code +=
        "// ═══════════════════════════════════════════════════════════════\n\n";

      code += "// COOKIE SPECIFICATION (RFC 6265bis-21):\n";
      code +=
        "// ─────────────────────────────────────────────────────────────\n\n";

      code += `// name: '${cookie.name}'\n`;
      code += "//   ├─ PURPOSE: Unique identifier for this cookie\n";
      code += "//   ├─ TYPE: String (case-sensitive)\n";
      code += "//   ├─ REQUIRED: Yes\n";
      code += `//   └─ NOTE: ${
        cookie.name.startsWith("__Host-")
          ? "Uses __Host- prefix (requires Secure, Path=/, no Domain)"
          : cookie.name.startsWith("__Secure-")
          ? "Uses __Secure- prefix (requires Secure flag)"
          : "Standard cookie name"
      }\n\n`;

      code += `// value: '${cookie.value}'\n`;
      code +=
        "//   ├─ PURPOSE: Cookie data (session token, user preferences, etc.)\n";
      code += "//   ├─ TYPE: String (URL-encoded if contains special chars)\n";
      code += "//   ├─ REQUIRED: Yes\n";
      code += `//   ├─ SIZE: ${cookie.value?.length || 0} characters\n`;
      code += `//   └─ NOTE: ${
        (cookie.name?.length || 0) + (cookie.value?.length || 0) > 4096
          ? "⚠️ EXCEEDS 4096 byte RFC limit!"
          : "✓ Within size limits"
      }\n\n`;

      code += `// domain: '${cookie.domain}'\n`;
      code += "//   ├─ PURPOSE: Specifies which domain receives this cookie\n";
      code += "//   ├─ TYPE: String (domain name)\n";
      code += "//   ├─ REQUIRED: Yes (for Playwright)\n";
      code += `//   ├─ SCOPE: ${
        cookie.domain.startsWith(".")
          ? "Subdomain cookie (*.example.com)"
          : "Exact domain match only"
      }\n`;
      code += `//   └─ EXAMPLE: ${
        cookie.domain.startsWith(".")
          ? `Sent to ${cookie.domain.substring(1)}, www${cookie.domain}, api${
              cookie.domain
            }`
          : `Only sent to ${cookie.domain}`
      }\n\n`;

      code += `// path: '${cookie.path || "/"}'\n`;
      code += "//   ├─ PURPOSE: Restricts cookie to specific URL paths\n";
      code += "//   ├─ TYPE: String (URL path)\n";
      code += "//   ├─ DEFAULT: '/' (all paths)\n";
      code += `//   └─ EXAMPLE: ${
        cookie.path === "/" || !cookie.path
          ? "Sent to all URLs on domain"
          : `Only sent to ${cookie.domain}${cookie.path}*`
      }\n\n`;

      code += `// expires: ${cookie.expires || -1}\n`;
      code += "//   ├─ PURPOSE: Cookie lifetime (Unix timestamp in seconds)\n";
      code += "//   ├─ TYPE: Number (seconds since Jan 1, 1970)\n";
      code += `//   ├─ VALUE: ${
        cookie.expires === -1 || !cookie.expires
          ? "-1 (session cookie)"
          : `${cookie.expires} (${new Date(
              cookie.expires * 1000
            ).toLocaleString()})`
      }\n`;
      code += `//   ├─ BEHAVIOR: ${
        cookie.expires === -1 || !cookie.expires
          ? "Deleted when browser closes"
          : "Persists until expiry date"
      }\n`;
      code += `//   └─ NOTE: ${
        cookie.expires === -1 || !cookie.expires
          ? "Temporary - good for sensitive data"
          : "Permanent - survives browser restart"
      }\n\n`;

      code += `// httpOnly: ${cookie.httpOnly || false}\n`;
      code += "//   ├─ PURPOSE: Prevents JavaScript access to cookie\n";
      code += "//   ├─ TYPE: Boolean\n";
      code += "//   ├─ DEFAULT: false\n";
      code += `//   ├─ SECURITY: ${
        cookie.httpOnly
          ? "✓ Protected from XSS attacks"
          : "⚠️ Vulnerable to XSS (document.cookie can read it)"
      }\n`;
      code += `//   └─ USE CASE: ${
        cookie.httpOnly
          ? "Authentication tokens, session IDs"
          : "Client-side accessible data"
      }\n\n`;

      code += `// secure: ${cookie.secure || false}\n`;
      code += "//   ├─ PURPOSE: Only send cookie over HTTPS\n";
      code += "//   ├─ TYPE: Boolean\n";
      code += "//   ├─ DEFAULT: false\n";
      code += `//   ├─ SECURITY: ${
        cookie.secure
          ? "✓ Encrypted transmission only"
          : "⚠️ Can be sent over HTTP (interceptable!)"
      }\n`;
      code += `//   ├─ REQUIRED: ${
        cookie.sameSite === "None" ||
        cookie.partitioned ||
        cookie.name.startsWith("__Secure-") ||
        cookie.name.startsWith("__Host-")
          ? "Yes (for SameSite=None, CHIPS, or cookie prefixes)"
          : "No (but recommended)"
      }\n`;
      code += `//   └─ NOTE: ${
        cookie.secure
          ? "Production-ready"
          : "Only use false for local development!"
      }\n\n`;

      code += `// sameSite: '${cookie.sameSite || "Lax"}'\n`;
      code += "//   ├─ PURPOSE: Controls cross-site request behavior\n";
      code += "//   ├─ TYPE: String ('Strict' | 'Lax' | 'None')\n";
      code += "//   ├─ DEFAULT: 'Lax' (Chrome 80+)\n";
      code += `//   ├─ BEHAVIOR:\n`;
      code += `//   │   ${
        cookie.sameSite === "Strict"
          ? "• Strict - ONLY same-site requests (most secure)"
          : cookie.sameSite === "Lax"
          ? "• Lax - Same-site + top-level navigation (default)"
          : "• None - All requests (requires Secure flag)"
      }\n`;
      code += `//   │   ${
        cookie.sameSite === "Strict"
          ? "• Blocks: Third-party embeds, CSRF attacks"
          : cookie.sameSite === "Lax"
          ? "• Blocks: POST from other sites, allows GET links"
          : "• Allows: Third-party embeds, cross-site requests"
      }\n`;
      code += `//   └─ USE CASE: ${
        cookie.sameSite === "Strict"
          ? "Banking, sensitive operations"
          : cookie.sameSite === "Lax"
          ? "General authentication (recommended)"
          : "Third-party widgets, embeds"
      }\n`;

      if (cookie.partitioned) {
        code += `\n// partitioned: true\n`;
        code +=
          "//   ├─ PURPOSE: CHIPS (Cookies Having Independent Partitioned State)\n";
        code += "//   ├─ TYPE: Boolean\n";
        code += "//   ├─ BROWSER: Chrome 114+, Firefox 141+\n";
        code += "//   ├─ BEHAVIOR: Separate cookie jar per top-level site\n";
        code +=
          "//   ├─ EXAMPLE: Cookie on embed.com embedded in site-a.com vs site-b.com\n";
        code +=
          "//   │            → Two separate cookies (partitioned by top-level site)\n";
        code += "//   ├─ REQUIRED: Secure flag must be true\n";
        code += "//   ├─ LIMIT: Max 180 cookies per partition, 10 KB total\n";
        code += "//   └─ USE CASE: Third-party embeds (chat, maps, payments)\n";
      }

      code +=
        "\n\n// ═══════════════════════════════════════════════════════════════\n";
      code += "// ACTUAL CODE:\n";
      code +=
        "// ═══════════════════════════════════════════════════════════════\n\n";
    } else if (opts.includeComments) {
      code += `// Cookie: ${cookie.name}\n`;
      code += `// Domain: ${cookie.domain}\n`;
      code += `// Security: ${cookie.secure ? "Secure" : "Insecure"}, ${
        cookie.httpOnly ? "HttpOnly" : "No HttpOnly"
      }\n`;
      code += `// SameSite: ${cookie.sameSite || "None"}\n`;
      if (cookie.partitioned) {
        code += `// CHIPS: Partitioned cookie (Chrome 114+)\n`;
      }
      code += "\n";
    }

    code += "await context.addCookies([";

    if (opts.prettyPrint) {
      code += "{\n";
      code += `  name: '${cookie.name}',\n`;
      code += `  value: '${cookie.value}',\n`;
      code += `  domain: '${cookie.domain}',\n`;
      code += `  path: '${cookie.path || "/"}',\n`;
      code += `  expires: ${cookie.expires || -1},\n`;
      code += `  httpOnly: ${cookie.httpOnly || false},\n`;
      code += `  secure: ${cookie.secure || false},\n`;
      code += `  sameSite: '${cookie.sameSite || "Lax"}'`;
      if (cookie.partitioned) {
        code += `,\n  partitioned: true`;
      }
      code += "\n}";
    } else {
      code += `{name: '${cookie.name}', value: '${cookie.value}', domain: '${
        cookie.domain
      }', path: '${cookie.path || "/"}', expires: ${
        cookie.expires || -1
      }, httpOnly: ${cookie.httpOnly || false}, secure: ${
        cookie.secure || false
      }, sameSite: '${cookie.sameSite || "Lax"}'`;
      if (cookie.partitioned) {
        code += `, partitioned: true`;
      }
      code += "}";
    }

    code += "]);";

    return code;
  };

  const openExportModal = (type: "curl" | "playwright") => {
    setExportType(type);
    const newOptions = {
      ...exportOptions,
      url: `https://${editingCookie.domain}${editingCookie.path || "/"}`,
    };
    setExportOptions(newOptions);
    setShowExportModal(true);

    // Generate initial code
    setTimeout(() => {
      const code =
        type === "curl" ? generateCurlCommand() : generatePlaywrightCode();
      setExportCode(code);
    }, 0);
  };

  const copyExportCode = () => {
    navigator.clipboard.writeText(exportCode);
    alert(
      `✅ ${
        exportType === "curl" ? "cURL" : "Playwright"
      } code copied to clipboard!`
    );
    setShowExportModal(false);
  };

  // OWASP-compliant security audit
  const runSecurityAudit = () => {
    const issues: any[] = [];
    const warnings: any[] = [];
    const recommendations: any[] = [];
    let score = 100;

    const cookie = editingCookie;

    // Check 1: Secure flag (OWASP requirement)
    if (!cookie.secure) {
      issues.push({
        severity: "HIGH",
        title: "Missing Secure Flag",
        description:
          "Cookie can be transmitted over unencrypted HTTP connections",
        impact: "Vulnerable to man-in-the-middle attacks and eavesdropping",
        fix: "Enable the Secure flag to ensure HTTPS-only transmission",
        owasp: "OWASP Session Management - A02:2021 Cryptographic Failures",
      });
      score -= 25;
    }

    // Check 2: HttpOnly flag (XSS protection)
    if (!cookie.httpOnly) {
      issues.push({
        severity: "HIGH",
        title: "Missing HttpOnly Flag",
        description: "Cookie is accessible via JavaScript (document.cookie)",
        impact: "Vulnerable to Cross-Site Scripting (XSS) attacks",
        fix: "Enable the HttpOnly flag to prevent JavaScript access",
        owasp: "OWASP Session Management - A03:2021 Injection",
      });
      score -= 25;
    }

    // Check 3: SameSite attribute (CSRF protection)
    if (!cookie.sameSite || cookie.sameSite === "None") {
      if (cookie.sameSite === "None" && cookie.secure) {
        warnings.push({
          severity: "MEDIUM",
          title: "SameSite=None Detected",
          description: "Cookie allows cross-site requests",
          impact: "Potential CSRF vulnerability if not properly validated",
          fix: "Consider using SameSite=Strict or Lax unless third-party access is required",
          owasp: "OWASP CSRF Prevention",
        });
        score -= 10;
      } else if (cookie.sameSite === "None" && !cookie.secure) {
        issues.push({
          severity: "CRITICAL",
          title: "SameSite=None Without Secure",
          description: "SameSite=None requires Secure flag",
          impact: "Cookie will be rejected by modern browsers",
          fix: "Enable Secure flag or change SameSite to Lax/Strict",
          owasp: "RFC 6265bis Section 5.4.7",
        });
        score -= 30;
      } else {
        warnings.push({
          severity: "MEDIUM",
          title: "Missing SameSite Attribute",
          description: "Browser will use default (Lax), but explicit is better",
          impact: "Inconsistent behavior across browsers",
          fix: "Explicitly set SameSite=Strict or Lax",
          owasp: "OWASP Session Management Best Practices",
        });
        score -= 10;
      }
    } else if (cookie.sameSite === "Lax") {
      recommendations.push({
        severity: "INFO",
        title: "Consider SameSite=Strict",
        description: "SameSite=Lax allows some cross-site requests",
        impact: "Slightly weaker CSRF protection than Strict",
        fix: "Use SameSite=Strict for sensitive operations (banking, admin)",
        owasp: "OWASP Defense in Depth",
      });
    }

    // Check 4: Cookie size (RFC 6265bis limit)
    const cookieSize = (cookie.name?.length || 0) + (cookie.value?.length || 0);
    if (cookieSize > 4096) {
      issues.push({
        severity: "HIGH",
        title: "Cookie Size Exceeds RFC Limit",
        description: `Cookie is ${cookieSize} bytes (max: 4096 bytes)`,
        impact: "Cookie may be rejected by browsers or truncated",
        fix: "Reduce cookie size or split into multiple cookies",
        owasp: "RFC 6265bis Section 5.7",
      });
      score -= 20;
    } else if (cookieSize > 3000) {
      warnings.push({
        severity: "LOW",
        title: "Large Cookie Size",
        description: `Cookie is ${cookieSize} bytes (approaching 4096 limit)`,
        impact: "May cause performance issues",
        fix: "Consider reducing cookie size",
        owasp: "Performance Best Practices",
      });
      score -= 5;
    }

    // Check 5: Cookie prefix validation
    if (cookie.name?.startsWith("__Host-")) {
      if (!cookie.secure) {
        issues.push({
          severity: "CRITICAL",
          title: "__Host- Prefix Violation",
          description: "__Host- prefix requires Secure flag",
          impact: "Cookie will be rejected by browsers",
          fix: "Enable Secure flag",
          owasp: "RFC 6265bis Section 4.1.3.2",
        });
        score -= 30;
      }
      if (cookie.path !== "/") {
        issues.push({
          severity: "CRITICAL",
          title: "__Host- Prefix Violation",
          description: "__Host- prefix requires Path=/",
          impact: "Cookie will be rejected by browsers",
          fix: "Set Path to /",
          owasp: "RFC 6265bis Section 4.1.3.2",
        });
        score -= 30;
      }
      if (cookie.domain) {
        issues.push({
          severity: "CRITICAL",
          title: "__Host- Prefix Violation",
          description: "__Host- prefix must not have Domain attribute",
          impact: "Cookie will be rejected by browsers",
          fix: "Remove Domain attribute",
          owasp: "RFC 6265bis Section 4.1.3.2",
        });
        score -= 30;
      }
    } else if (cookie.name?.startsWith("__Secure-")) {
      if (!cookie.secure) {
        issues.push({
          severity: "CRITICAL",
          title: "__Secure- Prefix Violation",
          description: "__Secure- prefix requires Secure flag",
          impact: "Cookie will be rejected by browsers",
          fix: "Enable Secure flag",
          owasp: "RFC 6265bis Section 4.1.3.1",
        });
        score -= 30;
      }
    }

    // Check 6: Partitioned cookie validation (CHIPS)
    if (cookie.partitioned) {
      if (!cookie.secure) {
        issues.push({
          severity: "HIGH",
          title: "Partitioned Cookie Without Secure",
          description: "CHIPS requires Secure flag",
          impact: "Cookie will be rejected by browsers",
          fix: "Enable Secure flag",
          owasp: "CHIPS Specification",
        });
        score -= 25;
      }
      if (!cookie.name?.startsWith("__Host-")) {
        recommendations.push({
          severity: "INFO",
          title: "CHIPS Best Practice",
          description: "Partitioned cookies should use __Host- prefix",
          impact: "Enhanced security and subdomain isolation",
          fix: "Rename cookie with __Host- prefix",
          owasp: "CHIPS Security Best Practices",
        });
      }
    }

    // Check 7: Domain scope
    if (cookie.domain?.startsWith(".")) {
      warnings.push({
        severity: "MEDIUM",
        title: "Subdomain Cookie Detected",
        description: "Cookie is shared across all subdomains",
        impact: "Increased attack surface if subdomains are compromised",
        fix: "Use exact domain match unless subdomain sharing is required",
        owasp: "OWASP Session Management - Domain Scope",
      });
      score -= 10;
    }

    // Check 8: Expiry validation
    if (cookie.expires && cookie.expires !== -1) {
      const expiryDate = new Date(cookie.expires * 1000);
      const now = new Date();
      const daysUntilExpiry =
        (expiryDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24);

      if (expiryDate < now) {
        issues.push({
          severity: "HIGH",
          title: "Expired Cookie",
          description: "Cookie has already expired",
          impact: "Cookie will be immediately deleted by browser",
          fix: "Update expiry date to future timestamp",
          owasp: "Cookie Lifecycle Management",
        });
        score -= 20;
      } else if (daysUntilExpiry > 365) {
        warnings.push({
          severity: "LOW",
          title: "Long-Lived Cookie",
          description: `Cookie expires in ${Math.round(daysUntilExpiry)} days`,
          impact: "Increased risk if cookie is compromised",
          fix: "Consider shorter expiry for sensitive cookies (30-90 days)",
          owasp: "OWASP Session Timeout Best Practices",
        });
        score -= 5;
      }
    }

    // Ensure score doesn't go below 0
    score = Math.max(0, score);

    // Generate overall rating
    let rating = "";
    let ratingColor = "";
    if (score >= 90) {
      rating = "EXCELLENT";
      ratingColor = "#10b981";
    } else if (score >= 75) {
      rating = "GOOD";
      ratingColor = "#3b82f6";
    } else if (score >= 50) {
      rating = "FAIR";
      ratingColor = "#f59e0b";
    } else if (score >= 25) {
      rating = "POOR";
      ratingColor = "#ef4444";
    } else {
      rating = "CRITICAL";
      ratingColor = "#dc2626";
    }

    setSecurityReport({
      score,
      rating,
      ratingColor,
      issues,
      warnings,
      recommendations,
      cookieName: cookie.name,
      timestamp: new Date().toLocaleString(),
    });
    setShowSecurityAudit(true);
  };

  // Export all cookies in various formats
  const exportAllCookiesInFormat = (format: string) => {
    try {
      const parsedCookies = JSON.parse(cookies);
      let output = "";

      switch (format) {
        case "json":
          // Standard JSON format (current)
          output = JSON.stringify(parsedCookies, null, 2);
          break;

        case "netscape":
          // Netscape cookies.txt format
          output = "# Netscape HTTP Cookie File\n";
          output += "# This is a generated file! Do not edit.\n\n";
          parsedCookies.forEach((cookie: any) => {
            const domain = cookie.domain || "";
            const flag = domain.startsWith(".") ? "TRUE" : "FALSE";
            const path = cookie.path || "/";
            const secure = cookie.secure ? "TRUE" : "FALSE";
            const expiration = cookie.expires || 0;
            const name = cookie.name || "";
            const value = cookie.value || "";
            output += `${domain}\t${flag}\t${path}\t${secure}\t${expiration}\t${name}\t${value}\n`;
          });
          break;

        case "har":
          // HTTP Archive (HAR) format
          const harCookies = parsedCookies.map((cookie: any) => ({
            name: cookie.name || "",
            value: cookie.value || "",
            path: cookie.path || "/",
            domain: cookie.domain || "",
            expires: cookie.expires
              ? new Date(cookie.expires * 1000).toISOString()
              : undefined,
            httpOnly: cookie.httpOnly || false,
            secure: cookie.secure || false,
            sameSite: cookie.sameSite || "Lax",
          }));
          output = JSON.stringify(
            {
              log: {
                version: "1.2",
                creator: {
                  name: "Screenshot Automation Tool",
                  version: "1.0",
                },
                entries: [
                  {
                    request: {
                      cookies: harCookies,
                    },
                  },
                ],
              },
            },
            null,
            2
          );
          break;

        case "csv":
          // CSV format
          output =
            "Name,Value,Domain,Path,Expires,Secure,HttpOnly,SameSite,Partitioned\n";
          parsedCookies.forEach((cookie: any) => {
            const name = (cookie.name || "").replace(/"/g, '""');
            const value = (cookie.value || "").replace(/"/g, '""');
            const domain = (cookie.domain || "").replace(/"/g, '""');
            const path = (cookie.path || "/").replace(/"/g, '""');
            const expires = cookie.expires || "";
            const secure = cookie.secure ? "true" : "false";
            const httpOnly = cookie.httpOnly ? "true" : "false";
            const sameSite = cookie.sameSite || "Lax";
            const partitioned = cookie.partitioned ? "true" : "false";
            output += `"${name}","${value}","${domain}","${path}","${expires}","${secure}","${httpOnly}","${sameSite}","${partitioned}"\n`;
          });
          break;

        case "headers":
          // Set-Cookie headers format
          parsedCookies.forEach((cookie: any) => {
            let header = `Set-Cookie: ${cookie.name}=${cookie.value}`;
            if (cookie.domain) header += `; Domain=${cookie.domain}`;
            if (cookie.path) header += `; Path=${cookie.path}`;
            if (cookie.expires && cookie.expires !== -1) {
              const date = new Date(cookie.expires * 1000);
              header += `; Expires=${date.toUTCString()}`;
            }
            if (cookie.secure) header += `; Secure`;
            if (cookie.httpOnly) header += `; HttpOnly`;
            if (cookie.sameSite) header += `; SameSite=${cookie.sameSite}`;
            if (cookie.partitioned) header += `; Partitioned`;
            output += header + "\n";
          });
          break;

        case "curl-headers":
          // cURL -H format (multiple cookies in one header)
          const cookieStrings = parsedCookies.map(
            (cookie: any) => `${cookie.name}=${cookie.value}`
          );
          output = `curl -H "Cookie: ${cookieStrings.join(
            "; "
          )}" "https://example.com/"`;
          break;

        default:
          output = JSON.stringify(parsedCookies, null, 2);
      }

      return output;
    } catch (error: any) {
      return `Error: ${error.message}`;
    }
  };

  const downloadCookiesInFormat = () => {
    const output = exportAllCookiesInFormat(exportFormat);
    const blob = new Blob([output], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;

    // Set filename based on format
    const extensions: { [key: string]: string } = {
      json: "json",
      netscape: "txt",
      har: "har",
      csv: "csv",
      headers: "txt",
      "curl-headers": "sh",
    };
    a.download = `cookies.${extensions[exportFormat] || "txt"}`;

    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    alert(`✅ Cookies exported as ${exportFormat.toUpperCase()}!`);
    setShowFormatExport(false);
  };

  const copyFormattedCookies = () => {
    const output = exportAllCookiesInFormat(exportFormat);
    navigator.clipboard.writeText(output);
    alert(`✅ ${exportFormat.toUpperCase()} format copied to clipboard!`);
  };

  // Import cookies from various formats
  const importCookiesFromFormat = (format: string, content: string) => {
    try {
      let parsedCookies: any[] = [];

      switch (format) {
        case "json":
          parsedCookies = JSON.parse(content);
          break;

        case "netscape":
          // Parse Netscape cookies.txt format
          const lines = content.split("\n");
          parsedCookies = lines
            .filter((line) => line.trim() && !line.startsWith("#"))
            .map((line) => {
              const parts = line.split("\t");
              if (parts.length >= 7) {
                return {
                  domain: parts[0],
                  path: parts[2],
                  secure: parts[3] === "TRUE",
                  expires: parseInt(parts[4]) || -1,
                  name: parts[5],
                  value: parts[6],
                  httpOnly: false,
                  sameSite: "Lax",
                };
              }
              return null;
            })
            .filter((cookie) => cookie !== null);
          break;

        case "har":
          // Parse HAR format
          const har = JSON.parse(content);
          const harCookies = har?.log?.entries?.[0]?.request?.cookies || [];
          parsedCookies = harCookies.map((cookie: any) => ({
            name: cookie.name,
            value: cookie.value,
            domain: cookie.domain || "",
            path: cookie.path || "/",
            expires: cookie.expires
              ? Math.floor(new Date(cookie.expires).getTime() / 1000)
              : -1,
            secure: cookie.secure || false,
            httpOnly: cookie.httpOnly || false,
            sameSite: cookie.sameSite || "Lax",
            partitioned: false,
          }));
          break;

        case "csv":
          // Parse CSV format
          const csvLines = content.split("\n");
          parsedCookies = csvLines
            .slice(1) // Skip header
            .filter((line) => line.trim())
            .map((line) => {
              // Simple CSV parser (handles quoted values)
              const values = line.match(/(".*?"|[^",\s]+)(?=\s*,|\s*$)/g) || [];
              const cleanValues = values.map((v) =>
                v.replace(/^"|"$/g, "").replace(/""/g, '"')
              );

              if (cleanValues.length >= 7) {
                return {
                  name: cleanValues[0],
                  value: cleanValues[1],
                  domain: cleanValues[2],
                  path: cleanValues[3],
                  expires: cleanValues[4] ? parseInt(cleanValues[4]) : -1,
                  secure: cleanValues[5] === "true",
                  httpOnly: cleanValues[6] === "true",
                  sameSite: cleanValues[7] || "Lax",
                  partitioned: cleanValues[8] === "true",
                };
              }
              return null;
            })
            .filter((cookie) => cookie !== null);
          break;

        default:
          throw new Error("Unsupported format");
      }

      setCookies(JSON.stringify(parsedCookies, null, 2));
      setShowFormatImport(false);
      alert(
        `✅ Successfully imported ${
          parsedCookies.length
        } cookies from ${format.toUpperCase()} format!`
      );
    } catch (error: any) {
      alert(`❌ Import failed: ${error.message}`);
    }
  };

  // Handle file upload for import
  const handleImportFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (e) => {
      const content = e.target?.result as string;
      importCookiesFromFormat(importFormat, content);
    };
    reader.readAsText(file);
  };

  // Beautify/format cookies JSON
  const beautifyCookies = () => {
    if (!cookies.trim()) {
      alert("No cookies to beautify!");
      return;
    }

    try {
      const parsed = JSON.parse(cookies);
      const beautified = JSON.stringify(parsed, null, 2);
      setCookies(beautified);
      addLog("✨ Cookies beautified successfully!");
    } catch (e) {
      alert("❌ Cannot beautify - Invalid JSON format!");
    }
  };

  // Validate and show cookie details
  const _validateCookies = () => { // Reserved for future cookie validation
    if (!cookies.trim()) {
      alert("⚠️ No cookies to validate!");
      return;
    }

    try {
      const parsed = JSON.parse(cookies);

      if (!Array.isArray(parsed)) {
        alert(
          '⚠️ JSON is valid but not an array of cookies.\n\nExpected format:\n[\n  { "name": "...", "value": "...", ... }\n]'
        );
        return;
      }

      if (parsed.length === 0) {
        alert("⚠️ Cookie array is empty!");
        return;
      }

      // Analyze cookies
      const cookieNames = parsed.map((c) => c.name || "unnamed");
      const domains = [...new Set(parsed.map((c) => c.domain || "no domain"))];
      const httpOnlyCount = parsed.filter((c) => c.httpOnly === true).length;
      const secureCount = parsed.filter((c) => c.secure === true).length;

      const message = `✅ Valid JSON! Cookie Analysis:

📊 Total Cookies: ${parsed.length}
🏷️  Cookie Names: ${cookieNames.join(", ")}

🌐 Domains: ${domains.join(", ")}

🔒 Security:
  - HttpOnly: ${httpOnlyCount}/${parsed.length}
  - Secure: ${secureCount}/${parsed.length}

${
  httpOnlyCount === 0
    ? "\n⚠️ WARNING: No HttpOnly cookies found!\nYou may be missing authentication cookies.\nUse Cookie Editor extension to get ALL cookies."
    : "✅ HttpOnly cookies found - good for authentication!"
}`;

      alert(message);
      addLog(`✓ Validated ${parsed.length} cookies`);
    } catch (e) {
      alert(
        `❌ Invalid JSON format!\n\nError: ${getErrorMessage(e)}\n\nPlease check your cookies and try again.`
      );
    }
  };

  // Beautify/format localStorage JSON
  const _beautifyLocalStorage = () => { // Reserved for future localStorage formatting
    if (!localStorageData.trim()) {
      alert("No localStorage data to beautify!");
      return;
    }

    try {
      const parsed = JSON.parse(localStorageData);
      const beautified = JSON.stringify(parsed, null, 2);
      setLocalStorageData(beautified);
      addLog("✨ localStorage beautified successfully!");
    } catch (e) {
      alert("❌ Cannot beautify - Invalid JSON format!");
    }
  };

  // Validate and show localStorage details
  const _validateLocalStorage = () => { // Reserved for future localStorage validation
    if (!localStorageData.trim()) {
      alert("⚠️ No localStorage data to validate!");
      return;
    }

    try {
      const parsed = JSON.parse(localStorageData);

      if (typeof parsed !== "object" || Array.isArray(parsed)) {
        alert(
          '⚠️ JSON is valid but not an object.\n\nExpected format:\n{\n  "key1": "value1",\n  "key2": "value2"\n}'
        );
        return;
      }

      if (Object.keys(parsed).length === 0) {
        alert("⚠️ localStorage object is empty!");
        return;
      }

      // Analyze localStorage
      const keys = Object.keys(parsed);
      const tokenKeys = keys.filter(
        (k) =>
          k.toLowerCase().includes("token") || k.toLowerCase().includes("auth")
      );

      const message = `✅ Valid JSON! localStorage Analysis:

📊 Total Items: ${keys.length}
🔑 Keys: ${keys.slice(0, 10).join(", ")}${
        keys.length > 10 ? ` ... and ${keys.length - 10} more` : ""
      }

🎯 Auth-related Keys Found: ${tokenKeys.length}
${
  tokenKeys.length > 0
    ? `  - ${tokenKeys.join("\n  - ")}`
    : "  (No keys with 'token' or 'auth' in name)"
}

${
  tokenKeys.length > 0
    ? "✅ Looks good for authentication!"
    : "⚠️ No obvious auth tokens found. Make sure you exported from a logged-in session."
}`;

      alert(message);
      addLog(`✓ Validated ${keys.length} localStorage items`);
    } catch (e) {
      alert(
        `❌ Invalid JSON format!\n\nError: ${getErrorMessage(e)}\n\nPlease check your localStorage data and try again.`
      );
    }
  };

  // Session management
  interface Screenshot {
    filename: string;
    path: string;
    url: string;
    timestamp: string;
    quality_score?: number;
    segments?: number;
  }

  interface Session {
    id: string;
    name: string;
    defaultName: string;
    timestamp: string;
    screenshots: Screenshot[];
    urls: string[];
    duration: number;
    settings: {
      captureMode: string;
      useStealth: boolean;
      useRealBrowser: boolean;
    };
  }

  // ✅ FIXED (Bug #14): Session state now at top of component (line 143)
  const [editingSessionId, setEditingSessionId] = useState<string | null>(null);
  const [editingSessionName, setEditingSessionName] = useState("");
  const [sessionNameError, setSessionNameError] = useState("");

  // URL Folder management
  interface URLFolder {
    id: string;
    name: string;
    urls: string[];
    created: string;
    updated: string;
  }

  // URL folders array - debounced for performance when organizing URLs
  const [urlFolders, setUrlFolders] = useDebouncedLocalStorage<URLFolder[]>(
    "screenshot-url-folders",
    [],
    500
  );

  // Persist which URL folders are expanded/collapsed across sessions
  const [expandedFolders, setExpandedFolders] = useLocalStorageWithSerializer<
    Set<string>
  >(
    "screenshot-expanded-folders",
    new Set<string>(),
    serializeStringSet,
    deserializeStringSet
  );
  const [editingFolderId, setEditingFolderId] = useState<string | null>(null);
  const [editingFolderName, setEditingFolderName] = useState("");
  const [folderNameError, setFolderNameError] = useState("");
  const [editingUrlId, setEditingUrlId] = useState<string | null>(null);
  const [editingUrlValue, setEditingUrlValue] = useState("");
  const [newFolderName, setNewFolderName] = useState("");
  const [bulkUrlInput, setBulkUrlInput] = useState<{
    [folderId: string]: string;
  }>({});
  const [selectedUrls, setSelectedUrls] = useState<{
    [folderId: string]: Set<number>;
  }>({});
  const [searchQuery, setSearchQuery] = useState<{
    [folderId: string]: string;
  }>({});
  const [sortOrder, setSortOrder] = useState<{
    [folderId: string]: "date-desc" | "date-asc" | "alpha-asc" | "alpha-desc";
  }>({});

  // Refs for scroll synchronization
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineNumbersRef = useRef<HTMLDivElement>(null);

  // Advanced segmented settings (persist expanded/collapsed state)
  const [showAdvanced, setShowAdvanced] = useLocalStorage(
    "screenshot-segment-showadvanced",
    false
  );
  const [segmentOverlap, setSegmentOverlap] = useLocalStorage(
    "screenshot-segment-overlap",
    20
  );
  const [segmentScrollDelay, setSegmentScrollDelay] = useLocalStorage(
    "screenshot-segment-scrolldelay",
    1000
  );
  const [segmentMaxSegments, setSegmentMaxSegments] = useLocalStorage(
    "screenshot-segment-maxsegments",
    50
  );
  const [segmentSkipDuplicates, setSegmentSkipDuplicates] = useLocalStorage(
    "screenshot-segment-skipduplicates",
    true
  );
  const [segmentSmartLazyLoad, setSegmentSmartLazyLoad] = useLocalStorage(
    "screenshot-segment-smartlazyload",
    true
  );

  // Dark mode state
  const [darkMode, setDarkMode] = useLocalStorage("screenshot-darkmode", false);

  // Animation trigger for mode toggle
  const [isToggling, setIsToggling] = useState(false);

  // Logs visibility and status
  const [_showLogs, _setShowLogs] = useState(false); // Reserved for future log panel toggle
  const [hasErrors, setHasErrors] = useState(false);

  // Sidebar visibility (left panel) - persisted across sessions
  const [isLeftPanelVisible, setIsLeftPanelVisible] = useLocalStorage(
    "screenshot-left-panel-visible",
    true
  );

  // ✅ FIX: Define addLog early so it can be used by all functions
  // ⚡ OPTIMIZATION: Wrap with useCallback to prevent recreation on every render
  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const newLog = `[${timestamp}] ${message}`;
    setLogs((prev) => [...prev, newLog]);

    // Check if this log contains REAL error indicators (more strict)
    // Only detect actual errors, not success messages with "failed" in context
    // Exclude summary lines that show "Failed: 0" or similar
    const isSummaryLine =
      message.includes("Success:") && message.includes("Failed:");

    const isActualError =
      !isSummaryLine &&
      (message.includes("❌") ||
        message.toLowerCase().includes("error:") ||
        message.toLowerCase().includes("failed:") ||
        message.toLowerCase().includes("exception:") ||
        (message.toLowerCase().includes("error") &&
          !message.includes("✅") &&
          !message.toLowerCase().includes("no error")));

    if (isActualError) {
      setHasErrors(true);
      // DO NOT auto-show logs - let user click to see them
    }
  }, []); // ✅ No dependencies - stable function

  // Backend restart state
  const [isRestartingBackend, setIsRestartingBackend] = useState(false);
  const [restartMessage, setRestartMessage] = useState<string | null>(null);

  // ✅ MONOLITH: Simple services status state (Backend + Frontend only)
  const [showServicesDetail, setShowServicesDetail] = useState(false);
  const [servicesStatus, setServicesStatus] = useState({
    backend: 'checking' as 'online' | 'offline' | 'checking',
    frontend: 'checking' as 'online' | 'offline' | 'checking'
  });

  // Derived backend status for Settings tab indicator
  const backendStatusIcon = isRestartingBackend
    ? "🔄"
    : systemUsage && systemUsage.status === "success"
    ? "🟢"
    : systemUsage && systemUsage.status === "error"
    ? "🔴"
    : "⏳";

  const backendStatusText = isRestartingBackend
    ? "Restarting…"
    : systemUsage && systemUsage.status === "success"
    ? "Online"
    : systemUsage && systemUsage.status === "error"
    ? "Offline / Unavailable"
    : "Checking…";

  // ✅ MONOLITH: Health check for backend + frontend only (microservices removed)
  useEffect(() => {
    const checkService = async (url: string): Promise<boolean> => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 3000);

        const response = await fetch(url, {
          method: 'GET',
          signal: controller.signal
        });

        clearTimeout(timeoutId);
        return response.ok;
      } catch (error) {
        return false;
      }
    };

    const checkAllServices = async () => {
      const results = await Promise.allSettled([
        checkService('http://localhost:8001/health'),
        checkService('http://localhost:5173')
      ]);

      setServicesStatus({
        backend: results[0].status === 'fulfilled' && results[0].value ? 'online' : 'offline',
        frontend: results[1].status === 'fulfilled' && results[1].value ? 'online' : 'offline'
      });
    };

    // Check immediately
    checkAllServices();

    // Check every 10 seconds
    const interval = setInterval(checkAllServices, 10000);

    return () => clearInterval(interval);
  }, []);

  // ✅ FIXED (Bug #14): activeTab now in AppContext (line 137-138)
  const [openTabs, setOpenTabs] = useState<
    Array<
      | "main"
      | "sessions"
      | "urls"
      | "cookies"
      | "network"
      | "settings"
      | "logs"
      | "keyword-config"
      | "tiles"
    >
  >(["main", "sessions", "urls", "tiles"]); // Main, Sessions, URLs, and Tiles are permanent tabs

  // Tiles department toggles state
  const [partsEnabled, setPartsEnabled] = useState(false);
  const [serviceEnabled, setServiceEnabled] = useState(false);
  const [accountingEnabled, setAccountingEnabled] = useState(false);
  const [crmEnabled, setCrmEnabled] = useState(true);  // ✅ CRM enabled by default

  // Map tabs to URL path segments for deep-linkable URLs
  const getTabPathSegment = (
    tab:
      | "main"
      | "sessions"
      | "urls"
      | "cookies"
      | "network"
      | "settings"
      | "logs"
      | "keyword-config"
      | "tiles"
  ) => {
    switch (tab) {
      case "main":
        return "main";
      case "sessions":
      case "urls":
      case "cookies":
      case "network":
      case "settings":
      case "logs":
      case "keyword-config":
      case "tiles":
        return tab;
      default:
        return "main";
    }
  };

  // Keep browser URL in sync with the currently active tab
  const updateUrlForTab = (
    tab:
      | "main"
      | "sessions"
      | "urls"
      | "cookies"
      | "network"
      | "settings"
      | "logs"
      | "keyword-config"
  ) => {
    if (typeof window === "undefined" || !window.history?.pushState) {
      return;
    }

    const segment = getTabPathSegment(tab);
    const newPath = segment ? `/${segment}` : "/";
    const search = window.location.search || "";
    const hash = window.location.hash || "";

    // ✅ FIX: Use pushState instead of replaceState to enable browser Back/Forward navigation
    window.history.pushState(null, "", `${newPath}${search}${hash}`);
  };

  // ✅ FIXED (Bug #14): Use context's setActiveTab with logging wrapper
  const switchTab = useCallback((
    tab:
      | "main"
      | "sessions"
      | "urls"
      | "cookies"
      | "network"
      | "settings"
      | "logs"
      | "keyword-config"
      | "tiles"
  ) => {
    const tabNames = {
      main: "Main",
      sessions: "Sessions",
      urls: "URLs",
      cookies: "Cookies",
      network: "Network",
      settings: "Settings",
      logs: "Logs",
      "keyword-config": "Keyword Config",
      tiles: "Tiles",
    };
    console.log(`🔄 switchTab called with: "${tab}"`);
    setActiveTab(tab);
    console.log(`✅ setActiveTab("${tab}") called`);
    updateUrlForTab(tab);

    // Add log AFTER state update to avoid infinite loop
    const timestamp = new Date().toLocaleTimeString();
    const newLog = `[${timestamp}] 📑 Switched to ${tabNames[tab]} tab`;
    setLogs((prev) => [...prev, newLog]);
  }, []); // ✅ No dependencies to avoid infinite loop

  // Helper function to parse URL pathname to tab name
  const getTabFromPath = useCallback(():
    | "main"
    | "sessions"
    | "urls"
    | "cookies"
    | "network"
    | "settings"
    | "logs"
    | "keyword-config" => {
    if (typeof window === "undefined") return "main";

    const path = window.location.pathname.replace(/\/+$/, "");
    const segment = path.split("/").filter(Boolean)[0] || "";

    if (
      segment === "sessions" ||
      segment === "urls" ||
      segment === "cookies" ||
      segment === "network" ||
      segment === "settings" ||
      segment === "logs" ||
      segment === "keyword-config"
    ) {
      return segment as any;
    }

    return "main";
  }, []);

  // ========================================
  // 🌐 ENHANCED URL ROUTING - Support for multi-app architecture
  // ========================================

  /**
   * Parse URL to determine which app and tab should be active
   * Supports:
   * - / = home (no app)
   * - /#screenshots/main = Screenshots app, main tab
   * - /#business-apps/crm = Business Apps, CRM tab
   */
  const parseUrlToAppAndTab = useCallback((): { app: string | null; tab: string } => {
    if (typeof window === "undefined") return { app: null, tab: "main" };

    const hash = window.location.hash.slice(1); // Remove '#'
    const parts = hash.split("/").filter(Boolean);

    if (parts.length === 0) {
      // No hash = home page
      return { app: null, tab: "main" };
    }

    const appId = parts[0]; // 'screenshots' or 'business-apps'
    const tabId = parts[1] || "main"; // Default to 'main' if no tab specified

    // Map app-specific default tabs
    if (appId === 'business-apps' && !parts[1]) {
      return { app: appId, tab: 'crm' }; // Business Apps defaults to CRM
    }

    return { app: appId, tab: tabId };
  }, []);

  /**
   * Update URL to reflect current app and tab
   * Creates shareable, bookmarkable URLs
   */
  const updateUrlForAppAndTab = useCallback((app: string | null, tab: string) => {
    if (typeof window === "undefined" || !window.history?.pushState) {
      return;
    }

    let newHash = '';
    if (app === null) {
      // Home page - no hash
      newHash = '';
    } else if (app === 'screenshots') {
      // Screenshots app uses traditional routing (for now, keep backward compat)
      // /#screenshots/main, /#screenshots/sessions, etc.
      newHash = `#${app}/${tab}`;
    } else if (app === 'business-apps') {
      // Business Apps routing
      // /#business-apps/crm, /#business-apps/parts, etc.
      newHash = `#${app}/${tab}`;
    }

    const newUrl = `/${newHash}`;
    window.history.pushState(null, "", newUrl);

    console.log(`🔗 URL updated: ${newUrl}`);
  }, []);

  // On initial load, read the URL path and activate the matching tab
  useEffect(() => {
    if (typeof window === "undefined") return;

    const initialTab = getTabFromPath();

    // Ensure optional tabs (settings, logs, keyword-config) are opened if deep-linked
    if (initialTab !== "main") {
      setOpenTabs((prev) =>
        prev.includes(initialTab) ? prev : [...prev, initialTab]
      );
    }

    switchTab(initialTab);
  }, [switchTab, getTabFromPath]);

  // ✅ FIX: Listen for browser Back/Forward navigation (popstate event)
  // This restores the navigation contract: browser navigation now works correctly
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handlePopState = () => {
      const tab = getTabFromPath();

      // Ensure optional tabs are opened when navigating via browser buttons
      if (tab !== "main") {
        setOpenTabs((prev) =>
          prev.includes(tab) ? prev : [...prev, tab]
        );
      }

      // Update active tab without calling updateUrlForTab (URL is already updated by browser)
      setActiveTab(tab);

      const tabNames = {
        main: "Main",
        sessions: "Sessions",
        urls: "URLs",
        cookies: "Cookies",
        network: "Network",
        settings: "Settings",
        logs: "Logs",
        "keyword-config": "Keyword Config",
      };

      const timestamp = new Date().toLocaleTimeString();
      const newLog = `[${timestamp}] ⬅️ Navigated to ${tabNames[tab]} tab (browser Back/Forward)`;
      setLogs((prev) => [...prev, newLog]);
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, [getTabFromPath, setActiveTab, setLogs]);

  // ✅ NEW: Initialize app and tab from URL on page load
  useEffect(() => {
    if (typeof window === "undefined") return;

    const { app, tab } = parseUrlToAppAndTab();
    console.log(`🔗 Initial URL parse: app="${app}", tab="${tab}"`);

    // Set the current app
    if (app) {
      setCurrentApp(app);
      console.log(`✅ Set current app to: ${app}`);
    } else {
      setCurrentApp(null);
      console.log(`✅ Set current app to: home (null)`);
    }

    // Set the active tab
    setActiveTab(tab as any);
    console.log(`✅ Set active tab to: ${tab}`);
  }, []); // Run only once on mount

  // ✅ NEW: Handle browser Back/Forward for multi-app navigation
  useEffect(() => {
    if (typeof window === "undefined") return;

    const handleHashChange = () => {
      const { app, tab } = parseUrlToAppAndTab();
      console.log(`🔗 Hash changed: app="${app}", tab="${tab}"`);

      setCurrentApp(app);
      setActiveTab(tab as any);

      const timestamp = new Date().toLocaleTimeString();
      const appName = app === 'screenshots' ? 'Screenshots' : app === 'business-apps' ? 'Business Apps' : 'Home';
      const newLog = `[${timestamp}] ⬅️ Navigated to ${appName} → ${tab} (browser navigation)`;
      setLogs((prev) => [...prev, newLog]);
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [parseUrlToAppAndTab, setCurrentApp, setActiveTab, setLogs]);

  // Tekion Logo Removal state
  const [removalJobId, setRemovalJobId] = useState<string | null>(null);
  const [removalProgress, setRemovalProgress] = useState<any>(null);
  const [removalStatus, setRemovalStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');

  // ✅ Settings modal state
  const [showLogoRemovalSettings, setShowLogoRemovalSettings] = useState(false);
  const [logoRemovalMaxRows, setLogoRemovalMaxRows] = useState<number>(200); // Default 200 rows
  const [logoRemovalCustomLimit, setLogoRemovalCustomLimit] = useState<string>(''); // Custom template limit (empty = all)
  const [keepTabsOpen, setKeepTabsOpen] = useState<boolean>(false); // ✅ NEW: Keep tabs open for verification

  // 🔧 FIX: Track WebSocket and AbortController for cleanup
  const logoRemovalWsRef = useRef<WebSocket | null>(null);
  const logoRemovalAbortControllerRef = useRef<AbortController | null>(null);

  // 🔧 FIX: Cleanup logo removal resources on unmount
  useEffect(() => {
    return () => {
      if (logoRemovalWsRef.current) {
        logoRemovalWsRef.current.close();
        logoRemovalWsRef.current = null;
      }
      if (logoRemovalAbortControllerRef.current) {
        logoRemovalAbortControllerRef.current.abort();
        logoRemovalAbortControllerRef.current = null;
      }
    };
  }, []);

  // Handler for Tekion Logo Removal button click - show settings modal
  const handleTekionLogoRemovalClick = () => {
    if (!crmEnabled) {
      alert('Please enable the CRM toggle first!');
      return;
    }
    setShowLogoRemovalSettings(true);
  };

  // Handler for Logo Addition button click - navigate to CRM tab
  const handleLogoAdditionClick = () => {
    if (!crmEnabled) {
      alert('Please enable the CRM toggle first!');
      return;
    }
    // Switch to Business Apps and CRM tab
    setCurrentApp('business-apps');
    switchTab('crm');
    addLog('✨ Navigated to Logo Addition feature');
  };

  // Handler to start the actual logo removal process
  const startTekionLogoRemoval = async () => {
    // Close the settings modal
    setShowLogoRemovalSettings(false);

    // ✅ FIXED: Hardcoded preprod URL - no need to ask user
    const baseUrl = 'https://preprodapp.tekioncloud.com';

    // 🔧 FIX: Cleanup previous WebSocket and AbortController if they exist
    if (logoRemovalWsRef.current) {
      logoRemovalWsRef.current.close();
      logoRemovalWsRef.current = null;
    }
    if (logoRemovalAbortControllerRef.current) {
      logoRemovalAbortControllerRef.current.abort();
    }

    try {
      console.log('🚀 Starting Tekion Logo Removal...');
      setRemovalStatus('running');

      // ✅ Clear old logs and start fresh
      clearLogs();
      addLog('🎨 ========================================');
      addLog('🎨 Tekion Logo Removal - Starting...');
      addLog('🎨 ========================================');
      addLog(`🌐 Base URL: ${baseUrl}`);
      addLog(`⚡ Connecting to backend...`);

      // Start the removal job with settings
      const customLimit = logoRemovalCustomLimit ? parseInt(logoRemovalCustomLimit) : undefined;

      // 🔧 FIX: Create AbortController for fetch cancellation
      logoRemovalAbortControllerRef.current = new AbortController();

      // 🔧 FIX: Use config.apiBaseUrl instead of hardcoded URL
      const response = await fetch(`${config.apiBaseUrl}/api/templates/start-logo-removal`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          base_url: baseUrl,
          max_rows: logoRemovalMaxRows,  // Max rows to fetch from API
          custom_limit: customLimit,  // Custom limit on how many to process
          keep_tabs_open: keepTabsOpen  // ✅ Keep tabs open for verification
        }),
        signal: logoRemovalAbortControllerRef.current.signal,  // 🔧 FIX: Add abort signal
      });

      const data = await response.json();
      const jobId = data.job_id;
      setRemovalJobId(jobId);

      console.log('✅ Job started:', jobId);
      addLog(`✅ Job started: ${jobId}`);

      // 🔧 FIX: Use config for WebSocket URL and track in ref
      const wsUrl = `ws://${config.apiBaseUrl.replace('http://', '').replace('https://', '')}/ws/template-removal/${jobId}`;
      const ws = new WebSocket(wsUrl);
      logoRemovalWsRef.current = ws;  // 🔧 FIX: Track for cleanup

      // Track which log index we've already displayed
      let lastLogIndex = 0;

      ws.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        console.log('Progress update:', progress);
        setRemovalProgress(progress);

        // ✅ FIXED: Only display NEW logs (not already shown)
        if (progress.logs && Array.isArray(progress.logs)) {
          const newLogs = progress.logs.slice(lastLogIndex);
          newLogs.forEach((logMessage: string) => {
            // Remove the timestamp prefix from backend (we add our own)
            const cleanMessage = logMessage.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
            addLog(cleanMessage);
          });
          lastLogIndex = progress.logs.length;
        }

        if (progress.status === 'completed') {
          setRemovalStatus('completed');
          addLog(`✅ Logo removal complete! Successful: ${progress.successful}/${progress.total}, Failed: ${progress.failed}`);

          // ✅ Show Excel report download link if available
          if (progress.excel_report) {
            addLog(`📊 Excel report generated: ${progress.excel_report}`);
            addLog(`📥 Download: http://localhost:8000/reports/${progress.excel_report.split('/').pop()}`);
          }

          let alertMsg = `✅ Complete!\n\nSuccessfully processed: ${progress.successful}/${progress.total}\nFailed: ${progress.failed}/${progress.total}`;
          if (progress.excel_report) {
            alertMsg += `\n\n📊 Excel report available in backend/reports/`;
          }
          alert(alertMsg);
          ws.close();
          logoRemovalWsRef.current = null;  // 🔧 FIX: Clear ref on close
        } else if (progress.status === 'failed') {
          setRemovalStatus('failed');
          addLog('❌ Logo removal job failed');
          alert('❌ Job failed. Check the Logs tab for details.');
          ws.close();
          logoRemovalWsRef.current = null;  // 🔧 FIX: Clear ref on close
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setRemovalStatus('failed');
        // Don't close here - let onclose handle cleanup
      };

      ws.onclose = () => {
        console.log('WebSocket closed');
        logoRemovalWsRef.current = null;  // 🔧 FIX: Clear ref on close
      };

    } catch (error: any) {
      // 🔧 FIX: Don't show error if request was aborted (intentional cancellation)
      if (error?.name === 'AbortError') {
        console.log('Logo removal request aborted');
        setRemovalStatus('idle');
        return;
      }

      console.error('Error starting removal:', error);
      setRemovalStatus('failed');
      alert('❌ Error starting removal job. Check console for details.');
    }
  };

  // Collapsible segments state - track which results have expanded segments
  const [expandedSegments, setExpandedSegments] = useState<Set<number>>(
    new Set()
  );

  // URL tooltip state - track which URL is being hovered and clicked
  const [hoveredUrl, setHoveredUrl] = useState<number | null>(null);
  const [clickedUrl, setClickedUrl] = useState<number | null>(null);
  const [hoverTimeout, setHoverTimeout] = useState<NodeJS.Timeout | null>(null);
  const [clickTimeout, setClickTimeout] = useState<NodeJS.Timeout | null>(null);

  // Save URLs to localStorage - handled by useDebouncedLocalStorage hook (500ms debounce)
  // This reduces localStorage I/O by ~99% (100+ writes → 1 write per edit session!)

  // Save settings to localStorage - handled by useLocalStorage hook for:
  // captureMode, useStealth, useRealBrowser, browserEngine, baseUrl

  // Save text inputs to localStorage - handled by useDebouncedLocalStorage hook (500ms debounce):
  // wordsToRemove, cookies, localStorageData
  // This reduces localStorage I/O by ~98% for these frequently-edited fields!

  // Save complex objects to localStorage - handled by useDebouncedLocalStorage hook (500ms debounce):
  // sessions, urlFolders
  // This reduces localStorage I/O by ~90% when creating/editing sessions and organizing URLs!

  // Save advanced segmented settings - handled by useLocalStorage hook for:
  // segmentOverlap, segmentScrollDelay, segmentMaxSegments, segmentSkipDuplicates, segmentSmartLazyLoad

  // Apply dark mode class to body (localStorage save handled by useLocalStorage hook)
  useEffect(() => {
    if (darkMode) {
      document.body.classList.add("dark-mode");
    } else {
      document.body.classList.remove("dark-mode");
    }
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    // Trigger celebration animation
    setIsToggling(true);
    setTimeout(() => {
      setIsToggling(false);
    }, 1000); // Animation lasts 1 second
  };

  const toggleSegmentExpansion = (index: number) => {
    setExpandedSegments((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  // ✅ Parse word transformation input (supports: word, word:"", word:"space", word:"custom")
  const parseWordInput = (input: string): WordTransformation | null => {
    const trimmed = input.trim();
    if (!trimmed) return null;

    // Match: word:"replacement" syntax
    const match = trimmed.match(/^(.+?):"(.*)"$/);

    if (match) {
      const word = match[1].trim();
      const replacement = match[2]; // Can be empty string, "space", or custom text

      if (!word) return null;

      if (replacement === "") {
        return { word, replacement: "", type: "remove" };
      } else if (replacement === "space") {
        return { word, replacement: " ", type: "space" };
      } else {
        return { word, replacement, type: "custom" };
      }
    }

    // Default: replace with space (backward compatible)
    return { word: trimmed, replacement: " ", type: "space" };
  };

  // Add word transformation to list
  const addWordToRemove = (input: string) => {
    const transformation = parseWordInput(input);
    if (!transformation) return;

    // Check if word already exists
    const exists = wordsToRemove.some((t) => t.word === transformation.word);
    if (!exists) {
      const newIndex = wordsToRemove.length;
      setWordsToRemove([...wordsToRemove, transformation]);
      setWordInput("");

      // ✅ Open editor modal immediately after adding
      setTimeout(() => {
        openWordEditor(newIndex);
      }, 100); // Small delay to ensure state is updated
    }
  };

  // Remove word transformation from list
  const removeWordToRemove = (index: number) => {
    setWordsToRemove(wordsToRemove.filter((_, i) => i !== index));
  };

  // Handle word input key press
  const handleWordInputKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter" || e.key === ",") {
      e.preventDefault();
      addWordToRemove(wordInput);
    } else if (
      e.key === "Backspace" &&
      wordInput === "" &&
      wordsToRemove.length > 0
    ) {
      // Remove last tag if backspace on empty input
      removeWordToRemove(wordsToRemove.length - 1);
    }
  };

  // ✅ Open word editor modal (for editing existing transformation)
  const openWordEditor = (index: number) => {
    const transform = wordsToRemove[index];
    setEditingWordIndex(index);
    setEditorWord(transform.word);
    setEditorReplacement(
      transform.type === "space" ? "" : transform.replacement
    );
    setEditorType(transform.type);
    setShowWordEditor(true);
  };

  // ✅ Save word transformation from editor modal
  const saveWordTransformation = () => {
    if (!editorWord.trim()) return;

    const newTransform: WordTransformation = {
      word: editorWord.trim(),
      replacement:
        editorType === "remove"
          ? ""
          : editorType === "space"
          ? " "
          : editorReplacement,
      type: editorType,
    };

    if (editingWordIndex !== null) {
      // Update existing
      const updated = [...wordsToRemove];
      updated[editingWordIndex] = newTransform;
      setWordsToRemove(updated);
    } else {
      // Add new
      const exists = wordsToRemove.some((t) => t.word === newTransform.word);
      if (!exists) {
        setWordsToRemove([...wordsToRemove, newTransform]);
      }
    }

    closeWordEditor();
  };

  // ✅ Close word editor modal
  const closeWordEditor = () => {
    setShowWordEditor(false);
    setEditingWordIndex(null);
    setEditorWord("");
    setEditorReplacement("");
    setEditorType("space");
  };

  // Session management functions
  const createSession = (
    screenshots: Screenshot[],
    captureUrls: string[],
    captureDuration: number
  ) => {
    const sessionNumber = sessions.length + 1;
    const defaultName = `Session ${sessionNumber}`;

    const newSession: Session = {
      id: `session-${Date.now()}`,
      name: defaultName,
      defaultName: defaultName,
      timestamp: new Date().toISOString(),
      screenshots: screenshots,
      urls: captureUrls,
      duration: captureDuration,
      settings: {
        captureMode: captureMode,
        useStealth: useStealth,
        useRealBrowser: useRealBrowser,
      },
    };

    // ✅ OPTIMIZATION: Limit to last 50 sessions to prevent localStorage bloat
    const MAX_SESSIONS = 50;
    const updatedSessions = [newSession, ...sessions].slice(0, MAX_SESSIONS);
    setSessions(updatedSessions);

    if (sessions.length >= MAX_SESSIONS) {
      log.info(
        `🗑️ Removed oldest session to maintain ${MAX_SESSIONS} session limit`
      );
    }

    return newSession;
  };

  const toggleSessionSelection = (sessionId: string) => {
    // ✅ FIX: Get session info BEFORE state update to avoid double logging
    const session = sessions.find((s) => s.id === sessionId);
    const sessionName = session ? session.name : sessionId;
    const isCurrentlySelected = selectedSessions.has(sessionId);

    setSelectedSessions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sessionId)) {
        newSet.delete(sessionId);
      } else {
        newSet.add(sessionId);
      }
      return newSet;
    });

    // ✅ FIX: Log AFTER state update to avoid being called multiple times
    if (isCurrentlySelected) {
      addLog(`☐ Deselected session: ${sessionName}`);
    } else {
      addLog(`☑ Selected session: ${sessionName}`);
    }
  };

  const selectAllSessions = () => {
    setSelectedSessions(new Set(sessions.map((s) => s.id)));
    addLog(`☑ Selected all ${sessions.length} session(s)`);
  };

  const deselectAllSessions = () => {
    setSelectedSessions(new Set());
    addLog(`☐ Deselected all sessions`);
  };

  // ✅ FIX: Track deletion in progress to prevent multiple clicks
  const [isDeletingSession, setIsDeletingSession] = useState(false);
  const isDeletingSessionRef = useRef(false);

  const deleteSelectedSessions = useCallback(async () => {
    // ✅ FIX: Prevent multiple simultaneous deletions using ref (more reliable than state)
    if (isDeletingSessionRef.current || selectedSessions.size === 0) {
      if (selectedSessions.size === 0) {
        addLog(`⚠️ No sessions selected for deletion`);
      }
      log.debug(
        `Skipping deletion - already deleting or no sessions selected`
      );
      return;
    }

    isDeletingSessionRef.current = true;
    setIsDeletingSession(true);
    addLog(`🗑️ Attempting to delete ${selectedSessions.size} session(s)...`);
    log.debug(`About to show confirmation dialog...`);

    try {
      // ✅ FIX: Use custom confirm dialog instead of browser confirm
      log.debug(`Calling custom confirm dialog...`);
      const confirmed = await showCustomConfirm(
        "🗑️ Delete Sessions",
        `Are you sure you want to delete ${selectedSessions.size} selected session(s)?\n\nThis action cannot be undone.`
      );
      log.debug(`Custom confirm returned: ${confirmed}`);

      if (confirmed) {
        log.debug(`User confirmed deletion`);
        const deletedCount = selectedSessions.size;
        const newSessions = sessions.filter((s) => !selectedSessions.has(s.id));

        // ✅ FIX: Write to localStorage BEFORE calling setSessions to avoid race condition
        // This ensures the immediate write happens before the debounced hook's useEffect
        try {
          localStorage.setItem(
            "screenshot-sessions",
            JSON.stringify(newSessions)
          );
          log.info(
            `✅ Deleted ${deletedCount} session(s) - saved to localStorage immediately`
          );
        } catch (error) {
          log.error("Error saving sessions to localStorage:", error);
        }

        // Now update state - the debounced hook will use the latest value from valueRef
        setSessions(newSessions);
        setSelectedSessions(new Set());
        addLog(`✅ Deleted ${deletedCount} session(s) successfully`);
      } else {
        log.debug(`User cancelled deletion`);
        addLog(`❌ Deletion cancelled by user`);
      }
    } catch (error) {
      log.error(`❌ ERROR in deleteSelectedSessions:`, error);
      addLog(`❌ Error during deletion: ${error}`);
    } finally {
      // ✅ FIX: Always reset the deletion flag
      isDeletingSessionRef.current = false;
      setIsDeletingSession(false);
    }
  }, [selectedSessions, sessions, addLog]);

  const startEditingSession = (sessionId: string) => {
    const session = sessions.find((s) => s.id === sessionId);
    if (session) {
      setEditingSessionId(sessionId);
      setEditingSessionName(session.name);
      setSessionNameError("");
      addLog(`✏️ Started editing session: ${session.name}`);
    }
  };

  const cancelEditingSession = () => {
    const session = sessions.find((s) => s.id === editingSessionId);
    if (session) {
      addLog(`❌ Cancelled editing session: ${session.name}`);
    }
    setEditingSessionId(null);
    setEditingSessionName("");
    setSessionNameError("");
  };

  const saveSessionName = (sessionId: string) => {
    const trimmedName = editingSessionName.trim();

    // Check if empty
    if (!trimmedName) {
      setSessionNameError("Session name cannot be empty!");
      return;
    }

    // Check for duplicates (case-insensitive, excluding current session)
    const isDuplicate = sessions.some(
      (s) =>
        s.id !== sessionId && s.name.toLowerCase() === trimmedName.toLowerCase()
    );

    if (isDuplicate) {
      setSessionNameError(
        "Session name already exists! Choose a different name."
      );
      return;
    }

    // Update session name
    const oldSession = sessions.find((s) => s.id === sessionId);
    setSessions(
      sessions.map((s) =>
        s.id === sessionId ? { ...s, name: trimmedName } : s
      )
    );

    if (oldSession) {
      addLog(`✏️ Renamed session: "${oldSession.name}" → "${trimmedName}"`);
    }

    setEditingSessionId(null);
    setEditingSessionName("");
    setSessionNameError("");
  };

  const handleSessionNameKeyDown = (
    e: React.KeyboardEvent<HTMLInputElement>,
    sessionId: string
  ) => {
    if (e.key === "Enter") {
      e.preventDefault();
      saveSessionName(sessionId);
    } else if (e.key === "Escape") {
      e.preventDefault();
      cancelEditingSession();
    }
  };

  // URL Folder Management Functions
  const createFolder = () => {
    const trimmedName = newFolderName.trim();

    if (!trimmedName) {
      alert("Folder name cannot be empty!");
      return;
    }

    // Check for duplicates (case-insensitive)
    const isDuplicate = urlFolders.some(
      (f) => f.name.toLowerCase() === trimmedName.toLowerCase()
    );

    if (isDuplicate) {
      alert("Folder name already exists! Choose a different name.");
      return;
    }

    const newFolder: URLFolder = {
      id: `folder-${Date.now()}`,
      name: trimmedName,
      urls: [],
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
    };

    setUrlFolders([...urlFolders, newFolder]);
    setNewFolderName("");
    setExpandedFolders(new Set([...expandedFolders, newFolder.id]));
    addLog(`📁 Created folder: ${newFolder.name}`);
  };

  // ✅ FIX: Track folder deletion in progress to prevent multiple clicks
  const [isDeletingFolder, setIsDeletingFolder] = useState<string | null>(null);

  const deleteFolder = async (folderId: string) => {
    // ✅ FIX: Prevent multiple simultaneous deletions
    if (isDeletingFolder) return;

    const folder = urlFolders.find((f) => f.id === folderId);
    if (!folder) return;

    setIsDeletingFolder(folderId);

    try {
      log.debug(
        `📁 deleteFolder: Requesting confirmation for ${folder.name}`
      );
      // ✅ Use custom confirm dialog
      const confirmed = await showCustomConfirm(
        "🗑️ Delete Folder",
        `Delete folder "${folder.name}" with ${folder.urls.length} URL(s)?`
      );

      if (confirmed) {
        const newFolders = urlFolders.filter((f) => f.id !== folderId);

        // ✅ FIX: Write to localStorage BEFORE calling setUrlFolders to avoid race condition
        try {
          localStorage.setItem(
            "screenshot-url-folders",
            JSON.stringify(newFolders)
          );
        } catch (error) {
          log.error("Error saving URL folders to localStorage:", error);
        }

        setUrlFolders(newFolders);
        addLog(`🗑️ Deleted folder: ${folder.name}`);
      }
    } finally {
      // ✅ FIX: Always reset the deletion flag
      setIsDeletingFolder(null);
    }
  };

  const startEditingFolder = (folderId: string) => {
    const folder = urlFolders.find((f) => f.id === folderId);
    if (folder) {
      setEditingFolderId(folderId);
      setEditingFolderName(folder.name);
      setFolderNameError("");
      addLog(`✏️ Started editing folder: ${folder.name}`);
    }
  };

  const cancelEditingFolder = () => {
    const folder = urlFolders.find((f) => f.id === editingFolderId);
    if (folder) {
      addLog(`❌ Cancelled editing folder: ${folder.name}`);
    }
    setEditingFolderId(null);
    setEditingFolderName("");
    setFolderNameError("");
  };

  const saveFolderName = (folderId: string) => {
    const trimmedName = editingFolderName.trim();

    if (!trimmedName) {
      setFolderNameError("Folder name cannot be empty!");
      return;
    }

    // Check for duplicates (case-insensitive, excluding current folder)
    const isDuplicate = urlFolders.some(
      (f) =>
        f.id !== folderId && f.name.toLowerCase() === trimmedName.toLowerCase()
    );

    if (isDuplicate) {
      setFolderNameError(
        "Folder name already exists! Choose a different name."
      );
      return;
    }

    const oldFolder = urlFolders.find((f) => f.id === folderId);
    setUrlFolders(
      urlFolders.map((f) =>
        f.id === folderId
          ? { ...f, name: trimmedName, updated: new Date().toISOString() }
          : f
      )
    );

    if (oldFolder) {
      addLog(`✏️ Renamed folder: "${oldFolder.name}" → "${trimmedName}"`);
    }

    setEditingFolderId(null);
    setEditingFolderName("");
    setFolderNameError("");
  };

  const toggleFolderExpanded = (folderId: string) => {
    const newExpanded = new Set(expandedFolders);
    const folder = urlFolders.find((f) => f.id === folderId);
    const folderName = folder ? folder.name : folderId;

    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
      addLog(`📁 Collapsed folder: ${folderName}`);
    } else {
      newExpanded.add(folderId);
      addLog(`📂 Expanded folder: ${folderName}`);
    }
    setExpandedFolders(newExpanded);
  };

  // URL Selection Functions
  const toggleUrlSelection = (folderId: string, urlIndex: number) => {
    const currentSelected = selectedUrls[folderId] || new Set<number>();
    const newSelected = new Set(currentSelected);

    if (newSelected.has(urlIndex)) {
      newSelected.delete(urlIndex);
    } else {
      newSelected.add(urlIndex);
    }

    setSelectedUrls({ ...selectedUrls, [folderId]: newSelected });
  };

  const selectAllUrls = (folderId: string) => {
    const folder = urlFolders.find((f) => f.id === folderId);
    if (!folder) return;

    const filteredUrls = getFilteredAndSortedUrls(folderId);
    const allIndices = new Set(
      filteredUrls.map((_, idx) => {
        // Get original index from filtered list
        return folder.urls.indexOf(filteredUrls[idx]);
      })
    );

    setSelectedUrls({ ...selectedUrls, [folderId]: allIndices });
  };

  const deselectAllUrls = (folderId: string) => {
    setSelectedUrls({ ...selectedUrls, [folderId]: new Set<number>() });
  };

  // ✅ FIX: Track URL deletion in progress to prevent multiple clicks
  const [isDeletingUrls, setIsDeletingUrls] = useState<string | null>(null);

  const deleteSelectedUrls = async (folderId: string) => {
    // ✅ FIX: Prevent multiple simultaneous deletions
    if (isDeletingUrls) return;

    const selected = selectedUrls[folderId];
    if (!selected || selected.size === 0) return;

    setIsDeletingUrls(folderId);

    try {
      log.debug(
        `🗑️ deleteSelectedUrls: Requesting confirmation for ${selected.size} URLs`
      );
      // ✅ Use custom confirm dialog
      const confirmed = await showCustomConfirm(
        "🗑️ Delete Selected URLs",
        `Delete ${selected.size} selected URL(s)? This cannot be undone.`
      );

      if (!confirmed) return;

      const newFolders = urlFolders.map((f) =>
        f.id === folderId
          ? {
              ...f,
              urls: f.urls.filter((_, idx) => !selected.has(idx)),
              updated: new Date().toISOString(),
            }
          : f
      );

      // ✅ FIX: Write to localStorage BEFORE calling setUrlFolders to avoid race condition
      try {
        localStorage.setItem(
          "screenshot-url-folders",
          JSON.stringify(newFolders)
        );
      } catch (error) {
        log.error("Error saving URL folders to localStorage:", error);
      }

      setUrlFolders(newFolders);
      setSelectedUrls({ ...selectedUrls, [folderId]: new Set<number>() });
      addLog(`🗑️ Deleted ${selected.size} URL(s) from folder`);
    } finally {
      // ✅ FIX: Always reset the deletion flag
      setIsDeletingUrls(null);
    }
  };

  const copySelectedUrls = (folderId: string) => {
    const folder = urlFolders.find((f) => f.id === folderId);
    const selected = selectedUrls[folderId];

    if (!folder || !selected || selected.size === 0) return;

    const selectedUrlsList = folder.urls.filter((_, idx) => selected.has(idx));
    const urlText = selectedUrlsList.join("\n");

    navigator.clipboard.writeText(urlText).then(() => {
      addLog(`📋 Copied ${selected.size} URL(s) to clipboard`);
      alert(`Copied ${selected.size} URL(s) to clipboard!`);
    });
  };

  // Filter and Sort Functions
  const getFilteredAndSortedUrls = (folderId: string): string[] => {
    const folder = urlFolders.find((f) => f.id === folderId);
    if (!folder) return [];

    let urls = [...folder.urls];

    // Apply search filter
    const query = searchQuery[folderId];
    if (query && query.trim()) {
      const lowerQuery = query.toLowerCase();
      urls = urls.filter((url) => url.toLowerCase().includes(lowerQuery));
    }

    // Apply sort
    const sort = sortOrder[folderId] || "date-desc";

    if (sort === "date-asc") {
      urls = [...urls].reverse(); // Oldest first
    } else if (sort === "alpha-asc") {
      urls = [...urls].sort((a, b) => a.localeCompare(b)); // A-Z
    } else if (sort === "alpha-desc") {
      urls = [...urls].sort((a, b) => b.localeCompare(a)); // Z-A
    }
    // "date-desc" is default (newest first, no change needed)

    return urls;
  };

  // ✅ Helper function to get display value based on unit
  const getTimeoutDisplayValue = (textBox: TextBox): number | string => {
    if (!textBox.batchTimeout) return "";

    const unit = textBox.batchTimeoutUnit || "seconds";

    if (unit === "minutes") {
      const minutes = textBox.batchTimeout / 60;
      // Round to 2 decimal places, remove trailing zeros
      return Number.isInteger(minutes)
        ? minutes
        : parseFloat(minutes.toFixed(2));
    } else if (unit === "hours") {
      const hours = textBox.batchTimeout / 3600;
      // Round to 2 decimal places, remove trailing zeros
      return Number.isInteger(hours) ? hours : parseFloat(hours.toFixed(2));
    } else {
      return textBox.batchTimeout;
    }
  };

  // ✅ EXTRACTED: Batch timeout change handler for TextBoxGroup component
  const handleBatchTimeoutChange = (textBoxId: string, inputValue: string) => {
    // Clear any existing validation error when user starts typing
    if (timeoutErrors.has(textBoxId)) {
      const newErrors = new Map(timeoutErrors);
      newErrors.delete(textBoxId);
      setTimeoutErrors(newErrors);
    }

    // Allow any input during typing, validate only on blur
    if (inputValue === "") {
      // Allow empty input
      const updatedTextBoxes = textBoxes.map((tb) =>
        tb.id === textBoxId
          ? {
              ...tb,
              batchTimeout: undefined,
            }
          : tb
      );
      setTextBoxes(updatedTextBoxes);
      return;
    }

    const numericValue = parseFloat(inputValue);
    if (!isNaN(numericValue) && numericValue >= 0) {
      // Find the text box to get its current unit
      const textBox = textBoxes.find((tb) => tb.id === textBoxId);
      const unit = textBox?.batchTimeoutUnit || "seconds";

      // Convert to seconds based on selected unit
      let timeoutInSeconds = numericValue;
      if (unit === "minutes") {
        timeoutInSeconds = numericValue * 60;
      } else if (unit === "hours") {
        timeoutInSeconds = numericValue * 3600;
      }

      // Update state immediately without validation
      const updatedTextBoxes = textBoxes.map((tb) =>
        tb.id === textBoxId
          ? {
              ...tb,
              batchTimeout: Math.round(timeoutInSeconds),
              batchTimeoutUnit: unit,
            }
          : tb
      );
      setTextBoxes(updatedTextBoxes);
    }
  };

  // ✅ EXTRACTED: Batch timeout blur handler for TextBoxGroup component
  const handleBatchTimeoutBlur = (textBoxId: string, inputValue: string) => {
    if (inputValue === "" || inputValue === "0") {
      // Reset to default if empty or zero
      const updatedTextBoxes = textBoxes.map((tb) =>
        tb.id === textBoxId
          ? {
              ...tb,
              batchTimeout: 90,
              batchTimeoutUnit: "seconds",
            }
          : tb
      );
      setTextBoxes(updatedTextBoxes);
      updateBatchTimeout(textBoxId, 90);
      // Clear any error
      const newErrors = new Map(timeoutErrors);
      newErrors.delete(textBoxId);
      setTimeoutErrors(newErrors);
      return;
    }

    const numericValue = parseFloat(inputValue);
    if (!isNaN(numericValue)) {
      // Find the text box to get its current unit
      const textBox = textBoxes.find((tb) => tb.id === textBoxId);
      const unit = textBox?.batchTimeoutUnit || "seconds";

      let timeoutInSeconds = numericValue;
      if (unit === "minutes") {
        timeoutInSeconds = numericValue * 60;
      } else if (unit === "hours") {
        timeoutInSeconds = numericValue * 3600;
      }

      const finalTimeout = Math.round(timeoutInSeconds);

      // Validate and provide inline feedback + log
      if (finalTimeout < 10) {
        const errorMsg = `Minimum is 10 seconds. Resetting to 90s.`;
        const newErrors = new Map(timeoutErrors);
        newErrors.set(textBoxId, errorMsg);
        setTimeoutErrors(newErrors);

        addLog(`⚠️ Batch timeout too low (${finalTimeout}s). ${errorMsg}`);
        const updatedTextBoxes = textBoxes.map((tb) =>
          tb.id === textBoxId
            ? {
                ...tb,
                batchTimeout: 90,
                batchTimeoutUnit: "seconds",
              }
            : tb
        );
        setTextBoxes(updatedTextBoxes);
        updateBatchTimeout(textBoxId, 90);
      } else if (finalTimeout > 7200) {
        const errorMsg = `Maximum is 7200 seconds (2 hours). Resetting to 7200s.`;
        const newErrors = new Map(timeoutErrors);
        newErrors.set(textBoxId, errorMsg);
        setTimeoutErrors(newErrors);

        addLog(`⚠️ Batch timeout too high (${finalTimeout}s). ${errorMsg}`);
        const updatedTextBoxes = textBoxes.map((tb) =>
          tb.id === textBoxId
            ? {
                ...tb,
                batchTimeout: 7200,
                batchTimeoutUnit: unit,
              }
            : tb
        );
        setTextBoxes(updatedTextBoxes);
        updateBatchTimeout(textBoxId, 7200);
      } else {
        // Valid range - clear any error and update
        const newErrors = new Map(timeoutErrors);
        newErrors.delete(textBoxId);
        setTimeoutErrors(newErrors);

        updateBatchTimeout(textBoxId, finalTimeout);
      }
    }
  };

  // ✅ EXTRACTED: Batch timeout unit change handler for TextBoxGroup component
  const handleBatchTimeoutUnitChange = (textBoxId: string, newUnit: string) => {
    // Find the text box to get current display value
    const textBox = textBoxes.find((tb) => tb.id === textBoxId);
    if (!textBox) return;

    // Get current display value (what user sees)
    const currentDisplayValue = getTimeoutDisplayValue(textBox);

    if (currentDisplayValue && typeof currentDisplayValue === "number") {
      // Re-convert using NEW unit to keep display value the same
      let timeoutInSeconds = currentDisplayValue;
      if (newUnit === "minutes") {
        timeoutInSeconds = currentDisplayValue * 60;
      } else if (newUnit === "hours") {
        timeoutInSeconds = currentDisplayValue * 3600;
      }

      const updatedTextBoxes = textBoxes.map((tb) =>
        tb.id === textBoxId
          ? {
              ...tb,
              batchTimeout: Math.round(timeoutInSeconds),
              batchTimeoutUnit: newUnit,
            }
          : tb
      );
      setTextBoxes(updatedTextBoxes);
    } else {
      // Fallback: just update unit if no valid display value
      const updatedTextBoxes = textBoxes.map((tb) =>
        tb.id === textBoxId
          ? {
              ...tb,
              batchTimeoutUnit: newUnit,
            }
          : tb
      );
      setTextBoxes(updatedTextBoxes);
    }
  };

  // ✅ NEW: Update batch timeout for a specific text box and trigger doc generation if changed
  const updateBatchTimeout = async (textBoxId: string, newTimeout: number) => {
    // Validate input (10 seconds to 2 hours = 7200 seconds)
    if (isNaN(newTimeout) || newTimeout < 10 || newTimeout > 7200) {
      addLog(
        "⚠️ Batch timeout must be between 10 seconds and 2 hours (7200 seconds)"
      );
      return;
    }

    // Find the text box
    const textBox = textBoxes.find((tb) => tb.id === textBoxId);
    if (!textBox) return;

    const oldTimeout = textBox.batchTimeout || 90;

    // ✅ FIX: Don't update state here - onChange already did it!
    // Just check if value changed and call API

    // Check if value actually changed
    if (newTimeout !== oldTimeout) {
      addLog(`⏱️ Text Box timeout changed: ${oldTimeout}s → ${newTimeout}s`);
      addLog("📊 Regenerating performance documentation...");

      try {
        const response = await fetch(
          `${config.apiBaseUrl}/api/update-batch-timeout`,
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ timeout: newTimeout }),
          }
        );

        if (response.ok) {
          addLog("✅ Performance documentation updated successfully!");
        } else {
          addLog("⚠️ Failed to update documentation (backend error)");
        }
      } catch (error: any) {
        addLog(`⚠️ Failed to update documentation: ${error.message}`);
      }
    }
  };

  // URL Management Functions (with auto-beautify)
  // Bulk add URLs to folder from textarea
  const addBulkUrlsToFolder = (folderId: string) => {
    const inputText = bulkUrlInput[folderId] || "";

    if (!inputText.trim()) {
      alert("Please enter at least one URL!");
      return;
    }

    // Parse and format URLs
    // First, insert newlines before every http:// or https:// that's not at the start
    const withSeparatedUrls = inputText.replace(/(https?:\/\/)/g, "\n$1");

    // Split by newlines, spaces, commas, semicolons
    const parsedUrls = withSeparatedUrls
      .split(/[\n\s,;]+/)
      .map((url) => url.trim())
      .filter((url) => url.length > 0)
      .filter((url) => url.startsWith("http://") || url.startsWith("https://"));

    if (parsedUrls.length === 0) {
      alert(
        "No valid URLs found! Please enter URLs starting with http:// or https://"
      );
      return;
    }

    // Remove duplicates within the input itself (case-insensitive)
    const uniqueParsedUrls: string[] = [];
    const seenUrls = new Set<string>();

    for (const url of parsedUrls) {
      const lowerUrl = url.toLowerCase();
      if (!seenUrls.has(lowerUrl)) {
        seenUrls.add(lowerUrl);
        uniqueParsedUrls.push(url);
      }
    }

    // Get existing URLs for this folder
    const folder = urlFolders.find((f) => f.id === folderId);
    const existingUrls = folder ? folder.urls : [];

    // Remove duplicates against existing URLs (case-insensitive)
    const newUrls = uniqueParsedUrls.filter(
      (url) =>
        !existingUrls.some(
          (existing) => existing.toLowerCase() === url.toLowerCase()
        )
    );

    if (newUrls.length === 0) {
      alert("All URLs already exist in this folder!");
      return;
    }

    // Add URLs to folder
    setUrlFolders(
      urlFolders.map((f) =>
        f.id === folderId
          ? {
              ...f,
              urls: [...f.urls, ...newUrls],
              updated: new Date().toISOString(),
            }
          : f
      )
    );

    // Clear textarea for this folder
    setBulkUrlInput({ ...bulkUrlInput, [folderId]: "" });

    const inputDuplicates = parsedUrls.length - uniqueParsedUrls.length;
    const existingDuplicates = uniqueParsedUrls.length - newUrls.length;
    const totalDuplicates = inputDuplicates + existingDuplicates;

    let logMessage = `✅ Added ${newUrls.length} URL(s) to folder`;
    if (totalDuplicates > 0) {
      logMessage += ` (${totalDuplicates} duplicate${
        totalDuplicates > 1 ? "s" : ""
      } skipped`;
      if (inputDuplicates > 0 && existingDuplicates > 0) {
        logMessage += `: ${inputDuplicates} in input, ${existingDuplicates} already exist`;
      } else if (inputDuplicates > 0) {
        logMessage += ` in input`;
      } else {
        logMessage += ` - already exist`;
      }
      logMessage += ")";
    }

    addLog(logMessage);
  };

  // Clean up duplicate URLs in all folders (case-insensitive)
  const removeDuplicateUrls = () => {
    const cleanedFolders = urlFolders.map((folder) => {
      const uniqueUrls: string[] = [];
      const seenUrls = new Set<string>();

      for (const url of folder.urls) {
        const lowerUrl = url.toLowerCase();
        if (!seenUrls.has(lowerUrl)) {
          seenUrls.add(lowerUrl);
          uniqueUrls.push(url);
        }
      }

      // Only update if duplicates were found
      if (uniqueUrls.length !== folder.urls.length) {
        return {
          ...folder,
          urls: uniqueUrls,
          updated: new Date().toISOString(),
        };
      }
      return folder;
    });

    // Check if any folder was cleaned
    const hadDuplicates = cleanedFolders.some(
      (folder, index) => folder.urls.length !== urlFolders[index].urls.length
    );

    if (hadDuplicates) {
      setUrlFolders(cleanedFolders);
      addLog("🧹 Cleaned up duplicate URLs from folders");
    }
  };

  const startEditingUrl = (folderId: string, urlIndex: number) => {
    const folder = urlFolders.find((f) => f.id === folderId);
    if (folder && folder.urls[urlIndex]) {
      setEditingUrlId(`${folderId}-${urlIndex}`);
      setEditingUrlValue(folder.urls[urlIndex]);
    }
  };

  const cancelEditingUrl = () => {
    setEditingUrlId(null);
    setEditingUrlValue("");
  };

  const saveUrl = (folderId: string, urlIndex: number) => {
    const trimmedUrl = editingUrlValue.trim();

    if (!trimmedUrl) {
      alert("URL cannot be empty!");
      return;
    }

    // Validate URL
    try {
      new URL(trimmedUrl);
    } catch {
      alert(
        "Invalid URL! Please enter a valid URL starting with http:// or https://"
      );
      return;
    }

    // Just validate, don't beautify - keep query params and fragments
    if (
      !trimmedUrl.startsWith("http://") &&
      !trimmedUrl.startsWith("https://")
    ) {
      alert(
        "Invalid URL! Please enter a valid URL starting with http:// or https://"
      );
      return;
    }

    setUrlFolders(
      urlFolders.map((f) =>
        f.id === folderId
          ? {
              ...f,
              urls: f.urls.map((url, idx) =>
                idx === urlIndex ? trimmedUrl : url
              ),
              updated: new Date().toISOString(),
            }
          : f
      )
    );

    setEditingUrlId(null);
    setEditingUrlValue("");
    addLog(`✏️ Updated URL`);
  };

  // ✅ FIX: Track single URL deletion in progress to prevent multiple clicks
  const [isDeletingSingleUrl, setIsDeletingSingleUrl] = useState<string | null>(
    null
  );

  const deleteUrl = async (folderId: string, urlIndex: number) => {
    // ✅ FIX: Prevent multiple simultaneous deletions
    if (isDeletingSingleUrl) return;

    setIsDeletingSingleUrl(`${folderId}-${urlIndex}`);

    try {
      log.debug(
        `🗑️ deleteSingleUrl: Requesting confirmation for URL deletion`
      );
      // ✅ Use custom confirm dialog
      const confirmed = await showCustomConfirm(
        "🗑️ Delete URL",
        "Delete this URL?"
      );

      if (confirmed) {
        const newFolders = urlFolders.map((f) =>
          f.id === folderId
            ? {
                ...f,
                urls: f.urls.filter((_, idx) => idx !== urlIndex),
                updated: new Date().toISOString(),
              }
            : f
        );

        // ✅ FIX: Write to localStorage BEFORE calling setUrlFolders to avoid race condition
        try {
          localStorage.setItem(
            "screenshot-url-folders",
            JSON.stringify(newFolders)
          );
        } catch (error) {
          log.error("Error saving URL folders to localStorage:", error);
        }

        setUrlFolders(newFolders);
        addLog(`🗑️ Deleted URL from folder`);
      }
    } finally {
      // ✅ FIX: Always reset the deletion flag
      setIsDeletingSingleUrl(null);
    }
  };

  // @mention Detection and Loading Functions
  const detectFolderMention = (text: string): string | null => {
    const match = text.match(/@(\w+)/);
    return match ? match[1] : null;
  };

  const loadFolderUrls = (folderName: string) => {
    const folder = urlFolders.find(
      (f) => f.name.toLowerCase() === folderName.toLowerCase()
    );

    if (folder) {
      // Load URLs as-is, keeping query params and fragments
      setUrls(folder.urls.join("\n"));
      addLog(
        `Loaded ${folder.urls.length} URL(s) from folder "${folder.name}"`
      );
    } else {
      addLog(`Folder "${folderName}" not found`);
      alert(`Folder "${folderName}" not found`);
    }
  };

  // Load a folder's URLs into a specific text box (multiple text boxes mode)
  const loadFolderUrlsIntoTextBox = (textBoxId: string, folderName: string) => {
    const folder = urlFolders.find(
      (f) => f.name.toLowerCase() === folderName.toLowerCase()
    );

    if (!folder) {
      addLog(`Folder "${folderName}" not found`);
      alert(`Folder "${folderName}" not found`);
      return;
    }

    setTextBoxes((prev) =>
      prev.map((tb) =>
        tb.id === textBoxId
          ? {
              ...tb,
              urls: folder.urls.join("\n"),
            }
          : tb
      )
    );

    addLog(
      `Loaded ${folder.urls.length} URL(s) from folder "${folder.name}" into text box`
    );
  };

  // Handle URL hover - show tooltip after 3 seconds
  const handleUrlMouseEnter = (index: number) => {
    const timeout = setTimeout(() => {
      setHoveredUrl(index);
    }, 3000); // 3 seconds delay
    setHoverTimeout(timeout);
  };

  const handleUrlMouseLeave = () => {
    if (hoverTimeout) {
      clearTimeout(hoverTimeout);
      setHoverTimeout(null);
    }
    setHoveredUrl(null);
  };

  // Handle URL click - show tooltip for 10 seconds
  const handleUrlClick = (index: number) => {
    // Clear any existing click timeout
    if (clickTimeout) {
      clearTimeout(clickTimeout);
    }

    setClickedUrl(index);
    const timeout = setTimeout(() => {
      setClickedUrl(null);
    }, 10000); // 10 seconds
    setClickTimeout(timeout);
  };

  // Sync line numbers scroll with textarea scroll
  const handleTextareaScroll = () => {
    if (textareaRef.current && lineNumbersRef.current) {
      lineNumbersRef.current.scrollTop = textareaRef.current.scrollTop;
    }
  };

  // Auto-launch Chrome with remote debugging on app startup
  const launchDebugChrome = async () => {
    try {
      const response = await fetch(apiUrl("/api/launch-debug-chrome"), {
        method: "POST",
      });

      if (response.ok) {
        const data = await response.json();
        log.info("✅ Debug Chrome launched:", data);
        addLog("🔴 Debug Chrome launched automatically");
      } else {
        log.warn(
          "⚠️ Failed to launch debug Chrome:",
          await response.text()
        );
      }
    } catch (error) {
      log.error("❌ Error launching debug Chrome:", error);
      // Don't show error to user - it's not critical if Chrome is already running
    }
  };

  // Ensure Brave (or any Chromium browser) is exposing CDP on port 9222.
  // If nothing is listening, this will ask the backend to launch Brave via
  // launch-brave-cdp.sh. Used by the "🦁 Ensure Brave CDP is running" button
  // in Settings → Real Browser Mode.
  const ensureBraveCdp = async () => {
    try {
      const response = await fetch(apiUrl("/api/launch-brave-cdp"), {
        method: "POST",
      });

      if (!response.ok) {
        const text = await response.text();
        log.warn("⚠️ Failed to ensure Brave CDP:", text);
        addLog(`❌ Failed to ensure Brave CDP: ${text}`);
        notify("Failed to ensure Brave CDP is running. Check backend logs.", {
          title: "Brave CDP",
          type: "error",
          duration: 7000,
        });
        return;
      }

      const data = await response.json();
      log.info("🦁 Brave CDP response:", data);
      addLog(`🦁 Brave CDP: ${data.status} - ${data.message}`);

      if (data.status === "already_running") {
        notify(
          "A browser is already exposing CDP on port 9223. You can use Real Browser Mode now.",
          {
            title: "Brave CDP",
            type: "info",
            duration: 6000,
          }
        );
      } else {
        notify(
          "Brave launched with CDP on port 9223. Your existing Brave windows are still open.",
          {
            title: "Brave CDP",
            type: "success",
            duration: 7000,
          }
        );
      }
    } catch (error: any) {
      log.error("❌ Error ensuring Brave CDP:", error);
      addLog(`❌ Error ensuring Brave CDP: ${String(error)}`);
      notify("Error ensuring Brave CDP is running. Check backend logs.", {
        title: "Brave CDP",
        type: "error",
        duration: 7000,
      });
    }
  };

  // Lightweight CDP status checker used by the Settings UI to display
  // "CDP on 9223: ✅/❌". This does NOT launch any browsers; it only checks
  // whether something is listening on localhost:9223.
  const checkCdpStatus = async () => {
    try {
      const response = await fetch(apiUrl(`/api/cdp-status/${cdpPort}`));
      if (!response.ok) {
        const text = await response.text();
        log.warn("⚠️ Failed to check CDP status:", text);
        addLog(`⚠️ Failed to check CDP status: ${text}`);
        setCdpStatus("unknown");
        return;
      }

      const data = await response.json();
      const isListening = !!data.is_listening;
      setCdpStatus(isListening ? "up" : "down");
      addLog(`🌐 CDP status on port ${data.port ?? cdpPort}: ${isListening ? "UP" : "DOWN"}`);
    } catch (error: any) {
      log.error("❌ Error checking CDP status:", error);
      addLog(`❌ Error checking CDP status: ${String(error)}`);
      setCdpStatus("unknown");
    }
  };

  // Launch selected browser on chosen port (Chrome: CDP, Safari: safaridriver)
  const launchSelectedBrowserCdp = async () => {
    try {
      addLog(`🚀 Launching ${cdpBrowser} on port ${cdpPort}...`);
      const response = await fetch(apiUrl("/api/launch-browser-cdp"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ browser: cdpBrowser, port: cdpPort, use_temp_profile: true, copy_cookies: copyCookies })
      });
      const data = await response.json();
      if (!response.ok) {
        log.warn("⚠️ Failed to launch:", data?.detail || data);
        addLog(`❌ Failed to launch ${cdpBrowser}: ${data?.detail || JSON.stringify(data)}`);
        notify(`Failed to launch ${cdpBrowser}: ${data?.detail || "Unknown error"}`, { title: "Launch Browser", type: "error", duration: 7000 });
        return;
      }
      addLog(`✅ ${cdpBrowser} ${data.status} on port ${cdpPort}`);
      notify(`${cdpBrowser} ${data.status} on port ${cdpPort}`, { title: "Launch Browser", type: "success", duration: 5000 });
      // Immediately refresh status
      checkCdpStatus();
    } catch (error: any) {
      log.error("❌ Error launching browser:", error);
      addLog(`❌ Error launching browser: ${String(error)}`);
      notify(`Error launching browser: ${String(error)}`, { title: "Launch Browser", type: "error", duration: 7000 });
    }
  };

  // Connect backend to CDP on selected port
  const connectToSelectedCdp = async () => {
    try {
      addLog(`🔌 Connecting to CDP on port ${cdpPort}...`);
      const response = await fetch(apiUrl(`/api/connect-cdp?port=${cdpPort}`), {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        addLog(`❌ Failed to connect: ${data?.detail || JSON.stringify(data)}`);
        notify(`Failed to connect: ${data?.detail || "Unknown error"}`, { title: "Connect CDP", type: "error", duration: 7000 });
        return;
      }
      addLog(`✅ ${data.message || "Connected."}`);
      notify(data.message || `Connected on ${cdpPort}`, { title: "Connect CDP", type: "success", duration: 5000 });
    } catch (e: any) {
      addLog(`❌ Error connecting: ${String(e)}`);
      notify(String(e), { title: "Connect CDP", type: "error", duration: 7000 });
    }
  };

  // Stop/cleanup the selected browser session
  const stopSelectedBrowser = async () => {
    try {
      addLog(`🛑 Stopping browser on port ${cdpPort}...`);
      const response = await fetch(apiUrl(`/api/stop-browser-cdp?port=${cdpPort}`), {
        method: "POST",
      });
      const data = await response.json();
      if (!response.ok) {
        addLog(`❌ Failed to stop: ${data?.detail || JSON.stringify(data)}`);
        notify(`Failed to stop: ${data?.detail || "Unknown error"}`, { title: "Stop Browser", type: "error", duration: 7000 });
        return;
      }
      addLog(`✅ ${data.status} (port ${data.port})`);
      notify(`${data.status} (port ${data.port})`, { title: "Stop Browser", type: "success", duration: 5000 });
      // Refresh status
      checkCdpStatus();
    } catch (e: any) {
      addLog(`❌ Error stopping: ${String(e)}`);
      notify(String(e), { title: "Stop Browser", type: "error", duration: 7000 });
    }
  };

  const importCookies = async () => {
    try {
      let cookies: any[] = [];
      try {
        const parsed = JSON.parse(cookieText || "[]");
        cookies = Array.isArray(parsed) ? parsed : [];
      } catch (e) {
        notify("Invalid JSON. Please paste an array of cookie objects.", { title: "Import Cookies", type: "error", duration: 6000 });
        return;
      }
      if (!cookies.length) {
        notify("No cookies provided.", { title: "Import Cookies", type: "warning", duration: 4000 });
        return;
      }
      addLog(`🍪 Importing ${cookies.length} cookies to active CDP context...`);
      const resp = await fetch(apiUrl("/api/cdp/import-cookies"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ cookies })
      });
      const data = await resp.json();
      if (!resp.ok) {
        notify(data?.detail || "Failed to import cookies.", { title: "Import Cookies", type: "error", duration: 7000 });
        return;
      }
      notify(`Imported ${data.count} cookies.`, { title: "Import Cookies", type: "success", duration: 5000 });
    } catch (e: any) {
      notify(String(e), { title: "Import Cookies", type: "error", duration: 7000 });
    }
  };

  // ✅ NEW: URL-specific click configuration functions
  const loadUrlConfigs = async (): Promise<boolean> => {
    try {
      const response = await fetch(apiUrl("/api/url-configs"));
      if (response.ok) {
        const data = await response.json();
        setUrlConfigs(data.url_patterns || []);
        addLog(
          `📋 Loaded ${data.url_patterns?.length || 0} URL configurations`
        );
        return true;
      } else {
        log.error(`❌ Error loading URL configs: HTTP ${response.status}`);
        addLog(`❌ Failed to load URL configurations (HTTP ${response.status})`);
        return false;
      }
    } catch (error) {
      log.error("❌ Error loading URL configs:", error);
      const errorMsg = error instanceof Error ? error.message : String(error);

      // Check if it's a network error (backend not running)
      if (errorMsg.includes('fetch') || errorMsg.includes('NetworkError') || errorMsg.includes('Failed to fetch')) {
        addLog("❌ Failed to load URL configurations - Backend not reachable. Please check if backend is running.");
      } else {
        addLog(`❌ Failed to load URL configurations: ${errorMsg}`);
      }
      return false;
    }
  };

  const createUrlConfig = async (config: UrlClickConfig) => {
    log.debug("🔄 createUrlConfig() called:", config.name);
    try {
      const response = await fetch(apiUrl("/api/url-configs"), {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        await loadUrlConfigs();
        addLog(`✅ Created URL configuration: ${config.name}`);

        // ✅ NEW: Show toast notification for create success
        addNotification({
          type: "success",
          title: "✅ Configuration Created",
          message: `URL configuration "${config.name}" created successfully!`,
          duration: 5000,
        });
        log.debug("🔔 Toast notification sent: URL config created");

        return true;
      } else {
        const error = await response.json();
        addLog(`❌ Failed to create configuration: ${error.detail}`);

        // ✅ NEW: Show toast notification for create failure
        addNotification({
          type: "error",
          title: "❌ Create Failed",
          message: `Failed to create configuration: ${error.detail}`,
          duration: 8000,
        });
        log.debug("🔔 Toast notification sent: URL config create failed");

        return false;
      }
    } catch (error) {
      log.error("❌ Error creating URL config:", error);
      addLog("❌ Failed to create URL configuration");

      // ✅ NEW: Show toast notification for connection error
      addNotification({
        type: "error",
        title: "❌ Connection Error",
        message: `Failed to create URL configuration: ${error}`,
        duration: 8000,
      });
      log.debug("🔔 Toast notification sent: URL config create error");

      return false;
    }
  };

  const updateUrlConfig = async (configId: string, config: UrlClickConfig) => {
    log.debug("🔄 updateUrlConfig() called:", configId, config.name);
    log.debug("🔄 updateUrlConfig() - configId:", configId);
    log.debug(
      "🔄 updateUrlConfig() - config:",
      JSON.stringify(config, null, 2)
    );
    log.debug(
      "🔄 updateUrlConfig() - addNotification available:",
      typeof addNotification
    );

    try {
      const url = apiUrl(`/api/url-configs/${configId}`);
      log.debug("🔄 updateUrlConfig() - Fetching URL:", url);

      const response = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(config),
      });

      log.debug("🔄 updateUrlConfig() - Response status:", response.status);
      log.debug("🔄 updateUrlConfig() - Response ok:", response.ok);

      if (response.ok) {
        await loadUrlConfigs();
        addLog(`✅ Updated URL configuration: ${config.name}`);

        // ✅ NEW: Show toast notification for update success
        log.debug("🔔 About to call addNotification for success...");
        addNotification({
          type: "success",
          title: "✅ Configuration Updated",
          message: `URL configuration "${config.name}" updated successfully!`,
          duration: 5000,
        });
        log.debug("🔔 Toast notification sent: URL config updated");

        return true;
      } else {
        const errorText = await response.text();
        log.debug("🔄 updateUrlConfig() - Error response text:", errorText);

        let errorDetail = "Unknown error";
        try {
          const errorJson = JSON.parse(errorText);
          errorDetail =
            errorJson.detail || errorJson.message || "Unknown error";
        } catch (e) {
          errorDetail = errorText || "Unknown error";
        }

        addLog(`❌ Failed to update configuration: ${errorDetail}`);

        // ✅ NEW: Show toast notification for update failure
        log.debug("🔔 About to call addNotification for failure...");
        addNotification({
          type: "error",
          title: "❌ Update Failed",
          message: `Failed to update configuration: ${errorDetail}`,
          duration: 8000,
        });
        log.debug("🔔 Toast notification sent: URL config update failed");

        return false;
      }
    } catch (error) {
      log.error("❌ Error updating URL config - Full error object:", error);
      log.error(
        "❌ Error updating URL config - Error message:",
        error instanceof Error ? error.message : String(error)
      );
      log.error(
        "❌ Error updating URL config - Error stack:",
        error instanceof Error ? error.stack : "No stack trace"
      );

      addLog("❌ Failed to update URL configuration");

      // ✅ NEW: Show toast notification for connection error
      log.debug("🔔 About to call addNotification for error...");
      try {
        addNotification({
          type: "error",
          title: "❌ Connection Error",
          message: `Failed to update URL configuration: ${
            error instanceof Error ? error.message : String(error)
          }`,
          duration: 8000,
        });
        log.debug("🔔 Toast notification sent: URL config update error");
      } catch (notifError) {
        log.error("❌ Failed to show notification:", notifError);
      }

      return false;
    }
  };

  const deleteUrlConfig = async (configId: string) => {
    log.debug("🔄 deleteUrlConfig() called:", configId);
    try {
      const response = await fetch(apiUrl(`/api/url-configs/${configId}`), {
        method: "DELETE",
      });

      if (response.ok) {
        await loadUrlConfigs();
        addLog(`✅ Deleted URL configuration`);

        // ✅ NEW: Show toast notification for delete success
        addNotification({
          type: "success",
          title: "✅ Configuration Deleted",
          message: "URL configuration deleted successfully!",
          duration: 5000,
        });
        log.debug("🔔 Toast notification sent: URL config deleted");

        return true;
      } else {
        const error = await response.json();
        addLog(`❌ Failed to delete configuration: ${error.detail}`);

        // ✅ NEW: Show toast notification for delete failure
        addNotification({
          type: "error",
          title: "❌ Delete Failed",
          message: `Failed to delete configuration: ${error.detail}`,
          duration: 8000,
        });
        log.debug("🔔 Toast notification sent: URL config delete failed");

        return false;
      }
    } catch (error) {
      log.error("❌ Error deleting URL config:", error);
      addLog("❌ Failed to delete URL configuration");

      // ✅ NEW: Show toast notification for connection error
      addNotification({
        type: "error",
        title: "❌ Connection Error",
        message: `Failed to delete URL configuration: ${error}`,
        duration: 8000,
      });
      log.debug("🔔 Toast notification sent: URL config delete error");

      return false;
    }
  };

  const openUrlConfigEditor = (config?: UrlClickConfig) => {
    if (config) {
      // Edit existing
      setEditingUrlConfigId(config.id);
      setUrlConfigForm(config);
    } else {
      // Create new
      setEditingUrlConfigId(null);
      setUrlConfigForm({
        id: `config-${Date.now()}`,
        name: "",
        url_pattern: "",
        match_type: "exact",
        actions: [{ type: "click", text: "", wait_after_ms: 2000 }],
        enabled: true,
	        notes: "",
	        auto_expand_dropdowns: false,
      });
    }
    setShowUrlConfigEditor(true);
  };

  const closeUrlConfigEditor = () => {
    setShowUrlConfigEditor(false);
    setEditingUrlConfigId(null);
  };

  const saveUrlConfig = async () => {
    // Validate required fields
    if (!urlConfigForm.url_pattern) {
      addLog("❌ URL is required");
      return;
    }

    if (!urlConfigForm.actions[0]?.text) {
      addLog("❌ Text to click is required");
      return;
    }

    // Auto-fill missing fields
    const configToSave: UrlClickConfig = {
      ...urlConfigForm,
      id: urlConfigForm.id || `config-${Date.now()}`,
      name: urlConfigForm.name || `Config for ${urlConfigForm.url_pattern}`,
      match_type: "exact", // Always use exact match
      enabled: true, // Always enabled
      notes: "", // No notes
    };

    const success = editingUrlConfigId
      ? await updateUrlConfig(editingUrlConfigId, configToSave)
      : await createUrlConfig(configToSave);

    if (success) {
      closeUrlConfigEditor();
    }
  };

  // Load URL configs on mount with retry logic
  useEffect(() => {
    let retryCount = 0;
    const maxRetries = 3;

    const loadWithRetry = async () => {
      const success = await loadUrlConfigs();

      // If failed and retries remaining, try again after delay
      if (!success && retryCount < maxRetries) {
        retryCount++;
        log.debug(`🔄 Retrying URL config load (${retryCount}/${maxRetries})...`);
        setTimeout(loadWithRetry, 2000 * retryCount); // Exponential backoff
      }
    };

    loadWithRetry();
  }, []);

  // Listen for backend logs emitted from the Tauri sidecar supervisor
  useEffect(() => {
    let unlisten: (() => void) | null = null;

    // Only attach listener when running inside a Tauri context
    if (typeof window === "undefined" || !(window as any).__TAURI__) {
      return;
    }

    listen<string>("backend-log", (event) => {
      if (event && event.payload) {
        addLog(event.payload);
      }
    })
      .then((fn) => {
        unlisten = fn;
      })
      .catch((err) => {
        log.error("Failed to listen for backend-log events:", err);
        addLog(
          "⚠️ Failed to attach backend log listener (see console for details)"
        );
      });

    return () => {
      if (unlisten) {
        unlisten();
      }
    };
  }, [addLog]);

  // Log app initialization on first load
  useEffect(() => {
    const timestamp = new Date().toLocaleTimeString();
    setLogs([`[${timestamp}] Screenshot Tool started`]);

    // ❌ DISABLED: Auto-launch debug Chrome (it closes your existing Chrome!)
    // Users should manually launch debug Chrome if they want CDP mode
    // if (useRealBrowser) {
    //   launchDebugChrome();
    // }
  }, []); // Empty dependency array = run once on mount

  // ✅ FIX: Wrapper functions that log setting changes (defined after addLog)
  const setCaptureMode = (mode: string) => {
    const modeNames = {
      viewport: "Viewport only",
      fullpage: "Full page",
      segmented: "Segmented",
    };
    addLog(
      `⚙️ Changed capture mode to: ${
        modeNames[mode as keyof typeof modeNames] || mode
      }`
    );
    setCaptureModeContext(mode); // ✅ FIXED: Use context setter
  };

  const setUseStealth = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} stealth mode`);
    setUseStealthContext(enabled); // ✅ FIXED: Use context setter
  };

  const setUseRealBrowser = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} real browser mode`);
    setUseRealBrowserContext(enabled); // ✅ FIXED: Use context setter

    // When Real Browser Mode is turned on, proactively check/ensure CDP:
    // - First, run ensureBraveCdp() to start Brave with CDP if nothing
    //   is already listening on port 9223.
    // - Then, fire a lightweight status check so the UI indicator updates.
    if (enabled) {
      ensureBraveCdp();
      // Don't await; fire-and-forget is fine for status.
      checkCdpStatus();
    } else {
      // When disabling Real Browser Mode, we no longer care about CDP.
      setCdpStatus("unknown");
    }
  };

  // ✅ NEW: Headless mode wrapper
  const setHeadless = (enabled: boolean) => {
    addLog(
      `⚙️ ${enabled ? "Enabled" : "Disabled"} headless mode (${
        enabled ? "invisible" : "visible"
      } browser)`
    );
    setHeadlessContext(enabled); // ✅ FIXED: Use context setter
  };

  const setTrackNetwork = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} network event tracking`);
    setTrackNetworkContext(enabled); // ✅ FIXED: Use context setter
  };

  const setAutoExpandDropdowns = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} auto dropdown expansion`);
    setAutoExpandDropdownsContext(enabled); // ✅ FIXED: Use context setter
  };

  const setBrowserEngine = (engine: string) => {
    const engineNames = {
      playwright: "Playwright",
      camoufox: "Camoufox",
    };
    addLog(
      `⚙️ Changed browser engine to: ${
        engineNames[engine as keyof typeof engineNames] || engine
      }`
    );
    setBrowserEngineContext(engine); // ✅ FIXED: Use context setter
  };

  // ⚡ OPTIMIZATION: Wrap with useCallback to prevent recreation
  const clearLogs = useCallback(() => {
    console.log("🗑️ clearLogs called!");
    setLogs((prev) => {
      console.log("📊 Previous logs count:", prev.length);
      console.log("✅ Clearing logs now...");
      return [];
    });
    setHasErrors(false); // Reset error status when clearing logs
    _setShowLogs(false); // Hide logs panel when clearing
  }, []); // ✅ No dependencies - stable function

  // ⚡ OPTIMIZATION: Wrap with useCallback to prevent recreation
  const _toggleLogs = useCallback(() => { // Reserved for future log panel toggle
    _setShowLogs((prev: boolean) => !prev);
  }, []); // ✅ No dependencies

  // Count actual errors in logs (for badge display)
  const getErrorCount = () => {
    return logs.filter((log) => {
      const message = log.substring(log.indexOf("]") + 1).trim(); // Remove timestamp

      // Exclude summary lines that show "Failed: 0" or similar
      if (message.includes("Success:") && message.includes("Failed:")) {
        return false; // This is a summary line, not an error
      }

      return (
        message.includes("❌") ||
        message.toLowerCase().includes("error:") ||
        message.toLowerCase().includes("failed:") ||
        message.toLowerCase().includes("exception:") ||
        (message.toLowerCase().includes("error") &&
          !message.includes("✅") &&
          !message.toLowerCase().includes("no error"))
      );
    }).length;
  };

  // Tab management functions
  const openSettingsTab = () => {
    console.log("⚙️ openSettingsTab clicked!");
    console.log("📋 Current openTabs:", openTabs);
    if (!openTabs.includes("settings")) {
      console.log("➕ Adding 'settings' to openTabs");
      setOpenTabs([...openTabs, "settings"]);
    } else {
      console.log("ℹ️ 'settings' already in openTabs");
    }
    switchTab("settings");
  };

  const closeSettingsTab = () => {
    setOpenTabs(openTabs.filter((tab) => tab !== "settings"));
    switchTab("main");
  };

  const openLogsTab = () => {
    console.log("📋 openLogsTab clicked!");
    console.log("📋 Current openTabs:", openTabs);
    if (!openTabs.includes("logs")) {
      console.log("➕ Adding 'logs' to openTabs");
      setOpenTabs([...openTabs, "logs"]);
    } else {
      console.log("ℹ️ 'logs' already in openTabs");
    }
    switchTab("logs");
  };

  const closeLogsTab = () => {
    setOpenTabs(openTabs.filter((tab) => tab !== "logs"));
    switchTab("main");
  };

  const openKeywordConfigTab = () => {
    if (!openTabs.includes("keyword-config")) {
      setOpenTabs([...openTabs, "keyword-config"]);
    }
    switchTab("keyword-config");
  };

  const closeKeywordConfigTab = () => {
    setOpenTabs(openTabs.filter((tab) => tab !== "keyword-config"));
    switchTab("main");
  };

  // ✅ NEW: Update backend screenshots directory
  const updateBackendScreenshotsDir = async (newDir: string) => {
    try {
      const response = await fetch("http://127.0.0.1:8001/api/config/paths", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          screenshots_dir: newDir,
        }),
      });

      if (!response.ok) {
        addLog(`   ⚠️ Failed to update backend screenshots directory`);
        return;
      }

      const result = await response.json();
      addLog(
        `   ✅ Backend screenshots directory updated: ${result.screenshots_dir_absolute}`
      );
    } catch (error) {
      addLog(`   ❌ Error updating backend: ${error}`);
    }
  };

  // ✅ NEW: Let user pick folders via native dialog for file storage locations
  const handleSelectScreenshotsDir = async () => {
    try {
      // If not running inside the Tauri desktop app, folder picker is not available
      const isTauriEnv =
        typeof window !== "undefined" &&
        Boolean(
          (window as any).__TAURI_INTERNALS__ ||
            (window as any).__TAURI__ ||
            (window as any).isTauri
        );

      if (!isTauriEnv) {
        // Browser-only fallback: try to use a hidden <input type="file" webkitdirectory> so
        // the user can still pick a folder visually. We only get the folder *name*, which we
        // treat as a relative path on the backend. For full control and absolute paths, the
        // desktop app (Tauri) is still required.
        if (typeof document !== "undefined") {
          const el = document.getElementById(
            "screenshots-dir-browser-picker"
          ) as HTMLInputElement | null;
          if (el) {
            el.value = ""; // clear previous selection so onChange always fires
            el.click();
            notify(
              "Using browser folder picker. This will set a *relative* folder name. For exact OS paths, use the desktop app.",
              {
                title: "File Storage",
                type: "info",
                duration: 7000,
              }
            );
          } else {
            notify(
              "Folder picker is only available in the desktop app. Please run via Tauri or type the path manually.",
              {
                title: "File Storage",
                type: "info",
                duration: 6000,
              }
            );
          }
        }
        return;
      }

      const result = await open({
        directory: true,
        multiple: false,
        title: "Select screenshots folder",
        defaultPath: screenshotsDir || undefined,
      });

      if (!result) {
        // User cancelled
        return;
      }

      const selectedPath = Array.isArray(result) ? result[0] : result;

      if (!selectedPath || typeof selectedPath !== "string") {
        return;
      }

      setScreenshotsDir(selectedPath);
      await updateBackendScreenshotsDir(selectedPath);
      addLog(`📁 Screenshots folder set from picker: ${selectedPath}`);
      notify("Screenshots folder updated.", {
        title: "File Storage",
        type: "success",
        duration: 4000,
      });
    } catch (error) {
      log.error("Failed to select screenshots folder:", error);
      notify("Failed to open folder picker for screenshots:", {
        title: "File Storage",
        type: "error",
        duration: 5000,
      });
    }
  };

  const handleSelectWordDocsBaseDir = async () => {
    try {
      // If not running inside the Tauri desktop app, folder picker is not available
      const isTauriEnv =
        typeof window !== "undefined" &&
        Boolean(
          (window as any).__TAURI_INTERNALS__ ||
            (window as any).__TAURI__ ||
            (window as any).isTauri
        );

      if (!isTauriEnv) {
        // Browser-only fallback: hidden directory input similar to screenshots folder.
        if (typeof document !== "undefined") {
          const el = document.getElementById(
            "worddocs-dir-browser-picker"
          ) as HTMLInputElement | null;
          if (el) {
            el.value = "";
            el.click();
            notify(
              "Using browser folder picker. This will set a *relative* folder name. For exact OS paths, use the desktop app.",
              {
                title: "File Storage",
                type: "info",
                duration: 7000,
              }
            );
          } else {
            notify(
              "Folder picker is only available in the desktop app. Please run via Tauri or type the path manually.",
              {
                title: "File Storage",
                type: "info",
                duration: 6000,
              }
            );
          }
        }
        return;
      }

      const result = await open({
        directory: true,
        multiple: false,
        title: "Select Word docs base folder",
        defaultPath: wordDocsBaseDir || undefined,
      });

      if (!result) {
        // User cancelled
        return;
      }

      const selectedPath = Array.isArray(result) ? result[0] : result;

      if (!selectedPath || typeof selectedPath !== "string") {
        return;
      }

      setWordDocsBaseDir(selectedPath);
      addLog(`📁 Word docs base folder set from picker: ${selectedPath}`);
      notify("Word docs folder updated.", {
        title: "File Storage",
        type: "success",
        duration: 4000,
      });
    } catch (error) {
      log.error("Failed to select Word docs base folder:", error);
      notify("Failed to open folder picker for Word docs.", {
        title: "File Storage",
        type: "error",
        duration: 5000,
      });
    }
  };

  // Main, Sessions, URLs, Cookies, and Network tabs are now permanent (always open), so no open/close functions needed
  // ✅ FIXED: Removed duplicate switchTab function (already defined at line 2262)

  // Helper: convert unknown error to string
  const toErrorMessage = (err: unknown): string =>
    err instanceof Error ? err.message : String(err ?? "Unknown error");

  // Helper: fetch with timeout to avoid hanging forever on restart
  const fetchWithTimeout = async (
    url: string,
    options: RequestInit,
    ms = 10000
  ): Promise<Response> => {
    const controller = new AbortController();
    const id = setTimeout(() => controller.abort(), ms);
    try {
      return await fetch(url, { ...options, signal: controller.signal });
    } finally {
      clearTimeout(id);
    }
  };

  // Helper: wait for backend /health to report healthy after restart
  const waitForBackendHealthy = async (
    timeoutMs = 30000,
    intervalMs = 1500
  ): Promise<boolean> => {
    const deadline = Date.now() + timeoutMs;
    while (Date.now() < deadline) {
      try {
	        const res = await fetch(apiUrl("/health"));
        if (res.ok) {
          const body = (await res.json()) as { status?: string };
          if (body.status === "healthy") {
            return true;
          }
        }
      } catch {
        // ignore until timeout
      }
      await new Promise((resolve) => setTimeout(resolve, intervalMs));
    }
    return false;
  };

  // Restart backend with health-check based confirmation
  const restartBackend = async () => {
    log.debug("🔄 restartBackend() called");
    setIsRestartingBackend(true);
	    setRestartMessage("🔄 Restarting backend...");
	    addLog("🔄 Restarting backend server...");

	    // If our system usage polling already knows the backend is offline,
	    // show a clear manual instruction instead of attempting an HTTP
	    // restart that cannot succeed.
	    const isOnline = systemUsage?.status === "success";
	    if (!isOnline) {
	      const manualMsg =
	        "Backend is currently offline. Please start it manually using: " +
	        "cd backend && python3 main.py";
	      setRestartMessage(`❌ ${manualMsg}`);
	      addLog(`❌ ${manualMsg}`);
	      addNotification({
	        type: "error",
	        title: "❌ Backend Offline",
	        message: manualMsg,
	        duration: 10000,
	      });
	      setIsRestartingBackend(false);
	      log.debug(
	        "🔔 Restart skipped because backend is already offline; manual start required."
	      );
	      return;
	    }

    addNotification({
      type: "info",
      title: "🔄 Restarting Backend",
      message: "Backend server is restarting...",
      duration: 3000,
    });
    log.debug("🔔 Toast notification sent: Backend restart started");

    try {
      // 1) Request restart with a hard timeout so we don't hang forever
      const response = await fetchWithTimeout(
	        apiUrl("/api/restart"),
        { method: "POST" },
        10000
      );

      if (!response.ok) {
	        let msg: string;
	
	        if (response.status === 403) {
	          // Restart endpoint explicitly disabled (e.g. production mode)
	          let detail: string | undefined;
	          try {
	            const body = (await response.json()) as { detail?: string };
	            detail = typeof body?.detail === "string" ? body.detail : undefined;
	          } catch {
	            // ignore JSON parse errors and fall back to generic wording
	          }
	
	          const reason =
	            detail && detail.toLowerCase().includes("disabled")
	              ? detail
	              : "Restart endpoint is disabled in this environment.";
	
	          msg =
	            `${reason} ` +
	            "If you need to restart the backend, please do it manually in a terminal " +
	            "using: cd backend && python3 main.py";
	        } else {
	          const errorText = await response.text();
	          msg = `Failed to restart backend: ${
	            errorText || `HTTP ${response.status}`
	          }`;
	        }
	
	        setRestartMessage(`❌ ${msg}`);
	        addLog(`❌ ${msg}`);
	        addNotification({
	          type: "error",
	          title: "❌ Restart Failed",
	          message: msg,
	          duration: 8000,
	        });
	        log.debug(
	          "🔔 Toast notification sent: Backend restart failed (HTTP error or disabled)"
	        );
	        return;
      }

      // 2) Restart requested OK – now wait for backend /health to become healthy
      setRestartMessage(
        "⏳ Restart requested. Waiting for backend to become healthy..."
      );
      addLog("⏳ Waiting for backend /health to report healthy...");

      const healthy = await waitForBackendHealthy(30000, 1500);
      if (healthy) {
        setRestartMessage("✅ Backend is up and healthy.");
        addLog("✅ Backend is up and healthy after restart.");
        addNotification({
          type: "success",
          title: "✅ Backend Restarted",
          message: "Backend server restarted and passed health check.",
          duration: 5000,
        });
        log.debug(
          "🔔 Toast notification sent: Backend restart success (healthy)"
        );
        setTimeout(() => {
          setRestartMessage(null);
        }, 3000);
      } else {
        const manualMsg =
          "Backend did not become healthy within 30 seconds. " +
          "Please run `cd backend && python3 main.py` and check backend.log.";
        setRestartMessage(`❌ ${manualMsg}`);
        addLog(`❌ ${manualMsg}`);
        addNotification({
          type: "error",
          title: "❌ Backend Not Healthy",
          message: manualMsg,
          duration: 12000,
        });
        log.debug(
          "🔔 Toast notification sent: Backend restart failed (health timeout)"
        );
      }
	    } catch (error) {
	      // Network / timeout / unexpected errors while calling /api/restart
	      const errMsg = toErrorMessage(error);
	      const manualMsg =
	        "Could not reach the backend restart endpoint from the UI. " +
	        "If the app seems unresponsive, please restart the backend manually " +
	        "using: cd backend && python3 main.py";
	      setRestartMessage(`❌ ${manualMsg}`);
	      addLog(
	        `❌ Backend restart request failed: ${errMsg}. Backend may still be running; restart manually if needed.`
	      );
	      addNotification({
	        type: "error",
	        title: "❌ Connection Error",
	        message: manualMsg,
	        duration: 10000,
	      });
	      log.debug("🔔 Toast notification sent: Backend connection error");
    } finally {
      setIsRestartingBackend(false);
      log.debug("🔄 restartBackend() completed");
    }
  };

  // Beautify URLs - clean up formatting
  const beautifyUrls = () => {
    if (!urls.trim()) return;

    // First, insert newlines before every http:// or https:// that's not at the start
    const withSeparatedUrls = urls.replace(/(https?:\/\/)/g, "\n$1");

    // Split by newlines, spaces, commas, semicolons
    const allUrls = withSeparatedUrls
      .split(/[\n\s,;]+/)
      .map((url) => url.trim())
      .filter((url) => url.length > 0)
      .filter((url) => url.startsWith("http://") || url.startsWith("https://")); // Only valid URLs

    // Join with newlines (one URL per line)
    const beautified = allUrls.join("\n");
    setUrls(beautified);

    addLog(`✨ Beautified ${allUrls.length} URL(s)`);
  };

  // Helper function to validate and clean a string of URLs (doesn't beautify, just validates)
  const _validateUrlString = (urlString: string): string => { // Reserved for future URL validation
    if (!urlString.trim()) return "";

    // First, insert newlines before every http:// or https:// that's not at the start
    const withSeparatedUrls = urlString.replace(/(https?:\/\/)/g, "\n$1");

    // Split by newlines, spaces, commas, semicolons
    const allUrls = withSeparatedUrls
      .split(/[\n\s,;]+/)
      .map((url) => url.trim())
      .filter((url) => url.length > 0)
      .filter((url) => url.startsWith("http://") || url.startsWith("https://")); // Only valid URLs

    // Join with newlines (one URL per line) - KEEPS query params and fragments
    return allUrls.join("\n");
  };

  // Helper function to validate an array of URLs (doesn't beautify, just validates)
  const _validateUrlArray = (urls: string[]): string[] => { // Reserved for future URL array validation
    return urls
      .map((url) => url.trim())
      .filter((url) => url.length > 0)
      .filter((url) => url.startsWith("http://") || url.startsWith("https://"));
  };

  // ✅ NEW FEATURE: Multiple text boxes management
  const addTextBox = () => {
    const newTextBox: TextBox = {
      id: `textbox-${Date.now()}`,
      sessionName: "",
      urls: "",
      batchTimeout: 90, // ✅ Default timeout for new text boxes
      batchTimeoutUnit: "seconds", // ✅ Default unit
      selected: true, // ✅ NEW: Default checked
    };
    setTextBoxes([...textBoxes, newTextBox]);
    addLog(`➕ Added new text box`);
  };

  const removeTextBox = (id: string) => {
    if (textBoxes.length <= 1) {
      alert("Cannot remove the last text box!");
      return;
    }
    setTextBoxes(textBoxes.filter((box) => box.id !== id));
    addLog(`➖ Removed text box`);
  };

  const updateTextBox = (
    id: string,
    field: "sessionName" | "urls",
    value: string
  ) => {
    setTextBoxes(
      textBoxes.map((box) => (box.id === id ? { ...box, [field]: value } : box))
    );
  };

  // ✅ NEW: Toggle text box selection
  const toggleTextBoxSelection = (id: string) => {
    setTextBoxes(
      textBoxes.map((box) =>
        box.id === id ? { ...box, selected: !box.selected } : box
      )
    );
  };

  // ✅ NEW: Select/Deselect all text boxes
  const toggleSelectAll = () => {
    const allSelected = textBoxes.every((box) => box.selected);
    setTextBoxes(textBoxes.map((box) => ({ ...box, selected: !allSelected })));
  };

  // ✅ NEW: Calculate selected text box statistics
  const selectedTextBoxStats = useMemo(() => {
    const selected = textBoxes.filter((box) => box.selected !== false);
    const totalUrls = selected.reduce((sum, box) => {
      const urls = box.urls
        .split("\n")
        .map((url) => url.trim())
        .filter((url) => url.length > 0)
        .filter(
          (url) => url.startsWith("http://") || url.startsWith("https://")
        );
      return sum + urls.length;
    }, 0);
    return {
      selectedCount: selected.length,
      totalCount: textBoxes.length,
      totalUrls: totalUrls,
      allSelected: textBoxes.every((box) => box.selected !== false),
    };
  }, [textBoxes]);

  // ✅ NEW FEATURE: Beautify all text boxes
  const beautifyAllTextBoxes = () => {
    let totalUrls = 0;
    const beautifiedTextBoxes = textBoxes.map((box) => {
      if (!box.urls.trim()) return box;

      // First, insert newlines before every http:// or https:// that's not at the start
      const withSeparatedUrls = box.urls.replace(/(https?:\/\/)/g, "\n$1");

      // Split by newlines, spaces, commas, semicolons
      const allUrls = withSeparatedUrls
        .split(/[\n\s,;]+/)
        .map((url) => url.trim())
        .filter((url) => url.length > 0)
        .filter(
          (url) => url.startsWith("http://") || url.startsWith("https://")
        ); // Only valid URLs

      totalUrls += allUrls.length;

      // Join with newlines (one URL per line)
      const beautified = allUrls.join("\n");
      return { ...box, urls: beautified };
    });

    setTextBoxes(beautifiedTextBoxes);
    addLog(
      `✨ Beautified ${totalUrls} URL(s) across ${textBoxes.length} text box(es)`
    );
  };

  // ✅ NEW FEATURE: Format timestamp for display
  const formatTimestamp = (isoString: string): string => {
    const date = new Date(isoString);
    const options: Intl.DateTimeFormatOptions = {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      second: "2-digit",
      hour12: true,
    };
    return date.toLocaleString("en-US", options).replace(",", " at");
  };

  const copyLogs = async () => {
    try {
      const logsText = logs.join("\n");
      await navigator.clipboard.writeText(logsText);
      addLog("📋 Logs copied to clipboard!");
      // Show a temporary success message
      setTimeout(() => {
        setLogs((prev) =>
          prev.filter((log) => !log.includes("Logs copied to clipboard"))
        );
      }, 2000);
    } catch (error) {
      log.error("Failed to copy logs:", error);
      alert("Failed to copy logs to clipboard");
    }
  };

  // ========================================
  // 🔔 NOTIFICATION HELPERS
  // ========================================

  // ✅ NEW: Custom notification system (replaces browser Notification API)
  // Uses custom dialog instead of system notifications for better UX
  const showNotification = (title: string, body: string) => {
    // Use custom notification dialog instead of browser notifications
    log.debug("🔔 Custom notification:", title, body);

    // Auto-detect notification type from title/body
    let type: "success" | "error" | "warning" | "info" = "info";
    const combined = `${title} ${body}`.toLowerCase();

    if (
      combined.includes("success") ||
      combined.includes("✅") ||
      combined.includes("generated") ||
      combined.includes("captured")
    ) {
      type = "success";
    } else if (
      combined.includes("error") ||
      combined.includes("❌") ||
      combined.includes("failed")
    ) {
      type = "error";
    } else if (combined.includes("warning") || combined.includes("⚠️")) {
      type = "warning";
    }

    // Show custom notification using notify() function
    return notify(body, { title, type });
  };

  // ========================================
  // 🎯 ROLLING MODE PROGRESS HELPERS
  // ========================================

  // ✅ NEW (Phase 3): Reset rolling mode stats
  const resetRollingModeStats = () => {
    setActiveUrls([]);
    setCompletedUrls([]);
    setFailedUrls([]);
    setRollingModeStats({
      totalUrls: 0,
      completed: 0,
      failed: 0,
      active: 0,
      avgTimePerUrl: 0,
      estimatedTimeRemaining: 0,
    });
  };

  // ✅ NEW (Phase 3): Initialize rolling mode stats
  const initializeRollingModeStats = (totalUrls: number) => {
    setRollingModeStats({
      totalUrls,
      completed: 0,
      failed: 0,
      active: 0,
      avgTimePerUrl: 0,
      estimatedTimeRemaining: 0,
    });
  };

  // ✅ NEW (Phase 3): Update rolling mode stats
  const updateRollingModeStats = (
    completed: number,
    failed: number,
    active: number,
    avgTime: number
  ) => {
    setRollingModeStats((prev) => {
      const remaining = prev.totalUrls - completed - failed;
      const estimatedTimeRemaining = remaining > 0 ? remaining * avgTime : 0;

      return {
        ...prev,
        completed,
        failed,
        active,
        avgTimePerUrl: avgTime,
        estimatedTimeRemaining,
      };
    });
  };

  // ✅ NEW (Phase 4): Initialize URL statuses
  const initializeUrlStatuses = (urls: Array<{ url: string; textBoxName: string }>) => {
    const statusMap = new Map<string, UrlStatus>();
    urls.forEach(({ url, textBoxName }) => {
      statusMap.set(url, {
        url,
        status: 'pending',
        textBoxName,
      });
    });
    setUrlStatuses(statusMap);
    setPerformanceMetrics({
      throughput: 0,
      successRate: 0,
      avgScreenshotsPerUrl: 0,
      totalScreenshots: 0,
      peakConcurrency: 0,
      startTime: Date.now(),
      elapsedTime: 0,
    });
  };

  // ✅ NEW (Phase 4): Update URL status
  const updateUrlStatus = (
    url: string,
    status: 'pending' | 'active' | 'completed' | 'failed',
    additionalData?: Partial<UrlStatus>
  ) => {
    setUrlStatuses((prev) => {
      const newMap = new Map(prev);
      const existing = newMap.get(url);
      if (existing) {
        newMap.set(url, {
          ...existing,
          status,
          ...additionalData,
        });
      }
      return newMap;
    });
  };

  // ✅ NEW (Phase 4): Update performance metrics
  const updatePerformanceMetrics = () => {
    const statuses = Array.from(urlStatuses.values());
    const completed = statuses.filter(s => s.status === 'completed').length;
    const failed = statuses.filter(s => s.status === 'failed').length;
    const active = statuses.filter(s => s.status === 'active').length;
    const total = statuses.length;

    const elapsedTime = (Date.now() - performanceMetrics.startTime) / 1000; // seconds
    const throughput = completed > 0 ? (completed / elapsedTime) * 60 : 0; // URLs per minute
    const successRate = (completed + failed) > 0 ? (completed / (completed + failed)) * 100 : 0;

    const totalScreenshots = statuses
      .filter(s => s.status === 'completed')
      .reduce((sum, s) => sum + (s.screenshotCount || 0), 0);
    const avgScreenshotsPerUrl = completed > 0 ? totalScreenshots / completed : 0;

    setPerformanceMetrics({
      throughput,
      successRate,
      avgScreenshotsPerUrl,
      totalScreenshots,
      peakConcurrency: Math.max(performanceMetrics.peakConcurrency, active),
      startTime: performanceMetrics.startTime,
      elapsedTime,
    });
  };

  // ========================================
  // 🎯 MAIN CAPTURE FUNCTION
  // ========================================

  // ⚡ OPTIMIZATION: Memoize URL list parsing to avoid re-computing on every render
  const urlList = useMemo(() => {
    return urls.split("\n").filter((url) => url.trim());
  }, [urls]);

  // ⚡ OPTIMIZATION: Memoize URL lines for line number rendering
  const urlLines = useMemo(() => {
    return urls.split("\n");
  }, [urls]);

  // ✅ NEW FEATURE: Handle multiple text boxes capture with cross-text-box batching
  const handleMultipleTextBoxesCapture = async () => {
    // ✅ NEW: Filter by selected text boxes first
    const selectedTextBoxes = textBoxes.filter((box) => box.selected !== false);

    if (selectedTextBoxes.length === 0) {
      alert("Please select at least one text box to capture!");
      return;
    }

    // Validate that at least one selected text box has URLs
    const validTextBoxes = selectedTextBoxes.filter(
      (box) => box.urls.trim().length > 0
    );

    if (validTextBoxes.length === 0) {
      alert("Please enter URLs in at least one selected text box!");
      return;
    }

    // Validate all selected text boxes have session names
    const missingNames = validTextBoxes.filter(
      (box) => !box.sessionName.trim()
    );
    if (missingNames.length > 0) {
      alert(
        `Please provide session names for all selected text boxes with URLs!\n\n${missingNames.length} text box(es) missing session names.`
      );
      return;
    }

    setLoading(true);
    clearLogs();

    // ✅ NEW (Phase 3): Reset rolling mode stats
    resetRollingModeStats();

    addLog(
      `🚀 Starting cross-text-box batch capture for ${validTextBoxes.length} text box(es)`
    );

    // ✅ NEW: Check if rolling parallelization is enabled
    if (enableParallelTextBoxes) {
      addLog(`   ⚡ Rolling parallelization mode: ENABLED`);
      addLog(`   🔄 URLs will start immediately as slots become available (no idle time)`);
      addLog(`   🔢 Max concurrent: ${maxParallelUrls} URLs at once`);
    } else {
      addLog(`   📦 Fixed batch mode: ${maxParallelUrls} URLs per batch`);
    }

    try {
      // ✅ STEP 1: Collect all URLs from all text boxes with metadata
      const allUrlsWithMetadata: Array<{
        url: string;
        textBoxId: string;
        textBoxIndex: number;
        sessionName: string;
        batchTimeout: number;
      }> = [];

      const textBoxUrlCounts: { [key: string]: number } = {};
      const textBoxInfo: { [key: string]: TextBox } = {};

      validTextBoxes.forEach((textBox, index) => {
        const boxUrls = textBox.urls
          .split("\n")
          .map((url) => url.trim())
          .filter((url) => url.length > 0)
          .filter(
            (url) => url.startsWith("http://") || url.startsWith("https://")
          );

        textBoxUrlCounts[textBox.id] = boxUrls.length;
        textBoxInfo[textBox.id] = textBox;

        addLog(
          `\n📦 Text Box ${index + 1}: "${textBox.sessionName}" - ${
            boxUrls.length
          } URLs`
        );

        boxUrls.forEach((url) => {
          allUrlsWithMetadata.push({
            url: url,
            textBoxId: textBox.id,
            textBoxIndex: index,
            sessionName: textBox.sessionName,
            batchTimeout: textBox.batchTimeout || 90,
          });
        });
      });

      const totalUrls = allUrlsWithMetadata.length;
      addLog(`\n📊 Total URLs across all text boxes: ${totalUrls}`);

      // ✅ NEW (Phase 3): Initialize rolling mode stats
      if (enableParallelTextBoxes) {
        initializeRollingModeStats(totalUrls);

        // ✅ NEW (Phase 4): Initialize URL statuses
        const urlsWithNames = allUrlsWithMetadata.map(item => ({
          url: item.url,
          textBoxName: item.sessionName,
        }));
        initializeUrlStatuses(urlsWithNames);
      }

      // ✅ STEP 2: Create batches based on mode (rolling vs fixed)
      const batchSize = maxParallelUrls;
      const batches: (typeof allUrlsWithMetadata)[] = [];

      if (enableParallelTextBoxes) {
        // ✅ ROLLING MODE: Single batch with ALL URLs
        batches.push(allUrlsWithMetadata);
        addLog(`   🔄 Rolling mode: Processing all ${totalUrls} URLs in one batch`);
        addLog(`   ⏱️ Estimated time: ~${Math.ceil(totalUrls / maxParallelUrls)} minutes (with ${maxParallelUrls} concurrent)`);
      } else {
        // ✅ FIXED BATCH MODE: Split into batches of maxParallelUrls
        for (let i = 0; i < allUrlsWithMetadata.length; i += batchSize) {
          batches.push(allUrlsWithMetadata.slice(i, i + batchSize));
        }
        addLog(
          `   🔢 Created ${batches.length} batches of up to ${batchSize} URLs each`
        );
      }

      // ✅ STEP 3: Track results per text box
      const textBoxResults: { [key: string]: any[] } = {};
      const textBoxProcessedCounts: { [key: string]: number } = {};
      // ✅ FIX: Track which text boxes have already had sessions created (prevent duplicates)
      const createdSessions = new Set<string>();

      validTextBoxes.forEach((tb) => {
        textBoxResults[tb.id] = [];
        textBoxProcessedCounts[tb.id] = 0;
      });

      // ✅ STEP 4: Process each batch sequentially
      for (let batchNum = 0; batchNum < batches.length; batchNum++) {
        const batch = batches[batchNum];
        const batchUrls = batch.map((item) => item.url);

        // Determine timeout for this batch (use maximum from all text boxes in batch)
        const batchTimeout = Math.max(
          ...batch.map((item) => item.batchTimeout)
        );

        // Log batch info
        const textBoxesInBatch = [
          ...new Set(batch.map((item) => item.sessionName)),
        ];

        if (enableParallelTextBoxes) {
          // ✅ ROLLING MODE: Log differently
          addLog(`\n🔄 Rolling Mode: Processing ${batchUrls.length} URLs (${maxParallelUrls} concurrent)`);
          addLog(`   📝 Text boxes: ${textBoxesInBatch.join(", ")}`);

          // Calculate timeout: batchTimeout is per text box, multiply by number of text boxes
          const numTextBoxes = textBoxesInBatch.length;
          const calculatedTimeout = batchTimeout * numTextBoxes;
          const finalTimeout = Math.min(calculatedTimeout, 7200);

          addLog(`   ⏱️ Timeout: ${batchTimeout}s/text box × ${numTextBoxes} text boxes = ${calculatedTimeout}s`);
          if (calculatedTimeout > 7200) {
            addLog(`   ⏱️ Capped at maximum: 7200s (2 hours)`);
          }
          addLog(`   💡 URLs will start immediately as slots free up`);
        } else {
          // ✅ FIXED BATCH MODE: Original logging
          addLog(
            `\n⚡ Batch ${batchNum + 1}/${batches.length}: Processing ${
              batchUrls.length
            } URLs`
          );
          addLog(
            `   📝 Text boxes in this batch: ${textBoxesInBatch.join(", ")}`
          );
          addLog(
            `   ⏱️ Batch timeout: ${batchTimeout}s (${batchTimeout / 2}s per URL)`
          );

          // ✅ NEW: Log URLs being processed in this batch
          addLog(`   📋 URLs in this batch:`);
          batchUrls.forEach((url, idx) => {
            const shortUrl = url.length > 80 ? url.substring(0, 77) + "..." : url;
            addLog(`      ${idx + 1}. ${shortUrl}`);
          });
        }

        // ✅ NEW: Track batch start time
        const batchStartTime = Date.now();

        // ✅ NEW (Phase 4): Mark first batch of URLs as active (up to maxParallelUrls)
        if (enableParallelTextBoxes) {
          // Only mark the first maxParallelUrls as active (the rest stay pending)
          const urlsToActivate = batch.slice(0, maxParallelUrls);
          urlsToActivate.forEach((item) => {
            updateUrlStatus(item.url, 'active', {
              startTime: Date.now(),
            });
          });
          // Update metrics to show active URLs
          updatePerformanceMetrics();

          // ✅ NEW (Phase 4): Start interval to update UI while processing
          const updateInterval = setInterval(() => {
            // Force re-render by updating performance metrics
            // This will update elapsed times for active URLs
            setPerformanceMetrics(prev => ({
              ...prev,
              elapsedTime: (Date.now() - prev.startTime) / 1000
            }));
          }, 1000); // Update every second

          // Store interval ID to clear it later
          (window as any).__rollingProgressInterval = updateInterval;

          // ✅ OPTION 4: Heartbeat for long batches (every 30 seconds)
          let heartbeatCount = 0;
          const heartbeatInterval = setInterval(() => {
            heartbeatCount++;
            const elapsed = Math.floor((Date.now() - batchStartTime) / 1000);
            const completed = Object.values(urlStatuses).filter(s => s.status === 'completed').length;
            const active = Object.values(urlStatuses).filter(s => s.status === 'active').length;
            const avgTime = completed > 0 ? elapsed / completed : 0;

            addLog(`   ⏱️  Heartbeat #${heartbeatCount}: ${completed}/${batchUrls.length} completed, ${active} active, ${elapsed}s elapsed (avg ${avgTime.toFixed(1)}s/URL)`);
          }, 30000); // Every 30 seconds

          // Store heartbeat interval to clear later
          (window as any).__rollingHeartbeatInterval = heartbeatInterval;
        }

        try {
          // Send batch to backend
          const controller = new AbortController();

          // ✅ NEW (Phase 4): Calculate appropriate timeout for rolling mode
          let requestTimeout = config.requestTimeout;
          if (enableParallelTextBoxes) {
            // Rolling mode: timeout = batchTimeout × number of text boxes
            const numTextBoxes = textBoxesInBatch.length;
            const calculatedTimeout = batchTimeout * numTextBoxes;
            requestTimeout = Math.min(calculatedTimeout * 1000, 7200000); // Convert to ms, cap at 2 hours
            addLog(`   ⏱️ Frontend request timeout: ${(requestTimeout / 1000).toFixed(0)}s (${batchTimeout}s × ${numTextBoxes} text boxes)`);
          }

          const timeoutId = setTimeout(
            () => controller.abort(),
            requestTimeout
          );

          addLog(`   🚀 Sending batch to backend...`);
          console.log(`🐛 DEBUG: headless value = ${headless}`);

          const response = await fetch(
            `${config.apiBaseUrl}/api/screenshots/capture`,
            {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                urls: batchUrls,
                viewport_width: 1366,
                viewport_height: 768,
                capture_mode: captureMode,
                use_stealth: useStealth,
                use_real_browser: useRealBrowser,
                headless: headless,
                browser_engine: browserEngine,
                base_url: baseUrl,
                words_to_remove: JSON.stringify(wordsToRemove),
                cookies: cookies,
                local_storage: localStorageData,
                track_network: trackNetwork,
                auto_expand_dropdowns: autoExpandDropdowns,
                segment_overlap: segmentOverlap,
                segment_scroll_delay: segmentScrollDelay,
                segment_max_segments: segmentMaxSegments,
                segment_skip_duplicates: segmentSkipDuplicates,
                segment_smart_lazy_load: segmentSmartLazyLoad,
                batch_timeout: batchTimeout,
                max_parallel_urls: maxParallelUrls,
                enable_rolling_parallelization: enableParallelTextBoxes, // ✅ NEW: Rolling parallelization
                non_scrollable_urls: JSON.stringify(nonScrollableUrls), // ✅ NEW: Non-scrollable URLs
              }),
              signal: controller.signal,
            }
          );

          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const data = await response.json();

          // ✅ NEW: Calculate batch processing time
          const batchEndTime = Date.now();
          const batchDuration = (
            (batchEndTime - batchStartTime) /
            1000
          ).toFixed(1);

          if (enableParallelTextBoxes) {
            addLog(`   ⏱️ Rolling mode completed in ${batchDuration}s`);
            addLog(`   🚀 Average time per URL: ${(parseFloat(batchDuration) / batchUrls.length).toFixed(1)}s (wall-clock)`);
          } else {
            addLog(`   ⏱️ Batch completed in ${batchDuration}s`);
          }

          // ✅ STEP 5: Distribute results back to text boxes
          const completedTextBoxIds = new Set<string>();

          // ✅ NEW (Phase 3): Track rolling mode progress
          let successCount = 0;
          let failCount = 0;
          const completedUrlsList: string[] = [];
          const failedUrlsList: string[] = [];

          // ✅ NEW: Log detailed per-URL results
          addLog(`   📊 Per-URL Results:`);
          batch.forEach((item, index) => {
            const result = data.results[index];
            const shortUrl =
              item.url.length > 60
                ? item.url.substring(0, 57) + "..."
                : item.url;

            if (result.status === "success") {
              successCount++;
              completedUrlsList.push(item.url);
              const screenshotCount = result.screenshot_paths?.length || 1;
              const processingTime = result.processing_time
                ? `${result.processing_time.toFixed(1)}s`
                : "N/A";
              addLog(
                `      ✅ ${shortUrl} (${processingTime}, ${screenshotCount} screenshot${
                  screenshotCount > 1 ? "s" : ""
                })`
              );

              // ✅ NEW (Phase 4): Update URL status
              if (enableParallelTextBoxes) {
                updateUrlStatus(item.url, 'completed', {
                  endTime: Date.now(),
                  duration: result.processing_time,
                  screenshotCount,
                });
              }
            } else {
              failCount++;
              failedUrlsList.push(item.url);
              const errorMsg = result.error || "Unknown error";
              const shortError =
                errorMsg.length > 50
                  ? errorMsg.substring(0, 47) + "..."
                  : errorMsg;
              addLog(`      ❌ ${shortUrl} - ${shortError}`);

              // ✅ NEW (Phase 4): Update URL status
              if (enableParallelTextBoxes) {
                updateUrlStatus(item.url, 'failed', {
                  endTime: Date.now(),
                  error: errorMsg,
                });
              }
            }

            textBoxResults[item.textBoxId].push(result);
            textBoxProcessedCounts[item.textBoxId]++;

            // Check if this text box is complete
            if (
              textBoxProcessedCounts[item.textBoxId] ===
              textBoxUrlCounts[item.textBoxId]
            ) {
              completedTextBoxIds.add(item.textBoxId);
              addLog(
                `   ✅ Text Box "${item.sessionName}" complete! (${
                  textBoxProcessedCounts[item.textBoxId]
                }/${textBoxUrlCounts[item.textBoxId]} URLs)`
              );
            }
          });

          // ✅ NEW (Phase 3): Update rolling mode stats
          if (enableParallelTextBoxes) {
            setCompletedUrls((prev) => [...prev, ...completedUrlsList]);
            setFailedUrls((prev) => [...prev, ...failedUrlsList]);

            const avgTime = parseFloat(batchDuration) / batchUrls.length;
            updateRollingModeStats(
              completedUrlsList.length + completedUrls.length,
              failedUrlsList.length + failedUrls.length,
              0, // active URLs (all completed in this batch)
              avgTime
            );

            // ✅ NEW (Phase 4): Update performance metrics
            updatePerformanceMetrics();

            // ✅ NEW (Phase 4): Clear the update interval
            if ((window as any).__rollingProgressInterval) {
              clearInterval((window as any).__rollingProgressInterval);
              (window as any).__rollingProgressInterval = null;
            }

            // ✅ OPTION 4: Clear the heartbeat interval
            if ((window as any).__rollingHeartbeatInterval) {
              clearInterval((window as any).__rollingHeartbeatInterval);
              (window as any).__rollingHeartbeatInterval = null;
            }

            addLog(
              `   📈 Rolling Summary: ✅ ${successCount} succeeded, ❌ ${failCount} failed`
            );
          } else {
            addLog(
              `   📈 Batch Summary: ✅ ${successCount} succeeded, ❌ ${failCount} failed`
            );
          }

          // ✅ NEW: Log timeout warnings for slow URLs
          const perUrlTimeout = batchTimeout / 2;
          const slowUrls = data.results.filter(
            (r: any) =>
              r.processing_time && r.processing_time > perUrlTimeout * 0.8
          );
          if (slowUrls.length > 0) {
            addLog(
              `   ⚠️ Warning: ${
                slowUrls.length
              } URL(s) took >80% of timeout (${(perUrlTimeout * 0.8).toFixed(
                0
              )}s)`
            );
            slowUrls.forEach((r: any) => {
              const shortUrl =
                r.url.length > 60 ? r.url.substring(0, 57) + "..." : r.url;
              addLog(
                `      ⏱️ ${shortUrl} took ${r.processing_time.toFixed(1)}s`
              );
            });
          }

          // ✅ NEW: Log overall progress
          const totalProcessed = Object.values(textBoxProcessedCounts).reduce(
            (a: number, b: number) => a + b,
            0
          );
          const totalUrlsCount = Object.values(textBoxUrlCounts).reduce(
            (a: number, b: number) => a + b,
            0
          );
          const progressPercent = (
            (totalProcessed / totalUrlsCount) *
            100
          ).toFixed(1);
          addLog(
            `   📊 Overall Progress: ${totalProcessed}/${totalUrlsCount} URLs (${progressPercent}%)`
          );

          // ✅ STEP 5.5: Generate Word documents immediately for completed text boxes
          for (const textBoxId of completedTextBoxIds) {
            const textBox = textBoxInfo[textBoxId];
            const results = textBoxResults[textBoxId];
            const successResults = results.filter(
              (r) => r.status === "success"
            );

            if (successResults.length > 0) {
              addLog(
                `   📄 Generating Word document for "${textBox.sessionName}" (${successResults.length} successful screenshots)...`
              );

              // ✅ FIX: Wrap entire Word doc generation in try-catch
              try {
                // Create session screenshots array
                const sessionScreenshots = successResults.flatMap((r: any) => {
                  if (r.screenshot_paths && r.screenshot_paths.length > 0) {
                    return r.screenshot_paths.map((path: string) => ({
                      filename: path.split("/").pop() || path,
                      path: path,
                      url: r.url,
                      timestamp: new Date().toISOString(),
                      quality_score: r.quality_score,
                      segments: r.segment_count,
                    }));
                  } else if (r.screenshot_path) {
                    return [
                      {
                        filename:
                          r.screenshot_path.split("/").pop() ||
                          r.screenshot_path,
                        path: r.screenshot_path,
                        url: r.url,
                        timestamp: new Date().toISOString(),
                        quality_score: r.quality_score,
                      },
                    ];
                  }
                  return [];
                });

                // Create session
                // ✅ FIX: Use timestamp for session number to avoid race conditions
                const sessionNumber = Date.now();
                const newSession: Session = {
                  id: `session-${Date.now()}-${textBoxId}`,
                  name: textBox.sessionName,
                  defaultName: `Session ${sessionNumber}`,
                  timestamp: new Date().toISOString(),
                  screenshots: sessionScreenshots,
                  urls: textBox.urls.split("\n").filter((u) => u.trim()),
                  duration: 0,
                  settings: {
                    captureMode: captureMode,
                    useStealth: useStealth,
                    useRealBrowser: useRealBrowser,
                  },
                };

                // ✅ FIX: Only create session if not already created (prevent duplicates)
                if (!createdSessions.has(textBoxId)) {
                  setSessions((prev) => [newSession, ...prev]);
                  createdSessions.add(textBoxId);

                  // Generate Word document immediately
                  await generateWordDocumentForSession(
                    textBox.sessionName,
                    sessionScreenshots
                  );

                  addLog(
                    `   ✅ Word document generated: ${textBox.sessionName}.docx`
                  );
                } else {
                  addLog(
                    `   ⚠️ Session already created for "${textBox.sessionName}" - skipping duplicate`
                  );
                }
              } catch (docError: any) {
                addLog(
                  `   ❌ Failed to generate Word document for "${textBox.sessionName}": ${docError.message}`
                );
              }
            } else {
              addLog(
                `   ⚠️ Skipping "${textBox.sessionName}" - no successful screenshots`
              );
            }
          }

          // ✅ Update progress after batch completes successfully
          setProgress({
            current: Math.min((batchNum + 1) * batchSize, totalUrls),
            total: totalUrls,
          });
        } catch (error: any) {
          // ✅ NEW (Phase 4): Clear the update interval on error
          if (enableParallelTextBoxes && (window as any).__rollingProgressInterval) {
            clearInterval((window as any).__rollingProgressInterval);
            (window as any).__rollingProgressInterval = null;
          }

          // ✅ OPTION 4: Clear the heartbeat interval on error
          if (enableParallelTextBoxes && (window as any).__rollingHeartbeatInterval) {
            clearInterval((window as any).__rollingHeartbeatInterval);
            (window as any).__rollingHeartbeatInterval = null;
          }

          if (enableParallelTextBoxes) {
            addLog(`   ❌ Rolling mode failed: ${error.message}`);
          } else {
            addLog(`   ❌ Batch ${batchNum + 1} failed: ${error.message}`);
          }

          // Mark all URLs in this batch as failed
          const completedTextBoxIds = new Set<string>();

          batch.forEach((item) => {
            textBoxResults[item.textBoxId].push({
              url: item.url,
              status: "error",
              error: error.message,
            });
            textBoxProcessedCounts[item.textBoxId]++;

            // ✅ FIX: Check if this text box is complete (even with failures)
            if (
              textBoxProcessedCounts[item.textBoxId] ===
              textBoxUrlCounts[item.textBoxId]
            ) {
              completedTextBoxIds.add(item.textBoxId);
              addLog(
                `   ✅ Text Box "${item.sessionName}" complete! (${
                  textBoxProcessedCounts[item.textBoxId]
                }/${textBoxUrlCounts[item.textBoxId]} URLs)`
              );
            }
          });

          // ✅ FIX: Generate Word documents for completed text boxes (even if batch failed)
          for (const textBoxId of completedTextBoxIds) {
            const textBox = textBoxInfo[textBoxId];
            const results = textBoxResults[textBoxId];
            const successResults = results.filter(
              (r) => r.status === "success"
            );

            if (successResults.length > 0) {
              addLog(
                `   📄 Generating Word document for "${textBox.sessionName}" (${successResults.length} successful screenshots)...`
              );

              try {
                // Create session screenshots array
                const sessionScreenshots = successResults.flatMap((r: any) => {
                  if (r.screenshot_paths && r.screenshot_paths.length > 0) {
                    return r.screenshot_paths.map((path: string) => ({
                      filename: path.split("/").pop() || path,
                      path: path,
                      url: r.url,
                      timestamp: new Date().toISOString(),
                      quality_score: r.quality_score,
                      segments: r.segment_count,
                    }));
                  } else if (r.screenshot_path) {
                    return [
                      {
                        filename:
                          r.screenshot_path.split("/").pop() ||
                          r.screenshot_path,
                        path: r.screenshot_path,
                        url: r.url,
                        timestamp: new Date().toISOString(),
                        quality_score: r.quality_score,
                      },
                    ];
                  }
                  return [];
                });

                // Create session
                const sessionNumber = Date.now();
                const newSession: Session = {
                  id: `session-${Date.now()}-${textBoxId}`,
                  name: textBox.sessionName,
                  defaultName: `Session ${sessionNumber}`,
                  timestamp: new Date().toISOString(),
                  screenshots: sessionScreenshots,
                  urls: textBox.urls.split("\n").filter((u) => u.trim()),
                  duration: 0,
                  settings: {
                    captureMode: captureMode,
                    useStealth: useStealth,
                    useRealBrowser: useRealBrowser,
                  },
                };

                // ✅ FIX: Only create session if not already created (prevent duplicates)
                if (!createdSessions.has(textBoxId)) {
                  setSessions((prev) => [newSession, ...prev]);
                  createdSessions.add(textBoxId);

                  // Generate Word document immediately
                  await generateWordDocumentForSession(
                    textBox.sessionName,
                    sessionScreenshots
                  );

                  addLog(
                    `   ✅ Word document generated: ${textBox.sessionName}.docx`
                  );
                } else {
                  addLog(
                    `   ⚠️ Session already created for "${textBox.sessionName}" - skipping duplicate`
                  );
                }
              } catch (docError: any) {
                addLog(
                  `   ❌ Failed to generate Word document for "${textBox.sessionName}": ${docError.message}`
                );
              }
            } else {
              addLog(
                `   ⚠️ Skipping "${textBox.sessionName}" - no successful screenshots`
              );
            }
          }

          // ✅ Update progress even if batch fails
          setProgress({
            current: Math.min((batchNum + 1) * batchSize, totalUrls),
            total: totalUrls,
          });
        }
      }

      // ✅ STEP 6: All Word documents have been generated immediately as text boxes completed
      if (enableParallelTextBoxes) {
        addLog(`\n✅ Rolling parallelization complete!`);
        addLog(`   📊 Processed ${validTextBoxes.length} text box(es)`);
        addLog(`   🔄 Mode: Rolling (zero idle time)`);
        addLog(`   🔗 Total URLs: ${totalUrls}`);
      } else {
        addLog(`\n✅ Cross-text-box batch capture complete!`);
        addLog(`   📊 Processed ${validTextBoxes.length} text box(es)`);
        addLog(`   📦 Total batches: ${batches.length}`);
        addLog(`   🔗 Total URLs: ${totalUrls}`);
      }
    } catch (error: any) {
      addLog(`❌ Batch capture failed: ${error.message}`);
      alert(`Batch capture failed: ${error.message}`);
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0 });
    }
  };

  // ✅ NEW FEATURE: Capture screenshots for a single text box
  const _captureSingleTextBox = async (textBox: TextBox, urls: string[]) => { // Reserved for future single text box capture
    const captureStartTime = Date.now();

    try {
      addLog(`   📸 Capturing ${urls.length} URL(s)...`);

      const controller = new AbortController();
      const timeoutId = setTimeout(
        () => controller.abort(),
        config.requestTimeout
      );

      const response = await fetch(
        `${config.apiBaseUrl}/api/screenshots/capture`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            urls: urls,
            viewport_width: 1366, // Standard laptop resolution (most common)
            viewport_height: 768,
            capture_mode: captureMode,
            use_stealth: useStealth,
            use_real_browser: useRealBrowser,
            headless: headless, // ✅ NEW: Headless mode setting
            browser_engine: browserEngine,
            base_url: baseUrl,
            words_to_remove: JSON.stringify(wordsToRemove),
            cookies: cookies,
            local_storage: localStorageData,
            track_network: trackNetwork,
            auto_expand_dropdowns: autoExpandDropdowns, // ✅ NEW: Auto expand dropdowns
            segment_overlap: segmentOverlap,
            segment_scroll_delay: segmentScrollDelay,
            segment_max_segments: segmentMaxSegments,
            segment_skip_duplicates: segmentSkipDuplicates,
            segment_smart_lazy_load: segmentSmartLazyLoad,
            batch_timeout: textBox.batchTimeout || 90, // ✅ NEW: Send per-text-box timeout to backend
            max_parallel_urls: maxParallelUrls, // ✅ NEW: Batch size for processing
            non_scrollable_urls: JSON.stringify(nonScrollableUrls), // ✅ NEW: Non-scrollable URLs
          }),
          signal: controller.signal,
        }
      );

      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      const successCount = data.results.filter(
        (r: any) => r.status === "success"
      ).length;
      const failCount = data.results.filter(
        (r: any) => r.status === "error"
      ).length;

      addLog(`   ✅ Success: ${successCount}, ❌ Failed: ${failCount}`);

      // Create session with custom name
      if (successCount > 0) {
        const sessionScreenshots = data.results
          .filter((r: any) => r.status === "success")
          .flatMap((r: any) => {
            if (r.screenshot_paths && r.screenshot_paths.length > 0) {
              return r.screenshot_paths.map((path: string, _idx: number) => ({ // idx reserved for future use
                filename: path.split("/").pop() || path,
                path: path,
                url: r.url,
                timestamp: new Date().toISOString(),
                quality_score: r.quality_score,
                segments: r.segment_count,
              }));
            } else if (r.screenshot_path) {
              return [
                {
                  filename:
                    r.screenshot_path.split("/").pop() || r.screenshot_path,
                  path: r.screenshot_path,
                  url: r.url,
                  timestamp: new Date().toISOString(),
                  quality_score: r.quality_score,
                },
              ];
            }
            return [];
          });

        const captureDuration = Date.now() - captureStartTime;
        const sessionNumber = sessions.length + 1;

        const newSession: Session = {
          id: `session-${Date.now()}`,
          name: textBox.sessionName, // ✅ Use custom session name from textBox
          defaultName: `Session ${sessionNumber}`,
          timestamp: new Date().toISOString(),
          screenshots: sessionScreenshots,
          urls: urls,
          duration: captureDuration,
          settings: {
            captureMode: captureMode,
            useStealth: useStealth,
            useRealBrowser: useRealBrowser,
          },
        };

        setSessions([newSession, ...sessions]);
        addLog(`   🗂️ Session created: ${textBox.sessionName}`);
        addLog(`   📅 Created: ${formatTimestamp(newSession.timestamp)}`);
        addLog(`   📊 Total segments: ${sessionScreenshots.length}`);

        // ✅ NEW: Auto-generate Word document with session name
        await generateWordDocumentForSession(
          textBox.sessionName,
          sessionScreenshots
        );
      }
    } catch (error: any) {
      addLog(`   ❌ Error: ${error.message}`);
      throw error;
    }
  };

  const handleCapture = async () => {
    // ✅ NEW FEATURE: Check if multiple text boxes mode is enabled
    if (enableMultipleTextBoxes) {
      // Process each text box separately
      await handleMultipleTextBoxesCapture();
      return;
    }

    // ✅ EXISTING: Single text box mode
    // Use memoized urlList instead of re-parsing

    if (urlList.length === 0) {
      alert("Please enter at least one URL");
      return;
    }

    // Validate URLs
    const invalidUrls = urlList.filter((url) => {
      try {
        const parsedUrl = new URL(url);
        // Only allow http and https protocols
        if (!["http:", "https:"].includes(parsedUrl.protocol)) {
          return true; // Invalid
        }
        return false; // Valid
      } catch {
        return true; // Invalid
      }
    });

    if (invalidUrls.length > 0) {
      const message = `Invalid URL(s) detected:\n\n${invalidUrls.join(
        "\n"
      )}\n\nPlease use full URLs with http:// or https://\n\nExamples:\n- https://example.com\n- https://google.com\n- http://localhost:3000`;
      alert(message);
      addLog(`❌ Invalid URLs: ${invalidUrls.join(", ")}`);
      return;
    }

    setLoading(true);
    setResults([]);
    setProgress({ current: 0, total: urlList.length });
    clearLogs();
    addLog(`Starting capture for ${urlList.length} URLs`);

    // Track start time for session duration
    const captureStartTime = Date.now();

    // Log capture mode
    const modeNames = {
      viewport: "Viewport only (single screenshot)",
      fullpage: "Full page (single tall screenshot)",
      segmented: "Segmented (multiple viewport screenshots)",
    };
    addLog(`Capture mode: ${modeNames[captureMode as keyof typeof modeNames]}`);

    if (captureMode === "segmented") {
      addLog(`  ├─ Overlap: ${segmentOverlap}%`);
      addLog(`  ├─ Scroll delay: ${segmentScrollDelay}ms`);
      addLog(`  ├─ Max segments: ${segmentMaxSegments}`);
      addLog(`  ├─ Skip duplicates: ${segmentSkipDuplicates ? "ON" : "OFF"}`);
      addLog(`  └─ Smart lazy-load: ${segmentSmartLazyLoad ? "ON" : "OFF"}`);
    }

    addLog(`Stealth mode: ${useStealth ? "ON (anti-bot detection)" : "OFF"}`);
    addLog(
      `Real browser: ${
        useRealBrowser ? "ON (visible window)" : "OFF (headless)"
      }`
    );
    addLog(
      `Network tracking: ${trackNetwork ? "ON (capturing HTTP events)" : "OFF"}`
    );

    try {
      addLog("Sending request to backend...");

      // ✅ FIXED: Use config for API URL and add timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(
        () => controller.abort(),
        config.requestTimeout
      );

      try {
        const response = await fetch(
          `${config.apiBaseUrl}/api/screenshots/capture`, // ✅ From config
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            signal: controller.signal, // ✅ Add timeout support
            body: JSON.stringify({
              urls: urlList,
              viewport_width: 1366, // Standard laptop resolution (most common)
              viewport_height: 768,
              capture_mode: captureMode,
              use_stealth: useStealth,
              use_real_browser: useRealBrowser,
              headless: headless, // ✅ NEW: Headless mode setting
              browser_engine: browserEngine, // "playwright" or "camoufox"
              base_url: baseUrl,
              words_to_remove: JSON.stringify(wordsToRemove), // ✅ Send as JSON array of WordTransformation objects
              cookies: cookies, // Add cookies for authentication
              local_storage: localStorageData, // Add localStorage for authentication
              segment_overlap: segmentOverlap,
              segment_scroll_delay: segmentScrollDelay,
              segment_max_segments: segmentMaxSegments,
              segment_skip_duplicates: segmentSkipDuplicates,
              segment_smart_lazy_load: segmentSmartLazyLoad,
              track_network: trackNetwork, // ✅ NEW: Network event tracking
              auto_expand_dropdowns: autoExpandDropdowns, // ✅ NEW: Auto expand dropdowns
              max_parallel_urls: maxParallelUrls, // ✅ NEW: Batch size for processing
              non_scrollable_urls: JSON.stringify(nonScrollableUrls), // ✅ NEW: Non-scrollable URLs
            }),
          }
        );

        clearTimeout(timeoutId); // ✅ Clear timeout on success

        addLog("Received response from backend");

        // Log raw response for debugging
        const responseText = await response.text();
        addLog(`Raw response: ${responseText.substring(0, 200)}...`);
        log.debug("Full backend response:", responseText);

        let data;
        try {
          data = JSON.parse(responseText);
        } catch (parseError: any) {
          throw new Error(`Failed to parse JSON: ${parseError.message}`);
        }

        // Safety check
        if (!data || !data.results || !Array.isArray(data.results)) {
          throw new Error(
            `Invalid response from backend: ${JSON.stringify(data)}`
          );
        }

        addLog(`Parsed ${data.results.length} results successfully`);
        log.debug("Parsed results:", data.results);

        setResults(data.results);
        addLog(`Capture complete: ${data.results.length} results received`);

        if (data.cancelled) {
          addLog("⚠️ Operation was cancelled by user");
          alert("Screenshot capture was cancelled");
        } else {
          const successCount = data.results.filter(
            (r: ScreenshotResult) => r.status === "success"
          ).length;
          const failedCount = data.results.filter(
            (r: ScreenshotResult) => r.status === "failed"
          ).length;
          const cancelledCount = data.results.filter(
            (r: ScreenshotResult) => r.status === "cancelled"
          ).length;
          addLog(
            `✅ Success: ${successCount}, ❌ Failed: ${failedCount}, ⏹️ Cancelled: ${cancelledCount}`
          );

          // ✅ Show custom dialog based on URL count
          log.debug(
            `🔍 Dialog check: urlList.length=${urlList.length}, successCount=${successCount}`
          );
          if (urlList.length === 1 && successCount === 1) {
            // Single URL - show custom dialog
            log.debug("🔔 Showing single URL dialog");
            showNotification(
              "📸 Screenshot Captured",
              `Screenshot captured successfully for ${urlList[0]}`
            );
            // Show custom dialog after notification
            await showCustomAlert(
              "📸 Screenshot Captured",
              `Screenshot captured successfully!\n\nURL: ${urlList[0]}`
            );
          } else if (urlList.length > 1 && successCount > 0) {
            // Multiple URLs - show custom dialog with summary
            log.debug("🔔 Showing multiple URLs dialog");
            showNotification(
              "📸 Screenshots Captured",
              `${successCount} of ${urlList.length} screenshots captured successfully`
            );
            // Show custom dialog after notification
            const summary = `✅ Success: ${successCount}\n❌ Failed: ${failedCount}${
              cancelledCount > 0 ? `\n⏹️ Cancelled: ${cancelledCount}` : ""
            }`;
            await showCustomAlert(
              "📸 Screenshots Captured",
              `Capture complete!\n\n${summary}\n\nTotal: ${urlList.length} URLs`
            );
          } else {
            log.debug("⚠️ No dialog shown (conditions not met)");
          }

          // Create session if there are successful screenshots
          if (successCount > 0) {
            const captureDuration = Date.now() - captureStartTime;

            // Build screenshots array from successful results
            const sessionScreenshots: Screenshot[] = data.results
              .filter((r: ScreenshotResult) => r.status === "success")
              .flatMap((r: ScreenshotResult) => {
                if (r.screenshot_paths && r.screenshot_paths.length > 0) {
                  // Segmented capture - multiple screenshots
                  return r.screenshot_paths.map(
                    (path: string, _index: number) => ({ // index reserved for future use
                      filename: path.split("/").pop() || path,
                      path: path,
                      url: r.url,
                      timestamp: new Date().toISOString(),
                      quality_score: r.quality_score,
                      segments: r.screenshot_paths?.length ?? 0,
                    })
                  );
                } else if (r.screenshot_path) {
                  // Single screenshot
                  return [
                    {
                      filename:
                        r.screenshot_path.split("/").pop() || r.screenshot_path,
                      path: r.screenshot_path,
                      url: r.url,
                      timestamp: new Date().toISOString(),
                      quality_score: r.quality_score,
                    },
                  ];
                }
                return [];
              });

            // Create session
            const newSession = createSession(
              sessionScreenshots,
              urlList,
              captureDuration
            );
            addLog(`🗂️ Session created: ${newSession.name}`);
            addLog(`   📅 Created: ${formatTimestamp(newSession.timestamp)}`);
            addLog(`   📊 Total segments: ${sessionScreenshots.length}`);
          }
        }
      } catch (fetchError: any) {
        // ✅ FIXED: Handle timeout errors specifically
        if (fetchError.name === "AbortError") {
          throw new Error(
            `Request timed out after ${
              config.requestTimeout / 1000
            } seconds. The backend may be slow or unresponsive.`
          );
        }
        throw fetchError;
      }
    } catch (error: any) {
      log.error("Error:", error);
      const errorMessage = error?.message || String(error);
      addLog(`❌ Error: ${errorMessage}`);
      addLog(`❌ Stack: ${error?.stack || "No stack trace"}`);
      alert(
        `Error capturing screenshots: ${errorMessage}\n\nCheck logs for details.`
      );
    } finally {
      setLoading(false);
      addLog("Capture operation finished");
    }
  };

  // ⚡ OPTIMIZATION: Wrap with useCallback to prevent recreation
  const handleStop = useCallback(async () => {
    try {
      addLog("🛑 Stop button clicked - sending cancel request...");
      await fetch(`${config.apiBaseUrl}/api/screenshots/cancel`, {
        // ✅ Use config
        method: "POST",
      });
      addLog("Cancel request sent to backend");
    } catch (error) {
      log.error("Error stopping capture:", error);
      addLog(`❌ Error sending cancel request: ${error}`);
    }
  }, [addLog]); // ✅ Stable dependency


  const handleCleanupTabs = useCallback(async () => {
    try {
      addLog("🧹 Closing all open tabs...");
      const response = await fetch(`${config.apiBaseUrl}/api/tabs/cleanup`, {
        method: "POST",
      });
      
      if (response.ok) {
        addLog("✅ All tabs closed successfully!");
      } else {
        addLog("❌ Failed to close tabs");
      }
    } catch (error) {
      console.error("Tab cleanup error:", error);
      addLog(`❌ Error closing tabs: ${error}`);
    }
  }, [addLog]);

  const handleRetry = async (url: string) => {
    try {
      addLog(`🔄 Retrying screenshot for: ${url}`);
      const response = await fetch(
        `http://127.0.0.1:8001/api/screenshots/retry?url=${encodeURIComponent(
          url
        )}`,
        {
          method: "POST",
        }
      );

      const result = await response.json();
      addLog(`✅ Retry completed for: ${url} - Status: ${result.status}`);

      // Update results
      setResults((prev) => prev.map((r) => (r.url === url ? result : r)));
    } catch (error) {
      log.error("Error:", error);
      addLog(`❌ Retry failed for: ${url} - ${error}`);
      alert("Error retrying screenshot");
    }
  };

  const handleOpenFile = async (filePath: string) => {
    try {
      addLog(`📂 Opening file: ${filePath}`);
      const response = await fetch(
        `http://127.0.0.1:8001/api/screenshots/open-file?path=${encodeURIComponent(
          filePath
        )}`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        addLog(`✅ File opened successfully`);
      } else {
        throw new Error("Failed to open file");
      }
    } catch (error) {
      log.error("Error:", error);
      addLog(`❌ Failed to open file: ${error}`);
      alert("Error opening file");
    }
  };

  const handleOpenFolder = async (filePath: string) => {
    try {
      addLog(`📁 Opening folder for: ${filePath}`);
      const response = await fetch(
        `http://127.0.0.1:8001/api/screenshots/open-folder?path=${encodeURIComponent(
          filePath
        )}`,
        {
          method: "POST",
        }
      );

      if (response.ok) {
        addLog(`✅ Folder opened successfully`);
      } else {
        throw new Error("Failed to open folder");
      }
    } catch (error) {
      log.error("Error:", error);
      addLog(`❌ Failed to open folder: ${error}`);
      alert("Error opening folder");
    }
  };

	  // ✅ NEW: Generate Word document for a specific session with session name as filename
	  const generateWordDocumentForSession = async (
	    sessionName: string,
	    sessionScreenshots: Screenshot[],
	  ) => {
	    // 🔒 RACE CONDITION FIX: Use mutex to prevent concurrent document generation
	    return await documentGenerationMutexRef.current.runExclusive(async () => {
	      try {
	        // Collect all screenshot paths
	        const screenshotPaths = sessionScreenshots.map((s) => s.path);
	
	      if (screenshotPaths.length === 0) {
	        addLog(`   ⚠️ No screenshots to include in document`);
	        return;
	      }
	
	      addLog(
	        `   📄 Generating Word document with ${screenshotPaths.length} screenshot(s)...`,
	      );
	
	      // Use session name as document filename
	      const documentName = `${sessionName}.docx`;
	
	      // ✅ UPDATED: Use configurable base directory
	      let outputPath = wordDocsBaseDir; // Use user-configured base directory
	      if (wordDocFolderName.trim()) {
	        outputPath += `/${wordDocFolderName.trim()}`;
	        addLog(`   📁 Saving to folder: ${wordDocFolderName.trim()}`);
	      }
	      outputPath += `/${documentName}`;
	      addLog(`   📁 Full output path: ${outputPath}`);
	
	      const response = await fetch(
	        "http://127.0.0.1:8001/api/document/generate",
	        {
	          method: "POST",
	          headers: {
	            "Content-Type": "application/json",
	          },
	          body: JSON.stringify({
	            screenshot_paths: screenshotPaths,
	            output_path: outputPath,
	            title: sessionName,
	          }),
	        },
	      );
	
	      if (!response.ok) {
	        const errorText = await response.text();
	        addLog(`   ❌ Document generation failed: ${response.status}`);
	        // Propagate error so callers can log accurate failure instead of false success.
	        throw new Error(
	          `Backend returned ${response.status}: ${errorText || "Document Service error"}`,
	        );
	      }
	
	      const data = await response.json();
	
	      if (data.status === "success") {
	        addLog(`   ✅ Document generated: ${documentName}`);
	
	        // Show notification
	        showNotification(
	          "📄 Word Document Generated",
	          `Document saved: ${documentName}`,
	        );
	      } else {
	        const errorMsg = data.error || "Unknown document generation error";
	        addLog(`   ❌ Document generation failed: ${errorMsg}`);
	        throw new Error(errorMsg);
	      }
	      } catch (error: any) {
	        const message = error?.message || String(error);
	        addLog(`   ❌ Document generation error: ${message}`);
	        // Re-throw so outer try/catch blocks can handle the failure correctly
	        throw error;
	      }
	    });
	  };

	  // Generate Word document(s) from the Sessions tab based on currently-selected sessions
	  const handleCreateDocsFromSelectedSessions = async () => {
	    if (selectedSessions.size === 0) {
	      addLog("⚠️ No sessions selected for document generation");
	      return;
	    }

	    const sessionsToProcess = sessions.filter((s) =>
	      selectedSessions.has(s.id)
	    );

	    if (sessionsToProcess.length === 0) {
	      addLog("⚠️ Selected session IDs not found in current session list");
	      return;
	    }

	    setIsGeneratingSessionDocs(true);
	    try {
	      for (const session of sessionsToProcess) {
	        const hasScreenshots = Array.isArray(session.screenshots) &&
	          session.screenshots.length > 0;
	        if (!hasScreenshots) {
	          addLog(
	            `⚠️ Skipping session "${session.name}" - no screenshots to include`,
	          );
	          continue;
	        }

	        addLog(
	          `📄 Generating Word document from session "${session.name}" with ${session.screenshots.length} screenshot(s)...`,
	        );
	        await generateWordDocumentForSession(
	          session.name || session.defaultName,
	          session.screenshots,
	        );
	      }
	    } catch (error: any) {
	      addLog(
	        `❌ Failed to generate Word document(s) from selected sessions: ${error?.message || String(error)}`,
	      );
	    } finally {
	      setIsGeneratingSessionDocs(false);
	    }
	  };

  const handleGenerateDocument = async () => {
    log.debug("🔍 DEBUG: handleGenerateDocument called");

    // ✅ FIX: Close ALL modals before showing alert to prevent overlay interference
    setShowLoginModal(false);
    setShowCookieEditor(false);
    setShowExportModal(false);
    setShowSecurityAudit(false);
    setShowFormatExport(false);
    setShowFormatImport(false);

    // Wait for React to remove modal overlays from DOM
    await new Promise((resolve) => setTimeout(resolve, 50));
    log.debug("🔍 DEBUG: All modals closed, DOM cleaned");

    // Collect all screenshots (including all segments from segmented captures)
    const successfulScreenshots: string[] = [];

    results
      .filter((r) => r.status === "success")
      .forEach((r) => {
        // If segmented capture, add all segments
        if (r.screenshot_paths && r.screenshot_paths.length > 0) {
          successfulScreenshots.push(...r.screenshot_paths);
        }
        // Otherwise, add single screenshot
        else if (r.screenshot_path) {
          successfulScreenshots.push(r.screenshot_path);
        }
      });

    log.debug(`🔍 DEBUG: Found ${successfulScreenshots.length} screenshots`);

    if (successfulScreenshots.length === 0) {
      alert("No successful screenshots to include in document");
      return;
    }

    try {
      addLog(
        `📄 Generating Word document with ${successfulScreenshots.length} screenshots...`
      );

      // Generate document name from first screenshot filename
      // Remove segment numbers (_001, _002, etc.) and .png extension
      const firstScreenshot = successfulScreenshots[0];
      const firstFilename =
        firstScreenshot.split("/").pop() || "screenshots_report";
      const documentName =
        firstFilename
          .replace(/_\d{3}\.png$/, "") // Remove _001.png, _002.png, etc.
          .replace(/\.png$/, "") + // Remove .png
        ".docx";

      log.debug(`🔍 DEBUG: Document name: ${documentName}`);
      log.debug(`🔍 DEBUG: Sending request to backend...`);

      const response = await fetch(
        "http://127.0.0.1:8001/api/document/generate",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            screenshot_paths: successfulScreenshots,
            output_path: `~/Desktop/ARC DEALERS SCREENSHOT WORD DOCS/${documentName}`,
            title: "Screenshot Report",
          }),
        }
      );

      log.debug(`🔍 DEBUG: Response status: ${response.status}`);

      if (!response.ok) {
        const errorText = await response.text();
        log.error(`❌ DEBUG: Response error: ${errorText}`);
        addLog(
          `❌ Document generation failed: ${response.status} ${errorText}`
        );

        // ✅ FIX: Use setTimeout to ensure alert stays visible
        setTimeout(() => {
          alert(`❌ Error: ${response.status} - ${errorText}`);
        }, 100);
        return;
      }

      const data = await response.json();
      log.debug(`🔍 DEBUG: Response data:`, data);

      if (data.status === "success") {
        addLog(`✅ Document generated successfully: ${data.output_path}`);
        log.debug(`✅ DEBUG: Document generated successfully!`);
        log.debug(`📄 DEBUG: Output path: ${data.output_path}`);

        // Show notification
        showNotification(
          "📄 Word Document Generated",
          `Document saved: ${documentName}`
        );

        // ✅ FIX: Use custom dialog instead of browser alert
        log.debug(`🔍 DEBUG: About to show success dialog...`);
        await showCustomAlert(
          "✅ Document Generated Successfully!",
          `Saved to:\n${data.output_path}`
        );
        log.debug(`🔍 DEBUG: User acknowledged dialog`);
      } else {
        log.error(`❌ DEBUG: Generation failed: ${data.error}`);
        addLog(`❌ Document generation failed: ${data.error}`);

        // ✅ FIX: Use setTimeout to ensure alert stays visible
        setTimeout(() => {
          alert(`❌ Error: ${data.error}`);
        }, 100);
      }
    } catch (error) {
      log.error("❌ DEBUG: Exception caught:", error);
      log.error(
        "❌ DEBUG: Error stack:",
        error instanceof Error ? error.stack : "No stack"
      );
      addLog(`❌ Error generating document: ${error}`);

      // ✅ FIX: Use setTimeout to ensure alert stays visible
      setTimeout(() => {
        const errorMessage = `❌ Error generating document: ${error}\n\nCheck console for details.`;
        log.debug(`🔍 DEBUG: About to show error alert: ${errorMessage}`);
        alert(errorMessage);
        log.debug(`🔍 DEBUG: Error alert shown`);
      }, 100);
    }

    log.debug(`🔍 DEBUG: handleGenerateDocument function completed`);
  };

  // ✅ REMOVED: Test notification function (no longer needed)

  // Catch any rendering errors
  try {
    return (
      <div className="container">
        {/* Conditional Header: Minimal for home, Full for apps */}
        {currentApp === null ? (
          /* Minimal Header - Home Page (only waffle + dark mode) */
          <div className="header-minimal">
            <div className="header-controls-minimal">
              {/* Waffle Menu - App Launcher */}
              <WaffleButton />

              {/* Dark Mode Toggle Button */}
              <button
                className="dark-mode-toggle"
                onClick={toggleDarkMode}
                aria-label="Toggle dark mode"
                title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
              >
                <div
                  className={`toggle-icon ${darkMode ? "dark" : "light"} ${
                    isToggling ? "celebrating" : ""
                  }`}
                >
                  {darkMode ? (
                    <span className="icon-moon">🌙</span>
                  ) : (
                    <span className="icon-sun">☀️</span>
                  )}
                </div>
              </button>
            </div>
          </div>
        ) : (
          /* Full Header - App View (logo + all controls) */
          <div className="header">
            <div className="header-left">
              <a
                href="#"
                className="header-title-link"
                aria-label="Home"
                tabIndex={0}
                onClick={(e) => {
                  e.preventDefault();
                  goHome();
                }}
              >
                <div className="app-logo">ST</div>
              </a>
            </div>

            <div className="header-controls">
            {/* Settings Toggle Button */}
              <button
                className={`settings-toggle ${
                  openTabs.includes("settings") ? "active" : ""
                }`}
                onClick={openSettingsTab}
                aria-label="Open settings"
                title="Open settings"
              >
                <span className="icon-settings">⚙️</span>
              </button>

              {/* Logs Toggle Button */}
              <button
                className={`logs-toggle ${hasErrors ? "error" : "success"} ${
                  openTabs.includes("logs") ? "active" : ""
                }`}
                onClick={openLogsTab}
                aria-label="Open logs"
                title={
                  hasErrors
                    ? `⚠️ ${getErrorCount()} error(s) detected - Click to view logs`
                    : "Show logs (all good!)"
                }
              >
                <div className="logs-icon">
                  {hasErrors ? (
                    <span className="icon-error">⚠️</span>
                  ) : (
                    <span className="icon-success">⏱️</span>
                  )}
                </div>
                {hasErrors && getErrorCount() > 0 && (
                  <span className="error-badge">{getErrorCount()}</span>
                )}
              </button>

              {/* Waffle Menu - App Launcher */}
              <WaffleButton />

              {/* Dark Mode Toggle Button */}
              <button
                className="dark-mode-toggle"
                onClick={toggleDarkMode}
                aria-label="Toggle dark mode"
                title={darkMode ? "Switch to light mode" : "Switch to dark mode"}
              >
                <div
                  className={`toggle-icon ${darkMode ? "dark" : "light"} ${
                    isToggling ? "celebrating" : ""
                  }`}
                >
                  {darkMode ? (
                    <span className="icon-moon">🌙</span>
                  ) : (
                    <span className="icon-sun">☀️</span>
                  )}
                </div>
              </button>
            </div>
          </div>
        )}

        {/* App Launcher Panel - Always available */}
        <LauncherPanel onNavigate={switchTab} />

        {/* Conditional Content: Home, Screenshots app, or Business Apps */}
        {currentApp === null ? (
          /* Home Page - Blank/Welcome Screen */
          <div className="home-blank">
            <div className="home-content">
              <h1 className="home-title">Welcome</h1>
              <p className="home-subtitle">Click the waffle menu to launch an app</p>
            </div>
          </div>
        ) : currentApp === 'business-apps' ? (
          /* Business Apps - Parts, Service, Accounting, CRM, API Testing */
          <BusinessApps
            activeTab={activeTab}
            onTabChange={switchTab}
            addLog={addLog}
            clearLogs={clearLogs}
            addNotification={addNotification}
            logs={logs}
            copyLogs={copyLogs}
          />
        ) : (
          /* Screenshots App - Full UI */
          <>
            {renderError && (
              <div
                style={{
                  background: "#ffebee",
                  border: "2px solid #f44336",
                  padding: "15px",
                  borderRadius: "8px",
                  margin: "20px 0",
                  color: "#c62828",
                }}
              >
                <h3>⚠️ Render Error</h3>
                <p>{renderError}</p>
                <button onClick={() => setRenderError(null)}>Dismiss</button>
              </div>
            )}

            {/* Main layout with left tab panel */}
            <div className="main-layout">
          <aside
            className={`left-tab-panel ${
              isLeftPanelVisible ? "" : "collapsed"
            }`}
          >
            {/* Claude-style sidebar header */}
            <div className="left-tab-header">
              {/* Left side - Logo/Title link (hidden when collapsed) */}
              {isLeftPanelVisible && (
                <div className="left-tab-header-left">
                  <a
                    href="http://localhost:5173/"
                    className="left-tab-title-link"
                    aria-label="Home"
                    tabIndex={0}
                  >
                    <div className="app-logo-small">Screen Shot Tool</div>
                  </a>
                </div>
              )}

              {/* Right side - Sidebar toggle button */}
              <div className="left-tab-header-right">
                <button
                  className="sidebar-toggle group"
                  onClick={() => setIsLeftPanelVisible((prev) => !prev)}
                  aria-label={
                    isLeftPanelVisible
                      ? "Close sidebar"
                      : "Open sidebar"
                  }
                  aria-pressed={!isLeftPanelVisible}
                  data-state={isLeftPanelVisible ? "open" : "closed"}
                  type="button"
                >
                  <div className="sidebar-icon-wrapper">
                    {/* Single panel icon - always visible, flips when collapsed */}
                    <div className="sidebar-icon-state visible">
                      <svg
                        width="20"
                        height="20"
                        viewBox="0 0 20 20"
                        fill="currentColor"
                        xmlns="http://www.w3.org/2000/svg"
                        className="sidebar-icon"
                        aria-hidden="true"
                      >
                        <path d="M16.5 4C17.3284 4 18 4.67157 18 5.5V14.5C18 15.3284 17.3284 16 16.5 16H3.5C2.67157 16 2 15.3284 2 14.5V5.5C2 4.67157 2.67157 4 3.5 4H16.5ZM7 15H16.5C16.7761 15 17 14.7761 17 14.5V5.5C17 5.22386 16.7761 5 16.5 5H7V15ZM3.5 5C3.22386 5 3 5.22386 3 5.5V14.5C3 14.7761 3.22386 15 3.5 15H6V5H3.5Z" />
                      </svg>
                    </div>
                  </div>
                </button>
              </div>
            </div>

            <div className="left-tab-list">
              {/* ❌ DISABLED: Hiding "cookies" tab - not needed for screenshot tool */}
              {openTabs.filter(tab => tab !== "cookies").map((tab) => {
                const icon =
                  tab === "main"
                    ? "📸"
                    : tab === "sessions"
                    ? "🗂️"
                    : tab === "urls"
                    ? "📁"
                    : tab === "cookies"
                    ? "🔐"
                    : tab === "network"
                    ? "🌐"
                    : tab === "settings"
                    ? "⚙️"
                    : tab === "logs"
                    ? "⏱️"
                    : tab === "tiles"
                    ? "🎨"
                    : "🔤";

                const label =
                  tab === "main"
                    ? "Main"
                    : tab === "sessions"
                    ? "Sessions"
                    : tab === "urls"
                    ? "URLs"
                    : tab === "cookies"
                    ? "Auth Data"
                    : tab === "network"
                    ? "Network"
                    : tab === "settings"
                    ? "Settings"
                    : tab === "logs"
                    ? "Logs"
                    : tab === "tiles"
                    ? "Tiles"
                    : "Keyword Config";

                return (
                  <div
                    key={tab}
                    className={`tab left-tab ${
                      activeTab === tab ? "active" : ""
                    } ${tab === "logs" && hasErrors ? "tab-error" : ""}`}
                    onClick={() => switchTab(tab)}
                  >
                    <span className="tab-label">
                      <span className="tab-icon">{icon}</span>
                      {isLeftPanelVisible && (
                        <span className="tab-label-text">
                          {label}
                          {tab === "logs" &&
                            hasErrors &&
                            getErrorCount() > 0 && (
                              <span className="tab-error-badge">
                                {getErrorCount()}
                              </span>
                            )}
                          {tab === "sessions" &&
                            sessions.length > 0 &&
                            activeTab !== "sessions" && (
                              <span className="tab-count-badge">
                                {sessions.length}
                              </span>
                            )}
                        </span>
                      )}
                    </span>
                    {/* No close button for Main, Sessions, URLs, and Cookies tabs - they are permanent */}
                    {tab === "settings" && (
                      <button
                        className="tab-close"
                        onClick={(e) => {
                          e.stopPropagation();
                          closeSettingsTab();
                        }}
                        aria-label="Close settings tab"
                      >
                        ✕
                      </button>
                    )}
                    {tab === "logs" && (
                      <button
                        className="tab-close"
                        onClick={(e) => {
                          e.stopPropagation();
                          closeLogsTab();
                        }}
                        aria-label="Close logs tab"
                      >
                        ✕
                      </button>
                    )}
                    {tab === "keyword-config" && (
                      <button
                        className="tab-close"
                        onClick={(e) => {
                          e.stopPropagation();
                          closeKeywordConfigTab();
                        }}
                        aria-label="Close keyword config tab"
                      >
                        ✕
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </aside>

          <div className="main-layout-content">
            <div className="status-bar">
              {systemUsage && systemUsage.status === "success" ? (
                <span title="System resource usage (updated every 2 seconds)">
                  <span title="Backend process memory usage (RSS - Resident Set Size)">
                    🧠 Backend{" "}
                    {typeof systemUsage.backend_rss_mb === "number"
                      ? `${systemUsage.backend_rss_mb.toFixed(0)} MB`
                      : "–"}
                  </span>
                  {" · "}
                  <span title="Backend CPU usage (5-sample rolling average for accuracy)">
                    CPU{" "}
                    {typeof systemUsage.backend_cpu_percent === "number" ? (
                      <>
                        {systemUsage.backend_cpu_percent.toFixed(0)}%
                        {systemUsage.backend_cpu_percent === 0 && (
                          <span style={{ fontSize: '10px', opacity: 0.7 }}> (idle)</span>
                        )}
                      </>
                    ) : (
                      "–"
                    )}
                  </span>
                  {typeof systemUsage.system_ram_percent === "number" && (
                    <>
                      {" · "}
                      <span title="System-wide RAM usage percentage">
                        💻 System {systemUsage.system_ram_percent.toFixed(0)}% RAM
                      </span>
                      {typeof systemUsage.system_cpu_percent === "number" && (
                        <span title="System-wide CPU usage (5-sample rolling average)">
                          {" · CPU "}
                          {systemUsage.system_cpu_percent.toFixed(0)}%
                        </span>
                      )}
                    </>
                  )}
                  {typeof systemUsage.browser_rss_mb === "number" &&
                  systemUsage.browser_rss_mb > 0 ? (
                    <>
                      {" · "}
                      <span title="Total memory used by all browser instances (Chrome, Brave, Firefox, Camoufox) on your system">
                        🌐 Browser {systemUsage.browser_rss_mb.toFixed(0)} MB
                        <span style={{ fontSize: '10px', opacity: 0.7 }}> (all)</span>
                      </span>
                    </>
                  ) : null}
                </span>
              ) : systemUsage && systemUsage.status === "error" ? (
                <span>🧠 Backend usage: unavailable</span>
              ) : (
                <span>🧠 Backend usage: calculating…</span>
              )}
            </div>

            {/* Tab Content */}
            <Suspense fallback={<div className="tab-content"><div style={{padding: "20px", textAlign: "center"}}>Loading...</div></div>}>
            {activeTab === "logs" ? (
              <ErrorBoundary FallbackComponent={FeatureErrorFallback} onError={(error, errorInfo) => log.error('Logs tab error:', error, errorInfo)}>
                <LogsTab
                  logs={logs}
                  copyLogs={copyLogs}
                  clearLogs={clearLogs}
                  rollingModeStats={rollingModeStats}
                  enableRollingMode={enableParallelTextBoxes}
                  urlStatuses={urlStatuses}
                  performanceMetrics={performanceMetrics}
                />
              </ErrorBoundary>
            ) : activeTab === "tiles" ? (
              <div className="tab-content">
                <div className="settings-content">
                  <div className="settings-section">
                    <h2>🎨 Tiles</h2>
                    <p style={{ color: "#666", marginBottom: "20px" }}>
                      Manage and organize tiles across different departments
                    </p>

                    {/* 4-Column Layout */}
                    <div style={{
                      display: "grid",
                      gridTemplateColumns: "repeat(4, 1fr)",
                      gap: "20px",
                      marginTop: "20px"
                    }}>
                      {/* PARTS Column */}
                      <div style={{
                        backgroundColor: "#f5f5f5",
                        borderRadius: "8px",
                        padding: "20px",
                        minHeight: "400px"
                      }}>
                        <div style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "16px"
                        }}>
                          <h3 style={{
                            fontSize: "18px",
                            fontWeight: "600",
                            color: "#2196F3",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            margin: 0
                          }}>
                            🔧 PARTS
                          </h3>
                          <label style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            cursor: "pointer"
                          }}>
                            <input
                              type="checkbox"
                              checked={partsEnabled}
                              onChange={(e) => setPartsEnabled(e.target.checked)}
                              style={{
                                width: "40px",
                                height: "20px",
                                cursor: "pointer"
                              }}
                            />
                            <span style={{ fontSize: "12px", color: "#666" }}>
                              {partsEnabled ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </div>
                        <div style={{
                          borderTop: "2px solid #2196F3",
                          paddingTop: "16px",
                          opacity: partsEnabled ? 1 : 0.5
                        }}>
                          {/* Parts content will go here */}
                          <p style={{ color: "#666", fontSize: "14px" }}>
                            Parts tiles and configurations
                          </p>
                        </div>
                      </div>

                      {/* SERVICE Column */}
                      <div style={{
                        backgroundColor: "#f5f5f5",
                        borderRadius: "8px",
                        padding: "20px",
                        minHeight: "400px"
                      }}>
                        <div style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "16px"
                        }}>
                          <h3 style={{
                            fontSize: "18px",
                            fontWeight: "600",
                            color: "#4CAF50",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            margin: 0
                          }}>
                            🛠️ SERVICE
                          </h3>
                          <label style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            cursor: "pointer"
                          }}>
                            <input
                              type="checkbox"
                              checked={serviceEnabled}
                              onChange={(e) => setServiceEnabled(e.target.checked)}
                              style={{
                                width: "40px",
                                height: "20px",
                                cursor: "pointer"
                              }}
                            />
                            <span style={{ fontSize: "12px", color: "#666" }}>
                              {serviceEnabled ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </div>
                        <div style={{
                          borderTop: "2px solid #4CAF50",
                          paddingTop: "16px",
                          opacity: serviceEnabled ? 1 : 0.5
                        }}>
                          {/* Service content will go here */}
                          <p style={{ color: "#666", fontSize: "14px" }}>
                            Service tiles and configurations
                          </p>
                        </div>
                      </div>

                      {/* ACCOUNTING Column */}
                      <div style={{
                        backgroundColor: "#f5f5f5",
                        borderRadius: "8px",
                        padding: "20px",
                        minHeight: "400px"
                      }}>
                        <div style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "16px"
                        }}>
                          <h3 style={{
                            fontSize: "18px",
                            fontWeight: "600",
                            color: "#FF9800",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            margin: 0
                          }}>
                            💰 ACCOUNTING
                          </h3>
                          <label style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            cursor: "pointer"
                          }}>
                            <input
                              type="checkbox"
                              checked={accountingEnabled}
                              onChange={(e) => setAccountingEnabled(e.target.checked)}
                              style={{
                                width: "40px",
                                height: "20px",
                                cursor: "pointer"
                              }}
                            />
                            <span style={{ fontSize: "12px", color: "#666" }}>
                              {accountingEnabled ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </div>
                        <div style={{
                          borderTop: "2px solid #FF9800",
                          paddingTop: "16px",
                          opacity: accountingEnabled ? 1 : 0.5
                        }}>
                          {/* Accounting content will go here */}
                          <p style={{ color: "#666", fontSize: "14px" }}>
                            Accounting tiles and configurations
                          </p>
                        </div>
                      </div>

                      {/* CRM Column */}
                      <div style={{
                        backgroundColor: "#f5f5f5",
                        borderRadius: "8px",
                        padding: "20px",
                        minHeight: "400px"
                      }}>
                        <div style={{
                          display: "flex",
                          justifyContent: "space-between",
                          alignItems: "center",
                          marginBottom: "16px"
                        }}>
                          <h3 style={{
                            fontSize: "18px",
                            fontWeight: "600",
                            color: "#9C27B0",
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            margin: 0
                          }}>
                            👥 CRM
                          </h3>
                          <label style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "8px",
                            cursor: "pointer"
                          }}>
                            <input
                              type="checkbox"
                              checked={crmEnabled}
                              onChange={(e) => setCrmEnabled(e.target.checked)}
                              style={{
                                width: "40px",
                                height: "20px",
                                cursor: "pointer"
                              }}
                            />
                            <span style={{ fontSize: "12px", color: "#666" }}>
                              {crmEnabled ? "Enabled" : "Disabled"}
                            </span>
                          </label>
                        </div>
                        <div style={{
                          borderTop: "2px solid #9C27B0",
                          paddingTop: "16px",
                          opacity: crmEnabled ? 1 : 0.5
                        }}>
                          {/* Tekion Logo Removal Button */}
                          <button
                            onClick={handleTekionLogoRemovalClick}
                            disabled={!crmEnabled}
                            style={{
                              width: "100%",
                              padding: "12px 20px",
                              backgroundColor: crmEnabled ? "#9C27B0" : "#ccc",
                              color: "white",
                              border: "none",
                              borderRadius: "6px",
                              fontSize: "14px",
                              fontWeight: "600",
                              cursor: crmEnabled ? "pointer" : "not-allowed",
                              transition: "all 0.3s ease",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              gap: "8px"
                            }}
                            onMouseEnter={(e) => {
                              if (crmEnabled) {
                                e.currentTarget.style.backgroundColor = "#7B1FA2";
                                e.currentTarget.style.transform = "translateY(-2px)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(156, 39, 176, 0.3)";
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (crmEnabled) {
                                e.currentTarget.style.backgroundColor = "#9C27B0";
                                e.currentTarget.style.transform = "translateY(0)";
                                e.currentTarget.style.boxShadow = "none";
                              }
                            }}
                          >
                            <span style={{ fontSize: "16px" }}>🎨</span>
                            Tekion Logo Removal
                          </button>

                          {/* Logo Adding Button */}
                          <button
                            onClick={handleLogoAdditionClick}
                            disabled={!crmEnabled}
                            style={{
                              width: "100%",
                              padding: "12px 20px",
                              backgroundColor: crmEnabled ? "#FF6B6B" : "#ccc",
                              color: "white",
                              border: "none",
                              borderRadius: "6px",
                              fontSize: "14px",
                              fontWeight: "600",
                              cursor: crmEnabled ? "pointer" : "not-allowed",
                              transition: "all 0.3s ease",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              gap: "8px",
                              marginTop: "12px"
                            }}
                            onMouseEnter={(e) => {
                              if (crmEnabled) {
                                e.currentTarget.style.backgroundColor = "#EE5A6F";
                                e.currentTarget.style.transform = "translateY(-2px)";
                                e.currentTarget.style.boxShadow = "0 4px 8px rgba(255, 107, 107, 0.3)";
                              }
                            }}
                            onMouseLeave={(e) => {
                              if (crmEnabled) {
                                e.currentTarget.style.backgroundColor = "#FF6B6B";
                                e.currentTarget.style.transform = "translateY(0)";
                                e.currentTarget.style.boxShadow = "none";
                              }
                            }}
                          >
                            <span style={{ fontSize: "16px" }}>✨</span>
                            Logo Adding
                          </button>

                          {!crmEnabled && (
                            <p style={{
                              marginTop: "12px",
                              fontSize: "12px",
                              color: "#ff9800",
                              textAlign: "center",
                              fontStyle: "italic"
                            }}>
                              Enable CRM toggle to use this feature
                            </p>
                          )}

                          {/* ✅ Settings Modal */}
                          {showLogoRemovalSettings && (
                            <div style={{
                              position: "fixed",
                              top: 0,
                              left: 0,
                              right: 0,
                              bottom: 0,
                              backgroundColor: "rgba(0, 0, 0, 0.5)",
                              display: "flex",
                              alignItems: "center",
                              justifyContent: "center",
                              zIndex: 10000
                            }}>
                              <div style={{
                                backgroundColor: "white",
                                borderRadius: "12px",
                                padding: "32px",
                                maxWidth: "500px",
                                width: "90%",
                                boxShadow: "0 10px 40px rgba(0, 0, 0, 0.2)"
                              }}>
                                <h2 style={{
                                  margin: "0 0 24px 0",
                                  fontSize: "24px",
                                  color: "#9C27B0",
                                  display: "flex",
                                  alignItems: "center",
                                  gap: "12px"
                                }}>
                                  <span style={{ fontSize: "28px" }}>🎨</span>
                                  Tekion Logo Removal Settings
                                </h2>

                                <div style={{ marginBottom: "24px" }}>
                                  <label style={{
                                    display: "block",
                                    marginBottom: "8px",
                                    fontSize: "14px",
                                    fontWeight: "600",
                                    color: "#333"
                                  }}>
                                    📊 Maximum Rows to Fetch from API
                                  </label>
                                  <input
                                    type="number"
                                    value={logoRemovalMaxRows}
                                    onChange={(e) => setLogoRemovalMaxRows(parseInt(e.target.value) || 200)}
                                    min="1"
                                    max="500"
                                    style={{
                                      width: "100%",
                                      padding: "12px",
                                      fontSize: "16px",
                                      border: "2px solid #e0e0e0",
                                      borderRadius: "6px",
                                      outline: "none"
                                    }}
                                    onFocus={(e) => e.target.style.borderColor = "#9C27B0"}
                                    onBlur={(e) => e.target.style.borderColor = "#e0e0e0"}
                                  />
                                  <p style={{
                                    marginTop: "8px",
                                    fontSize: "12px",
                                    color: "#666"
                                  }}>
                                    Fetch up to this many templates from the API (1-500). Default: 200
                                  </p>
                                </div>

                                <div style={{ marginBottom: "24px" }}>
                                  <label style={{
                                    display: "block",
                                    marginBottom: "8px",
                                    fontSize: "14px",
                                    fontWeight: "600",
                                    color: "#333"
                                  }}>
                                    🎯 Process Custom Number of Templates (Optional)
                                  </label>
                                  <input
                                    type="number"
                                    placeholder="Leave empty to process all"
                                    value={logoRemovalCustomLimit}
                                    onChange={(e) => setLogoRemovalCustomLimit(e.target.value)}
                                    min="1"
                                    style={{
                                      width: "100%",
                                      padding: "12px",
                                      fontSize: "16px",
                                      border: "2px solid #e0e0e0",
                                      borderRadius: "6px",
                                      outline: "none"
                                    }}
                                    onFocus={(e) => e.target.style.borderColor = "#9C27B0"}
                                    onBlur={(e) => e.target.style.borderColor = "#e0e0e0"}
                                  />
                                  <p style={{
                                    marginTop: "8px",
                                    fontSize: "12px",
                                    color: "#666"
                                  }}>
                                    {logoRemovalCustomLimit
                                      ? `Will process only the first ${logoRemovalCustomLimit} templates that match filters`
                                      : "Leave empty to process ALL templates that match filters"}
                                  </p>
                                </div>

                                <div style={{ marginBottom: "24px" }}>
                                  <label style={{
                                    display: "flex",
                                    alignItems: "center",
                                    gap: "12px",
                                    cursor: "pointer",
                                    padding: "12px",
                                    backgroundColor: keepTabsOpen ? "#E8F5E9" : "#f5f5f5",
                                    borderRadius: "6px",
                                    border: `2px solid ${keepTabsOpen ? "#4CAF50" : "#e0e0e0"}`,
                                    transition: "all 0.3s"
                                  }}>
                                    <input
                                      type="checkbox"
                                      checked={keepTabsOpen}
                                      onChange={(e) => setKeepTabsOpen(e.target.checked)}
                                      style={{
                                        width: "20px",
                                        height: "20px",
                                        cursor: "pointer"
                                      }}
                                    />
                                    <div style={{ flex: 1 }}>
                                      <div style={{
                                        fontSize: "14px",
                                        fontWeight: "600",
                                        color: "#333"
                                      }}>
                                        🔍 Keep Tabs Open for Verification
                                      </div>
                                      <div style={{
                                        fontSize: "12px",
                                        color: "#666",
                                        marginTop: "4px"
                                      }}>
                                        {keepTabsOpen
                                          ? "✅ Tabs will stay open - manually close after verifying"
                                          : "❌ Tabs will close automatically after processing"}
                                      </div>
                                    </div>
                                  </label>
                                </div>

                                <div style={{
                                  padding: "16px",
                                  backgroundColor: "#f5f5f5",
                                  borderRadius: "6px",
                                  marginBottom: "24px"
                                }}>
                                  <p style={{ margin: "0 0 8px 0", fontSize: "14px" }}>
                                    <strong>ℹ️ What will happen:</strong>
                                  </p>
                                  <ul style={{ margin: "0", paddingLeft: "20px", fontSize: "13px", color: "#666" }}>
                                    <li>Fetch up to {logoRemovalMaxRows} templates from preprod API</li>
                                    <li>Filter for ACTIVE EMAIL templates with SALES dept</li>
                                    {logoRemovalCustomLimit && (
                                      <li style={{ fontWeight: "600", color: "#9C27B0" }}>
                                        🎯 Process only the first {logoRemovalCustomLimit} templates
                                      </li>
                                    )}
                                    {!logoRemovalCustomLimit && (
                                      <li>Process ALL templates that match the filters</li>
                                    )}
                                    <li>Remove "Powered by Tekion" logo from each</li>
                                    <li>Click Publish and save changes</li>
                                    <li>Generate Excel report with results</li>
                                  </ul>
                                </div>

                                <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
                                  <button
                                    onClick={() => setShowLogoRemovalSettings(false)}
                                    style={{
                                      padding: "12px 24px",
                                      fontSize: "14px",
                                      fontWeight: "600",
                                      backgroundColor: "#f5f5f5",
                                      color: "#666",
                                      border: "none",
                                      borderRadius: "6px",
                                      cursor: "pointer"
                                    }}
                                  >
                                    Cancel
                                  </button>
                                  <button
                                    onClick={startTekionLogoRemoval}
                                    style={{
                                      padding: "12px 24px",
                                      fontSize: "14px",
                                      fontWeight: "600",
                                      backgroundColor: "#9C27B0",
                                      color: "white",
                                      border: "none",
                                      borderRadius: "6px",
                                      cursor: "pointer"
                                    }}
                                  >
                                    🚀 Start Removal
                                  </button>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Progress Indicator */}
                          {removalStatus === 'running' && removalProgress && (
                            <div style={{
                              marginTop: "20px",
                              padding: "16px",
                              backgroundColor: "white",
                              borderRadius: "6px",
                              border: "1px solid #9C27B0"
                            }}>
                              <h4 style={{ margin: "0 0 12px 0", fontSize: "14px", color: "#9C27B0" }}>
                                🔄 Processing Templates...
                              </h4>

                              {/* Progress Bar */}
                              <div style={{
                                width: "100%",
                                height: "20px",
                                backgroundColor: "#f0f0f0",
                                borderRadius: "10px",
                                overflow: "hidden",
                                marginBottom: "8px"
                              }}>
                                <div style={{
                                  width: `${(removalProgress.processed / removalProgress.total) * 100}%`,
                                  height: "100%",
                                  backgroundColor: "#9C27B0",
                                  transition: "width 0.3s ease"
                                }} />
                              </div>

                              {/* Stats */}
                              <div style={{ fontSize: "12px", color: "#666" }}>
                                <div><strong>{removalProgress.processed}</strong> / {removalProgress.total} processed</div>
                                <div style={{ color: "#4CAF50" }}>✅ Success: {removalProgress.successful}</div>
                                <div style={{ color: "#F44336" }}>❌ Failed: {removalProgress.failed}</div>
                                {removalProgress.current_template && (
                                  <div style={{ marginTop: "8px", fontStyle: "italic", color: "#9C27B0" }}>
                                    Current: {removalProgress.current_template}
                                  </div>
                                )}
                              </div>
                            </div>
                          )}

                          {/* Completion Message */}
                          {removalStatus === 'completed' && removalProgress && (
                            <div style={{
                              marginTop: "20px",
                              padding: "16px",
                              backgroundColor: "#E8F5E9",
                              borderRadius: "6px",
                              border: "1px solid #4CAF50"
                            }}>
                              <h4 style={{ margin: "0 0 8px 0", fontSize: "14px", color: "#4CAF50" }}>
                                ✅ Completed!
                              </h4>
                              <div style={{ fontSize: "12px", color: "#666" }}>
                                <div>Total: {removalProgress.total}</div>
                                <div>✅ Successful: {removalProgress.successful}</div>
                                <div>❌ Failed: {removalProgress.failed}</div>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ) : activeTab === "keyword-config" ? (
              <div className="tab-content">
                <div className="settings-content">
                  {/* URL Click Configurations */}
                  <div className="settings-section">
                    <div
                      style={{
                        display: "flex",
                        justifyContent: "space-between",
                        alignItems: "center",
                        marginBottom: "16px",
                      }}
                    >
                      <h3>
                        🖱️ URL Click Configurations
                        <InfoButton
                          ariaLabel="Information about URL click configurations"
                          tooltip="Define click actions for specific URLs that are automatically applied when capturing screenshots."
                        />
                      </h3>
                      <button
                        onClick={() => openUrlConfigEditor()}
                        className="add-config-btn"
                        style={{
                          padding: "8px 16px",
                          backgroundColor: "#4CAF50",
                          color: "white",
                          border: "none",
                          borderRadius: "4px",
                          cursor: "pointer",
                          fontSize: "14px",
                          fontWeight: "500",
                        }}
                      >
                        ➕ Add Configuration
                      </button>
                    </div>

                    {/* Configuration List */}
                    {urlConfigs.length === 0 ? (
                      <div
                        style={{
                          padding: "32px",
                          textAlign: "center",
                          color: "#666",
                          backgroundColor: "#f5f5f5",
                          borderRadius: "8px",
                        }}
                      >
                        <p style={{ fontSize: "16px", marginBottom: "8px" }}>
                          📋 No configurations yet
                        </p>
                        <p style={{ fontSize: "14px" }}>
                          Click "Add Configuration" to create your first URL
                          click configuration
                        </p>
                      </div>
                    ) : (
                      <div style={{ display: "flex", flexDirection: "column" }}>
                        {urlConfigs.map((config) => (
                          <div
                            key={config.id}
                            style={{
                              display: "flex",
                              alignItems: "center",
                              padding: "10px 0",
                              borderBottom: "1px solid #eee",
                              opacity: config.enabled ? 1 : 0.5,
                            }}
                          >
                            {/* URL and actions */}
                            <div style={{ flex: 1, fontSize: "14px" }}>
                              <span
                                style={{ color: "#333", fontWeight: "500" }}
                              >
                                {config.url_pattern}
                              </span>
                              <span style={{ margin: "0 8px", color: "#999" }}>
                                :
                              </span>
                              <span style={{ color: "#666" }}>
                                {config.actions.map((a) => a.text).join(", ")}
                              </span>
                            </div>

                            {/* Edit/Delete buttons */}
                            <div style={{ display: "flex", gap: "8px" }}>
                              <button
                                onClick={() => openUrlConfigEditor(config)}
                                style={{
                                  padding: "4px 10px",
                                  backgroundColor: "#2196F3",
                                  color: "white",
                                  border: "none",
                                  borderRadius: "4px",
                                  cursor: "pointer",
                                  fontSize: "12px",
                                }}
                              >
                                ✏️ Edit
                              </button>
                              <button
                                onClick={(e) => {
                                  log.debug(
                                    "🗑️ Delete button clicked for config:",
                                    config.id,
                                    config.name
                                  );
                                  e.preventDefault();
                                  e.stopPropagation();

                                  // Show custom confirm dialog
                                  setConfirmDialog({
                                    isOpen: true,
                                    title: "🗑️ Delete Configuration",
                                    message: `Are you sure you want to delete "${config.name}"? This action cannot be undone.`,
                                    type: "danger",
                                    onConfirm: async () => {
                                      log.debug("🔄 User confirmed delete");
                                      setConfirmDialog((prev) => ({
                                        ...prev,
                                        isOpen: false,
                                      }));
                                      log.debug(
                                        "🔄 Calling deleteUrlConfig..."
                                      );
                                      const result = await deleteUrlConfig(
                                        config.id
                                      );
                                      log.debug("✅ Delete result:", result);
                                    },
                                  });
                                }}
                                style={{
                                  padding: "4px 10px",
                                  backgroundColor: "#f44336",
                                  color: "white",
                                  border: "none",
                                  borderRadius: "4px",
                                  cursor: "pointer",
                                  fontSize: "12px",
                                }}
                              >
                                🗑️ Delete
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  {/* Base URL for Screenshot Naming */}
                  <div className="settings-section">
                    <label htmlFor="base-url-input">
                      <h3>
                        📍 Base URL (Optional)
                        <InfoButton
                          ariaLabel="Information about base URL for screenshot naming"
                          tooltip="Used for screenshot naming. Path after base URL becomes filename in PascalCase. Example: Base URL https://example.com/ + URL https://example.com/accounting/autoPostingSettings = Accounting_AutoPostingSettings.png"
                        />
                      </h3>
                    </label>
                    <input
                      id="base-url-input"
                      name="baseUrl"
                      type="text"
                      className="base-url-input"
                      placeholder="https://example.com"
                      value={baseUrl}
                      onChange={(e) => setBaseUrl(e.target.value)}
                      disabled={loading}
                    />
                  </div>

                  {/* Words to Remove from Naming */}
                  <div className="settings-section">
                    <h3>
                      🧹 Word Transformations
                      <InfoButton
                        ariaLabel="Information about word transformation syntax"
                        tooltip='Syntax: word (space), word:"" (remove), word:"text" (custom). Examples: dse-v2, .png:"", Accounting:"Sales". Click a tag to edit. Press Enter or , to add.'
                      />
                    </h3>
                    <div className="tag-input-container">
                      {/* Display existing transformation tags */}
                      {wordsToRemove.map((transform, index) => (
                        <div
                          key={index}
                          className={`word-tag word-tag-${transform.type}`}
                          onClick={() => openWordEditor(index)}
                          style={{ cursor: "pointer" }}
                          title="Click to edit"
                        >
                          <span className="word-part">{transform.word}</span>
                          <span className="arrow">→</span>
                          <span className="replacement-part">
                            {transform.type === "remove"
                              ? "[remove]"
                              : transform.type === "space"
                              ? "[space]"
                              : transform.replacement}
                          </span>
                          <button
                            className="word-tag-remove"
                            onClick={(e) => {
                              e.stopPropagation();
                              removeWordToRemove(index);
                            }}
                            disabled={loading}
                            title="Delete"
                          >
                            ×
                          </button>
                        </div>
                      ))}
                      {/* Input for adding new transformations */}
                      <input
                        type="text"
                        className="tag-input"
                        placeholder={
                          wordsToRemove.length === 0
                            ? 'word or word:"replacement"'
                            : "Add more..."
                        }
                        value={wordInput}
                        onChange={(e) => setWordInput(e.target.value)}
                        onKeyDown={handleWordInputKeyDown}
                        onBlur={() => {
                          if (wordInput.trim()) {
                            addWordToRemove(wordInput);
                          }
                        }}
                        disabled={loading}
                      />
                    </div>
                  </div>
                </div>
              </div>
            ) : activeTab === "sessions" ? (
              <ErrorBoundary FallbackComponent={FeatureErrorFallback} onError={(error, errorInfo) => log.error('Sessions tab error:', error, errorInfo)}>
                <SessionsTab
                  sessions={sessions}
                  selectedSessions={selectedSessions}
                  isDeletingSession={isDeletingSession}
                  editingSessionId={editingSessionId}
                  editingSessionName={editingSessionName}
                  sessionNameError={sessionNameError}
                  formatTimestamp={formatTimestamp}
                  deselectAllSessions={deselectAllSessions}
                  selectAllSessions={selectAllSessions}
                  deleteSelectedSessions={deleteSelectedSessions}
                  toggleSessionSelection={toggleSessionSelection}
                  setEditingSessionName={setEditingSessionName}
                  handleSessionNameKeyDown={handleSessionNameKeyDown}
                  saveSessionName={saveSessionName}
                  cancelEditingSession={cancelEditingSession}
	                  startEditingSession={startEditingSession}
	                  onCreateDocsFromSelected={handleCreateDocsFromSelectedSessions}
	                  isCreatingDocs={isGeneratingSessionDocs}
                />
              </ErrorBoundary>
            ) : activeTab === "urls" ? (
              <div className="tab-content">
                <div className="urls-section">
                  <div className="urls-header">
                    <h2>📁 URL Library</h2>
                    <div className="urls-header-actions">
                      <button
                        onClick={removeDuplicateUrls}
                        className="clean-duplicates-btn"
                        title="Remove duplicate URLs from all folders"
                      >
                        🧹 Clean Duplicates
                      </button>
                      <div className="new-folder-form">
                        <input
                          type="text"
                          className="new-folder-input"
                          placeholder="New folder name..."
                          value={newFolderName}
                          onChange={(e) => setNewFolderName(e.target.value)}
                          onKeyDown={(e) => {
                            if (e.key === "Enter") {
                              e.preventDefault();
                              createFolder();
                            }
                          }}
                        />
                        <button
                          onClick={createFolder}
                          className="create-folder-btn"
                        >
                          + New Folder
                        </button>
                      </div>
                    </div>
                  </div>

                  <div className="folders-container">
                    {urlFolders.length === 0 ? (
                      <div className="no-folders">
                        <p>📁 No folders yet.</p>
                        <p>Create your first folder to organize URLs!</p>
                      </div>
                    ) : (
                      urlFolders.map((folder) => (
                        <div key={folder.id} className="folder-card">
                          <div className="folder-header">
                            <button
                              className="folder-expand-btn"
                              onClick={() => toggleFolderExpanded(folder.id)}
                            >
                              {expandedFolders.has(folder.id) ? "▼" : "▶"}
                            </button>

                            {editingFolderId === folder.id ? (
                              <div className="folder-name-edit">
                                <input
                                  type="text"
                                  className="folder-name-input"
                                  value={editingFolderName}
                                  onChange={(e) =>
                                    setEditingFolderName(e.target.value)
                                  }
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                      e.preventDefault();
                                      saveFolderName(folder.id);
                                    } else if (e.key === "Escape") {
                                      e.preventDefault();
                                      cancelEditingFolder();
                                    }
                                  }}
                                  onBlur={() => saveFolderName(folder.id)}
                                  autoFocus
                                />
                                <button
                                  className="folder-name-save"
                                  onClick={() => saveFolderName(folder.id)}
                                  title="Save"
                                >
                                  ✓
                                </button>
                                <button
                                  className="folder-name-cancel"
                                  onClick={cancelEditingFolder}
                                  title="Cancel"
                                >
                                  ✗
                                </button>
                                {folderNameError && (
                                  <span className="folder-name-error">
                                    {folderNameError}
                                  </span>
                                )}
                              </div>
                            ) : (
                              <div className="folder-name-display">
                                <h3 className="folder-name">
                                  📂 {folder.name} ({folder.urls.length})
                                </h3>
                                <button
                                  className="folder-edit-btn"
                                  onClick={() => startEditingFolder(folder.id)}
                                  title="Rename folder"
                                >
                                  ✏️
                                </button>
                                <button
                                  className="folder-delete-btn"
                                  onClick={() => deleteFolder(folder.id)}
                                  title="Delete folder"
                                >
                                  🗑️
                                </button>
                              </div>
                            )}
                          </div>

                          {expandedFolders.has(folder.id) && (
                            <div className="folder-content">
                              {/* Toolbar: Select All, Search, Sort */}
                              {folder.urls.length > 0 && (
                                <div className="folder-toolbar">
                                  <div className="toolbar-left">
                                    <label className="select-all-checkbox">
                                      <input
                                        type="checkbox"
                                        checked={
                                          (selectedUrls[folder.id]?.size ||
                                            0) === folder.urls.length
                                        }
                                        onChange={() => {
                                          if (
                                            (selectedUrls[folder.id]?.size ||
                                              0) === folder.urls.length
                                          ) {
                                            deselectAllUrls(folder.id);
                                          } else {
                                            selectAllUrls(folder.id);
                                          }
                                        }}
                                      />
                                      <span>
                                        {(selectedUrls[folder.id]?.size ||
                                          0) === folder.urls.length
                                          ? "Deselect All"
                                          : "Select All"}
                                      </span>
                                    </label>

                                    <input
                                      type="text"
                                      className="search-input"
                                      placeholder="Search URLs..."
                                      value={searchQuery[folder.id] || ""}
                                      onChange={(e) =>
                                        setSearchQuery({
                                          ...searchQuery,
                                          [folder.id]: e.target.value,
                                        })
                                      }
                                    />
                                  </div>

                                  <div className="toolbar-right">
                                    <select
                                      className="sort-select"
                                      value={
                                        sortOrder[folder.id] || "date-desc"
                                      }
                                      onChange={(e) =>
                                        setSortOrder({
                                          ...sortOrder,
                                          [folder.id]: e.target.value as any,
                                        })
                                      }
                                    >
                                      <option value="date-desc">
                                        Newest First
                                      </option>
                                      <option value="date-asc">
                                        Oldest First
                                      </option>
                                      <option value="alpha-asc">A → Z</option>
                                      <option value="alpha-desc">Z → A</option>
                                    </select>
                                  </div>
                                </div>
                              )}

                              {/* Bulk Actions Bar (appears when URLs selected) */}
                              {(selectedUrls[folder.id]?.size || 0) > 0 && (
                                <div className="bulk-actions-bar">
                                  <span className="selected-count">
                                    {selectedUrls[folder.id]?.size || 0}{" "}
                                    selected
                                  </span>
                                  <div className="bulk-actions">
                                    <button
                                      className="bulk-action-btn delete"
                                      onClick={() =>
                                        deleteSelectedUrls(folder.id)
                                      }
                                    >
                                      🗑️ Delete ({selectedUrls[folder.id]?.size}
                                      )
                                    </button>
                                    <button
                                      className="bulk-action-btn copy"
                                      onClick={() =>
                                        copySelectedUrls(folder.id)
                                      }
                                    >
                                      📋 Copy ({selectedUrls[folder.id]?.size})
                                    </button>
                                  </div>
                                </div>
                              )}

                              {/* URL List */}
                              <div className="folder-urls">
                                {folder.urls.length === 0 ? (
                                  <p className="no-urls">
                                    No URLs in this folder yet.
                                  </p>
                                ) : (
                                  (() => {
                                    const filteredUrls =
                                      getFilteredAndSortedUrls(folder.id);
                                    const query = searchQuery[folder.id];

                                    if (filteredUrls.length === 0 && query) {
                                      return (
                                        <p className="no-results">
                                          No URLs match "{query}"
                                        </p>
                                      );
                                    }

                                    return (
                                      <>
                                        {query && (
                                          <p className="search-results-count">
                                            Showing {filteredUrls.length} of{" "}
                                            {folder.urls.length} URLs
                                          </p>
                                        )}
                                        {filteredUrls.map(
                                          (url, _displayIndex) => { // displayIndex reserved for future use
                                            const originalIndex =
                                              folder.urls.indexOf(url);
                                            return (
                                              <div
                                                key={originalIndex}
                                                className="url-item"
                                              >
                                                {editingUrlId ===
                                                `${folder.id}-${originalIndex}` ? (
                                                  <div className="url-edit">
                                                    <input
                                                      type="text"
                                                      className="url-input"
                                                      value={editingUrlValue}
                                                      onChange={(e) =>
                                                        setEditingUrlValue(
                                                          e.target.value
                                                        )
                                                      }
                                                      onKeyDown={(e) => {
                                                        if (e.key === "Enter") {
                                                          e.preventDefault();
                                                          saveUrl(
                                                            folder.id,
                                                            originalIndex
                                                          );
                                                        } else if (
                                                          e.key === "Escape"
                                                        ) {
                                                          e.preventDefault();
                                                          cancelEditingUrl();
                                                        }
                                                      }}
                                                      onBlur={() =>
                                                        saveUrl(
                                                          folder.id,
                                                          originalIndex
                                                        )
                                                      }
                                                      autoFocus
                                                    />
                                                    <button
                                                      className="url-save-btn"
                                                      onClick={() =>
                                                        saveUrl(
                                                          folder.id,
                                                          originalIndex
                                                        )
                                                      }
                                                      title="Save"
                                                    >
                                                      ✓
                                                    </button>
                                                    <button
                                                      className="url-cancel-btn"
                                                      onClick={cancelEditingUrl}
                                                      title="Cancel"
                                                    >
                                                      ✗
                                                    </button>
                                                  </div>
                                                ) : (
                                                  <div className="url-display">
                                                    <input
                                                      type="checkbox"
                                                      className="url-checkbox"
                                                      checked={
                                                        selectedUrls[
                                                          folder.id
                                                        ]?.has(originalIndex) ||
                                                        false
                                                      }
                                                      onChange={() =>
                                                        toggleUrlSelection(
                                                          folder.id,
                                                          originalIndex
                                                        )
                                                      }
                                                    />
                                                    <span className="url-number">
                                                      {originalIndex + 1}.
                                                    </span>
                                                    <span className="url-text">
                                                      {url}
                                                    </span>
                                                    <button
                                                      className="url-edit-btn"
                                                      onClick={() =>
                                                        startEditingUrl(
                                                          folder.id,
                                                          originalIndex
                                                        )
                                                      }
                                                      title="Edit URL"
                                                    >
                                                      ✏️
                                                    </button>
                                                    <button
                                                      className="url-delete-btn"
                                                      onClick={() =>
                                                        deleteUrl(
                                                          folder.id,
                                                          originalIndex
                                                        )
                                                      }
                                                      title="Delete URL"
                                                    >
                                                      🗑️
                                                    </button>
                                                  </div>
                                                )}
                                              </div>
                                            );
                                          }
                                        )}
                                      </>
                                    );
                                  })()
                                )}
                              </div>

                              {/* Bulk URL textarea - always visible */}
                              <div className="bulk-url-section">
                                <textarea
                                  className="bulk-url-textarea"
                                  placeholder="Paste URLs here (one per line or separated by spaces/commas)&#10;&#10;Example:&#10;https://example.com/page1&#10;https://example.com/page2&#10;https://example.com/page3"
                                  value={bulkUrlInput[folder.id] || ""}
                                  onChange={(e) =>
                                    setBulkUrlInput({
                                      ...bulkUrlInput,
                                      [folder.id]: e.target.value,
                                    })
                                  }
                                  rows={6}
                                />
                                <button
                                  className="add-bulk-urls-btn"
                                  onClick={() => addBulkUrlsToFolder(folder.id)}
                                  disabled={
                                    !(bulkUrlInput[folder.id] || "").trim()
                                  }
                                >
                                  ✨ Add URLs to Folder
                                </button>
                              </div>
                            </div>
                          )}
                        </div>
                      ))
                    )}
                  </div>
                </div>
              </div>
            ) : false && activeTab === "cookies" ? (
              // ❌ DISABLED: Cookie/Auth features not needed for screenshot tool
              <div className="tab-content">
                <div className="auth-methods-container">
                  <h2 className="auth-methods-title">
                    🔐 Authentication Methods
                  </h2>
                  <p className="auth-methods-subtitle">
                    Choose your preferred method to handle authentication for
                    screenshots
                  </p>

                  {/* Auth Method Buttons */}
                  <div className="auth-method-buttons">
                    {/* Button 1: Cookie Analysis */}
                    <button
                      className={`auth-method-btn ${
                        expandedAuthMethod === "analysis" ? "active" : ""
                      }`}
                      onClick={() =>
                        setExpandedAuthMethod(
                          expandedAuthMethod === "analysis" ? null : "analysis"
                        )
                      }
                    >
                      <div className="btn-icon">🔍</div>
                      <div className="btn-content">
                        <div className="btn-title">
                          Cookie Analysis & Inspector
                        </div>
                        <div className="btn-description">
                          Analyze and inspect extracted cookies
                        </div>
                      </div>
                      <div className="btn-arrow">
                        {expandedAuthMethod === "analysis" ? "▼" : "▶"}
                      </div>
                    </button>

                    {expandedAuthMethod === "analysis" &&
                      cookieImportStatus.playwright?.exists && (
                        <div className="auth-method-content">
                          <div className="analysis-filters">
                            <input
                              type="text"
                              placeholder="Filter by domain (e.g., zomato, google)"
                              value={analysisDomainFilter}
                              onChange={(e) =>
                                setAnalysisDomainFilter(e.target.value)
                              }
                              className="domain-filter-input"
                            />
                            <label className="auth-only-checkbox">
                              <input
                                type="checkbox"
                                checked={showAuthCookiesOnly}
                                onChange={(e) =>
                                  setShowAuthCookiesOnly(e.target.checked)
                                }
                              />
                              Show only auth cookies
                            </label>
                            <button
                              className="analyze-btn-primary"
                              onClick={analyzeCookies}
                              disabled={isAnalyzingCookies}
                            >
                              {isAnalyzingCookies
                                ? "⏳ Analyzing..."
                                : "🔍 Analyze Cookies"}
                            </button>
                          </div>

                          {showCookieAnalysis && cookieAnalysis && (
                            <div className="analysis-results">
                              <div className="analysis-stats">
                                <div className="stat-card">
                                  <div className="stat-value">
                                    {cookieAnalysis.total}
                                  </div>
                                  <div className="stat-label">
                                    Total Cookies
                                  </div>
                                </div>
                                <div className="stat-card">
                                  <div className="stat-value">
                                    {cookieAnalysis.unique_domains}
                                  </div>
                                  <div className="stat-label">
                                    Unique Domains
                                  </div>
                                </div>
                                <div className="stat-card">
                                  <div className="stat-value">
                                    {cookieAnalysis.auth_count}
                                  </div>
                                  <div className="stat-label">Auth Cookies</div>
                                </div>
                                <div className="stat-card">
                                  <div className="stat-value">
                                    {Math.round(
                                      (cookieAnalysis.secure_count /
                                        cookieAnalysis.total) *
                                        100
                                    )}
                                    %
                                  </div>
                                  <div className="stat-label">Secure</div>
                                </div>
                              </div>

                              {cookieAnalysis.top_domains &&
                                cookieAnalysis.top_domains.length > 0 && (
                                  <div className="top-domains">
                                    <h3>🌐 Top Domains</h3>
                                    <div className="domain-list">
                                      {cookieAnalysis.top_domains.map(
                                        (item: any, idx: number) => (
                                          <div
                                            key={idx}
                                            className="domain-item"
                                          >
                                            <span className="domain-name">
                                              {item.domain}
                                            </span>
                                            <span className="domain-count">
                                              {item.count} cookies
                                            </span>
                                          </div>
                                        )
                                      )}
                                    </div>
                                  </div>
                                )}

                              {cookieAnalysis.auth_cookies &&
                                cookieAnalysis.auth_cookies.length > 0 && (
                                  <div className="auth-cookies-list">
                                    <h3>🔑 Authentication Cookies</h3>
                                    <div className="cookie-table">
                                      <table>
                                        <thead>
                                          <tr>
                                            <th>Name</th>
                                            <th>Value</th>
                                            <th>Domain</th>
                                            <th>Expires</th>
                                            <th>SameSite</th>
                                            <th>Flags</th>
                                            <th>Actions</th>
                                          </tr>
                                        </thead>
                                        <tbody>
                                          {cookieAnalysis.auth_cookies.map(
                                            (cookie: any, idx: number) => (
                                              <tr
                                                key={idx}
                                                className="cookie-row-clickable"
                                                onClick={() =>
                                                  viewCookie(cookie)
                                                }
                                              >
                                                <td className="cookie-name">
                                                  {cookie.name}
                                                </td>
                                                <td className="cookie-value">
                                                  {cookie.value || "(empty)"}
                                                </td>
                                                <td className="cookie-domain">
                                                  {cookie.domain}
                                                </td>
                                                <td className="cookie-expires">
                                                  {cookie.expires === -1 ||
                                                  cookie.expires === null
                                                    ? "Session"
                                                    : new Date(
                                                        cookie.expires * 1000
                                                      ).toLocaleDateString()}
                                                </td>
                                                <td className="cookie-samesite">
                                                  <span
                                                    className={`samesite-badge samesite-${(
                                                      cookie.sameSite || "Lax"
                                                    ).toLowerCase()}`}
                                                  >
                                                    {cookie.sameSite || "Lax"}
                                                  </span>
                                                </td>
                                                <td className="cookie-flags">
                                                  {cookie.secure && (
                                                    <span className="flag secure">
                                                      🔒
                                                    </span>
                                                  )}
                                                  {cookie.httpOnly && (
                                                    <span className="flag httponly">
                                                      🚫
                                                    </span>
                                                  )}
                                                </td>
                                                <td className="cookie-actions">
                                                  <button
                                                    className="btn-icon-small"
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      viewCookie(cookie);
                                                    }}
                                                    title="View/Edit"
                                                  >
                                                    ✏️
                                                  </button>
                                                  <button
                                                    className="btn-icon-small btn-danger-small"
                                                    onClick={(e) => {
                                                      e.stopPropagation();
                                                      deleteCookie(cookie);
                                                    }}
                                                    title="Delete"
                                                  >
                                                    🗑️
                                                  </button>
                                                </td>
                                              </tr>
                                            )
                                          )}
                                        </tbody>
                                      </table>
                                    </div>
                                  </div>
                                )}
                            </div>
                          )}
                        </div>
                      )}

                    {/* Cookie Editor Modal */}
                    {showCookieEditor && editingCookie && (
                      <div
                        className="modal-overlay"
                        onClick={() => setShowCookieEditor(false)}
                      >
                        <div
                          className="modal-content cookie-editor-modal"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="modal-header">
                            <h2>🍪 Cookie Editor</h2>
                            <button
                              className="modal-close-btn"
                              onClick={() => setShowCookieEditor(false)}
                            >
                              ✕
                            </button>
                          </div>

                          <div className="modal-body">
                            {/* Security & Type Badges */}
                            <div className="cookie-badges">
                              <span
                                className={`badge ${
                                  editingCookie.secure && editingCookie.httpOnly
                                    ? "badge-success"
                                    : editingCookie.secure ||
                                      editingCookie.httpOnly
                                    ? "badge-warning"
                                    : "badge-danger"
                                }`}
                              >
                                {editingCookie.secure && editingCookie.httpOnly
                                  ? "🛡️ Secure"
                                  : editingCookie.secure
                                  ? "🔒 HTTPS Only"
                                  : editingCookie.httpOnly
                                  ? "🚫 No JS Access"
                                  : "⚠️ Insecure"}
                              </span>

                              {/* Cookie Prefix Badge */}
                              {editingCookie.name?.startsWith("__Secure-") && (
                                <span className="badge badge-prefix-secure">
                                  🔐 __Secure- Prefix
                                </span>
                              )}
                              {editingCookie.name?.startsWith("__Host-") && (
                                <span className="badge badge-prefix-host">
                                  🏠 __Host- Prefix
                                </span>
                              )}

                              <span className="badge badge-info">
                                {editingCookie.domain?.startsWith(".")
                                  ? "🌐 Subdomain Cookie"
                                  : "📍 Exact Domain"}
                              </span>
                              {editingCookie.expires === -1 ||
                              !editingCookie.expires ? (
                                <span className="badge badge-session">
                                  ⏱️ Session Cookie
                                </span>
                              ) : (
                                <span className="badge badge-persistent">
                                  💾 Expires:{" "}
                                  {new Date(
                                    editingCookie.expires * 1000
                                  ).toLocaleDateString()}
                                </span>
                              )}

                              {/* Cookie Size Warning */}
                              {(() => {
                                const cookieSize =
                                  (editingCookie.name?.length || 0) +
                                  (editingCookie.value?.length || 0);
                                if (cookieSize > 4096) {
                                  return (
                                    <span className="badge badge-danger">
                                      ⚠️ Size: {cookieSize} bytes (exceeds 4096
                                      limit!)
                                    </span>
                                  );
                                } else if (cookieSize > 3000) {
                                  return (
                                    <span className="badge badge-warning">
                                      📏 Size: {cookieSize} bytes
                                    </span>
                                  );
                                }
                                return null;
                              })()}

                              {/* CHIPS Badge */}
                              {editingCookie.partitioned && (
                                <span className="badge badge-chips">
                                  🔒 CHIPS (Partitioned)
                                </span>
                              )}
                            </div>

                            <div className="cookie-editor-form">
                              <div className="form-group">
                                <label>
                                  Name
                                  <span
                                    className="tooltip-icon"
                                    title="Cookie identifier (case-sensitive). Use __Secure- or __Host- prefixes for enhanced security (RFC 6265bis)"
                                  >
                                    ℹ️
                                  </span>
                                </label>
                                <input
                                  type="text"
                                  value={editingCookie.name}
                                  onChange={(e) =>
                                    setEditingCookie({
                                      ...editingCookie,
                                      name: e.target.value,
                                    })
                                  }
                                  className="form-input"
                                  placeholder="session_id or __Secure-session_id"
                                />
                                {editingCookie.name?.startsWith("__Secure-") &&
                                  !editingCookie.secure && (
                                    <small className="warning-text">
                                      ⚠️ __Secure- prefix requires Secure flag!
                                    </small>
                                  )}
                                {editingCookie.name?.startsWith("__Host-") && (
                                  <>
                                    {!editingCookie.secure && (
                                      <small className="warning-text">
                                        ⚠️ __Host- prefix requires Secure flag!
                                      </small>
                                    )}
                                    {editingCookie.path !== "/" && (
                                      <small className="warning-text">
                                        ⚠️ __Host- prefix requires Path=/!
                                      </small>
                                    )}
                                    {editingCookie.domain && (
                                      <small className="warning-text">
                                        ⚠️ __Host- prefix must not have Domain
                                        attribute!
                                      </small>
                                    )}
                                  </>
                                )}
                              </div>

                              <div className="form-group">
                                <label>
                                  Value
                                  <span
                                    className="tooltip-icon"
                                    title="Cookie data (opaque token recommended for auth)"
                                  >
                                    ℹ️
                                  </span>
                                </label>
                                <textarea
                                  value={editingCookie.value || ""}
                                  onChange={(e) =>
                                    setEditingCookie({
                                      ...editingCookie,
                                      value: e.target.value,
                                    })
                                  }
                                  className="form-textarea"
                                  rows={3}
                                  placeholder="abc123xyz..."
                                />
                              </div>

                              <div className="form-row">
                                <div className="form-group">
                                  <label>
                                    Domain
                                    <span
                                      className="tooltip-icon"
                                      title="Use .example.com for subdomains, example.com for exact match"
                                    >
                                      ℹ️
                                    </span>
                                  </label>
                                  <input
                                    type="text"
                                    value={editingCookie.domain}
                                    onChange={(e) =>
                                      setEditingCookie({
                                        ...editingCookie,
                                        domain: e.target.value,
                                      })
                                    }
                                    className="form-input"
                                    placeholder=".example.com"
                                  />
                                </div>

                                <div className="form-group">
                                  <label>
                                    Path
                                    <span
                                      className="tooltip-icon"
                                      title="URL path scope (/ for entire domain)"
                                    >
                                      ℹ️
                                    </span>
                                  </label>
                                  <input
                                    type="text"
                                    value={editingCookie.path || "/"}
                                    onChange={(e) =>
                                      setEditingCookie({
                                        ...editingCookie,
                                        path: e.target.value,
                                      })
                                    }
                                    className="form-input"
                                    placeholder="/"
                                  />
                                </div>
                              </div>

                              <div className="form-group">
                                <label>
                                  SameSite
                                  <span
                                    className="tooltip-icon"
                                    title="Controls cross-site request behavior (RFC 6265bis)"
                                  >
                                    ℹ️
                                  </span>
                                </label>
                                <select
                                  value={editingCookie.sameSite || "Lax"}
                                  onChange={(e) =>
                                    setEditingCookie({
                                      ...editingCookie,
                                      sameSite: e.target.value,
                                    })
                                  }
                                  className="form-select"
                                >
                                  <option value="Strict">
                                    Strict - Same-site only (most secure)
                                  </option>
                                  <option value="Lax">
                                    Lax - Top-level navigation (default)
                                  </option>
                                  <option value="None">
                                    None - Allow third-party (requires Secure)
                                  </option>
                                </select>
                                {editingCookie.sameSite === "None" &&
                                  !editingCookie.secure && (
                                    <small className="warning-text">
                                      ⚠️ SameSite=None requires Secure flag!
                                    </small>
                                  )}
                              </div>

                              <div className="form-row-checkboxes">
                                <div className="form-group-checkbox">
                                  <label>
                                    <input
                                      type="checkbox"
                                      checked={editingCookie.secure || false}
                                      onChange={(e) =>
                                        setEditingCookie({
                                          ...editingCookie,
                                          secure: e.target.checked,
                                        })
                                      }
                                    />
                                    <span className="checkbox-label">
                                      🔒 Secure
                                      <span
                                        className="tooltip-icon"
                                        title="Only sent over HTTPS connections"
                                      >
                                        ℹ️
                                      </span>
                                    </span>
                                  </label>
                                </div>

                                <div className="form-group-checkbox">
                                  <label>
                                    <input
                                      type="checkbox"
                                      checked={editingCookie.httpOnly || false}
                                      onChange={(e) =>
                                        setEditingCookie({
                                          ...editingCookie,
                                          httpOnly: e.target.checked,
                                        })
                                      }
                                    />
                                    <span className="checkbox-label">
                                      🚫 HttpOnly
                                      <span
                                        className="tooltip-icon"
                                        title="Prevents JavaScript access (XSS protection)"
                                      >
                                        ℹ️
                                      </span>
                                    </span>
                                  </label>
                                </div>

                                <div className="form-group-checkbox">
                                  <label>
                                    <input
                                      type="checkbox"
                                      checked={
                                        editingCookie.partitioned || false
                                      }
                                      onChange={(e) =>
                                        setEditingCookie({
                                          ...editingCookie,
                                          partitioned: e.target.checked,
                                        })
                                      }
                                    />
                                    <span className="checkbox-label">
                                      🔐 Partitioned (CHIPS)
                                      <span
                                        className="tooltip-icon"
                                        title="Cookies Having Independent Partitioned State - separate cookie jar per top-level site (Chrome 114+)"
                                      >
                                        ℹ️
                                      </span>
                                    </span>
                                  </label>
                                </div>
                              </div>
                              {editingCookie.partitioned &&
                                !editingCookie.secure && (
                                  <small className="warning-text">
                                    ⚠️ Partitioned cookies must have Secure
                                    flag!
                                  </small>
                                )}
                              {editingCookie.partitioned &&
                                !editingCookie.name?.startsWith("__Host-") && (
                                  <small className="info-text">
                                    💡 Recommended: Use __Host- prefix with
                                    Partitioned cookies for enhanced security
                                  </small>
                                )}

                              <div className="form-group">
                                <label>
                                  Expires
                                  <span
                                    className="tooltip-icon"
                                    title="Persistent cookie expiration (leave empty for session cookie)"
                                  >
                                    ℹ️
                                  </span>
                                </label>
                                <input
                                  type="datetime-local"
                                  value={
                                    editingCookie.expires &&
                                    editingCookie.expires !== -1
                                      ? new Date(editingCookie.expires * 1000)
                                          .toISOString()
                                          .slice(0, 16)
                                      : ""
                                  }
                                  onChange={(e) => {
                                    const timestamp = e.target.value
                                      ? Math.floor(
                                          new Date(e.target.value).getTime() /
                                            1000
                                        )
                                      : -1;
                                    setEditingCookie({
                                      ...editingCookie,
                                      expires: timestamp,
                                    });
                                  }}
                                  className="form-input"
                                />
                                <small>
                                  Leave empty for session cookie (cleared when
                                  browser closes)
                                </small>
                              </div>
                            </div>
                          </div>

                          <div className="modal-footer">
                            <div className="modal-footer-left">
                              <button
                                className="btn-danger"
                                onClick={() => {
                                  deleteCookie(editingCookie);
                                }}
                              >
                                🗑️ Delete
                              </button>
                              <button
                                className="btn-secondary"
                                onClick={() => openExportModal("curl")}
                                title="Export as cURL command with options"
                              >
                                📋 cURL
                              </button>
                              <button
                                className="btn-secondary"
                                onClick={() => openExportModal("playwright")}
                                title="Export as Playwright code with options"
                              >
                                🎭 Playwright
                              </button>
                              <button
                                className="btn-security"
                                onClick={runSecurityAudit}
                                title="Run OWASP-compliant security audit"
                              >
                                🔒 Security Audit
                              </button>
                            </div>
                            <div className="modal-footer-right">
                              <button
                                className="btn-secondary"
                                onClick={() => setShowCookieEditor(false)}
                              >
                                Cancel
                              </button>
                              <button
                                className="btn-primary"
                                onClick={updateCookie}
                              >
                                💾 Save Changes
                              </button>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 📤 Export Modal */}
                    {showExportModal && (
                      <div
                        className="modal-overlay"
                        onClick={() => setShowExportModal(false)}
                      >
                        <div
                          className="modal-content export-modal"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="modal-header">
                            <h3>
                              {exportType === "curl"
                                ? "📋 Export as cURL"
                                : "🎭 Export as Playwright"}
                            </h3>
                            <button
                              className="modal-close"
                              onClick={() => setShowExportModal(false)}
                            >
                              ✕
                            </button>
                          </div>

                          <div className="modal-body">
                            {/* Export Options */}
                            <div className="export-options">
                              <h4>Export Options</h4>

                              {exportType === "curl" && (
                                <>
                                  <label className="checkbox-label">
                                    <input
                                      type="checkbox"
                                      checked={exportOptions.includeMethod}
                                      onChange={(e) =>
                                        setExportOptions({
                                          ...exportOptions,
                                          includeMethod: e.target.checked,
                                        })
                                      }
                                    />
                                    <span>Include HTTP Method</span>
                                  </label>

                                  {exportOptions.includeMethod && (
                                    <div className="form-group">
                                      <label>HTTP Method</label>
                                      <select
                                        value={exportOptions.method}
                                        onChange={(e) =>
                                          setExportOptions({
                                            ...exportOptions,
                                            method: e.target.value,
                                          })
                                        }
                                        className="form-select"
                                      >
                                        <option value="GET">GET</option>
                                        <option value="POST">POST</option>
                                        <option value="PUT">PUT</option>
                                        <option value="DELETE">DELETE</option>
                                        <option value="PATCH">PATCH</option>
                                      </select>
                                    </div>
                                  )}

                                  <label className="checkbox-label">
                                    <input
                                      type="checkbox"
                                      checked={exportOptions.includeUrl}
                                      onChange={(e) =>
                                        setExportOptions({
                                          ...exportOptions,
                                          includeUrl: e.target.checked,
                                        })
                                      }
                                    />
                                    <span>Include URL</span>
                                  </label>

                                  {exportOptions.includeUrl && (
                                    <div className="form-group">
                                      <label>Target URL</label>
                                      <input
                                        type="text"
                                        value={exportOptions.url}
                                        onChange={(e) =>
                                          setExportOptions({
                                            ...exportOptions,
                                            url: e.target.value,
                                          })
                                        }
                                        className="form-input"
                                        placeholder="https://example.com/api"
                                      />
                                    </div>
                                  )}
                                </>
                              )}

                              {exportType === "playwright" && (
                                <>
                                  <label className="checkbox-label">
                                    <input
                                      type="checkbox"
                                      checked={exportOptions.prettyPrint}
                                      onChange={(e) =>
                                        setExportOptions({
                                          ...exportOptions,
                                          prettyPrint: e.target.checked,
                                        })
                                      }
                                    />
                                    <span>Pretty Print (Multi-line)</span>
                                  </label>
                                </>
                              )}

                              <label className="checkbox-label">
                                <input
                                  type="checkbox"
                                  checked={exportOptions.includeComments}
                                  onChange={(e) =>
                                    setExportOptions({
                                      ...exportOptions,
                                      includeComments: e.target.checked,
                                    })
                                  }
                                />
                                <span>Include Comments</span>
                              </label>

                              <label className="checkbox-label">
                                <input
                                  type="checkbox"
                                  checked={exportOptions.explainEverything}
                                  onChange={(e) =>
                                    setExportOptions({
                                      ...exportOptions,
                                      explainEverything: e.target.checked,
                                    })
                                  }
                                />
                                <span>
                                  📚 Explain Everything (Educational Mode)
                                </span>
                              </label>
                            </div>

                            {/* Editable Code Preview */}
                            <div className="export-preview">
                              <h4>
                                Code Preview (Editable)
                                <span className="preview-hint">
                                  ✏️ Edit before copying
                                </span>
                              </h4>
                              <textarea
                                className="code-editor"
                                value={exportCode}
                                onChange={(e) => setExportCode(e.target.value)}
                                spellCheck={false}
                                rows={20}
                              />
                            </div>
                          </div>

                          <div className="modal-footer">
                            <button
                              className="btn-secondary"
                              onClick={() => setShowExportModal(false)}
                            >
                              Cancel
                            </button>
                            <button
                              className="btn-primary"
                              onClick={copyExportCode}
                            >
                              📋 Copy to Clipboard
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 🔒 Security Audit Modal */}
                    {showSecurityAudit && securityReport && (
                      <div
                        className="modal-overlay"
                        onClick={() => setShowSecurityAudit(false)}
                      >
                        <div
                          className="modal-content security-audit-modal"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="modal-header">
                            <h3>🔒 Cookie Security Audit</h3>
                            <button
                              className="modal-close"
                              onClick={() => setShowSecurityAudit(false)}
                            >
                              ✕
                            </button>
                          </div>

                          <div className="modal-body">
                            {/* Security Score */}
                            <div className="security-score-card">
                              <div
                                className="score-circle"
                                style={{
                                  borderColor: securityReport.ratingColor,
                                }}
                              >
                                <div
                                  className="score-value"
                                  style={{ color: securityReport.ratingColor }}
                                >
                                  {securityReport.score}
                                </div>
                                <div className="score-label">/ 100</div>
                              </div>
                              <div className="score-details">
                                <h2
                                  style={{ color: securityReport.ratingColor }}
                                >
                                  {securityReport.rating}
                                </h2>
                                <p className="cookie-name">
                                  Cookie: {securityReport.cookieName}
                                </p>
                                <p className="audit-timestamp">
                                  Audited: {securityReport.timestamp}
                                </p>
                              </div>
                            </div>

                            {/* Critical Issues */}
                            {securityReport.issues.length > 0 && (
                              <div className="audit-section">
                                <h4 className="section-title critical">
                                  🚨 Critical Issues (
                                  {securityReport.issues.length})
                                </h4>
                                {securityReport.issues.map(
                                  (issue: any, idx: number) => (
                                    <div
                                      key={idx}
                                      className={`audit-item severity-${issue.severity.toLowerCase()}`}
                                    >
                                      <div className="audit-header">
                                        <span
                                          className={`severity-badge ${issue.severity.toLowerCase()}`}
                                        >
                                          {issue.severity}
                                        </span>
                                        <strong>{issue.title}</strong>
                                      </div>
                                      <p className="audit-description">
                                        {issue.description}
                                      </p>
                                      <p className="audit-impact">
                                        <strong>Impact:</strong> {issue.impact}
                                      </p>
                                      <p className="audit-fix">
                                        <strong>Fix:</strong> {issue.fix}
                                      </p>
                                      <p className="audit-owasp">
                                        <strong>Reference:</strong>{" "}
                                        {issue.owasp}
                                      </p>
                                    </div>
                                  )
                                )}
                              </div>
                            )}

                            {/* Warnings */}
                            {securityReport.warnings.length > 0 && (
                              <div className="audit-section">
                                <h4 className="section-title warning">
                                  ⚠️ Warnings ({securityReport.warnings.length})
                                </h4>
                                {securityReport.warnings.map(
                                  (warning: any, idx: number) => (
                                    <div
                                      key={idx}
                                      className={`audit-item severity-${warning.severity.toLowerCase()}`}
                                    >
                                      <div className="audit-header">
                                        <span
                                          className={`severity-badge ${warning.severity.toLowerCase()}`}
                                        >
                                          {warning.severity}
                                        </span>
                                        <strong>{warning.title}</strong>
                                      </div>
                                      <p className="audit-description">
                                        {warning.description}
                                      </p>
                                      <p className="audit-impact">
                                        <strong>Impact:</strong>{" "}
                                        {warning.impact}
                                      </p>
                                      <p className="audit-fix">
                                        <strong>Recommendation:</strong>{" "}
                                        {warning.fix}
                                      </p>
                                      <p className="audit-owasp">
                                        <strong>Reference:</strong>{" "}
                                        {warning.owasp}
                                      </p>
                                    </div>
                                  )
                                )}
                              </div>
                            )}

                            {/* Recommendations */}
                            {securityReport.recommendations.length > 0 && (
                              <div className="audit-section">
                                <h4 className="section-title info">
                                  💡 Recommendations (
                                  {securityReport.recommendations.length})
                                </h4>
                                {securityReport.recommendations.map(
                                  (rec: any, idx: number) => (
                                    <div
                                      key={idx}
                                      className={`audit-item severity-${rec.severity.toLowerCase()}`}
                                    >
                                      <div className="audit-header">
                                        <span
                                          className={`severity-badge ${rec.severity.toLowerCase()}`}
                                        >
                                          {rec.severity}
                                        </span>
                                        <strong>{rec.title}</strong>
                                      </div>
                                      <p className="audit-description">
                                        {rec.description}
                                      </p>
                                      <p className="audit-impact">
                                        <strong>Benefit:</strong> {rec.impact}
                                      </p>
                                      <p className="audit-fix">
                                        <strong>Suggestion:</strong> {rec.fix}
                                      </p>
                                      <p className="audit-owasp">
                                        <strong>Reference:</strong> {rec.owasp}
                                      </p>
                                    </div>
                                  )
                                )}
                              </div>
                            )}

                            {/* All Clear */}
                            {securityReport.issues.length === 0 &&
                              securityReport.warnings.length === 0 &&
                              securityReport.recommendations.length === 0 && (
                                <div className="audit-all-clear">
                                  <div className="all-clear-icon">✅</div>
                                  <h3>Perfect Security Configuration!</h3>
                                  <p>
                                    This cookie follows all OWASP best practices
                                    and RFC 6265bis standards.
                                  </p>
                                </div>
                              )}
                          </div>

                          <div className="modal-footer">
                            <button
                              className="btn-secondary"
                              onClick={() => setShowSecurityAudit(false)}
                            >
                              Close
                            </button>
                            <button
                              className="btn-primary"
                              onClick={() => {
                                const report = JSON.stringify(
                                  securityReport,
                                  null,
                                  2
                                );
                                navigator.clipboard.writeText(report);
                                alert(
                                  "✅ Security report copied to clipboard!"
                                );
                              }}
                            >
                              📋 Copy Report
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 📤 Multi-Format Export Modal */}
                    {showFormatExport && (
                      <div
                        className="modal-overlay"
                        onClick={() => setShowFormatExport(false)}
                      >
                        <div
                          className="modal-content format-export-modal"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="modal-header">
                            <h3>📤 Export Cookies - Multiple Formats</h3>
                            <button
                              className="modal-close"
                              onClick={() => setShowFormatExport(false)}
                            >
                              ✕
                            </button>
                          </div>

                          <div className="modal-body">
                            <div className="format-selection">
                              <h4>Select Export Format</h4>

                              <div className="format-options">
                                <label
                                  className={`format-option ${
                                    exportFormat === "json" ? "selected" : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="exportFormat"
                                    value="json"
                                    checked={exportFormat === "json"}
                                    onChange={(e) =>
                                      setExportFormat(e.target.value)
                                    }
                                  />
                                  <div className="format-details">
                                    <div className="format-title">📄 JSON</div>
                                    <div className="format-description">
                                      Standard JSON format (current format)
                                    </div>
                                    <div className="format-extension">
                                      .json
                                    </div>
                                  </div>
                                </label>

                                <label
                                  className={`format-option ${
                                    exportFormat === "netscape"
                                      ? "selected"
                                      : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="exportFormat"
                                    value="netscape"
                                    checked={exportFormat === "netscape"}
                                    onChange={(e) =>
                                      setExportFormat(e.target.value)
                                    }
                                  />
                                  <div className="format-details">
                                    <div className="format-title">
                                      🍪 Netscape
                                    </div>
                                    <div className="format-description">
                                      cookies.txt format (compatible with curl,
                                      wget)
                                    </div>
                                    <div className="format-extension">.txt</div>
                                  </div>
                                </label>

                                <label
                                  className={`format-option ${
                                    exportFormat === "har" ? "selected" : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="exportFormat"
                                    value="har"
                                    checked={exportFormat === "har"}
                                    onChange={(e) =>
                                      setExportFormat(e.target.value)
                                    }
                                  />
                                  <div className="format-details">
                                    <div className="format-title">📦 HAR</div>
                                    <div className="format-description">
                                      HTTP Archive format (browser DevTools
                                      compatible)
                                    </div>
                                    <div className="format-extension">.har</div>
                                  </div>
                                </label>

                                <label
                                  className={`format-option ${
                                    exportFormat === "csv" ? "selected" : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="exportFormat"
                                    value="csv"
                                    checked={exportFormat === "csv"}
                                    onChange={(e) =>
                                      setExportFormat(e.target.value)
                                    }
                                  />
                                  <div className="format-details">
                                    <div className="format-title">📊 CSV</div>
                                    <div className="format-description">
                                      Comma-separated values (Excel, Google
                                      Sheets)
                                    </div>
                                    <div className="format-extension">.csv</div>
                                  </div>
                                </label>

                                <label
                                  className={`format-option ${
                                    exportFormat === "headers" ? "selected" : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="exportFormat"
                                    value="headers"
                                    checked={exportFormat === "headers"}
                                    onChange={(e) =>
                                      setExportFormat(e.target.value)
                                    }
                                  />
                                  <div className="format-details">
                                    <div className="format-title">
                                      📋 Set-Cookie Headers
                                    </div>
                                    <div className="format-description">
                                      HTTP Set-Cookie header format
                                      (server-side)
                                    </div>
                                    <div className="format-extension">.txt</div>
                                  </div>
                                </label>

                                <label
                                  className={`format-option ${
                                    exportFormat === "curl-headers"
                                      ? "selected"
                                      : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="exportFormat"
                                    value="curl-headers"
                                    checked={exportFormat === "curl-headers"}
                                    onChange={(e) =>
                                      setExportFormat(e.target.value)
                                    }
                                  />
                                  <div className="format-details">
                                    <div className="format-title">
                                      🔧 cURL Command
                                    </div>
                                    <div className="format-description">
                                      Ready-to-use cURL command with all cookies
                                    </div>
                                    <div className="format-extension">.sh</div>
                                  </div>
                                </label>
                              </div>
                            </div>

                            <div className="format-preview">
                              <h4>Preview</h4>
                              <pre className="format-preview-code">
                                {exportAllCookiesInFormat(exportFormat)}
                              </pre>
                            </div>
                          </div>

                          <div className="modal-footer">
                            <button
                              className="btn-secondary"
                              onClick={() => setShowFormatExport(false)}
                            >
                              Cancel
                            </button>
                            <button
                              className="btn-secondary"
                              onClick={copyFormattedCookies}
                            >
                              📋 Copy to Clipboard
                            </button>
                            <button
                              className="btn-primary"
                              onClick={downloadCookiesInFormat}
                            >
                              💾 Download File
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* 📥 Multi-Format Import Modal */}
                    {showFormatImport && (
                      <div
                        className="modal-overlay"
                        onClick={() => setShowFormatImport(false)}
                      >
                        <div
                          className="modal-content format-import-modal"
                          onClick={(e) => e.stopPropagation()}
                        >
                          <div className="modal-header">
                            <h3>📥 Import Cookies - Multiple Formats</h3>
                            <button
                              className="modal-close"
                              onClick={() => setShowFormatImport(false)}
                            >
                              ✕
                            </button>
                          </div>

                          <div className="modal-body">
                            <div className="import-instructions">
                              <p>
                                <strong>📋 Supported Formats:</strong>
                              </p>
                              <ul>
                                <li>
                                  <strong>JSON</strong> - Standard JSON array
                                  format
                                </li>
                                <li>
                                  <strong>Netscape</strong> - cookies.txt format
                                  (curl, wget compatible)
                                </li>
                                <li>
                                  <strong>HAR</strong> - HTTP Archive format
                                  (browser DevTools export)
                                </li>
                                <li>
                                  <strong>CSV</strong> - Comma-separated values
                                  (Excel, Google Sheets)
                                </li>
                              </ul>
                            </div>

                            <div className="format-selection">
                              <h4>Select Import Format</h4>

                              <div className="format-options-compact">
                                <label
                                  className={`format-option-compact ${
                                    importFormat === "json" ? "selected" : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="importFormat"
                                    value="json"
                                    checked={importFormat === "json"}
                                    onChange={(e) =>
                                      setImportFormat(e.target.value)
                                    }
                                  />
                                  <span>📄 JSON</span>
                                </label>

                                <label
                                  className={`format-option-compact ${
                                    importFormat === "netscape"
                                      ? "selected"
                                      : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="importFormat"
                                    value="netscape"
                                    checked={importFormat === "netscape"}
                                    onChange={(e) =>
                                      setImportFormat(e.target.value)
                                    }
                                  />
                                  <span>🍪 Netscape</span>
                                </label>

                                <label
                                  className={`format-option-compact ${
                                    importFormat === "har" ? "selected" : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="importFormat"
                                    value="har"
                                    checked={importFormat === "har"}
                                    onChange={(e) =>
                                      setImportFormat(e.target.value)
                                    }
                                  />
                                  <span>📦 HAR</span>
                                </label>

                                <label
                                  className={`format-option-compact ${
                                    importFormat === "csv" ? "selected" : ""
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name="importFormat"
                                    value="csv"
                                    checked={importFormat === "csv"}
                                    onChange={(e) =>
                                      setImportFormat(e.target.value)
                                    }
                                  />
                                  <span>📊 CSV</span>
                                </label>
                              </div>
                            </div>

                            <div className="file-upload-section">
                              <label className="file-upload-label">
                                <input
                                  type="file"
                                  accept=".json,.txt,.har,.csv"
                                  onChange={handleImportFile}
                                  style={{ display: "none" }}
                                />
                                <div className="file-upload-button">
                                  📁 Choose File to Import
                                </div>
                              </label>
                              <p className="file-upload-hint">
                                Select a file in {importFormat.toUpperCase()}{" "}
                                format
                              </p>
                            </div>
                          </div>

                          <div className="modal-footer">
                            <button
                              className="btn-secondary"
                              onClick={() => setShowFormatImport(false)}
                            >
                              Cancel
                            </button>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Button 2: Automated Auth State */}
                    <button
                      className={`auth-method-btn ${
                        expandedAuthMethod === "automated" ? "active" : ""
                      }`}
                      onClick={() =>
                        setExpandedAuthMethod(
                          expandedAuthMethod === "automated"
                            ? null
                            : "automated"
                        )
                      }
                    >
                      <div className="btn-icon">🔐</div>
                      <div className="btn-content">
                        <div className="btn-title">Automated Auth State</div>
                        <div className="btn-description">
                          One-click login with browser automation (Recommended)
                        </div>
                        {authStateStatus.exists && (
                          <div className="btn-badge">✅ Active</div>
                        )}
                      </div>
                      <div className="btn-arrow">
                        {expandedAuthMethod === "automated" ? "▼" : "▶"}
                      </div>
                    </button>

                    {expandedAuthMethod === "automated" && (
                      <div className="auth-method-content">
                        {authStateStatus.exists ? (
                          <div className="auth-state-saved">
                            <div className="auth-state-info">
                              <span className="status-indicator active">●</span>
                              <div className="auth-state-details">
                                <strong>✅ Auth State Saved!</strong>
                                <p>
                                  Cookies: {authStateStatus.cookie_count || 0} |
                                  localStorage:{" "}
                                  {authStateStatus.localStorage_count || 0}{" "}
                                  items
                                </p>
                              </div>
                            </div>
                            <div className="auth-state-actions">
                              <button
                                className="btn-secondary"
                                onClick={openLoginBrowser}
                              >
                                🔄 Update Auth State
                              </button>
                              <button
                                className="btn-danger"
                                onClick={clearAuthState}
                              >
                                🗑️ Clear
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="auth-state-empty">
                            <p>No auth state saved yet.</p>
                            <button
                              className="btn-primary"
                              onClick={openLoginBrowser}
                              disabled={isLoginInProgress}
                            >
                              {isLoginInProgress
                                ? "⏳ Opening browser..."
                                : "🚀 Open Login Browser"}
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Button 3: Browser Cookie Import */}
                    <button
                      className={`auth-method-btn ${
                        expandedAuthMethod === "import" ? "active" : ""
                      }`}
                      onClick={() =>
                        setExpandedAuthMethod(
                          expandedAuthMethod === "import" ? null : "import"
                        )
                      }
                    >
                      <div className="btn-icon">🍪</div>
                      <div className="btn-content">
                        <div className="btn-title">Import Browser Cookies</div>
                        <div className="btn-description">
                          Extract cookies from your installed browsers
                        </div>
                        {cookieImportStatus.playwright?.exists && (
                          <div className="btn-badge">
                            ✅ {cookieImportStatus.playwright.cookie_count}{" "}
                            cookies
                          </div>
                        )}
                      </div>
                      <div className="btn-arrow">
                        {expandedAuthMethod === "import" ? "▼" : "▶"}
                      </div>
                    </button>

                    {expandedAuthMethod === "import" && (
                      <div className="auth-method-content">
                        <div className="cookie-import-controls">
                          <select
                            value={selectedBrowser}
                            onChange={(e) => setSelectedBrowser(e.target.value)}
                            className="browser-select"
                          >
                            <option value="auto">Auto-detect</option>
                            <option value="chrome">Chrome</option>
                            <option value="firefox">Firefox</option>
                            <option value="edge">Edge</option>
                            <option value="safari">Safari</option>
                            <option value="brave">Brave</option>
                            <option value="opera">Opera</option>
                          </select>

                          <input
                            type="text"
                            placeholder="Domains (optional, comma-separated)"
                            value={cookieDomains}
                            onChange={(e) => setCookieDomains(e.target.value)}
                            className="domain-input"
                          />

                          <button
                            className="btn-primary"
                            onClick={extractCookies}
                            disabled={isExtractingCookies}
                          >
                            {isExtractingCookies
                              ? "⏳ Extracting..."
                              : "🍪 Extract Cookies"}
                          </button>
                        </div>

                        {cookieImportStatus.playwright?.exists && (
                          <div className="cookie-status">
                            <p>
                              ✅ {cookieImportStatus.playwright.cookie_count}{" "}
                              cookies extracted
                              {cookieImportStatus.playwright.extracted_at && (
                                <span>
                                  {" "}
                                  •{" "}
                                  {new Date(
                                    cookieImportStatus.playwright.extracted_at
                                  ).toLocaleString()}
                                </span>
                              )}
                            </p>
                            <button
                              className="btn-secondary"
                              onClick={clearCookies}
                            >
                              🗑️ Clear Cookies
                            </button>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Button 4: Manual Cookie/LocalStorage */}
                    <button
                      className={`auth-method-btn ${
                        expandedAuthMethod === "manual" ? "active" : ""
                      }`}
                      onClick={() =>
                        setExpandedAuthMethod(
                          expandedAuthMethod === "manual" ? null : "manual"
                        )
                      }
                    >
                      <div className="btn-icon">✍️</div>
                      <div className="btn-content">
                        <div className="btn-title">
                          Manual Cookie & LocalStorage
                        </div>
                        <div className="btn-description">
                          Paste cookies and localStorage manually
                        </div>
                      </div>
                      <div className="btn-arrow">
                        {expandedAuthMethod === "manual" ? "▼" : "▶"}
                      </div>
                    </button>

                    {expandedAuthMethod === "manual" && (
                      <div className="auth-method-content">
                        <div className="manual-input-section">
                          <label>
                            <strong>🍪 Cookies (JSON format)</strong>
                            <textarea
                              value={cookies}
                              onChange={(e) => setCookies(e.target.value)}
                              placeholder='[{"name": "session", "value": "abc123", "domain": ".example.com"}]'
                              rows={6}
                              className="manual-textarea"
                            />
                          </label>

                          <label>
                            <strong>💾 LocalStorage (JSON format)</strong>
                            <textarea
                              value={localStorageData}
                              onChange={(e) =>
                                setLocalStorageData(e.target.value)
                              }
                              placeholder='{"key": "value", "token": "xyz789"}'
                              rows={6}
                              className="manual-textarea"
                            />
                          </label>

                          <button
                            className="btn-secondary"
                            onClick={beautifyCookies}
                          >
                            ✨ Format JSON
                          </button>

                          <button
                            className="btn-primary"
                            onClick={() => setShowFormatImport(true)}
                          >
                            📥 Import Cookies
                          </button>

                          <button
                            className="btn-primary"
                            onClick={() => setShowFormatExport(true)}
                            disabled={!cookies.trim()}
                          >
                            📤 Export Cookies
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            ) : activeTab === "network" ? (
              <div className="tab-content">
                <NetworkTab addNotification={addNotification} />
              </div>
            ) : activeTab === "settings" ? (
              <div className="tab-content">
                <div className="settings-content">
                  {/* Keyword Config Button */}
                  <div className="settings-section">
                    <button
                      onClick={openKeywordConfigTab}
                      className="keyword-config-btn"
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#2196F3",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontSize: "14px",
                        fontWeight: "500",
                        display: "flex",
                        alignItems: "center",
                        gap: "6px",
                        marginBottom: "0",
                      }}
                    >
                      🔤 Keyword Config
                    </button>
                  </div>

                  {/* Capture Mode Selection */}
                  <div className="settings-section">
                    <h3>📸 Capture Mode</h3>

                    <div className="capture-mode-options">
                      <div className="capture-mode-option">
                        <label className="radio-label">
                          <input
                            type="radio"
                            name="captureMode"
                            value="viewport"
                            checked={captureMode === "viewport"}
                            onChange={(e) => setCaptureMode(e.target.value)}
                            disabled={loading}
                          />
                          <span className="radio-text">🖼️ Viewport only</span>
                          <InfoButton
                            ariaLabel="Information about viewport capture mode"
                            tooltip="Single screenshot of visible area (1366x768)"
                          />
                        </label>
                      </div>

                      <div className="capture-mode-option">
                        <label className="radio-label">
                          <input
                            type="radio"
                            name="captureMode"
                            value="fullpage"
                            checked={captureMode === "fullpage"}
                            onChange={(e) => setCaptureMode(e.target.value)}
                            disabled={loading}
                          />
                          <span className="radio-text">📄 Full page</span>
                          <InfoButton
                            ariaLabel="Information about full page capture mode"
                            tooltip="Single tall screenshot of entire page (may be very long)"
                          />
                        </label>
                      </div>

                      <div className="capture-mode-option">
                        <label className="radio-label">
                          <input
                            type="radio"
                            name="captureMode"
                            value="segmented"
                            checked={captureMode === "segmented"}
                            onChange={(e) => setCaptureMode(e.target.value)}
                            disabled={loading}
                          />
                          <span className="radio-text">📚 Segmented</span>
                          <InfoButton
                            ariaLabel="Information about segmented capture mode"
                            tooltip="Multiple viewport screenshots (scroll-by-scroll capture)"
                          />
                        </label>
                      </div>
                    </div>

                    {/* Advanced Settings for Segmented Mode */}
                    {captureMode === "segmented" && (
                      <div className="advanced-settings">
                        <button
                          type="button"
                          onClick={() => setShowAdvanced(!showAdvanced)}
                          className="advanced-toggle"
                          disabled={loading}
                        >
                          ⚙️ Advanced Settings {showAdvanced ? "▼" : "▶"}
                        </button>

                        {showAdvanced && (
                          <div className="advanced-panel">
                            <div className="advanced-row">
                              <label>Overlap: {segmentOverlap}%</label>
                              <input
                                type="range"
                                min="0"
                                max="50"
                                value={segmentOverlap}
                                onChange={(e) =>
                                  setSegmentOverlap(parseInt(e.target.value))
                                }
                                disabled={loading}
                              />
                              <span className="hint-text">
                                Prevents gaps between segments
                              </span>
                            </div>

                            <div className="advanced-row">
                              <label>
                                Scroll delay: {segmentScrollDelay}ms
                              </label>
                              <input
                                type="number"
                                min="100"
                                max="5000"
                                step="100"
                                value={segmentScrollDelay}
                                onChange={(e) =>
                                  setSegmentScrollDelay(
                                    parseInt(e.target.value)
                                  )
                                }
                                disabled={loading}
                              />
                              <span className="hint-text">
                                Wait time for lazy-loaded content
                              </span>
                            </div>

                            <div className="advanced-row">
                              <label>Max segments: {segmentMaxSegments}</label>
                              <input
                                type="number"
                                min="1"
                                max="200"
                                value={segmentMaxSegments}
                                onChange={(e) =>
                                  setSegmentMaxSegments(
                                    parseInt(e.target.value)
                                  )
                                }
                                disabled={loading}
                              />
                              <span className="hint-text">
                                Prevents infinite scrolling sites
                              </span>
                            </div>

                            <div className="advanced-row">
                              <label className="checkbox-label">
                                <input
                                  type="checkbox"
                                  checked={segmentSkipDuplicates}
                                  onChange={(e) =>
                                    setSegmentSkipDuplicates(e.target.checked)
                                  }
                                  disabled={loading}
                                />
                                <span>Skip duplicate segments</span>
                              </label>
                            </div>

                            <div className="advanced-row">
                              <label className="checkbox-label">
                                <input
                                  type="checkbox"
                                  checked={segmentSmartLazyLoad}
                                  onChange={(e) =>
                                    setSegmentSmartLazyLoad(e.target.checked)
                                  }
                                  disabled={loading}
                                />
                                <span>Smart lazy-load detection</span>
                              </label>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>

          {/* Browser Engine Selection - HIDDEN */}
          {false && (
          <div className="settings-section">
                    <h3>🦊 Browser Engine</h3>

                    <div className="browser-engine-options">
                      <div className="browser-engine-option">
                        <label className="radio-label">
                          <input
                            type="radio"
                            name="browserEngine"
                            value="playwright"
                            checked={browserEngine === "playwright"}
                            onChange={(e) => setBrowserEngine(e.target.value)}
                            disabled={loading}
                          />
                          <span className="radio-text">
                            🎭 Playwright (Standard)
                          </span>
                          <InfoButton
                            ariaLabel="Information about Playwright browser engine"
                            tooltip="Standard Chromium with Patchright patches (40-60% success on protected sites)"
                          />
                        </label>
                      </div>

                      <div className="browser-engine-option">
                        <label className="radio-label">
                          <input
                            type="radio"
                            name="browserEngine"
                            value="camoufox"
                            checked={browserEngine === "camoufox"}
                            onChange={(e) => setBrowserEngine(e.target.value)}
                            disabled={loading}
                          />
                          <span className="radio-text">
                            🦊 Camoufox (Advanced)
                          </span>
                          <InfoButton
                            ariaLabel="Information about Camoufox browser engine"
                            tooltip="Custom Firefox with TLS fingerprint patches (90-95% success on protected sites like Zomato)"
                          />
                        </label>
                      </div>
                    </div>

                    {browserEngine === "camoufox" && (
                      <div
                        style={{
                          background: "#e3f2fd",
                          border: "2px solid #2196f3",
                          padding: "12px",
                          borderRadius: "8px",
                          marginTop: "10px",
                        }}
                      >
                        <p
                          style={{
                            margin: 0,
                            fontSize: "14px",
                            color: "#1565c0",
                          }}
                        >
                          ℹ️ <strong>Camoufox Info:</strong> Custom Firefox
                          build that bypasses TLS/HTTP2 fingerprinting.
                          Requires: <code>pip install camoufox</code>
                        </p>
                      </div>
                    )}
                  </div>

                  
          )}


          {/* Stealth Mode - HIDDEN */}
          {false && (
                  <div className="settings-section">
                    <h3>🥷 Stealth Mode</h3>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={useStealth}
                        onChange={(e) => setUseStealth(e.target.checked)}
                        disabled={loading}
                      />
                      <span className="checkbox-text">
                        Use stealth mode (bypass bot detection)
                      </span>
                      <InfoButton
                        ariaLabel="Information about stealth mode"
                        tooltip={
                          useStealth
                            ? "✅ Enabled: Hides automation, adds realistic headers (JavaScript-level bypass)"
                            : "⚠️ Disabled: Some sites may block automated browsers"
                        }
                      />
                    </label>
                  </div>


          )}

          {/* Real Browser Mode (CDP Mode) */}
                  <div className="settings-section">
                    <h3>🌐 Real Browser Mode (CDP Mode)</h3>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={useRealBrowser}
                        onChange={(e) => setUseRealBrowser(e.target.checked)}
                        disabled={loading}
                      />
                      <span className="checkbox-text">
                        Use real browser (slower, visible window)
                      </span>
                      <InfoButton
                        ariaLabel="Information about real browser mode"
                        tooltip={
                          useRealBrowser
                            ? "✅ Enabled: Connects to existing Chrome via CDP (Active Tab Mode)"
                            : "⚠️ Disabled: Tool launches its own browser (Standard Mode)"
                        }
                      />
                    </label>
                    {useRealBrowser && (
                      <div
                        style={{
                          marginTop: "10px",
                          display: "flex",
                          flexDirection: "column",
                          gap: "8px",
                        }}
                      >
                        {/* Small CDP status line */}
                        <div
                          style={{
                            fontSize: "13px",
                            color:
                              cdpStatus === "up"
                                ? "#16a34a" // green
                                : cdpStatus === "down"
                                ? "#b91c1c" // red
                                : "#6b7280", // gray
                          }}
                        >
                          CDP on port {cdpPort}:{" "}
                          {cdpStatus === "up"
                            ? "✅ UP"
                            : cdpStatus === "down"
                            ? "❌ DOWN"
                            : "… unknown"}
                          <button
                            type="button"
                            onClick={checkCdpStatus}
                            disabled={loading}
                            style={{
                              marginLeft: "8px",
                              fontSize: "12px",
                              padding: "2px 6px",
                              borderRadius: "4px",
                              border: "1px solid #d1d5db",
                              background: "#f9fafb",
                              cursor: loading ? "not-allowed" : "pointer",
                            }}
                          >
                            Refresh
                          </button>
                        </div>

                        {/* Browser + Port controls */}
                        <div style={{ display: "flex", gap: 8, alignItems: "center", flexWrap: 'wrap' }}>
                          <select
                            value={cdpBrowser}
                            onChange={(e) => setCdpBrowser(e.target.value as any)}
                            style={{ padding: 6, borderRadius: 6 }}
                          >
                            <option value="chrome">Chrome</option>
                            <option value="safari">Safari</option>
                          </select>
                          <input
                            type="number"
                            value={cdpPort}
                            onChange={(e) => setCdpPort(parseInt(e.target.value || "9223", 10))}
                            min={1024}
                            max={65535}
                            style={{ width: 100, padding: 6, borderRadius: 6 }}
                          />
                          <button
                            type="button"
                            onClick={launchSelectedBrowserCdp}
                            disabled={loading}
                            style={{ padding: "6px 12px", borderRadius: 6 }}
                          >
                            Launch {cdpBrowser}
                          </button>
                          <button
                            type="button"
                            onClick={connectToSelectedCdp}
                            disabled={loading}
                            style={{ padding: "6px 12px", borderRadius: 6 }}
                          >
                            Connect to CDP
                          </button>
                          <button
                            type="button"
                            onClick={stopSelectedBrowser}
                            disabled={loading}
                            style={{ padding: "6px 12px", borderRadius: 6 }}
                          >
                            Stop/Cleanup
                          </button>
                          <label style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                            <input type="checkbox" checked={copyCookies} onChange={(e)=>setCopyCookies(e.target.checked)} />
                            Copy cookies/tokens (Chrome only)
                          </label>
                        </div>

                        {cdpBrowser === 'safari' && (
                          <div style={{ fontSize: 12, color: '#6b7280' }}>
                            Safari uses WebDriver (not CDP). For CDP features, use Chrome.
                          </div>
                        )}

                        {/* Cookie Injection (Chrome CDP) */}
                        <div style={{ marginTop: 8, display: 'flex', flexDirection: 'column', gap: 6 }}>
                          <div style={{ fontSize: 12, color: '#6b7280' }}>Paste cookies JSON (array of cookie objects) and click Import (requires connected Chrome CDP).</div>
                          <textarea
                            value={cookieText}
                            onChange={(e)=>setCookieText(e.target.value)}
                            placeholder='[{"name":"token","value":"...","domain":".example.com","path":"/"}]'
                            rows={3}
                            style={{ width: '100%', padding: 8, borderRadius: 6, fontFamily: 'monospace', fontSize: 12 }}
                          />
                          <div>
                            <button onClick={importCookies} disabled={loading} style={{ padding: '6px 12px', borderRadius: 6 }}>Import Cookies</button>
                          </div>
                        </div>

                        <button
                          onClick={launchDebugChrome}
                          disabled={loading}
                          style={{
                            padding: "8px 16px",
                            backgroundColor: "#dc2626",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: loading ? "not-allowed" : "pointer",
                            fontSize: "14px",
                            fontWeight: "500",
                            opacity: loading ? 0.5 : 1,
                          }}
                        >
                          🔴 Launch Debug Chrome
                          <InfoButton
                            ariaLabel="Warning about launching debug Chrome"
                            tooltip="⚠️ Warning: This will close your existing Chrome browser!"
                            style={{ marginLeft: "6px" }}
                          />
                        </button>

                        <button
                          type="button"
                          onClick={ensureBraveCdp}
                          disabled={loading}
                          style={{
                            padding: "8px 16px",
                            backgroundColor: "#2563eb",
                            color: "white",
                            border: "none",
                            borderRadius: "4px",
                            cursor: loading ? "not-allowed" : "pointer",
                            fontSize: "14px",
                            fontWeight: "500",
                            opacity: loading ? 0.5 : 1,
                          }}
                        >
                          🦁 Ensure Brave CDP is running
                          <InfoButton
                            ariaLabel="Information about Brave CDP"
                            tooltip="Checks if any browser is exposing CDP on port 9223; if not, launches Brave with CDP enabled (keeps existing windows open)."
                            style={{ marginLeft: "6px" }}
                          />
                        </button>
                      </div>
                    )}
                  </div>

          {/* Headless Mode - HIDDEN */}
          {false && (
            <div className="settings-section">
              <h3>👁️ Headless Mode</h3>
              <label className="checkbox-label">
                <input
                  type="checkbox"
                  checked={headless}
                  onChange={(e) => setHeadless(e.target.checked)}
                  disabled={loading}
                />
                <span className="checkbox-text">
                  Run browser in headless mode (invisible)
                </span>
              </label>
            </div>
          )}

          {/* Parallel Text Box Processing */}
                  <div className="settings-section">
                    <h3>⚡ Parallel Text Box Processing</h3>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={enableParallelTextBoxes}
                        onChange={(e) =>
                          setEnableParallelTextBoxes(e.target.checked)
                        }
                        disabled={loading}
                      />
                      <span className="checkbox-text">
                        Enable Rolling Parallelization
                      </span>
                      <InfoButton
                        ariaLabel="Information about rolling parallelization mode"
                        tooltip={
                          enableParallelTextBoxes
                            ? "✅ ENABLED: Rolling parallelization mode\n• URLs start immediately as slots free up\n• Zero idle time between batches\n• 20-25% faster processing\n• All URLs sent in one request"
                            : "⚠️ DISABLED: Fixed batch mode\n• URLs processed in batches sequentially\n• Some idle time between batches\n• Clear batch boundaries for tracking"
                        }
                      />
                    </label>

                    {/* Batch Size for Cross-Text-Box Processing */}
                    <div className="input-group" style={{ marginTop: "15px" }}>
                      <label htmlFor="max-parallel-urls">
                        Batch size (URLs processed together):
                        <InfoButton
                          ariaLabel="Information about batch size configuration"
                          tooltip={
                            (maxParallelUrls === 1
                              ? "⚠️ Sequential: URLs processed one at a time (slowest, most stable)"
                              : maxParallelUrls <= 3
                              ? `✅ Conservative: ${maxParallelUrls} URLs per batch (stable, good for 50+ URLs)`
                              : maxParallelUrls <= 5
                              ? `✅ Optimal: ${maxParallelUrls} URLs per batch (recommended for most cases)`
                              : maxParallelUrls <= 7
                              ? `⚡ Fast: ${maxParallelUrls} URLs per batch (faster, uses more memory)`
                              : `⚠️ Maximum: ${maxParallelUrls} URLs per batch (fastest, may be unstable with many URLs)`) +
                            " Cross-text-box batching: URLs from all text boxes are processed in batches of this size. Example: With 5 URLs per batch, Batch 1 processes 5 URLs (may be from different text boxes), Batch 2 processes the next 5 URLs, etc."
                          }
                        />
                      </label>
                      <input
                        id="max-parallel-urls"
                        type="number"
                        min="1"
                        max="10"
                        value={maxParallelUrls}
                        onChange={(e) => {
                          const value = parseInt(e.target.value) || 1;
                          setMaxParallelUrls(Math.min(10, Math.max(1, value)));
                        }}
                        disabled={loading}
                        style={{ width: "80px" }}
                      />
                    </div>
                  </div>

                  {/* Network Event Tracking */}
                  <div className="settings-section">
                    <h3>📡 Network Event Tracking</h3>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={trackNetwork}
                        onChange={(e) => setTrackNetwork(e.target.checked)}
                        disabled={loading}
                      />
                      <span className="checkbox-text">
                        Track network events during capture
                      </span>
                      <InfoButton
                        ariaLabel="Information about network tracking"
                        tooltip={
                          trackNetwork
                            ? "✅ Enabled: Captures HTTP requests and responses (useful for debugging)"
                            : "⚠️ Disabled: Network events not tracked (faster capture)"
                        }
                      />
                    </label>
                  </div>

                  {/* Auto Expand Dropdowns */}
                  <div className="settings-section">
                    <h3>🎯 Auto Expand Dropdowns</h3>
                    <label className="checkbox-label">
                      <input
                        type="checkbox"
                        checked={autoExpandDropdowns}
                        onChange={(e) =>
                          setAutoExpandDropdowns(e.target.checked)
                        }
                        disabled={loading}
                      />
                      <span className="checkbox-text">
                        Automatically expand collapsed sections before capture
                      </span>
                      <InfoButton
                        ariaLabel="Information about auto expand dropdowns"
                        tooltip={
                          (autoExpandDropdowns
                            ? "✅ Enabled: Detects and expands accordions, dropdowns, and collapsible sections (captures full content)"
                            : "⚠️ Disabled: Collapsed sections remain collapsed in screenshots") +
                          " Supports: Ant Design, Bootstrap, Font Awesome icons, ARIA states, and custom implementations."
                        }
                      />
                    </label>
                  </div>

                  {/* ✅ NEW: Non-Scrollable URLs */}
                  <div className="settings-section">
                    <h3>
                      🔒 Non-Scrollable URLs
                      <InfoButton
                        ariaLabel="Information about non-scrollable URLs configuration"
                        tooltip={
                          "Force these URLs to capture as single screenshot (no scrolling), even if the page appears scrollable. Useful for tab-based UIs where hash fragments show different content. " +
                          (nonScrollableUrls.length > 0
                            ? `✅ ${nonScrollableUrls.length} pattern(s) configured - matching URLs will be captured as single screenshot. `
                            : "⚠️ No patterns configured - all URLs will use normal scrolling behavior. ") +
                          "Pattern Matching: patterns are matched using substring search. Examples: full URL https://example.com/page#tab, hash fragment #media-upload, path segment /dealer-configuration/."
                        }
                      />
                    </h3>

                    {/* List of existing non-scrollable URLs */}
                    {nonScrollableUrls.length > 0 && (
                      <div
                        className="non-scrollable-urls-list"
                        style={{ marginBottom: "12px" }}
                      >
                        {nonScrollableUrls.map((pattern, index) => (
                          <div
                            key={index}
                            className="url-pattern-tag"
                            style={{
                              display: "inline-flex",
                              alignItems: "center",
                              gap: "6px",
                              padding: "4px 10px",
                              margin: "4px",
                              backgroundColor: "var(--tag-bg)",
                              border: "1px solid var(--tag-border)",
                              borderRadius: "4px",
                              fontSize: "0.9em",
                            }}
                          >
                            <span style={{ fontFamily: "monospace" }}>
                              {pattern}
                            </span>
                            <button
                              onClick={() => {
                                setNonScrollableUrls(
                                  nonScrollableUrls.filter(
                                    (_, i) => i !== index
                                  )
                                );
                              }}
                              style={{
                                background: "none",
                                border: "none",
                                color: "var(--text-secondary)",
                                cursor: "pointer",
                                padding: "0 4px",
                                fontSize: "1.1em",
                              }}
                              title="Remove pattern"
                            >
                              ✕
                            </button>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Input for adding new patterns */}
                    <label htmlFor="non-scrollable-url-input" style={{ display: "none" }}>
                      Add non-scrollable URL pattern
                    </label>
                    <div
                      style={{
                        display: "flex",
                        gap: "8px",
                        marginBottom: "8px",
                      }}
                    >
                      <input
                        type="text"
                        id="non-scrollable-url-input"
                        name="nonScrollableUrlPattern"
                        className="base-url-input"
                        placeholder="e.g., #media-upload or /dealer-configuration/"
                        style={{ flex: 1 }}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            const input = e.currentTarget;
                            const pattern = input.value.trim();
                            if (
                              pattern &&
                              !nonScrollableUrls.includes(pattern)
                            ) {
                              setNonScrollableUrls([
                                ...nonScrollableUrls,
                                pattern,
                              ]);
                              input.value = "";
                            }
                          }
                        }}
                      />
                      <button
                        onClick={() => {
                          const input = document.getElementById(
                            "non-scrollable-url-input"
                          ) as HTMLInputElement;
                          const pattern = input.value.trim();
                          if (pattern && !nonScrollableUrls.includes(pattern)) {
                            setNonScrollableUrls([
                              ...nonScrollableUrls,
                              pattern,
                            ]);
                            input.value = "";
                          }
                        }}
                        className="add-pattern-btn"
                        style={{
                          padding: "8px 16px",
                          backgroundColor: "var(--primary-color)",
                          color: "white",
                          border: "none",
                          borderRadius: "4px",
                          cursor: "pointer",
                        }}
                      >
                        Add Pattern
                      </button>
                    </div>
                  </div>

                  {/* ✅ NEW: File Storage Locations */}
                  <div className="settings-section">
                    <h3>
                      📁 File Storage Locations
                      <InfoButton
                        ariaLabel="Information about file storage locations"
                        tooltip="Configure where screenshots and Word documents are saved."
                      />
                    </h3>

                    {/* Screenshots Directory */}
                    <div style={{ marginBottom: "20px" }}>
                      <label
                        htmlFor="screenshots-dir-input"
                        style={{
                          display: "block",
                          marginBottom: "8px",
                          fontWeight: "500",
                        }}
                      >
                        📸 Screenshots Directory:
                        <InfoButton
                          ariaLabel="Information about screenshots directory path"
                          tooltip={
                            (screenshotsDir.startsWith("~") ||
                            screenshotsDir.startsWith("/")
                              ? `✅ Absolute path: ${screenshotsDir}`
                              : `✅ Relative path: backend/${screenshotsDir}`) +
                            " Examples: 'screenshots' (default, relative to backend), '~/Desktop/My Screenshots' (absolute path), '/Users/yourname/Documents/Screenshots' (absolute path)."
                          }
                        />
                      </label>
                      <input
                        id="screenshots-dir-input"
                        name="screenshotsDir"
                        type="text"
                        className="base-url-input"
                        placeholder="screenshots (relative to backend folder)"
                        value={screenshotsDir}
                        onChange={(e) => {
                          const newDir = e.target.value;
                          setScreenshotsDir(newDir);

                          // Debounce API call (only update backend after user stops typing)
                          if (window.screenshotsDirTimeout) {
                            clearTimeout(window.screenshotsDirTimeout);
                          }
                          (window as any).screenshotsDirTimeout = setTimeout(
                            () => {
                              updateBackendScreenshotsDir(newDir);
                            },
                            1000
                          ); // Wait 1 second after user stops typing
                        }}
                        disabled={loading}
                        style={{ width: "100%", marginBottom: "8px" }}
                      />
                      {/* Browser-only hidden directory input for screenshots folder.
	                          In plain browsers we can't get the real absolute path, but we
	                          can let the user pick a folder and use its name as a relative
	                          path on the backend. */}
                      <input
                        id="screenshots-dir-browser-picker"
                        type="file"
                        style={{ display: "none" }}
                        multiple
                        onChange={(e) => {
                          const files = e.target.files;
                          if (!files || files.length === 0) return;
                          const first: any = files[0];
                          const relPath: string =
                            first.webkitRelativePath || first.name || "";
                          const folderName = relPath.split("/")[0] || relPath;
                          if (!folderName) return;

                          setScreenshotsDir(folderName);
                          updateBackendScreenshotsDir(folderName);
                          addLog(
                            ` 14 (Browser) Screenshots folder set to relative directory: ${folderName}`
                          );
                          notify(
                            `Screenshots folder set to '${folderName}' (relative to backend). For exact OS paths, use the desktop app.`,
                            {
                              title: "File Storage",
                              type: "info",
                              duration: 7000,
                            }
                          );
                        }}
                        {...({ webkitdirectory: "true" } as any)}
                      />
                      <button
                        type="button"
                        className="load-folder-btn"
                        style={{ marginTop: "4px" }}
                        onClick={handleSelectScreenshotsDir}
                        disabled={loading}
                      >
                        📂 Choose folder
                      </button>
                    </div>

                    {/* Word Documents Base Directory */}
                    <div style={{ marginBottom: "20px" }}>
                      <label
                        htmlFor="word-docs-base-dir-input"
                        style={{
                          display: "block",
                          marginBottom: "8px",
                          fontWeight: "500",
                        }}
                      >
                        📄 Word Documents Base Directory:
                        <InfoButton
                          ariaLabel="Information about Word documents directory path"
                          tooltip={
                            (wordDocFolderName.trim()
                              ? `✅ Full path: ${wordDocsBaseDir}/${wordDocFolderName.trim()}/`
                              : `✅ Full path: ${wordDocsBaseDir}/`) +
                            " Examples: '~/Desktop/ARC DEALERS SCREENSHOT WORD DOCS' (default), '~/Documents/Reports', '/Users/yourname/Dropbox/Screenshots'."
                          }
                        />
                      </label>
                      <input
                        id="word-docs-base-dir-input"
                        name="wordDocsBaseDir"
                        type="text"
                        className="base-url-input"
                        placeholder="~/Desktop/ARC DEALERS SCREENSHOT WORD DOCS"
                        value={wordDocsBaseDir}
                        onChange={(e) => setWordDocsBaseDir(e.target.value)}
                        disabled={loading}
                        style={{ width: "100%", marginBottom: "8px" }}
                      />
                      {/* Browser-only hidden directory input for Word docs base folder. */}
                      <input
                        id="worddocs-dir-browser-picker"
                        type="file"
                        style={{ display: "none" }}
                        multiple
                        onChange={(e) => {
                          const files = e.target.files;
                          if (!files || files.length === 0) return;
                          const first: any = files[0];
                          const relPath: string =
                            first.webkitRelativePath || first.name || "";
                          const folderName = relPath.split("/")[0] || relPath;
                          if (!folderName) return;

                          setWordDocsBaseDir(folderName);
                          addLog(
                            ` 14 (Browser) Word docs base folder set to relative directory: ${folderName}`
                          );
                          notify(
                            `Word docs base folder set to '${folderName}' (relative). For exact OS paths, use the desktop app.`,
                            {
                              title: "File Storage",
                              type: "info",
                              duration: 7000,
                            }
                          );
                        }}
                        {...({ webkitdirectory: "true" } as any)}
                      />
                      <button
                        type="button"
                        className="load-folder-btn"
                        style={{ marginTop: "4px" }}
                        onClick={handleSelectWordDocsBaseDir}
                        disabled={loading}
                      >
                        📂 Choose folder
                      </button>
                    </div>

                    {/* Reset to Defaults Button */}
                    <button
                      onClick={() => {
                        setScreenshotsDir("screenshots");
                        setWordDocsBaseDir(
                          "~/Desktop/ARC DEALERS SCREENSHOT WORD DOCS"
                        );
                        updateBackendScreenshotsDir("screenshots");
                        addLog("⚙️ Reset file paths to defaults");
                      }}
                      disabled={loading}
                      style={{
                        padding: "8px 16px",
                        backgroundColor: "#ff9800",
                        color: "white",
                        border: "none",
                        borderRadius: "4px",
                        cursor: "pointer",
                        fontSize: "14px",
                        fontWeight: "500",
                      }}
                    >
                      🔄 Reset to Defaults
                    </button>
                  </div>

                  {/* Backend Management */}
                  <div className="settings-section">
                    <h3>
                      🔧 Backend Management
                      <InfoButton
                        ariaLabel="Information about backend management"
                        tooltip="Restart the backend server to apply code changes or fix issues."
                      />
                    </h3>

                    {/* ✅ MONOLITH: Services Status (Backend + Frontend) */}
                    <div
                      onClick={() => setShowServicesDetail(!showServicesDetail)}
                      style={{
                        cursor: 'pointer',
                        display: 'flex',
                        flexWrap: 'wrap',
                        alignItems: 'center',
                        gap: '6px',
                        padding: '10px 12px',
                        borderRadius: '8px',
                        background: 'rgba(0,0,0,0.03)',
                        marginBottom: '12px',
                        transition: 'all 0.3s',
                        border: '1px solid rgba(0,0,0,0.08)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.background = 'rgba(0,0,0,0.05)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.background = 'rgba(0,0,0,0.03)';
                      }}
                    >
                      {/* Chevron indicator */}
                      <span style={{
                        fontSize: '11px',
                        color: '#666',
                        transition: 'transform 0.3s',
                        transform: showServicesDetail ? 'rotate(90deg)' : 'rotate(0deg)',
                        display: 'inline-block'
                      }}>
                        ▶
                      </span>

                      {/* ✅ MONOLITH: Compact badges (2 services only) */}
                      {[
                        { icon: '🎯', name: 'Backend', status: servicesStatus.backend },
                        { icon: '⚛️', name: 'Frontend', status: servicesStatus.frontend }
                      ].map((service, idx) => (
                        <div key={idx} style={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '4px',
                          padding: '3px 8px',
                          borderRadius: '999px',
                          background: service.status === 'online' ? '#dcfce7' :
                                      service.status === 'offline' ? '#fee2e2' : '#f1f5f9',
                          fontSize: '11px',
                          fontWeight: 600,
                          color: service.status === 'online' ? '#166534' :
                                 service.status === 'offline' ? '#991b1b' : '#64748b'
                        }}>
                          <span>{service.icon}</span>
                          <span>{service.name}</span>
                          <span style={{
                            width: '5px',
                            height: '5px',
                            borderRadius: '50%',
                            background: service.status === 'online' ? '#22c55e' :
                                       service.status === 'offline' ? '#ef4444' : '#94a3b8'
                          }} />
                        </div>
                      ))}
                    </div>

                    {/* ✅ MONOLITH: Expanded details with integrated services info */}
                    {showServicesDetail && (
                      <div style={{
                        padding: '16px',
                        background: 'rgba(0,0,0,0.02)',
                        borderRadius: '8px',
                        marginBottom: '16px',
                        border: '1px solid rgba(0,0,0,0.08)',
                        animation: 'fadeIn 0.3s ease-in-out'
                      }}>
                        <div style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(2, 1fr)',
                          gap: '10px'
                        }}>
                          {[
                            { name: 'Backend', port: 8001, status: servicesStatus.backend, desc: 'All services integrated' },
                            { name: 'Frontend', port: 5173, status: servicesStatus.frontend, desc: 'React UI' }
                          ].map((service, idx) => (
                            <div key={idx} style={{
                              padding: '10px 12px',
                              background: 'white',
                              borderRadius: '6px',
                              border: '1px solid #e5e7eb',
                              display: 'flex',
                              alignItems: 'center',
                              gap: '8px'
                            }}>
                              {/* Status dot */}
                              <span style={{
                                width: '8px',
                                height: '8px',
                                borderRadius: '50%',
                                background: service.status === 'online' ? '#22c55e' :
                                           service.status === 'offline' ? '#ef4444' : '#94a3b8',
                                flexShrink: 0
                              }} />

                              {/* Service info */}
                              <div style={{ flex: 1, minWidth: 0 }}>
                                <div style={{
                                  fontSize: '13px',
                                  fontWeight: 600,
                                  color: '#1f2937'
                                }}>
                                  {service.name}
                                </div>
                                <div style={{
                                  fontSize: '11px',
                                  color: '#6b7280'
                                }}>
                                  Port {service.port} · {service.desc}
                                </div>
                              </div>

                              {/* Status badge */}
                              <span style={{
                                fontSize: '10px',
                                fontWeight: 600,
                                padding: '2px 6px',
                                borderRadius: '4px',
                                background: service.status === 'online' ? '#dcfce7' :
                                           service.status === 'offline' ? '#fee2e2' : '#f1f5f9',
                                color: service.status === 'online' ? '#166534' :
                                       service.status === 'offline' ? '#991b1b' : '#64748b',
                                textTransform: 'capitalize'
                              }}>
                                {service.status}
                              </span>
                            </div>
                          ))}
                        </div>

                        {/* ✅ MONOLITH: Info about integrated services */}
                        <div style={{
                          marginTop: '12px',
                          padding: '12px',
                          background: '#f0f9ff',
                          borderRadius: '6px',
                          border: '1px solid #bfdbfe',
                          fontSize: '12px',
                          color: '#1e40af'
                        }}>
                          <div style={{ fontWeight: 600, marginBottom: '6px' }}>
                            💡 Monolithic Architecture
                          </div>
                          <div style={{ color: '#3b82f6' }}>
                            All services (Screenshot, Quality, Document, API) are integrated into the backend.
                            No microservices needed - everything runs in one process! 🚀
                          </div>
                        </div>
                      </div>
                    )}
                    <button
                      onClick={restartBackend}
                      disabled={isRestartingBackend || loading}
                      className="restart-backend-btn"
                    >
                      {isRestartingBackend
                        ? "🔄 Restarting..."
                        : "🔄 Restart Backend"}
                      <InfoButton
                        ariaLabel="Information about restarting the backend"
                        tooltip="Use this after updating code (e.g., applying Zomato fix). The backend will restart automatically."
                        style={{ marginLeft: "8px" }}
                      />
                    </button>
                    {restartMessage && (
                      <p
                        className={`restart-message ${
                          restartMessage.includes("❌") ? "error" : "success"
                        }`}
                      >
                        {restartMessage}
                      </p>
                    )}
                  </div>
                </div>
              </div>
            ) : activeTab === "main" ? (
              /* Main View */
              <div className="tab-content">
                {/* Core Column - Main functional area */}
                <div className="main-core-column">
                  <div className="core-column-header">
                    <h2 className="core-column-title">
                      <span aria-hidden="true">⚡ </span>Core
                    </h2>
                    <p className="core-column-subtitle">
                      Essential screenshot capture and processing tools
                    </p>
                  </div>

                  <div className="core-column-content">
                    {/* Core actions and controls will go here */}
                    <div className="core-action-cards">
                      {/* Quick Capture Card */}
                      <div className="core-card">
                        <div className="core-card-header">
                          <span className="core-card-icon">📸</span>
                          <h3 className="core-card-title">Quick Capture</h3>
                        </div>
                        <p className="core-card-description">
                          Capture screenshots from URLs with one click
                        </p>
                        <button className="core-card-action-btn" onClick={() => {
                          // Scroll to URL input section
                          const urlSection = document.querySelector('.input-section');
                          urlSection?.scrollIntoView({ behavior: 'smooth' });
                        }}>
                          → Go to Capture
                        </button>
                      </div>

                      {/* Batch Processing Card */}
                      <div className="core-card">
                        <div className="core-card-header">
                          <span className="core-card-icon">📦</span>
                          <h3 className="core-card-title">Batch Processing</h3>
                        </div>
                        <p className="core-card-description">
                          Process multiple URL groups simultaneously
                        </p>
                        <button
                          className="core-card-action-btn"
                          onClick={() => {
                            if (!enableMultipleTextBoxes) {
                              setEnableMultipleTextBoxes(true);
                            }
                          }}
                        >
                          {enableMultipleTextBoxes ? '✓ Enabled' : '→ Enable Batch Mode'}
                        </button>
                      </div>

                      {/* Sessions Card */}
                      <div className="core-card">
                        <div className="core-card-header">
                          <span className="core-card-icon">🗂️</span>
                          <h3 className="core-card-title">Saved Sessions</h3>
                        </div>
                        <p className="core-card-description">
                          View and manage your capture sessions
                        </p>
                        <button className="core-card-action-btn" onClick={() => switchTab('sessions')}>
                          → View Sessions
                        </button>
                      </div>

                      {/* URL Library Card */}
                      <div className="core-card">
                        <div className="core-card-header">
                          <span className="core-card-icon">📁</span>
                          <h3 className="core-card-title">URL Library</h3>
                        </div>
                        <p className="core-card-description">
                          Organize and manage your URL collections
                        </p>
                        <button className="core-card-action-btn" onClick={() => switchTab('urls')}>
                          → Open Library
                        </button>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="input-section">
                  {/* ========================================
                       PROJECT CONFIGURATION & MODE (Combined)
                       ======================================== */}
                  <div className="project-config-section">
                    <div className="section-header-with-mode">
                      <h3 className="section-heading">
                        <span aria-hidden="true">📁 </span>Output Organization
                      </h3>

                      <div className="header-controls">
                        {/* Compact batch mode toggle with count */}
                        <div className="batch-mode-control">
                          <label className="compact-mode-toggle">
                            <input
                              type="checkbox"
                              checked={enableMultipleTextBoxes}
                              onChange={(e) =>
                                setEnableMultipleTextBoxes(e.target.checked)
                              }
                              disabled={loading}
                            />
                            <span className="toggle-text">
                              <span aria-hidden="true">📦 </span>Batch Mode
                            </span>
                            <InfoButton
                              ariaLabel="Information about batch processing mode"
                              tooltip={
                                enableMultipleTextBoxes
                                  ? "✅ Enabled: Multiple text box groups for parallel processing"
                                  : "⚠️ Disabled: Single text box mode (classic behavior)"
                              }
                            />
                          </label>
                          {enableMultipleTextBoxes && (
                            <div className="batch-count-badge">
                              {textBoxes.length} {textBoxes.length === 1 ? 'box' : 'boxes'}
                            </div>
                          )}
                        </div>

                        {/* Clean URLs button */}
                        <button
                          onClick={enableMultipleTextBoxes ? beautifyAllTextBoxes : beautifyUrls}
                          disabled={
                            loading ||
                            (enableMultipleTextBoxes
                              ? textBoxes.every((box) => !box.urls.trim())
                              : !urls.trim())
                          }
                          className="compact-clean-btn"
                          title={
                            enableMultipleTextBoxes
                              ? "Clean and format URLs in all text boxes (one per line, only http:// or https://)"
                              : "Clean and format URLs (one per line, only http:// or https://)"
                          }
                        >
                          <span aria-hidden="true">🧹 </span>
                          Clean {enableMultipleTextBoxes ? 'All ' : ''}URLs
                        </button>
                      </div>
                    </div>

                    <div className="folder-config-card">
                      <div className="folder-input-row">
                        <div className="folder-input-section">
                          <label htmlFor="word-doc-folder-input" className="config-label">
                            Folder name for Word documents:
                            <InfoButton
                              ariaLabel="Information about Word documents folder organization"
                              tooltip="Organize Word documents into a subfolder. Leave empty to save directly to the base directory. This setting applies to both single and batch modes."
                            />
                          </label>
                          <input
                            id="word-doc-folder-input"
                            type="text"
                            className="word-doc-folder-input"
                            placeholder="e.g., November 2025, Client Name - Project ID"
                            value={wordDocFolderName}
                            onChange={(e) =>
                              setWordDocFolderName(e.target.value)
                            }
                            disabled={loading}
                          />
                        </div>

                        {/* Live Path Preview - Inline on the right */}
                        <div className="path-preview-inline">
                          <span className="preview-label">
                            <span aria-hidden="true">📂 </span>Saves to:
                          </span>
                          <code className="preview-path">
                            {wordDocsBaseDir}
                            {wordDocFolderName.trim() && `/${wordDocFolderName.trim()}`}/
                          </code>
                        </div>
                      </div>
                    </div>
                  </div>

                  {enableMultipleTextBoxes ? (
                    /* ✅ NEW: Multiple text boxes mode */
                    <>
                      {/* ✅ NEW: Select All / Deselect All + Expand/Collapse All + Selection Stats */}
                      <div className="textbox-selection-controls">
                        <button
                          onClick={toggleSelectAll}
                          disabled={loading}
                          className="select-all-btn"
                          title={
                            selectedTextBoxStats.allSelected
                              ? "Deselect all text boxes"
                              : "Select all text boxes"
                          }
                        >
                          {selectedTextBoxStats.allSelected
                            ? "☑️ Deselect All"
                            : "☐ Select All"}
                        </button>

                        <button
                          type="button"
                          className="expand-all-btn"
                          disabled={loading || textBoxes.length === 0}
                          onClick={() => {
                            const anyExpanded = textBoxes.some(
                              (tb) => !collapsedTextBoxes[tb.id]
                            );
                            // If any expanded -> collapse all; else expand all
                            const nextState: Record<string, boolean> = {};
                            textBoxes.forEach((tb) => {
                              nextState[tb.id] = anyExpanded; // true = collapsed
                            });
                            setCollapsedTextBoxes(nextState);
                          }}
                          title="Expand or collapse all text boxes"
                        >
                          {textBoxes.some((tb) => collapsedTextBoxes[tb.id])
                            ? "▼ Expand All"
                            : "▶ Collapse All"}
                        </button>

                        <span className="selection-stats">
                          {selectedTextBoxStats.selectedCount} of{" "}
                          {selectedTextBoxStats.totalCount} text boxes selected
                          {selectedTextBoxStats.totalUrls > 0 && (
                            <span className="url-count">
                              {" "}
                              • {selectedTextBoxStats.totalUrls} URL(s) to
                              capture
                            </span>
                          )}
                        </span>
                      </div>

                      <div className="multiple-textboxes-container">
                        {textBoxes.map((textBox, index) => (
                          <TextBoxGroup
                            key={textBox.id}
                            textBox={textBox}
                            index={index}
                            isCollapsed={collapsedTextBoxes[textBox.id] || false}
                            loading={loading}
                            urlFolders={urlFolders}
                            timeoutError={timeoutErrors.get(textBox.id) || null}
                            totalTextBoxes={textBoxes.length}
                            onToggleCollapse={(id) => {
                              setCollapsedTextBoxes((prev) => ({
                                ...prev,
                                [id]: !prev[id],
                              }));
                            }}
                            onToggleSelection={toggleTextBoxSelection}
                            onUpdateField={updateTextBox}
                            onLoadFolder={loadFolderUrlsIntoTextBox}
                            onRemove={removeTextBox}
                            onTimeoutChange={handleBatchTimeoutChange}
                            onTimeoutBlur={handleBatchTimeoutBlur}
                            onTimeoutUnitChange={handleBatchTimeoutUnitChange}
                            getTimeoutDisplayValue={getTimeoutDisplayValue}
                            detectFolderMention={detectFolderMention}
                            addLog={addLog}
                          />
                        ))}

                        {/* Old inline TextBoxGroup JSX (608 lines) replaced above with reusable component */}

                        <button
                          className="add-textbox-btn"
                          onClick={addTextBox}
                          disabled={loading}
                        >
                          Add another text box
                        </button>
                      </div>
                    </>
                  ) : (
                    /* ✅ EXISTING: Single text box mode */
                    <>
                      <div className="input-header">
                        <h2>Enter URLs (one per line)</h2>

                        <div className="input-header-actions">
                          {/* Folder dropdown for single text box mode */}
                          {urlFolders.length > 0 && (
                            <select
                              className="beautify-button"
                              disabled={loading}
                              defaultValue=""
                              onChange={(e) => {
                                const value = e.target.value;
                                if (!value) return;
                                loadFolderUrls(value);
                              }}
                            >
                              <option value="">Select folder…</option>
                              {urlFolders.map((folder) => (
                                <option key={folder.name} value={folder.name}>
                                  {folder.name}
                                </option>
                              ))}
                            </select>
                          )}

                          {/* Beautify button */}
                          <button
                            onClick={beautifyUrls}
                            disabled={loading || !urls.trim()}
                            className="beautify-button"
                            title="Clean up and format URLs (one per line, only http:// or https://)"
                          >
                            Beautify
                          </button>
                        </div>
                      </div>

                      <div className="textarea-wrapper">
                        {/* Line numbers overlay */}
                        <div className="line-numbers" ref={lineNumbersRef}>
                          {/* ⚡ OPTIMIZATION: Use memoized urlLines instead of re-splitting */}
                          {urlLines.map((line, index) => (
                            <div key={index} className="line-number">
                              {line.trim() !== "" ? index + 1 : ""}
                            </div>
                          ))}
                        </div>
                        {/* Textarea */}
                        <textarea
                          ref={textareaRef}
                          value={urls}
                          onChange={(e) => setUrls(e.target.value)}
                          onScroll={handleTextareaScroll}
                          placeholder="https://example.com&#10;https://google.com&#10;https://github.com"
                          rows={10}
                          disabled={loading}
                          className="numbered-textarea"
                        />
                      </div>

                      {/* @mention folder detection */}
                      {(() => {
                        const mentionedFolder = detectFolderMention(urls);
                        if (mentionedFolder && urlFolders.length > 0) {
                          const folder = urlFolders.find(
                            (f) =>
                              f.name.toLowerCase() ===
                              mentionedFolder.toLowerCase()
                          );
                          if (folder) {
                            return (
                              <div className="folder-mention-hint">
                                <p>
                                  Detected folder:{" "}
                                  <strong>@{mentionedFolder}</strong>
                                </p>
                                <button
                                  className="load-folder-btn"
                                  onClick={() =>
                                    loadFolderUrls(mentionedFolder)
                                  }
                                  disabled={loading}
                                >
                                  Load {folder.urls.length} URL(s) from "
                                  {folder.name}"
                                </button>
                              </div>
                            );
                          } else {
                            return (
                              <div className="folder-mention-hint error">
                                <p>
                                  Folder <strong>@{mentionedFolder}</strong> not
                                  found.
                                </p>
                              </div>
                            );
                          }
                        }
                        // Show available folders hint if there are folders
                        if (urlFolders.length > 0 && !urls.trim()) {
                          return (
                            <div className="folder-hint">
                              <p>
                                Tip: Type <strong>@foldername</strong> to load
                                saved URLs
                              </p>
                              <p className="available-folders">
                                Available folders:{" "}
                                {urlFolders.map((f) => `@${f.name}`).join(", ")}
                              </p>
                            </div>
                          );
                        }
                        return null;
                      })()}
                    </>
                  )}

                  <div className="button-group">
                    <button onClick={handleCapture} disabled={loading}>
                      {loading ? "Capturing..." : "Capture Screenshots"}
                    </button>

                    {loading && (
                      <button onClick={handleStop} className="stop-btn">
                        Stop capture
                      </button>
                    )}

            <button onClick={handleCleanupTabs} className="cleanup-btn" title="Close all open tabs">
              🧹 Close All Tabs
            </button>
                  </div>
                </div>
              </div>
            ) : null}
            </Suspense>

            {loading && (
              <div className="progress">
                <p>
                  Progress: {progress.current} / {progress.total}
                </p>
              </div>
            )}

            {results.length > 0 && (
              <div className="results-section">
                <h2>Results ({results.length})</h2>

                <button
                  onClick={handleGenerateDocument}
                  className="generate-btn"
                >
                  Generate Word Document
                </button>

                <div className="results-grid">
                  {results.map((result, index) => (
                    <div key={index} className={`result-card ${result.status}`}>
                      <h3>Screenshot {index + 1}</h3>

                      {/* Truncated URL with hover/click tooltip */}
                      <div className="url-container">
                        <p
                          className="url truncated"
                          onMouseEnter={() => handleUrlMouseEnter(index)}
                          onMouseLeave={handleUrlMouseLeave}
                          onClick={() => handleUrlClick(index)}
                          title="Hover 3s or click to see full URL"
                        >
                          {result.url}
                        </p>
                        {(hoveredUrl === index || clickedUrl === index) && (
                          <div className="url-tooltip">{result.url}</div>
                        )}
                      </div>

                      {/* Status badge with inline quality score */}
                      <div className="status-quality-row">
                        <div className="status-badge">
                          {result.status === "success"
                            ? "✅"
                            : result.status === "cancelled"
                            ? "⏹️"
                            : "❌"}{" "}
                          {result.status}
                        </div>

                        {result.quality_score !== undefined &&
                          result.quality_score !== null && (
                            <span className="quality-score inline">
                              Quality: {result.quality_score.toFixed(1)}%
                            </span>
                          )}
                      </div>

                      {result.quality_issues &&
                        result.quality_issues.length > 0 && (
                          <div className="quality-issues">
                            <strong>Issues:</strong>
                            <ul>
                              {result.quality_issues.map((issue, i) => (
                                <li key={i}>{issue}</li>
                              ))}
                            </ul>
                          </div>
                        )}

                      {result.error && (
                        <p className="error">Error: {result.error}</p>
                      )}

                      {/* Show segment count for segmented captures */}
                      {result.segment_count !== undefined &&
                        result.segment_count !== null &&
                        result.segment_count > 1 && (
                          <p className="segment-count">
                            📚 {result.segment_count} segments captured
                          </p>
                        )}

                      {result.screenshot_path && (
                        <p className="path">Saved: {result.screenshot_path}</p>
                      )}

                      {result.status === "success" &&
                        (result.screenshot_paths || result.screenshot_path) && (
                          <>
                            {/* Show all segments for segmented captures */}
                            {result.screenshot_paths &&
                            result.screenshot_paths.length > 0 ? (
                              <>
                                <div className="segments-container">
                                  <div
                                    className="segments-header"
                                    onClick={() =>
                                      toggleSegmentExpansion(index)
                                    }
                                    role="button"
                                    tabIndex={0}
                                    onKeyPress={(e) => {
                                      if (e.key === "Enter" || e.key === " ") {
                                        toggleSegmentExpansion(index);
                                      }
                                    }}
                                  >
                                    <p className="segments-label">
                                      <span className="expand-icon">
                                        {expandedSegments.has(index)
                                          ? "▼"
                                          : "▶"}
                                      </span>
                                      📸 {result.screenshot_paths.length}{" "}
                                      segments captured -{" "}
                                      {expandedSegments.has(index)
                                        ? "Click to collapse"
                                        : "Click to view all"}
                                    </p>
                                  </div>

                                  {expandedSegments.has(index) && (
                                    <div className="segments-list">
                                      {result.screenshot_paths.map(
                                        (segmentPath, segIdx) => (
                                          <div
                                            key={segIdx}
                                            className="screenshot-preview segment-preview"
                                          >
                                            <p className="segment-number">
                                              Segment {segIdx + 1}
                                            </p>
                                            <img
                                              src={`http://127.0.0.1:8001/api/screenshots/file/${encodeURIComponent(
                                                segmentPath
                                              )}`}
                                              alt={`Segment ${
                                                segIdx + 1
                                              } preview`}
                                              className="preview-image"
                                            />
                                          </div>
                                        )
                                      )}
                                    </div>
                                  )}
                                </div>
                                <div className="action-buttons">
                                  <button
                                    onClick={() =>
                                      handleOpenFile(
                                        result.screenshot_paths![0]
                                      )
                                    }
                                    className="open-file-btn"
                                  >
                                    📄 Open First Segment
                                  </button>
                                  <button
                                    onClick={() =>
                                      handleOpenFolder(
                                        result.screenshot_paths![0]
                                      )
                                    }
                                    className="open-folder-btn"
                                  >
                                    📁 Open Folder
                                  </button>
                                </div>
                              </>
                            ) : (
                              /* Show single screenshot for non-segmented captures */
                              <>
                                <div className="screenshot-preview">
                                  <img
                                    src={`http://127.0.0.1:8001/api/screenshots/file/${encodeURIComponent(
                                      result.screenshot_path!
                                    )}`}
                                    alt="Screenshot preview"
                                    className="preview-image"
                                  />
                                </div>
                                <div className="action-buttons">
                                  <button
                                    onClick={() =>
                                      handleOpenFile(result.screenshot_path!)
                                    }
                                    className="open-file-btn"
                                  >
                                    📄 Open File
                                  </button>
                                  <button
                                    onClick={() =>
                                      handleOpenFolder(result.screenshot_path!)
                                    }
                                    className="open-folder-btn"
                                  >
                                    📁 Open Folder
                                  </button>
                                </div>
                              </>
                            )}
                          </>
                        )}

                      {result.status === "failed" && (
                        <button
                          onClick={() => handleRetry(result.url)}
                          className="retry-btn"
                        >
                          🔄 Retry
                        </button>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Close main content & layout before global modals */}
          </div>
        </div>

        {/* Login URL Modal */}
        {showLoginModal && (
          <div
            className="modal-overlay"
            onClick={() => setShowLoginModal(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <h2>🔓 Login & Save Auth State</h2>
              <p className="modal-description">
                Enter the URL where you want to log in. A browser window will
                open where you can complete your login (Okta/MFA/etc.).
              </p>
              <label htmlFor="login-url-input">Login URL:</label>
              <input
                id="login-url-input"
                type="text"
                className="login-url-input"
                value={loginUrl}
                onChange={(e) => setLoginUrl(e.target.value)}
                placeholder="https://preprodapp.tekioncloud.com/home"
                autoFocus
                onKeyDown={(e) => {
                  if (e.key === "Enter") startLogin();
                  if (e.key === "Escape") setShowLoginModal(false);
                }}
              />
              <div className="modal-actions">
                <button
                  className="modal-btn modal-btn-primary"
                  onClick={startLogin}
                  disabled={!loginUrl.trim()}
                >
                  🔓 Start Login
                </button>
                <button
                  className="modal-btn modal-btn-secondary"
                  onClick={() => setShowLoginModal(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ✅ Word Transformation Editor Modal */}
        {showWordEditor && (
          <div
            className="modal-overlay"
            style={{ zIndex: 99998 }}
            onClick={closeWordEditor}
          >
            <div
              className="modal-content"
              onClick={(e) => e.stopPropagation()}
              style={{ maxWidth: "500px" }}
            >
              <h2>
                ✏️ {editingWordIndex !== null ? "Edit" : "Add"} Word
                Transformation
              </h2>

              <div style={{ marginTop: "20px" }}>
                <label
                  htmlFor="word-to-find-input"
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    fontWeight: "500",
                  }}
                >
                  Word to Find:
                </label>
                <input
                  id="word-to-find-input"
                  name="wordToFind"
                  type="text"
                  className="base-url-input"
                  placeholder="e.g., Accounting, dse-v2, .png"
                  value={editorWord}
                  onChange={(e) => setEditorWord(e.target.value)}
                  autoFocus
                  style={{ marginBottom: "20px" }}
                />

                <label
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    fontWeight: "500",
                  }}
                >
                  Replacement Type:
                </label>
                <div style={{ marginBottom: "20px" }}>
                  <label className="radio-label">
                    <input
                      type="radio"
                      name="editorType"
                      value="remove"
                      checked={editorType === "remove"}
                      onChange={(_e) => setEditorType("remove")}
                    />
                    <span className="radio-text">
                      🗑️ Remove (delete completely)
                    </span>
                  </label>

                  <label className="radio-label">
                    <input
                      type="radio"
                      name="editorType"
                      value="space"
                      checked={editorType === "space"}
                      onChange={(_e) => setEditorType("space")}
                    />
                    <span className="radio-text">␣ Replace with Space</span>
                  </label>

                  <label className="radio-label">
                    <input
                      type="radio"
                      name="editorType"
                      value="custom"
                      checked={editorType === "custom"}
                      onChange={(_e) => setEditorType("custom")}
                    />
                    <span className="radio-text">
                      ✏️ Replace with Custom Text
                    </span>
                  </label>
                </div>

                {editorType === "custom" && (
                  <>
                    <label
                      htmlFor="replacement-text-input"
                      style={{
                        display: "block",
                        marginBottom: "8px",
                        fontWeight: "500",
                      }}
                    >
                      Custom Replacement Text:
                    </label>
                    <input
                      id="replacement-text-input"
                      name="replacementText"
                      type="text"
                      className="base-url-input"
                      placeholder="e.g., Sales Chains"
                      value={editorReplacement}
                      onChange={(e) => setEditorReplacement(e.target.value)}
                      style={{ marginBottom: "20px" }}
                    />
                  </>
                )}

                <div
                  style={{
                    background: "#f0f0f0",
                    padding: "12px",
                    borderRadius: "6px",
                    marginBottom: "20px",
                    fontSize: "13px",
                  }}
                >
                  <strong>Preview:</strong> {editorWord || "[word]"} →{" "}
                  {editorType === "remove"
                    ? "[removed]"
                    : editorType === "space"
                    ? "[space]"
                    : editorReplacement || "[custom text]"}
                </div>
              </div>

              <div className="modal-actions">
                <button
                  className="modal-btn modal-btn-primary"
                  onClick={saveWordTransformation}
                  disabled={
                    !editorWord.trim() ||
                    (editorType === "custom" && !editorReplacement.trim())
                  }
                >
                  💾 Save
                </button>
                <button
                  className="modal-btn modal-btn-secondary"
                  onClick={closeWordEditor}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ✅ URL Click Configuration Editor Modal */}
        {showUrlConfigEditor && (
          <div
            className="modal-overlay"
            style={{ zIndex: 99998 }}
            onClick={closeUrlConfigEditor}
          >
            <div
              className="modal-content"
              onClick={(e) => e.stopPropagation()}
              style={{
                maxWidth: "700px",
                maxHeight: "90vh",
                overflowY: "auto",
              }}
            >
              <h2>
                {editingUrlConfigId ? "✏️ Edit" : "➕ Add"} URL Click
                Configuration
              </h2>

              <div style={{ marginTop: "20px" }}>
                {/* URL Pattern */}
                <label
                  htmlFor="url-pattern-input"
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    fontWeight: "500",
                  }}
                >
                  URL:
                </label>
                <input
                  id="url-pattern-input"
                  name="urlPattern"
                  type="text"
                  className="base-url-input"
                  placeholder="https://example.com/page"
                  value={urlConfigForm.url_pattern}
                  onChange={(e) =>
                    setUrlConfigForm({
                      ...urlConfigForm,
                      url_pattern: e.target.value,
                    })
                  }
                  autoFocus
                  style={{ marginBottom: "16px" }}
                />

                {/* Text to Click */}
                <label
                  htmlFor="text-to-click-input"
                  style={{
                    display: "block",
                    marginBottom: "8px",
                    fontWeight: "500",
                  }}
                >
                  Text:
                </label>
                <input
                  id="text-to-click-input"
                  name="textToClick"
                  type="text"
                  className="base-url-input"
                  placeholder="Text to click (e.g., Customer Return w/ Restocking)"
                  value={urlConfigForm.actions[0]?.text || ""}
                  onChange={(e) => {
                    const newActions = [...urlConfigForm.actions];
                    if (newActions.length === 0) {
                      newActions.push({
                        type: "click",
                        text: e.target.value,
                        wait_after_ms: 2000,
                      });
                    } else {
                      newActions[0].text = e.target.value;
                    }
                    setUrlConfigForm({
                      ...urlConfigForm,
                      actions: newActions,
                    });
                  }}
                  style={{ marginBottom: "16px" }}
                />

	                {/* Per-URL dropdown expansion toggle */}
	                <label className="checkbox-label" style={{ marginBottom: "16px" }}>
	                  <input
	                    type="checkbox"
	                    checked={!!urlConfigForm.auto_expand_dropdowns}
	                    onChange={(e) =>
	                      setUrlConfigForm({
	                        ...urlConfigForm,
	                        auto_expand_dropdowns: e.target.checked,
	                      })
	                    }
	                  />
	                  <span className="checkbox-text">
	                    Auto-expand dropdowns & icon-only controls after clicking this text
	                  </span>
	                </label>
              </div>

              <div className="modal-actions">
                <button
                  className="modal-btn modal-btn-primary"
                  onClick={saveUrlConfig}
                  disabled={
                    !urlConfigForm.url_pattern ||
                    !urlConfigForm.actions[0]?.text
                  }
                >
                  💾 Save Configuration
                </button>
                <button
                  className="modal-btn modal-btn-secondary"
                  onClick={closeUrlConfigEditor}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ✅ Custom Dialog (replaces browser alert/confirm) */}
        {customDialog.show && (
          <div
            className="modal-overlay"
            style={{ zIndex: 99999 }}
            onClick={(e) => {
              e.stopPropagation();
              // Prevent closing by clicking overlay for dialogs
            }}
          >
            <div
              className="modal-content custom-dialog-modal"
              onClick={(e) => e.stopPropagation()}
              style={{
                maxWidth: "500px",
                padding: "30px",
                textAlign: "center",
              }}
            >
              <h2 style={{ marginBottom: "20px", fontSize: "24px" }}>
                {customDialog.title}
              </h2>
              <p
                style={{
                  marginBottom: "30px",
                  fontSize: "16px",
                  lineHeight: "1.6",
                  whiteSpace: "pre-wrap",
                }}
              >
                {customDialog.message}
              </p>
              <div
                className="modal-actions"
                style={{ gap: "15px", justifyContent: "center" }}
              >
                {customDialog.type === "confirm" && (
                  <button
                    className="modal-btn modal-btn-secondary"
                    onClick={() => customDialog.onCancel?.()}
                    style={{
                      minWidth: "100px",
                      padding: "12px 24px",
                      fontSize: "16px",
                    }}
                  >
                    Cancel
                  </button>
                )}
                <button
                  className="modal-btn modal-btn-primary"
                  onClick={() => customDialog.onConfirm?.()}
                  autoFocus
                  style={{
                    minWidth: "100px",
                    padding: "12px 24px",
                    fontSize: "16px",
                  }}
                >
                  OK
                </button>
              </div>
            </div>
          </div>
        )}

            {/* 🍞 Toast Notification Container */}
            <ToastContainer
              notifications={notifications}
              onDismiss={removeNotification}
              position="top-right"
              maxVisible={5}
            />

            {/* 🔔 Confirm Dialog */}
            <ConfirmDialog
              isOpen={confirmDialog.isOpen}
              title={confirmDialog.title}
              message={confirmDialog.message}
              type={confirmDialog.type}
              confirmText="Delete"
              cancelText="Cancel"
              onConfirm={confirmDialog.onConfirm}
              onCancel={() => {
                log.debug("❌ User cancelled delete");
                setConfirmDialog((prev) => ({ ...prev, isOpen: false }));
              }}
            />
          </>
        )}
      </div>
    );
  } catch (error: any) {
    log.error("Render error:", error);
    return (
      <div className="container">
        <h1>📸 Screenshot Tool - ERROR</h1>
        <div
          style={{
            background: "#ffebee",
            border: "2px solid #f44336",
            padding: "20px",
            borderRadius: "8px",
            margin: "20px",
            color: "#c62828",
          }}
        >
          <h2>⚠️ Application Error</h2>
          <p>
            <strong>Error:</strong> {error.message}
          </p>
          <p>
            <strong>Stack:</strong>
          </p>
          <pre
            style={{ background: "#fff", padding: "10px", overflow: "auto" }}
          >
            {error.stack}
          </pre>
          <button onClick={() => window.location.reload()}>Reload Page</button>
        </div>
      </div>
    );
  }
}

// ✅ Phase 2: No longer need Context providers - using Zustand stores

function AppWithErrorBoundary() {
  return (
    <ErrorBoundary
      FallbackComponent={ErrorFallback}
      onError={(error, errorInfo) => {
        log.error('App-level error:', error, errorInfo);
        console.error('App crashed:', error, errorInfo);
      }}
      onReset={() => {
        // Reload the page on reset
        window.location.reload();
      }}
    >
      <App />
    </ErrorBoundary>
  );
}

export default AppWithErrorBoundary;

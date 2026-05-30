import { useState, useEffect, useCallback } from "react";
import { useLocalStorage } from "./useLocalStorage";
import { useDebouncedLocalStorage } from "./useDebouncedLocalStorage";
import config from "../config";
import { useNotifications } from "./useNotifications";
import { DEFAULT_TEXT_BOXES, type TextBox } from "../constants/defaultTextBoxes"; // ✅ FIX 2.3: Use shared constant

// Lightweight engine hook for the new shell UI (new-ui.html).
// This is a focused copy of the core multi–textbox capture logic from App.tsx
// so the shell can trigger REAL captures, sessions and Word docs while keeping
// all existing behaviour and localStorage keys.

export interface Screenshot {
  filename: string;
  path: string;
  url: string;
  timestamp: string;
  quality_score?: number;
  segments?: number;
}

export interface Session {
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

interface WordTransformation {
  word: string;
  replacement: string;
  type: "remove" | "space" | "custom";
}

export interface ProgressState {
  current: number;
  total: number;
}

export function useScreenshotEngineForShell() {
  const [loading, setLoading] = useState(false);
  const [progress, setProgress] = useState<ProgressState>({
    current: 0,
    total: 0,
  });
  const [logs, setLogs] = useState<string[]>([]);
  const [hasErrors, setHasErrors] = useState(false);

  // Capture + engine config (mirrors App.tsx keys/defaults)
  const [captureMode, setCaptureModeState] = useLocalStorage<string>(
    "screenshot-capturemode",
    "viewport"
  );
  const [useStealth, setUseStealthState] = useLocalStorage<boolean>(
    "screenshot-stealth",
    false
  );
  const [useRealBrowser, setUseRealBrowserState] = useLocalStorage<boolean>(
    "screenshot-realbrowser",
    false
  );
  const [headless, setHeadlessState] = useLocalStorage<boolean>(
    "screenshot-headless",
    false // ✅ FIX: Default to headful (visible browser) - matches Real Browser Mode behavior
  );
  const [trackNetwork, setTrackNetworkState] = useLocalStorage<boolean>(
    "screenshot-track-network",
    false
  );
  const [autoExpandDropdowns, setAutoExpandDropdownsState] =
    useLocalStorage<boolean>("screenshot-auto-expand-dropdowns", false);
  const [nonScrollableUrls, setNonScrollableUrls] = useLocalStorage<string[]>(
    "screenshot-non-scrollable-urls",
    []
  );
  const [browserEngine, setBrowserEngineState] = useLocalStorage<string>(
    "screenshot-browser-engine",
    "playwright"
  );
  const [baseUrl, setBaseUrl] = useLocalStorage<string>(
    "screenshot-base-url",
    ""
  );

  const [maxParallelUrls, setMaxParallelUrls] = useLocalStorage<number>(
    "screenshot-max-parallel-urls",
    5
  );

  const [wordDocFolderName, setWordDocFolderName] =
    useDebouncedLocalStorage<string>(
      "screenshot-word-doc-folder-name",
      "",
      500
    );

  const [wordDocsBaseDir, setWordDocsBaseDir] = useLocalStorage<string>(
    "screenshot-word-docs-base-dir",
    "~/Desktop/ARC DEALERS SCREENSHOT WORD DOCS"
  );

  const [wordsToRemove, setWordsToRemove] = useDebouncedLocalStorage<
    WordTransformation[]
  >("screenshot-words-to-remove", [], 500);

  const [cookies] = useDebouncedLocalStorage<string>(
    "screenshot-cookies",
    "",
    500
  );

  const [localStorageData] = useDebouncedLocalStorage<string>(
    "screenshot-localstorage",
    "",
    500
  );

  // Segmented settings
  const [segmentOverlap, setSegmentOverlap] = useLocalStorage<number>(
    "screenshot-segment-overlap",
    20
  );
  const [segmentScrollDelay, setSegmentScrollDelay] = useLocalStorage<number>(
    "screenshot-segment-scrolldelay",
    1000
  );
  const [segmentMaxSegments, setSegmentMaxSegments] = useLocalStorage<number>(
    "screenshot-segment-maxsegments",
    50
  );
  const [segmentSkipDuplicates, setSegmentSkipDuplicates] =
    useLocalStorage<boolean>("screenshot-segment-skipduplicates", true);
  const [segmentSmartLazyLoad, setSegmentSmartLazyLoad] =
    useLocalStorage<boolean>("screenshot-segment-smartlazyload", true);

  // Multi‑textbox + sessions (same keys as App.tsx)
  // ✅ FIX 2.3: Use shared DEFAULT_TEXT_BOXES constant
  const [textBoxes, setTextBoxes] = useDebouncedLocalStorage<TextBox[]>(
    "screenshot-textboxes",
    DEFAULT_TEXT_BOXES,
    500
  );

  const [sessions, setSessions] = useDebouncedLocalStorage<Session[]>(
    "screenshot-sessions",
    [],
    500
  );

  // Migration: ensure batchTimeout/batchTimeoutUnit/selected always exist
  useEffect(() => {
    const needsMigration = textBoxes.some(
      (tb) =>
        tb.batchTimeout === undefined ||
        tb.batchTimeoutUnit === undefined ||
        tb.selected === undefined
    );
    if (needsMigration) {
      const migrated = textBoxes.map((tb) => ({
        ...tb,
        batchTimeout: tb.batchTimeout || 90,
        batchTimeoutUnit: tb.batchTimeoutUnit || "seconds",
        selected: tb.selected !== undefined ? tb.selected : true,
      }));
      setTextBoxes(migrated);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const {
    notifications,
    history,
    addNotification,
    removeNotification,
    clearAll,
    clearHistory,
  } = useNotifications();

  const notify = useCallback(
    (
      message: string,
      options?: {
        title?: string;
        type?: "success" | "error" | "warning" | "info";
        duration?: number;
      }
    ) => {
      addNotification({
        message,
        title: options?.title,
        type: options?.type,
        duration: options?.duration,
      });
    },
    [addNotification]
  );

  const alert = useCallback(
    (message: string) => {
      return notify(message);
    },
    [notify]
  );

  // Wrapper setters mirroring App.tsx logging behaviour
  const setCaptureMode = (mode: string) => {
    const modeNames: Record<string, string> = {
      viewport: "Viewport only",
      fullpage: "Full page",
      segmented: "Segmented",
    };
    addLog(`⚙️ Changed capture mode to: ${modeNames[mode] || mode}`);
    setCaptureModeState(mode);
  };

  const setUseStealth = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} stealth mode`);
    setUseStealthState(enabled);
  };

  const setUseRealBrowser = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} real browser mode`);
    setUseRealBrowserState(enabled);
  };

  const setHeadless = (enabled: boolean) => {
    addLog(
      `⚙️ ${enabled ? "Enabled" : "Disabled"} headless mode (${
        enabled ? "invisible" : "visible"
      } browser)`
    );
    setHeadlessState(enabled);
  };

  const setTrackNetwork = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} network event tracking`);
    setTrackNetworkState(enabled);
  };

  const setAutoExpandDropdowns = (enabled: boolean) => {
    addLog(`⚙️ ${enabled ? "Enabled" : "Disabled"} auto dropdown expansion`);
    setAutoExpandDropdownsState(enabled);
  };

  const setBrowserEngine = (engine: string) => {
    const engineNames: Record<string, string> = {
      playwright: "Playwright",
      camoufox: "Camoufox",
    };
    addLog(`⚙️ Changed browser engine to: ${engineNames[engine] || engine}`);
    setBrowserEngineState(engine);
  };

  const addLog = useCallback((message: string) => {
    const timestamp = new Date().toLocaleTimeString();
    const newLog = `[${timestamp}] ${message}`;
    setLogs((prev) => [...prev, newLog]);

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
    }
  }, []);

  const clearLogs = useCallback(() => {
    setLogs([]);
    setHasErrors(false);
  }, []);

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

  // Backend helpers copied from App.tsx behaviour (exposed to shell UI)
  const updateBackendScreenshotsDir = async (newDir: string) => {
    try {
      const response = await fetch("http://127.0.0.1:8000/api/config/paths", {
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

  const restartBackend = async () => {
    addLog("🔄 Restarting backend server...");
    notify("Backend server is restarting...", {
      title: "🔄 Restarting Backend",
      type: "info",
      duration: 3000,
    });

    try {
      const response = await fetch("http://127.0.0.1:8000/api/restart", {
        method: "POST",
      });

      if (response.ok) {
        addLog("✅ Backend restarted successfully!");
        notify("Backend server restarted successfully!", {
          title: "✅ Backend Restarted",
          type: "success",
          duration: 5000,
        });
      } else {
        const error = await response.text();
        addLog(`❌ Failed to restart backend: ${error}`);
        notify(`Failed to restart backend: ${error}`, {
          title: "❌ Restart Failed",
          type: "error",
          duration: 8000,
        });
      }
    } catch (error) {
      addLog(
        `❌ Failed to connect to backend: ${error}. Please restart manually.`
      );
      notify(
        "Backend not responding. Please restart manually using: cd backend && python3 main.py",
        {
          title: "❌ Connection Error",
          type: "error",
          duration: 8000,
        }
      );
    }
  };

  const generateWordDocumentForSession = async (
    sessionName: string,
    sessionScreenshots: Screenshot[]
  ) => {
    try {
      const screenshotPaths = sessionScreenshots.map((s) => s.path);

      if (screenshotPaths.length === 0) {
        addLog(`   ⚠️ No screenshots to include in document`);
        return;
      }

      addLog(
        `   📄 Generating Word document with ${screenshotPaths.length} screenshot(s)...`
      );

      const documentName = `${sessionName}.docx`;

      let outputPath = wordDocsBaseDir;
      if (wordDocFolderName.trim()) {
        outputPath += `/${wordDocFolderName.trim()}`;
        addLog(`   📁 Saving to folder: ${wordDocFolderName.trim()}`);
      }
      outputPath += `/${documentName}`;
      addLog(`   📁 Full output path: ${outputPath}`);

      const response = await fetch(
        "http://127.0.0.1:8000/api/document/generate",
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            screenshot_paths: screenshotPaths,
            output_path: outputPath,
            title: sessionName,
          }),
        }
      );

      if (!response.ok) {
        addLog(`   ❌ Document generation failed: ${response.status}`);
        return;
      }

      const data = await response.json();
      if (data.status === "success") {
        addLog(`   ✅ Document generated: ${documentName}`);
        notify(`Document saved: ${documentName}`, {
          title: "📄 Word Document Generated",
          type: "success",
          duration: 5000,
        });
      } else {
        addLog(`   ❌ Document generation failed: ${data.error}`);
      }
    } catch (error: any) {
      addLog(`   ❌ Document generation error: ${error.message}`);
    }
  };

  const captureMultiTextBoxes = async () => {
    const selectedTextBoxes = textBoxes.filter((box) => box.selected !== false);

    if (selectedTextBoxes.length === 0) {
      alert("Please select at least one text box to capture!");
      return;
    }

    const validTextBoxes = selectedTextBoxes.filter(
      (box) => box.urls.trim().length > 0
    );

    if (validTextBoxes.length === 0) {
      alert("Please enter URLs in at least one selected text box!");
      return;
    }

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

    addLog(
      `🚀 Starting cross-text-box batch capture for ${validTextBoxes.length} text box(es)`
    );
    addLog(
      `   📦 Batching: ${maxParallelUrls} URLs per batch across all text boxes`
    );

    try {
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
            url,
            textBoxId: textBox.id,
            textBoxIndex: index,
            sessionName: textBox.sessionName,
            batchTimeout: textBox.batchTimeout || 90,
          });
        });
      });

      const totalUrls = allUrlsWithMetadata.length;
      addLog(`\n📊 Total URLs across all text boxes: ${totalUrls}`);

      const batchSize = maxParallelUrls;
      const batches: (typeof allUrlsWithMetadata)[] = [];
      for (let i = 0; i < allUrlsWithMetadata.length; i += batchSize) {
        batches.push(allUrlsWithMetadata.slice(i, i + batchSize));
      }

      addLog(
        `   🔢 Created ${batches.length} batches of up to ${batchSize} URLs each`
      );

      const textBoxResults: { [key: string]: any[] } = {};
      const textBoxProcessedCounts: { [key: string]: number } = {};
      const createdSessions = new Set<string>();

      validTextBoxes.forEach((tb) => {
        textBoxResults[tb.id] = [];
        textBoxProcessedCounts[tb.id] = 0;
      });

      for (let batchNum = 0; batchNum < batches.length; batchNum++) {
        const batch = batches[batchNum];
        const batchUrls = batch.map((item) => item.url);

        const batchTimeout = Math.max(
          ...batch.map((item) => item.batchTimeout)
        );

        const textBoxesInBatch = [
          ...new Set(batch.map((item) => item.sessionName)),
        ];
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

        addLog(`   📋 URLs in this batch:`);
        batchUrls.forEach((url, idx) => {
          const shortUrl = url.length > 80 ? url.substring(0, 77) + "..." : url;
          addLog(`      ${idx + 1}. ${shortUrl}`);
        });

        const batchStartTime = Date.now();

        try {
          const controller = new AbortController();
          const timeoutId = setTimeout(
            () => controller.abort(),
            (config as any).requestTimeout || 600000
          );

          addLog(`   🚀 Sending batch to backend...`);

          const response = await fetch(
            `${(config as any).apiBaseUrl}/api/screenshots/capture`,
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
                headless,
                browser_engine: browserEngine,
                base_url: baseUrl,
                words_to_remove: JSON.stringify(wordsToRemove),
                cookies,
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
                non_scrollable_urls: JSON.stringify(nonScrollableUrls),
              }),
              signal: controller.signal,
            }
          );

          clearTimeout(timeoutId);

          if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
          }

          const data = await response.json();

          const batchEndTime = Date.now();
          const batchDuration = (
            (batchEndTime - batchStartTime) /
            1000
          ).toFixed(1);
          addLog(`   ⏱️ Batch completed in ${batchDuration}s`);

          const completedTextBoxIds = new Set<string>();

          addLog(`   📊 Per-URL Results:`);
          batch.forEach((item, index) => {
            const result = data.results[index];
            const shortUrl =
              item.url.length > 60
                ? item.url.substring(0, 57) + "..."
                : item.url;

            if (result.status === "success") {
              const screenshotCount = result.screenshot_paths?.length || 1;
              const processingTime = result.processing_time
                ? `${result.processing_time.toFixed(1)}s`
                : "N/A";
              addLog(
                `      ✅ ${shortUrl} (${processingTime}, ${screenshotCount} screenshot${
                  screenshotCount > 1 ? "s" : ""
                })`
              );
            } else {
              const errorMsg = result.error || "Unknown error";
              const shortError =
                errorMsg.length > 50
                  ? errorMsg.substring(0, 47) + "..."
                  : errorMsg;
              addLog(`      ❌ ${shortUrl} - ${shortError}`);
            }

            textBoxResults[item.textBoxId].push(result);
            textBoxProcessedCounts[item.textBoxId]++;

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

          const successCount = data.results.filter(
            (r: any) => r.status === "success"
          ).length;
          const failCount = data.results.filter(
            (r: any) => r.status === "error"
          ).length;
          addLog(
            `   📈 Batch Summary: ✅ ${successCount} succeeded, ❌ ${failCount} failed`
          );

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

          for (const textBoxId of completedTextBoxIds) {
            const textBox = textBoxInfo[textBoxId];
            const results = textBoxResults[textBoxId];
            const successResults = results.filter(
              (r: any) => r.status === "success"
            );

            if (successResults.length > 0) {
              addLog(
                `   📄 Generating Word document for "${textBox.sessionName}" (${successResults.length} successful screenshots)...`
              );

              try {
                const sessionScreenshots = successResults.flatMap((r: any) => {
                  if (r.screenshot_paths && r.screenshot_paths.length > 0) {
                    return r.screenshot_paths.map((path: string) => ({
                      filename: path.split("/").pop() || path,
                      path,
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
                    captureMode,
                    useStealth,
                    useRealBrowser,
                  },
                };

                if (!createdSessions.has(textBoxId)) {
                  setSessions((prev) => [newSession, ...prev]);
                  createdSessions.add(textBoxId);

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

          setProgress({
            current: Math.min((batchNum + 1) * batchSize, totalUrls),
            total: totalUrls,
          });
        } catch (error: any) {
          addLog(`   ❌ Batch ${batchNum + 1} failed: ${error.message}`);

          const completedTextBoxIds = new Set<string>();

          batch.forEach((item) => {
            textBoxResults[item.textBoxId].push({
              url: item.url,
              status: "error",
              error: error.message,
            });
            textBoxProcessedCounts[item.textBoxId]++;

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

          for (const textBoxId of completedTextBoxIds) {
            const textBox = textBoxInfo[textBoxId];
            const results = textBoxResults[textBoxId];
            const successResults = results.filter(
              (r: any) => r.status === "success"
            );

            if (successResults.length > 0) {
              addLog(
                `   📄 Generating Word document for "${textBox.sessionName}" (${successResults.length} successful screenshots)...`
              );

              try {
                const sessionScreenshots = successResults.flatMap((r: any) => {
                  if (r.screenshot_paths && r.screenshot_paths.length > 0) {
                    return r.screenshot_paths.map((path: string) => ({
                      filename: path.split("/").pop() || path,
                      path,
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
                    captureMode,
                    useStealth,
                    useRealBrowser,
                  },
                };

                if (!createdSessions.has(textBoxId)) {
                  setSessions((prev) => [newSession, ...prev]);
                  createdSessions.add(textBoxId);

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

          setProgress({
            current: Math.min((batchNum + 1) * batchSize, totalUrls),
            total: totalUrls,
          });
        }
      }

      addLog(`\n✅ Cross-text-box batch capture complete!`);
      addLog(`   📊 Processed ${validTextBoxes.length} text box(es)`);
      addLog(`   📦 Total batches: ${batches.length}`);
      addLog(`   🔗 Total URLs: ${totalUrls}`);
    } catch (error: any) {
      addLog(`❌ Batch capture failed: ${error.message}`);
      alert(`Batch capture failed: ${error.message}`);
    } finally {
      setLoading(false);
      setProgress({ current: 0, total: 0 });
    }
  };

  return {
    // state
    loading,
    progress,
    logs,
    hasErrors,
    textBoxes,
    sessions,
    captureMode,
    useStealth,
    useRealBrowser,
    headless,
    trackNetwork,
    autoExpandDropdowns,
    nonScrollableUrls,
    browserEngine,
    baseUrl,
    maxParallelUrls,
    segmentOverlap,
    segmentScrollDelay,
    segmentMaxSegments,
    segmentSkipDuplicates,
    segmentSmartLazyLoad,
    wordDocFolderName,
    wordDocsBaseDir,
    wordsToRemove,
    notifications,
    history,

    // mutators
    setTextBoxes,
    setSessions,
    clearLogs,
    setCaptureMode,
    setUseStealth,
    setUseRealBrowser,
    setHeadless,
    setTrackNetwork,
    setAutoExpandDropdowns,
    setBrowserEngine,
    setBaseUrl,
    setMaxParallelUrls,
    setSegmentOverlap,
    setSegmentScrollDelay,
    setSegmentMaxSegments,
    setSegmentSkipDuplicates,
    setSegmentSmartLazyLoad,
    setWordDocFolderName,
    setWordDocsBaseDir,
    setNonScrollableUrls,
    setWordsToRemove,
    removeNotification,
    clearAll,
    clearHistory,

    // actions
    captureMultiTextBoxes,
    generateWordDocumentForSession,
    restartBackend,
    updateBackendScreenshotsDir,

    // helpers
    addLog,
    notify,
    alert,
    formatTimestamp,
  };
}

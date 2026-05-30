/**
 * ✅ Phase 2: Zustand App Store
 * Replaces AppContext with better performance and simpler API
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AppState {
  // URL Management
  urls: string;
  setUrls: (urls: string) => void;

  // Screenshot Settings
  viewportWidth: number;
  setViewportWidth: (width: number) => void;
  viewportHeight: number;
  setViewportHeight: (height: number) => void;

  // Browser Settings
  useRealBrowser: boolean;
  setUseRealBrowser: (use: boolean) => void;
  useStealth: boolean;
  setUseStealth: (use: boolean) => void;
  headless: boolean;
  setHeadless: (headless: boolean) => void;
  browserEngine: string;
  setBrowserEngine: (engine: string) => void;

  // Capture Settings
  captureMode: string;
  setCaptureMode: (mode: string) => void;
  autoExpandDropdowns: boolean;
  setAutoExpandDropdowns: (expand: boolean) => void;
  trackNetwork: boolean;
  setTrackNetwork: (track: boolean) => void;

  // Active Tab
  activeTab: string;
  setActiveTab: (tab: string) => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // URL Management
      urls: '',
      setUrls: (urls) => set({ urls }),

      // Screenshot Settings
      viewportWidth: 1920,
      setViewportWidth: (width) => set({ viewportWidth: width }),
      viewportHeight: 1080,
      setViewportHeight: (height) => set({ viewportHeight: height }),

      // Browser Settings
      useRealBrowser: false,
      setUseRealBrowser: (use) => set({ useRealBrowser: use }),
      useStealth: true,
      setUseStealth: (use) => set({ useStealth: use }),
      headless: false,  // ✅ Changed to false - we disabled headless mode
      setHeadless: (headless) => set({ headless }),
      browserEngine: 'chromium',
      setBrowserEngine: (engine) => set({ browserEngine: engine }),

      // Capture Settings
      captureMode: 'fullpage',
      setCaptureMode: (mode) => set({ captureMode: mode }),
      autoExpandDropdowns: false,
      setAutoExpandDropdowns: (expand) => set({ autoExpandDropdowns: expand }),
      trackNetwork: false,
      setTrackNetwork: (track) => set({ trackNetwork: track }),

      // Active Tab
      activeTab: 'screenshots',
      setActiveTab: (tab) => set({ activeTab: tab }),
    }),
    {
      name: 'app-storage-v2', // ✅ Changed key to force fresh start (headless: false)
      partialize: (state) => ({
        // Only persist these fields
        urls: state.urls,
        viewportWidth: state.viewportWidth,
        viewportHeight: state.viewportHeight,
        useRealBrowser: state.useRealBrowser,
        useStealth: state.useStealth,
        headless: state.headless,
        browserEngine: state.browserEngine,
        captureMode: state.captureMode,
        autoExpandDropdowns: state.autoExpandDropdowns,
        trackNetwork: state.trackNetwork,
        activeTab: state.activeTab,
      }),
    }
  )
);

// Selectors for optimized re-renders
export const selectUrls = (state: AppState) => state.urls;
export const selectViewport = (state: AppState) => ({
  width: state.viewportWidth,
  height: state.viewportHeight,
});
export const selectBrowserSettings = (state: AppState) => ({
  useRealBrowser: state.useRealBrowser,
  useStealth: state.useStealth,
  headless: state.headless,
  browserEngine: state.browserEngine,
});
export const selectCaptureSettings = (state: AppState) => ({
  captureMode: state.captureMode,
  autoExpandDropdowns: state.autoExpandDropdowns,
  trackNetwork: state.trackNetwork,
});
export const selectActiveTab = (state: AppState) => state.activeTab;


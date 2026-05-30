/**
 * ✅ Phase 2: Zustand Settings Store
 * Replaces SettingsContext with better performance
 */

import { create } from 'zustand';
import { persist } from 'zustand/middleware';

/**
 * ✅ DEFAULT NON-SCROLLABLE URLS
 * These parts-related and service-related URLs are ALWAYS included in the non-scrollable list.
 * They persist even if localStorage is cleared.
 * Users can add custom URLs on top of these defaults.
 */
const DEFAULT_NON_SCROLLABLE_URLS = [
  // ✅ PARTS-RELATED (10 URLs)
  'https://preprodapp.tekioncloud.com/parts/void-reasons',
  'https://preprodapp.tekioncloud.com/parts/priority-codes',
  'https://preprodapp.tekioncloud.com/parts/return-reasons',
  'https://preprodapp.tekioncloud.com/parts/core-management-setup/reasons-setup',
  'https://preprodapp.tekioncloud.com/parts/adjustment-reason',
  'https://preprodapp.tekioncloud.com/parts/default-part-pricing',
  'https://preprodapp.tekioncloud.com/parts/manufacturer',
  'https://preprodapp.tekioncloud.com/parts/warehouse-management',
  'https://preprodapp.tekioncloud.com/core/setups/dealer-configuration/dealerDetails#media-upload',
  'https://preprodapp.tekioncloud.com/core/setups/dealer-configuration/dealerDetails#oem-details',

  // ✅ SERVICE-RELATED (7 URLs)
  'https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/consumer-scheduling',
  'https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/transportation',
  'https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/shops',
  'https://preprodapp.tekioncloud.com/dse-v2/scheduling-settings/serviceAdvisors',
  'https://preprodapp.tekioncloud.com/ro/labor-pricing',
  'https://preprodapp.tekioncloud.com/ro/dispatch-settings',
  'https://preprodapp.tekioncloud.com/ro/opcode',

  // ✅ ACCOUNTING-RELATED (1 URL)
  'https://preprodapp.tekioncloud.com/accounting/journalMapping/list',
] as const;

interface WordTransformation {
  word: string;
  replacement: string;
  type: "remove" | "space" | "custom";
}

interface SettingsState {
  // Feature Toggles
  enableMultipleTextBoxes: boolean;
  setEnableMultipleTextBoxes: (enabled: boolean) => void;
  enableParallelTextBoxes: boolean;
  setEnableParallelTextBoxes: (enabled: boolean) => void;
  
  // Batch Settings
  maxParallelUrls: number;
  setMaxParallelUrls: (max: number) => void;
  
  // Directory Settings
  wordDocFolderName: string;
  setWordDocFolderName: (name: string) => void;
  screenshotsDir: string;
  setScreenshotsDir: (dir: string) => void;
  wordDocsBaseDir: string;
  setWordDocsBaseDir: (dir: string) => void;
  
  // URL Settings
  baseUrl: string;
  setBaseUrl: (url: string) => void;
  nonScrollableUrls: string[];
  setNonScrollableUrls: (urls: string[]) => void;
  
  // Word Transformations
  wordsToRemove: WordTransformation[];
  setWordsToRemove: (words: WordTransformation[]) => void;
  
  // Browser Settings
  selectedBrowser: string;
  setSelectedBrowser: (browser: string) => void;
  
  // Cookie Settings
  cookieDomains: string[];
  setCookieDomains: (domains: string[]) => void;
  cookies: string;
  setCookies: (cookies: string) => void;
  localStorageData: string;
  setLocalStorageData: (data: string) => void;
  
  // UI Settings
  expandedAuthMethod: string | null;
  setExpandedAuthMethod: (method: string | null) => void;
  showCookieAnalysis: boolean;
  setShowCookieAnalysis: (show: boolean) => void;
  analysisDomainFilter: string;
  setAnalysisDomainFilter: (filter: string) => void;
  showAuthCookiesOnly: boolean;
  setShowAuthCookiesOnly: (show: boolean) => void;
}

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      // Feature Toggles
      enableMultipleTextBoxes: true,
      setEnableMultipleTextBoxes: (enabled) => set({ enableMultipleTextBoxes: enabled }),
      enableParallelTextBoxes: true,
      setEnableParallelTextBoxes: (enabled) => set({ enableParallelTextBoxes: enabled }),
      
      // Batch Settings
      maxParallelUrls: 5,
      setMaxParallelUrls: (max) => set({ maxParallelUrls: max }),
      
      // Directory Settings
      wordDocFolderName: '',
      setWordDocFolderName: (name) => set({ wordDocFolderName: name }),
      screenshotsDir: 'screenshots',
      setScreenshotsDir: (dir) => set({ screenshotsDir: dir }),
      wordDocsBaseDir: '~/Desktop/ARC DEALERS SCREENSHOT WORD DOCS',
      setWordDocsBaseDir: (dir) => set({ wordDocsBaseDir: dir }),
      
      // URL Settings
      baseUrl: '',
      setBaseUrl: (url) => set({ baseUrl: url }),
      // ✅ Initialize with default non-scrollable URLs
      nonScrollableUrls: [...DEFAULT_NON_SCROLLABLE_URLS],
      setNonScrollableUrls: (urls) => {
        // ✅ Always merge with defaults to ensure they're never lost
        const merged = [...new Set([...DEFAULT_NON_SCROLLABLE_URLS, ...urls])];
        set({ nonScrollableUrls: merged });
      },
      
      // Word Transformations
      wordsToRemove: [],
      setWordsToRemove: (words) => set({ wordsToRemove: words }),
      
      // Browser Settings
      selectedBrowser: 'chrome',
      setSelectedBrowser: (browser) => set({ selectedBrowser: browser }),
      
      // Cookie Settings
      cookieDomains: [],
      setCookieDomains: (domains) => set({ cookieDomains: domains }),
      cookies: '',
      setCookies: (cookies) => set({ cookies }),
      localStorageData: '',
      setLocalStorageData: (data) => set({ localStorageData: data }),
      
      // UI Settings
      expandedAuthMethod: null,
      setExpandedAuthMethod: (method) => set({ expandedAuthMethod: method }),
      showCookieAnalysis: false,
      setShowCookieAnalysis: (show) => set({ showCookieAnalysis: show }),
      analysisDomainFilter: '',
      setAnalysisDomainFilter: (filter) => set({ analysisDomainFilter: filter }),
      showAuthCookiesOnly: false,
      setShowAuthCookiesOnly: (show) => set({ showAuthCookiesOnly: show }),
    }),
    {
      name: 'settings-storage',
      // ✅ Custom merge: Always include default non-scrollable URLs when loading from localStorage
      merge: (persistedState: any, currentState: SettingsState) => ({
        ...currentState,
        ...persistedState,
        // Merge persisted URLs with defaults (remove duplicates)
        nonScrollableUrls: persistedState?.nonScrollableUrls
          ? [...new Set([...DEFAULT_NON_SCROLLABLE_URLS, ...persistedState.nonScrollableUrls])]
          : [...DEFAULT_NON_SCROLLABLE_URLS],
      }),
    }
  )
);

// Selectors
export const selectFeatureToggles = (state: SettingsState) => ({
  enableMultipleTextBoxes: state.enableMultipleTextBoxes,
  enableParallelTextBoxes: state.enableParallelTextBoxes,
});
export const selectDirectories = (state: SettingsState) => ({
  wordDocFolderName: state.wordDocFolderName,
  screenshotsDir: state.screenshotsDir,
  wordDocsBaseDir: state.wordDocsBaseDir,
});
export const selectWordTransformations = (state: SettingsState) => state.wordsToRemove;
export const selectCookieSettings = (state: SettingsState) => ({
  selectedBrowser: state.selectedBrowser,
  cookieDomains: state.cookieDomains,
  cookies: state.cookies,
  localStorageData: state.localStorageData,
});


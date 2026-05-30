/**
 * ✅ FIXED (Bug #14): Settings state context
 * 
 * Manages all application settings and configuration.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useDebouncedLocalStorage } from '../hooks/useDebouncedLocalStorage';

interface WordTransformation {
  word: string;
  replacement: string;
  type: "remove" | "space" | "custom";
}

interface SettingsContextType {
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

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // Feature Toggles
  const [enableMultipleTextBoxes, setEnableMultipleTextBoxes] = useLocalStorage("screenshot-enable-multiple-textboxes", true);
  const [enableParallelTextBoxes, setEnableParallelTextBoxes] = useLocalStorage("screenshot-enable-parallel-textboxes", true);
  
  // Batch Settings
  const [maxParallelUrls, setMaxParallelUrls] = useLocalStorage("screenshot-max-parallel-urls", 5);
  
  // Directory Settings
  const [wordDocFolderName, setWordDocFolderName] = useDebouncedLocalStorage("screenshot-word-doc-folder-name", "", 500);
  const [screenshotsDir, setScreenshotsDir] = useLocalStorage("screenshot-screenshots-dir", "screenshots");
  const [wordDocsBaseDir, setWordDocsBaseDir] = useLocalStorage("screenshot-word-docs-base-dir", "~/Desktop/ARC DEALERS SCREENSHOT WORD DOCS");
  
  // URL Settings
  const [baseUrl, setBaseUrl] = useLocalStorage("screenshot-base-url", "");
  const [nonScrollableUrls, setNonScrollableUrls] = useLocalStorage<string[]>("screenshot-non-scrollable-urls", []);
  
  // Word Transformations
  const [wordsToRemove, setWordsToRemove] = useDebouncedLocalStorage<WordTransformation[]>("screenshot-words-to-remove", [], 500);
  
  // Browser Settings
  const [selectedBrowser, setSelectedBrowser] = useLocalStorage("screenshot-selected-browser", "chrome");
  
  // Cookie Settings
  const [cookieDomains, setCookieDomains] = useLocalStorage("screenshot-cookie-domains", []);
  const [cookies, setCookies] = useDebouncedLocalStorage("screenshot-cookies", "", 500);
  const [localStorageData, setLocalStorageData] = useDebouncedLocalStorage("screenshot-localstorage", "", 500);
  
  // UI Settings
  const [expandedAuthMethod, setExpandedAuthMethod] = useLocalStorage<string | null>("screenshot-expanded-auth-method", null);
  const [showCookieAnalysis, setShowCookieAnalysis] = React.useState(false);
  const [analysisDomainFilter, setAnalysisDomainFilter] = React.useState("");
  const [showAuthCookiesOnly, setShowAuthCookiesOnly] = React.useState(false);

  const value: SettingsContextType = {
    enableMultipleTextBoxes,
    setEnableMultipleTextBoxes,
    enableParallelTextBoxes,
    setEnableParallelTextBoxes,
    maxParallelUrls,
    setMaxParallelUrls,
    wordDocFolderName,
    setWordDocFolderName,
    screenshotsDir,
    setScreenshotsDir,
    wordDocsBaseDir,
    setWordDocsBaseDir,
    baseUrl,
    setBaseUrl,
    nonScrollableUrls,
    setNonScrollableUrls,
    wordsToRemove,
    setWordsToRemove,
    selectedBrowser,
    setSelectedBrowser,
    cookieDomains,
    setCookieDomains,
    cookies,
    setCookies,
    localStorageData,
    setLocalStorageData,
    expandedAuthMethod,
    setExpandedAuthMethod,
    showCookieAnalysis,
    setShowCookieAnalysis,
    analysisDomainFilter,
    setAnalysisDomainFilter,
    showAuthCookiesOnly,
    setShowAuthCookiesOnly,
  };

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
};

export const useSettingsContext = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettingsContext must be used within SettingsProvider');
  }
  return context;
};


/**
 * ✅ FIXED (Bug #14): Centralized application state context
 * 
 * This context provides shared state across the application to avoid
 * prop drilling and reduce the massive App.tsx component.
 */

import React, { createContext, useContext, ReactNode } from 'react';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { useDebouncedLocalStorage } from '../hooks/useDebouncedLocalStorage';

interface AppContextType {
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

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // URL Management
  const [urls, setUrls] = useDebouncedLocalStorage("screenshot-urls", "", 500);

  // Screenshot Settings
  const [viewportWidth, setViewportWidth] = useLocalStorage("viewport-width", 1920);
  const [viewportHeight, setViewportHeight] = useLocalStorage("viewport-height", 1080);

  // Browser Settings
  const [useRealBrowser, setUseRealBrowser] = useLocalStorage("use-real-browser", false);
  const [useStealth, setUseStealth] = useLocalStorage("use-stealth", true);
  const [headless, setHeadless] = useLocalStorage("headless", true);
  const [browserEngine, setBrowserEngine] = useLocalStorage("browser-engine", "chromium");

  // Capture Settings
  const [captureMode, setCaptureMode] = useLocalStorage("capture-mode", "fullpage");
  const [autoExpandDropdowns, setAutoExpandDropdowns] = useLocalStorage("auto-expand-dropdowns", false);
  const [trackNetwork, setTrackNetwork] = useLocalStorage("track-network", false);

  // Active Tab
  const [activeTab, setActiveTab] = useLocalStorage("active-tab", "screenshots");

  const value: AppContextType = {
    urls,
    setUrls,
    viewportWidth,
    setViewportWidth,
    viewportHeight,
    setViewportHeight,
    useRealBrowser,
    setUseRealBrowser,
    useStealth,
    setUseStealth,
    headless,
    setHeadless,
    browserEngine,
    setBrowserEngine,
    captureMode,
    setCaptureMode,
    autoExpandDropdowns,
    setAutoExpandDropdowns,
    trackNetwork,
    setTrackNetwork,
    activeTab,
    setActiveTab,
  };

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>;
};

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};


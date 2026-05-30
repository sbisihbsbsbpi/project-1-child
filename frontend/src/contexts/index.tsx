/**
 * ✅ FIXED (Bug #14): Combined context providers
 * 
 * Exports all context providers and a combined provider component.
 */

import React, { ReactNode } from 'react';
import { AppProvider } from './AppContext';
import { ScreenshotProvider } from './ScreenshotContext';
import { SessionProvider } from './SessionContext';
import { SettingsProvider } from './SettingsContext';

/**
 * Combined provider that wraps all context providers.
 * This simplifies the App.tsx setup.
 */
export const AppProviders: React.FC<{ children: ReactNode }> = ({ children }) => {
  return (
    <AppProvider>
      <ScreenshotProvider>
        <SessionProvider>
          <SettingsProvider>
            {children}
          </SettingsProvider>
        </SessionProvider>
      </ScreenshotProvider>
    </AppProvider>
  );
};

// Export individual providers and hooks
export { AppProvider, useAppContext } from './AppContext';
export { ScreenshotProvider, useScreenshotContext } from './ScreenshotContext';
export { SessionProvider, useSessionContext } from './SessionContext';
export { SettingsProvider, useSettingsContext } from './SettingsContext';


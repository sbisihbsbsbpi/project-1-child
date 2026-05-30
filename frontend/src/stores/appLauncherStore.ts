/**
 * App Launcher Store
 * Manages the 9-dot waffle menu launcher state
 */

import { create } from 'zustand';

interface AppDefinition {
  id: string;
  name: string;
  icon: string;
  description: string;
  routes?: Array<{
    name: string;
    path: string;
    icon: string;
  }>;
  defaultRoute?: string;
}

interface AppLauncherState {
  // Panel visibility
  isLauncherOpen: boolean;
  setLauncherOpen: (open: boolean) => void;
  toggleLauncher: () => void;
  closeLauncher: () => void;
  openLauncher: () => void;

  // Current app (null = home, 'screenshots' = in screenshots app)
  currentApp: string | null;
  setCurrentApp: (app: string | null) => void;
  goHome: () => void;

  // Available apps
  apps: AppDefinition[];
}

export const useAppLauncherStore = create<AppLauncherState>((set) => ({
  // Panel state
  isLauncherOpen: false,
  setLauncherOpen: (open) => set({ isLauncherOpen: open }),
  toggleLauncher: () => set((state) => ({ isLauncherOpen: !state.isLauncherOpen })),
  closeLauncher: () => set({ isLauncherOpen: false }),
  openLauncher: () => set({ isLauncherOpen: true }),

  // Current app state (null = home page)
  currentApp: null,
  setCurrentApp: (app) => set({ currentApp: app }),
  goHome: () => set({ currentApp: null }),

  // App definitions
  apps: [
    {
      id: 'screenshots',
      name: 'Screenshots',
      icon: '📸',
      description: 'Capture and manage screenshots',
      routes: [
        { name: 'Capture', path: 'main', icon: '📸' },
        { name: 'Sessions', path: 'sessions', icon: '🗂️' },
        { name: 'URLs', path: 'urls', icon: '📁' },
        { name: 'Settings', path: 'settings', icon: '⚙️' },
      ],
      defaultRoute: 'main',
    },
    {
      id: 'business-apps',
      name: 'Business Apps',
      icon: '💼',
      description: 'Parts, Service, Accounting & CRM tools',
      routes: [
        { name: 'Parts', path: 'parts', icon: '🔧' },
        { name: 'Service', path: 'service', icon: '🛠️' },
        { name: 'Accounting', path: 'accounting', icon: '💰' },
        { name: 'CRM', path: 'crm', icon: '📞' },
      ],
      defaultRoute: 'crm',
    },
  ],
}));

// Selectors
export const selectIsLauncherOpen = (state: AppLauncherState) => state.isLauncherOpen;
export const selectApps = (state: AppLauncherState) => state.apps;
export const selectCurrentApp = (state: AppLauncherState) => state.currentApp;

/**
 * LauncherPanel Component
 * Expandable overlay panel showing available apps in a grid
 */

import React, { useEffect, useCallback } from 'react';
import { useAppLauncherStore } from '../../stores/appLauncherStore';

interface LauncherPanelProps {
  onNavigate: (route: string) => void;
}

export const LauncherPanel: React.FC<LauncherPanelProps> = ({ onNavigate }) => {
  const isLauncherOpen = useAppLauncherStore((state) => state.isLauncherOpen);
  const closeLauncher = useAppLauncherStore((state) => state.closeLauncher);
  const setCurrentApp = useAppLauncherStore((state) => state.setCurrentApp);
  const apps = useAppLauncherStore((state) => state.apps);

  // Handle app click
  const handleAppClick = useCallback((appId: string, defaultRoute?: string) => {
    console.log('🚀 Opening app:', appId, defaultRoute);

    // Set the current app (this triggers the app view)
    setCurrentApp(appId);

    // Navigate to the default route within the app
    if (defaultRoute) {
      onNavigate(defaultRoute);
    }

    // ✅ Update URL hash for deep linking
    const tab = defaultRoute || 'main';
    const newHash = `#${appId}/${tab}`;
    window.history.pushState(null, '', `/${newHash}`);
    console.log(`🔗 URL updated to: /${newHash}`);

    closeLauncher();
  }, [onNavigate, closeLauncher, setCurrentApp]);

  // Handle backdrop click
  const handleBackdropClick = useCallback((e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      closeLauncher();
    }
  }, [closeLauncher]);

  // Handle Escape key
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isLauncherOpen) {
        closeLauncher();
      }
    };

    if (isLauncherOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }

    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isLauncherOpen, closeLauncher]);

  if (!isLauncherOpen) {
    return null;
  }

  return (
    <>
      {/* Backdrop */}
      <div className="launcher-backdrop" onClick={handleBackdropClick} />

      {/* Panel */}
      <div
        id="app-launcher-panel"
        className="launcher-panel"
        role="dialog"
        aria-modal="false"
        aria-label="App launcher"
      >
        {/* Header */}
        <div className="launcher-panel-header">
          <div className="launcher-panel-title">Apps</div>
          <button
            className="launcher-close-btn"
            onClick={closeLauncher}
            aria-label="Close app launcher"
            title="Close"
          >
            ✕
          </button>
        </div>

        {/* App Grid */}
        <div className="launcher-app-grid">
          {apps.map((app) => (
            <div
              key={app.id}
              className="launcher-app-tile"
              onClick={() => handleAppClick(app.id, app.defaultRoute)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault();
                  handleAppClick(app.id, app.defaultRoute);
                }
              }}
            >
              <div className="launcher-app-icon" aria-hidden="true">
                {app.icon}
              </div>
              <div className="launcher-app-name">{app.name}</div>
              {app.description && (
                <div className="launcher-app-description" title={app.description}>
                  {app.description}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </>
  );
};

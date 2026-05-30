/**
 * WaffleButton Component
 * 9-dot grid icon button that opens the app launcher
 */

import React from 'react';
import { useAppLauncherStore } from '../../stores/appLauncherStore';

export const WaffleButton: React.FC = () => {
  const isLauncherOpen = useAppLauncherStore((state) => state.isLauncherOpen);
  const toggleLauncher = useAppLauncherStore((state) => state.toggleLauncher);

  return (
    <button
      className={`icon-button waffle-button ${isLauncherOpen ? 'active' : ''}`}
      onClick={toggleLauncher}
      aria-label="Open app launcher"
      aria-expanded={isLauncherOpen}
      aria-controls="app-launcher-panel"
      title="Open app launcher"
    >
      <div className="waffle-icon" aria-hidden="true">
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
        <div className="waffle-dot"></div>
      </div>
    </button>
  );
};

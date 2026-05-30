/**
 * Breadcrumb Navigation for Business Apps
 * Shows: Home > Business Apps > [Current Tab]
 */

import React from 'react';

interface BreadcrumbProps {
  currentTab: string;
}

export const Breadcrumb: React.FC<BreadcrumbProps> = ({ currentTab }) => {
  const tabNames: Record<string, string> = {
    core: 'Core',
    parts: 'Parts',
    service: 'Service',
    accounting: 'Accounting',
    crm: 'CRM',
    'api-testing': 'API Testing',
  };

  const handleHomeClick = () => {
    window.history.pushState(null, '', '/');
    window.location.hash = '';
    window.location.reload(); // Force reload to go to home
  };

  const handleBusinessAppsClick = () => {
    window.history.pushState(null, '', '/#business-apps/crm');
    window.location.hash = '#business-apps/crm';
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
      padding: '16px 24px',
      backgroundColor: 'var(--bg-secondary)',
      borderBottom: '1px solid var(--border-color)',
      fontSize: '14px',
      color: 'var(--text-secondary)'
    }}>
      {/* Home link */}
      <button
        onClick={handleHomeClick}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--accent-color)',
          cursor: 'pointer',
          fontSize: '14px',
          padding: '4px 8px',
          borderRadius: '4px',
          transition: 'background-color 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--hover-bg)'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        🏠 Home
      </button>

      {/* Separator */}
      <span style={{ color: 'var(--text-tertiary)' }}>›</span>

      {/* Business Apps link */}
      <button
        onClick={handleBusinessAppsClick}
        style={{
          background: 'none',
          border: 'none',
          color: 'var(--accent-color)',
          cursor: 'pointer',
          fontSize: '14px',
          padding: '4px 8px',
          borderRadius: '4px',
          transition: 'background-color 0.2s'
        }}
        onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'var(--hover-bg)'}
        onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
      >
        💼 Business Apps
      </button>

      {/* Separator */}
      <span style={{ color: 'var(--text-tertiary)' }}>›</span>

      {/* Current tab (not clickable) */}
      <span style={{
        color: 'var(--text-primary)',
        fontWeight: '600',
        padding: '4px 8px'
      }}>
        {tabNames[currentTab] || currentTab}
      </span>
    </div>
  );
};

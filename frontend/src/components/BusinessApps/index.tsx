/**
 * Business Apps - Main Component
 * Contains: Core, Parts, Service, Accounting, CRM tabs
 */

import React from 'react';
import { CoreTab } from './CoreTab';
import { PartsTab } from './PartsTab';
import { ServiceTab } from './ServiceTab';
import { AccountingTab } from './AccountingTab';
import { CRMTab } from './CRMTab';
import { APITestingTab } from './APITestingTab';
import { Breadcrumb } from './Breadcrumb';
import { LogsTab } from '../tabs/LogsTab';

interface BusinessAppsProps {
  activeTab: string;
  onTabChange: (tab: string) => void;
  addLog: (message: string) => void;
  clearLogs: () => void;
  addNotification: (notification: any) => void;
  logs?: string[];
  copyLogs?: () => void;
}

export const BusinessApps: React.FC<BusinessAppsProps> = ({ activeTab, onTabChange, addLog, clearLogs, addNotification, logs, copyLogs }) => {
  const [isSidebarCollapsed, setIsSidebarCollapsed] = React.useState(false);

  const tabs = [
    { id: 'core', name: 'Core', icon: '⚡' },
    { id: 'parts', name: 'Parts', icon: '🔧' },
    { id: 'service', name: 'Service', icon: '🛠️' },
    { id: 'accounting', name: 'Accounting', icon: '💰' },
    { id: 'crm', name: 'CRM', icon: '📞' },
    { id: 'api-testing', name: 'API Testing', icon: '🌐' },
  ];

  // Handle tab change with URL update
  const handleTabClick = (tabId: string) => {
    // Update the URL hash
    const newHash = `#business-apps/${tabId}`;
    window.history.pushState(null, '', `/${newHash}`);
    console.log(`🔗 Business Apps tab changed: ${newHash}`);

    // Call the parent's tab change handler
    onTabChange(tabId);
  };

  const handleToggleSidebar = () => {
    setIsSidebarCollapsed(!isSidebarCollapsed);
  };

  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      height: '100vh',
      overflow: 'hidden'
    }}>
      {/* Breadcrumb Navigation */}
      <Breadcrumb currentTab={activeTab} />

      {/* Main content area with sidebar */}
      <div style={{
        display: 'flex',
        flex: 1,
        overflow: 'hidden'
      }}>
        {/* Sidebar with tabs */}
        <aside style={{
        width: isSidebarCollapsed ? '60px' : '200px',
        backgroundColor: 'var(--bg-secondary)',
        borderRight: '1px solid var(--border-color)',
        display: 'flex',
        flexDirection: 'column',
        padding: '20px 0',
        transition: 'width 0.3s ease'
      }}>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          margin: '0 0 20px 0',
          padding: '0 20px'
        }}>
          {!isSidebarCollapsed && (
            <h3 style={{
              margin: 0,
              fontSize: '16px',
              fontWeight: '600',
              color: 'var(--text-primary)',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}>
              <span style={{ fontSize: '20px' }}>💼</span>
              Business Apps
            </h3>
          )}
          <button
            onClick={handleToggleSidebar}
            style={{
              background: 'transparent',
              border: 'none',
              padding: '6px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--text-secondary)',
              transition: 'all 0.2s ease',
              borderRadius: '6px',
              marginLeft: isSidebarCollapsed ? '0' : 'auto'
            }}
            title={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            aria-label={isSidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            onMouseEnter={(e) => {
              e.currentTarget.style.color = 'var(--text-primary)';
              e.currentTarget.style.backgroundColor = 'var(--hover-bg)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.color = 'var(--text-secondary)';
              e.currentTarget.style.backgroundColor = 'transparent';
            }}
          >
            <svg
              width="20"
              height="20"
              viewBox="0 0 20 20"
              fill="currentColor"
              xmlns="http://www.w3.org/2000/svg"
              style={{
                transition: 'transform 0.3s cubic-bezier(0.165, 0.85, 0.45, 1)',
                transform: isSidebarCollapsed ? 'scaleX(-1)' : 'scaleX(1)'
              }}
            >
              <path d="M16.5 4C17.3284 4 18 4.67157 18 5.5V14.5C18 15.3284 17.3284 16 16.5 16H3.5C2.67157 16 2 15.3284 2 14.5V5.5C2 4.67157 2.67157 4 3.5 4H16.5ZM7 15H16.5C16.7761 15 17 14.7761 17 14.5V5.5C17 5.22386 16.7761 5 16.5 5H7V15ZM3.5 5C3.22386 5 3 5.22386 3 5.5V14.5C3 14.7761 3.22386 15 3.5 15H6V5H3.5Z" />
            </svg>
          </button>
        </div>

        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => handleTabClick(tab.id)}
            title={isSidebarCollapsed ? tab.name : ''}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: isSidebarCollapsed ? 'center' : 'flex-start',
              gap: '12px',
              padding: isSidebarCollapsed ? '12px 8px' : '12px 20px',
              backgroundColor: activeTab === tab.id ? 'var(--accent-color)' : 'transparent',
              color: activeTab === tab.id ? 'white' : 'var(--text-primary)',
              border: 'none',
              borderLeft: activeTab === tab.id ? '4px solid var(--accent-color-dark)' : '4px solid transparent',
              cursor: 'pointer',
              fontSize: '14px',
              fontWeight: activeTab === tab.id ? '600' : '400',
              textAlign: 'left',
              transition: 'all 0.2s ease'
            }}
            onMouseEnter={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.backgroundColor = 'var(--hover-bg)';
              }
            }}
            onMouseLeave={(e) => {
              if (activeTab !== tab.id) {
                e.currentTarget.style.backgroundColor = 'transparent';
              }
            }}
          >
            <span style={{
              fontSize: isSidebarCollapsed ? '22px' : '18px',
              transition: 'font-size 0.3s ease'
            }} aria-hidden="true">
              {tab.icon}
            </span>
            {!isSidebarCollapsed && tab.name}
          </button>
        ))}
      </aside>

      {/* Main content area */}
      <main style={{
        flex: 1,
        overflow: 'auto',
        backgroundColor: 'var(--bg-primary)'
      }}>
        {activeTab === 'core' && <CoreTab addLog={addLog} clearLogs={clearLogs} />}
        {activeTab === 'parts' && <PartsTab addLog={addLog} />}
        {activeTab === 'service' && <ServiceTab />}
        {activeTab === 'accounting' && <AccountingTab />}
        {activeTab === 'crm' && <CRMTab addLog={addLog} clearLogs={clearLogs} />}
        {activeTab === 'api-testing' && <APITestingTab addNotification={addNotification} />}
        {activeTab === 'logs' && (
          <LogsTab
            logs={logs || []}
            copyLogs={copyLogs || (() => {})}
            clearLogs={clearLogs}
          />
        )}
      </main>
      </div>
    </div>
  );
};

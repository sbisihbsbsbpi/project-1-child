/**
 * CRM Tab - Customer Relationship Management Tools
 * Contains: Tekion Logo Removal & Logo Addition features
 */

import React from 'react';
import { TekionLogoRemoval } from './CRMTab/TekionLogoRemoval';
import { LogoAddition } from './CRMTab/LogoAddition';

interface CRMTabProps {
  addLog: (message: string) => void;
  clearLogs: () => void;
}

export const CRMTab: React.FC<CRMTabProps> = ({ addLog, clearLogs }) => {
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: '1fr 1fr',
      gap: '32px',
      padding: '20px',
      maxWidth: '1600px',
      margin: '0 auto'
    }}>
      {/* Logo Removal Section */}
      <div style={{
        backgroundColor: '#f9f5ff',
        borderRadius: '12px',
        padding: '24px',
        border: '2px solid #9C27B0'
      }}>
        <TekionLogoRemoval addLog={addLog} clearLogs={clearLogs} />
      </div>

      {/* Logo Addition Section */}
      <div style={{
        backgroundColor: '#fff5f5',
        borderRadius: '12px',
        padding: '24px',
        border: '2px solid #FF6B6B'
      }}>
        <LogoAddition addLog={addLog} clearLogs={clearLogs} />
      </div>
    </div>
  );
};

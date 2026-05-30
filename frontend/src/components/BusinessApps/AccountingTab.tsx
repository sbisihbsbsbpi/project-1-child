/**
 * Accounting Tab - Placeholder for Accounting features
 */

import React from 'react';

export const AccountingTab: React.FC = () => {
  return (
    <div style={{
      padding: '40px',
      textAlign: 'center',
      color: '#666'
    }}>
      <div style={{ fontSize: '64px', marginBottom: '24px' }}>
        💰
      </div>
      <h2 style={{ 
        margin: '0 0 16px 0',
        fontSize: '24px',
        color: '#333'
      }}>
        Accounting Tools
      </h2>
      <p style={{ 
        fontSize: '16px',
        color: '#999',
        maxWidth: '400px',
        margin: '0 auto'
      }}>
        Accounting features coming soon...
      </p>
    </div>
  );
};

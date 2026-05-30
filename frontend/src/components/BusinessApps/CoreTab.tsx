/**
 * Core Tab - Core Operations
 * Tile-based layout for core features with URL hash routing
 */

import React, { useState, useEffect } from 'react';
import { OemIdUpdate } from './CoreTab/OemIdUpdate';

interface CoreTabProps {
  addLog: (message: string) => void;
  clearLogs: () => void;
}

type CoreFeature = 'none' | 'oem-id-update';

export const CoreTab: React.FC<CoreTabProps> = ({ addLog, clearLogs }) => {
  const [activeFeature, setActiveFeature] = useState<CoreFeature>('none');

  // Initialize from URL hash on mount
  useEffect(() => {
    const initializeFromHash = () => {
      const hash = window.location.hash;
      // Check if hash contains core/feature-name pattern
      const match = hash.match(/#business-apps\/core\/([^\/]+)/);

      if (match) {
        const featureName = match[1];
        if (featureName === 'oem-id-update') {
          setActiveFeature('oem-id-update');
        }
      }
    };

    initializeFromHash();

    // Listen for hash changes (browser back/forward)
    const handleHashChange = () => {
      initializeFromHash();
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  // Handle feature selection with URL update
  const handleSelectFeature = (feature: CoreFeature) => {
    setActiveFeature(feature);

    if (feature === 'none') {
      // Return to core tab root
      window.location.hash = '#business-apps/core';
    } else {
      // Navigate to specific feature
      window.location.hash = `#business-apps/core/${feature}`;
    }
  };

  // Handle back to tiles view
  const handleBackToTiles = () => {
    handleSelectFeature('none');
  };

  // Render feature component based on selection
  if (activeFeature === 'oem-id-update') {
    return (
      <div>
        {/* Back button */}
        <div style={{
          padding: '16px 32px',
          backgroundColor: '#f5f5f5',
          borderBottom: '1px solid #ddd'
        }}>
          <button
            onClick={handleBackToTiles}
            style={{
              padding: '8px 16px',
              backgroundColor: '#FF9800',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              cursor: 'pointer',
              fontWeight: '600',
              fontSize: '14px',
              display: 'flex',
              alignItems: 'center',
              gap: '8px'
            }}
          >
            ← Back to Core Features
          </button>
        </div>
        <OemIdUpdate addLog={addLog} clearLogs={clearLogs} />
      </div>
    );
  }

  // Default: Show tiles view
  return (
    <div style={{
      padding: '24px 32px',
      maxWidth: '1200px',
      margin: '0 auto'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '24px',
        textAlign: 'center'
      }}>
        <div style={{ fontSize: '48px', marginBottom: '12px' }}>⚡</div>
        <h1 style={{
          margin: '0 0 6px 0',
          fontSize: '28px',
          color: '#FF9800'
        }}>
          Core Operations
        </h1>
        <p style={{
          margin: 0,
          fontSize: '14px',
          color: '#666'
        }}>
          Select a feature to get started
        </p>
      </div>

      {/* Feature Tiles Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
        gap: '16px',
        marginTop: '32px'
      }}>
        {/* OEM ID Update Tile */}
        <div
          onClick={() => handleSelectFeature('oem-id-update')}
          style={{
            padding: '20px',
            backgroundColor: 'white',
            border: '2px solid #FF9800',
            borderRadius: '8px',
            cursor: 'pointer',
            transition: 'all 0.2s',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(255, 152, 0, 0.2)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 2px 4px rgba(0,0,0,0.1)';
          }}
        >
          <div style={{ fontSize: '36px', marginBottom: '12px', textAlign: 'center' }}>
            🔑
          </div>
          <h3 style={{
            margin: '0 0 8px 0',
            fontSize: '16px',
            color: '#FF9800',
            textAlign: 'center',
            fontWeight: '600'
          }}>
            OEM ID Update
          </h3>
          <p style={{
            margin: '0 0 12px 0',
            fontSize: '13px',
            color: '#666',
            textAlign: 'center',
            lineHeight: '1.4'
          }}>
            Bulk update OEM IDs for user setup
          </p>
          <div style={{
            padding: '6px 8px',
            backgroundColor: '#FFF3E0',
            borderRadius: '4px',
            fontSize: '11px',
            color: '#E65100',
            textAlign: 'center',
            fontWeight: '600'
          }}>
            Ready
          </div>
        </div>

        {/* Placeholder Tile 1 - Coming Soon */}
        <div
          style={{
            padding: '20px',
            backgroundColor: '#f9f9f9',
            border: '2px dashed #ddd',
            borderRadius: '8px',
            cursor: 'not-allowed',
            opacity: 0.5
          }}
        >
          <div style={{ fontSize: '36px', marginBottom: '12px', textAlign: 'center' }}>
            🔧
          </div>
          <h3 style={{
            margin: '0 0 8px 0',
            fontSize: '16px',
            color: '#999',
            textAlign: 'center',
            fontWeight: '600'
          }}>
            Feature Name
          </h3>
          <p style={{
            margin: 0,
            fontSize: '13px',
            color: '#999',
            textAlign: 'center',
            lineHeight: '1.4'
          }}>
            Coming soon...
          </p>
        </div>

        {/* Placeholder Tile 2 - Coming Soon */}
        <div
          style={{
            padding: '20px',
            backgroundColor: '#f9f9f9',
            border: '2px dashed #ddd',
            borderRadius: '8px',
            cursor: 'not-allowed',
            opacity: 0.5
          }}
        >
          <div style={{ fontSize: '36px', marginBottom: '12px', textAlign: 'center' }}>
            ⚙️
          </div>
          <h3 style={{
            margin: '0 0 8px 0',
            fontSize: '16px',
            color: '#999',
            textAlign: 'center',
            fontWeight: '600'
          }}>
            Feature Name
          </h3>
          <p style={{
            margin: 0,
            fontSize: '13px',
            color: '#999',
            textAlign: 'center',
            lineHeight: '1.4'
          }}>
            Coming soon...
          </p>
        </div>
      </div>
    </div>
  );
};

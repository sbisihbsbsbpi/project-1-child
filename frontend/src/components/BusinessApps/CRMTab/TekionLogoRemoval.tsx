/**
 * Tekion Logo Removal Component
 * Handles bulk removal of "Powered by Tekion" logos from all templates
 * 
 * Extracted from Screenshots App Settings tab
 */

import React, { useState } from 'react';

interface TekionLogoRemovalProps {
  addLog: (message: string) => void;
  clearLogs: () => void;
}

export const TekionLogoRemoval: React.FC<TekionLogoRemovalProps> = ({ addLog, clearLogs }) => {
  // ========================================
  // STATE - Extracted from App.tsx lines 2618-2627
  // ========================================
  
  // Job tracking state
  const [removalJobId, setRemovalJobId] = useState<string | null>(null);
  const [removalProgress, setRemovalProgress] = useState<any>(null);
  const [removalStatus, setRemovalStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');

  // Settings modal state
  const [showLogoRemovalSettings, setShowLogoRemovalSettings] = useState(false);
  const [logoRemovalMaxRows, setLogoRemovalMaxRows] = useState<number>(200); // Default 200 rows
  const [logoRemovalCustomLimit, setLogoRemovalCustomLimit] = useState<string>(''); // Custom template limit (empty = all)
  const [keepTabsOpen, setKeepTabsOpen] = useState<boolean>(false); // Keep tabs open for verification

  // ========================================
  // HANDLERS - Extracted from App.tsx lines 2629-2730
  // ========================================

  // Handler for Tekion Logo Removal button click - show settings modal
  const handleTekionLogoRemovalClick = () => {
    setShowLogoRemovalSettings(true);
  };

  // Handler to start the actual logo removal process
  const startTekionLogoRemoval = async () => {
    // Close the settings modal
    setShowLogoRemovalSettings(false);

    // ✅ FIXED: Hardcoded preprod URL - no need to ask user
    const baseUrl = 'https://preprodapp.tekioncloud.com';

    try {
      console.log('🚀 Starting Tekion Logo Removal...');
      setRemovalStatus('running');

      // ✅ Clear old logs and start fresh
      clearLogs();
      addLog('🎨 ========================================');
      addLog('🎨 Tekion Logo Removal - Starting...');
      addLog('🎨 ========================================');
      addLog(`🌐 Base URL: ${baseUrl}`);
      addLog(`⚡ Connecting to backend...`);

      // Start the removal job with settings
      const customLimit = logoRemovalCustomLimit ? parseInt(logoRemovalCustomLimit) : undefined;

      const response = await fetch('http://localhost:8001/api/templates/start-logo-removal', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          base_url: baseUrl,
          max_rows: logoRemovalMaxRows,  // Max rows to fetch from API
          custom_limit: customLimit,  // Custom limit on how many to process
          keep_tabs_open: keepTabsOpen  // ✅ Keep tabs open for verification
        }),
      });

      const data = await response.json();
      const jobId = data.job_id;
      setRemovalJobId(jobId);

      console.log('✅ Job started:', jobId);
      addLog(`✅ Job started: ${jobId}`);

      // Connect to WebSocket for real-time updates
      const ws = new WebSocket(`ws://localhost:8001/ws/template-removal/${jobId}`);

      // Track which log index we've already displayed
      let lastLogIndex = 0;

      ws.onmessage = (event) => {
        const progress = JSON.parse(event.data);
        console.log('Progress update:', progress);
        setRemovalProgress(progress);

        // ✅ FIXED: Only display NEW logs (not already shown)
        if (progress.logs && Array.isArray(progress.logs)) {
          const newLogs = progress.logs.slice(lastLogIndex);
          newLogs.forEach((logMessage: string) => {
            // Remove the timestamp prefix from backend (we add our own)
            const cleanMessage = logMessage.replace(/^\[\d{2}:\d{2}:\d{2}\]\s*/, '');
            addLog(cleanMessage);
          });
          lastLogIndex = progress.logs.length;
        }

        if (progress.status === 'completed') {
          setRemovalStatus('completed');
          addLog(`✅ Logo removal complete! Successful: ${progress.successful}/${progress.total}, Failed: ${progress.failed}`);

          // ✅ Show Excel report download link if available
          if (progress.excel_report) {
            addLog(`📊 Excel report generated: ${progress.excel_report}`);
            addLog(`📥 Download: http://localhost:8000/reports/${progress.excel_report.split('/').pop()}`);
          }

          let alertMsg = `✅ Complete!\n\nSuccessfully processed: ${progress.successful}/${progress.total}\nFailed: ${progress.failed}/${progress.total}`;
          if (progress.excel_report) {
            alertMsg += `\n\n📊 Excel report available in backend/reports/`;
          }
          alert(alertMsg);
          ws.close();
        } else if (progress.status === 'failed') {
          setRemovalStatus('failed');
          addLog('❌ Logo removal job failed');
          alert('❌ Job failed. Check the Logs tab for details.');
          ws.close();
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setRemovalStatus('failed');
      };

      ws.onclose = () => {
        console.log('WebSocket connection closed');
      };

    } catch (error: any) {
      console.error('Failed to start logo removal:', error);
      setRemovalStatus('failed');
      addLog(`❌ Error: ${error.message}`);
      alert(`❌ Failed to start: ${error.message}`);
    }
  };

  // ========================================
  // RENDER - Extracted from App.tsx lines 7456-7750
  // ========================================

  return (
    <div style={{
      padding: '32px',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '32px',
        borderBottom: '2px solid #9C27B0',
        paddingBottom: '16px'
      }}>
        <h2 style={{
          margin: '0 0 8px 0',
          fontSize: '28px',
          color: '#9C27B0',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '32px' }}>🎨</span>
          Template Management
        </h2>
        <p style={{
          margin: 0,
          fontSize: '14px',
          color: '#666'
        }}>
          Bulk remove "Powered by Tekion" logos from email templates
        </p>
      </div>

      {/* Tekion Logo Removal Button */}
      <button
        onClick={handleTekionLogoRemovalClick}
        style={{
          width: '100%',
          padding: '16px 24px',
          backgroundColor: '#9C27B0',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '16px',
          fontWeight: '600',
          cursor: 'pointer',
          transition: 'all 0.3s ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          boxShadow: '0 2px 8px rgba(156, 39, 176, 0.2)'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.backgroundColor = '#7B1FA2';
          e.currentTarget.style.transform = 'translateY(-2px)';
          e.currentTarget.style.boxShadow = '0 4px 12px rgba(156, 39, 176, 0.3)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.backgroundColor = '#9C27B0';
          e.currentTarget.style.transform = 'translateY(0)';
          e.currentTarget.style.boxShadow = '0 2px 8px rgba(156, 39, 176, 0.2)';
        }}
      >
        <span style={{ fontSize: '20px' }}>🎨</span>
        Start Tekion Logo Removal
      </button>

      {/* Settings Modal - Extracted from App.tsx lines 7508-7718 */}
      {showLogoRemovalSettings && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '12px',
            padding: '32px',
            maxWidth: '500px',
            width: '90%',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)'
          }}>
            <h2 style={{
              margin: '0 0 24px 0',
              fontSize: '24px',
              color: '#9C27B0',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <span style={{ fontSize: '28px' }}>🎨</span>
              Tekion Logo Removal Settings
            </h2>

            <div style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#333'
              }}>
                📊 Maximum Rows to Fetch from API
              </label>
              <input
                type="number"
                value={logoRemovalMaxRows}
                onChange={(e) => setLogoRemovalMaxRows(parseInt(e.target.value) || 200)}
                min="1"
                max="500"
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '16px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '6px',
                  outline: 'none'
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#9C27B0'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#e0e0e0'}
              />
              <p style={{
                marginTop: '8px',
                fontSize: '12px',
                color: '#666'
              }}>
                Fetch up to this many templates from the API (1-500). Default: 200
              </p>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#333'
              }}>
                🎯 Process Custom Number of Templates (Optional)
              </label>
              <input
                type="number"
                placeholder="Leave empty to process all"
                value={logoRemovalCustomLimit}
                onChange={(e) => setLogoRemovalCustomLimit(e.target.value)}
                min="1"
                style={{
                  width: '100%',
                  padding: '12px',
                  fontSize: '16px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '6px',
                  outline: 'none'
                }}
                onFocus={(e) => e.currentTarget.style.borderColor = '#9C27B0'}
                onBlur={(e) => e.currentTarget.style.borderColor = '#e0e0e0'}
              />
              <p style={{
                marginTop: '8px',
                fontSize: '12px',
                color: '#666'
              }}>
                {logoRemovalCustomLimit
                  ? `Will process only the first ${logoRemovalCustomLimit} templates that match filters`
                  : "Leave empty to process ALL templates that match filters"}
              </p>
            </div>

            <div style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: 'pointer',
                padding: '12px',
                backgroundColor: keepTabsOpen ? '#E8F5E9' : '#f5f5f5',
                borderRadius: '6px',
                border: `2px solid ${keepTabsOpen ? '#4CAF50' : '#e0e0e0'}`,
                transition: 'all 0.3s'
              }}>
                <input
                  type="checkbox"
                  checked={keepTabsOpen}
                  onChange={(e) => setKeepTabsOpen(e.target.checked)}
                  style={{
                    width: '20px',
                    height: '20px',
                    cursor: 'pointer'
                  }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#333'
                  }}>
                    🔍 Keep Tabs Open for Verification
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#666',
                    marginTop: '4px'
                  }}>
                    {keepTabsOpen
                      ? "✅ Tabs will stay open - manually close after verifying"
                      : "❌ Tabs will close automatically after processing"}
                  </div>
                </div>
              </label>
            </div>

            <div style={{
              padding: '16px',
              backgroundColor: '#f5f5f5',
              borderRadius: '6px',
              marginBottom: '24px'
            }}>
              <p style={{ margin: '0 0 8px 0', fontSize: '14px' }}>
                <strong>ℹ️ What will happen:</strong>
              </p>
              <ul style={{ margin: '0', paddingLeft: '20px', fontSize: '13px', color: '#666' }}>
                <li>Fetch up to {logoRemovalMaxRows} templates from preprod API</li>
                <li>Filter for ACTIVE EMAIL templates with SALES dept</li>
                {logoRemovalCustomLimit && (
                  <li style={{ fontWeight: '600', color: '#9C27B0' }}>
                    🎯 Process only the first {logoRemovalCustomLimit} templates
                  </li>
                )}
                {!logoRemovalCustomLimit && (
                  <li>Process ALL templates that match the filters</li>
                )}
                <li>Remove "Powered by Tekion" logo from each</li>
                <li>Click Publish and save changes</li>
                <li>Generate Excel report with results</li>
              </ul>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowLogoRemovalSettings(false)}
                style={{
                  padding: '12px 24px',
                  fontSize: '14px',
                  fontWeight: '600',
                  backgroundColor: '#f5f5f5',
                  color: '#666',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                Cancel
              </button>
              <button
                onClick={startTekionLogoRemoval}
                style={{
                  padding: '12px 24px',
                  fontSize: '14px',
                  fontWeight: '600',
                  backgroundColor: '#9C27B0',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                🚀 Start Removal
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Progress Indicator - Extracted from App.tsx lines 7720-7750 */}
      {removalStatus === 'running' && removalProgress && (
        <div style={{
          marginTop: '24px',
          padding: '20px',
          backgroundColor: 'white',
          borderRadius: '8px',
          border: '2px solid #9C27B0',
          boxShadow: '0 2px 8px rgba(156, 39, 176, 0.1)'
        }}>
          <h4 style={{ margin: '0 0 16px 0', fontSize: '16px', color: '#9C27B0', fontWeight: '600' }}>
            🔄 Processing Templates...
          </h4>
          <div style={{
            marginBottom: '16px',
            fontSize: '14px',
            color: '#333'
          }}>
            <div><strong>Progress:</strong> {removalProgress.processed || 0} / {removalProgress.total || 0}</div>
            <div><strong>Successful:</strong> {removalProgress.successful || 0}</div>
            <div><strong>Failed:</strong> {removalProgress.failed || 0}</div>
            {removalProgress.current_template && (
              <div style={{ marginTop: '8px', color: '#666', fontSize: '12px' }}>
                Current: {removalProgress.current_template}
              </div>
            )}
          </div>
          <div style={{
            width: '100%',
            height: '8px',
            backgroundColor: '#e0e0e0',
            borderRadius: '4px',
            overflow: 'hidden'
          }}>
            <div style={{
              width: `${(removalProgress.processed / removalProgress.total) * 100}%`,
              height: '100%',
              backgroundColor: '#9C27B0',
              transition: 'width 0.3s ease'
            }} />
          </div>
        </div>
      )}
    </div>
  );
};

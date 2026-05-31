/**
 * Logo Addition Component
 * Handles bulk addition of custom logos to Tekion email templates
 */

import React, { useState } from 'react';

interface LogoAdditionProps {
  addLog: (message: string) => void;
  clearLogs: () => void;
}

export const LogoAddition: React.FC<LogoAdditionProps> = ({ addLog, clearLogs }) => {
  const [showSettings, setShowSettings] = useState(false);
  const [additionStatus, setAdditionStatus] = useState<'idle' | 'running' | 'completed' | 'failed'>('idle');
  const [jobId, setJobId] = useState<string | null>(null);
  const [browserConnected, setBrowserConnected] = useState(false);
  const [checkingBrowser, setCheckingBrowser] = useState(false);

  // Settings
  const [maxRows, setMaxRows] = useState('200');
  const [customLimit, setCustomLimit] = useState('');
  const [keepTabsOpen, setKeepTabsOpen] = useState(true);
  const [logoMediaId, setLogoMediaId] = useState(''); // User must provide their store's logo
  const [logoWidth, setLogoWidth] = useState('160');
  const [departments, setDepartments] = useState<string[]>(['Service', 'Parts']); // NEW: Department filtering
  const [autoPublish, setAutoPublish] = useState(true); // NEW: Auto-publish

  // Check CDP browser status on mount
  React.useEffect(() => {
    checkBrowserStatus();
  }, []);

  const checkBrowserStatus = async () => {
    try {
      setCheckingBrowser(true);
      const response = await fetch('http://localhost:8001/api/cdp-status');
      const data = await response.json();
      setBrowserConnected(data.is_listening);
      if (data.is_listening) {
        addLog('✅ Browser connected via CDP (port 9223)');
      }
    } catch (error) {
      console.error('Error checking browser status:', error);
      setBrowserConnected(false);
    } finally {
      setCheckingBrowser(false);
    }
  };

  const connectBrowser = async () => {
    try {
      setCheckingBrowser(true);
      addLog('🔌 Launching browser with CDP...');

      const response = await fetch('http://localhost:8001/api/launch-brave-cdp', {
        method: 'POST'
      });

      const data = await response.json();
      addLog(`🦁 ${data.message}`);

      // Wait a bit for browser to start, then check status
      setTimeout(async () => {
        await checkBrowserStatus();
      }, 2000);

    } catch (error: any) {
      console.error('Error connecting browser:', error);
      addLog(`❌ Failed to connect browser: ${error.message}`);
    } finally {
      setCheckingBrowser(false);
    }
  };

  const handleLogoAdditionClick = () => {
    if (!browserConnected) {
      alert('⚠️ Browser not connected!\n\nPlease click "🔌 Connect Browser" first to establish CDP connection on port 9223.');
      return;
    }
    setShowSettings(true);
  };

  const startLogoAddition = async () => {
    // Validate required fields
    if (!logoMediaId || logoMediaId.trim() === '') {
      alert('❌ Please enter your store\'s Logo Media ID before starting.\n\nFind it in: Media Library → Your Store Logo → Copy Media ID');
      return;
    }

    setShowSettings(false);

    const baseUrl = 'https://preprodapp.tekioncloud.com';

    try {
      console.log('✨ Starting Logo Addition...');
      setAdditionStatus('running');

      clearLogs();
      addLog('✨ ========================================');
      addLog('✨ Logo Addition - Starting...');
      addLog('✨ ========================================');
      addLog(`🌐 Base URL: ${baseUrl}`);
      addLog(`🖼️  Logo Media ID: ${logoMediaId}`);
      addLog(`⚡ Connecting to backend...`);

      const customLimitNum = customLimit ? parseInt(customLimit) : undefined;
      
      const response = await fetch('http://localhost:8001/api/templates/start-logo-addition', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          base_url: baseUrl,
          max_rows: parseInt(maxRows),
          custom_limit: customLimitNum,
          keep_tabs_open: keepTabsOpen,
          logo_media_id: logoMediaId,
          logo_width: parseInt(logoWidth),
          departments: departments,  // NEW: Send departments filter
          auto_publish: autoPublish  // NEW: Send auto-publish setting
        }),
      });
      
      const data = await response.json();
      const newJobId = data.job_id;
      setJobId(newJobId);
      
      console.log('✅ Job started:', newJobId);
      addLog(`✅ Job started: ${newJobId}`);
      
      // Connect to WebSocket for real-time updates
      const ws = new WebSocket(`ws://localhost:8001/ws/template-addition/${newJobId}`);
      
      let lastLogIndex = 0;
      
      ws.onmessage = (event) => {
        const update = JSON.parse(event.data);
        
        if (update.error) {
          addLog(`❌ Error: ${update.error}`);
          setAdditionStatus('failed');
          ws.close();
          return;
        }
        
        // Display new logs
        if (update.logs && update.logs.length > lastLogIndex) {
          const newLogs = update.logs.slice(lastLogIndex);
          newLogs.forEach((log: any) => {
            addLog(`[${log.timestamp}] ${log.message}`);
          });
          lastLogIndex = update.logs.length;
        }
        
        // Check if complete
        if (update.status === 'completed') {
          setAdditionStatus('completed');
          addLog('');
          addLog('🎉 ========================================');
          addLog('🎉 LOGO ADDITION COMPLETED SUCCESSFULLY!');
          addLog('🎉 ========================================');
          ws.close();
        } else if (update.status === 'failed') {
          setAdditionStatus('failed');
          addLog('❌ Logo addition failed');
          ws.close();
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        addLog('❌ Connection error');
        setAdditionStatus('failed');
      };
      
      ws.onclose = () => {
        console.log('WebSocket closed');
      };
      
    } catch (error: any) {
      console.error('Error starting logo addition:', error);
      addLog(`❌ Error: ${error.message}`);
      setAdditionStatus('failed');
    }
  };

  return (
    <div style={{
      padding: '32px',
      maxWidth: '800px',
      margin: '0 auto'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '32px',
        borderBottom: '2px solid #FF6B6B',
        paddingBottom: '16px'
      }}>
        <h2 style={{
          margin: '0 0 8px 0',
          fontSize: '28px',
          color: '#FF6B6B',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '32px' }}>✨</span>
          Logo Addition
        </h2>
        <p style={{
          margin: 0,
          fontSize: '14px',
          color: '#666'
        }}>
          Bulk add custom logos to email templates
        </p>
      </div>

      {/* Browser Connection Status */}
      <div style={{
        marginBottom: '20px',
        padding: '16px',
        backgroundColor: browserConnected ? '#e7f5e7' : '#fff3cd',
        border: `2px solid ${browserConnected ? '#4CAF50' : '#ff9800'}`,
        borderRadius: '8px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <span style={{ fontSize: '24px' }}>{browserConnected ? '✅' : '⚠️'}</span>
          <div>
            <div style={{ fontWeight: '600', fontSize: '14px', marginBottom: '4px' }}>
              {browserConnected ? 'Browser Connected' : 'Browser Not Connected'}
            </div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {browserConnected
                ? 'CDP connection active on port 9223'
                : 'Click "Connect Browser" to enable CDP on port 9223'}
            </div>
          </div>
        </div>
        {!browserConnected && (
          <button
            onClick={connectBrowser}
            disabled={checkingBrowser}
            style={{
              padding: '10px 16px',
              backgroundColor: '#2196F3',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              fontSize: '14px',
              fontWeight: '600',
              cursor: checkingBrowser ? 'not-allowed' : 'pointer',
              opacity: checkingBrowser ? 0.6 : 1,
              whiteSpace: 'nowrap'
            }}
          >
            {checkingBrowser ? '⏳ Connecting...' : '🔌 Connect Browser'}
          </button>
        )}
        {browserConnected && (
          <button
            onClick={checkBrowserStatus}
            disabled={checkingBrowser}
            style={{
              padding: '8px 14px',
              backgroundColor: '#f5f5f5',
              color: '#666',
              border: '1px solid #ddd',
              borderRadius: '6px',
              fontSize: '12px',
              fontWeight: '600',
              cursor: checkingBrowser ? 'not-allowed' : 'pointer'
            }}
          >
            {checkingBrowser ? '⏳' : '🔄'} Refresh
          </button>
        )}
      </div>

      {/* Main Action Button */}
      <button
        onClick={handleLogoAdditionClick}
        disabled={additionStatus === 'running' || !browserConnected}
        style={{
          width: '100%',
          padding: '16px 24px',
          backgroundColor: (additionStatus === 'running' || !browserConnected) ? '#ccc' : '#FF6B6B',
          color: 'white',
          border: 'none',
          borderRadius: '8px',
          fontSize: '16px',
          fontWeight: '600',
          cursor: (additionStatus === 'running' || !browserConnected) ? 'not-allowed' : 'pointer',
          transition: 'all 0.3s ease',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '12px',
          boxShadow: '0 2px 8px rgba(255, 107, 107, 0.2)'
        }}
        onMouseEnter={(e) => {
          if (additionStatus !== 'running' && browserConnected) {
            e.currentTarget.style.backgroundColor = '#EE5A6F';
            e.currentTarget.style.transform = 'translateY(-2px)';
            e.currentTarget.style.boxShadow = '0 4px 12px rgba(255, 107, 107, 0.3)';
          }
        }}
        onMouseLeave={(e) => {
          if (additionStatus !== 'running' && browserConnected) {
            e.currentTarget.style.backgroundColor = '#FF6B6B';
            e.currentTarget.style.transform = 'translateY(0)';
            e.currentTarget.style.boxShadow = '0 2px 8px rgba(255, 107, 107, 0.2)';
          }
        }}
      >
        <span style={{ fontSize: '20px' }}>✨</span>
        {additionStatus === 'running' ? 'Adding Logos...' : 'Start Logo Addition'}
      </button>

      {/* Settings Modal */}
      {showSettings && (
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
            maxHeight: '80vh',
            overflowY: 'auto',
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.2)'
          }}>
            <h2 style={{
              margin: '0 0 24px 0',
              fontSize: '24px',
              color: '#FF6B6B',
              display: 'flex',
              alignItems: 'center',
              gap: '12px'
            }}>
              <span style={{ fontSize: '28px' }}>✨</span>
              Logo Addition Settings
            </h2>

            {/* Department Filter */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#333'
              }}>
                Departments to Process
              </label>
              <div style={{
                display: 'flex',
                gap: '12px',
                padding: '12px',
                backgroundColor: '#f5f5f5',
                borderRadius: '6px'
              }}>
                {['Sales', 'Service', 'Parts'].map(dept => (
                  <label key={dept} style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '6px',
                    cursor: 'pointer'
                  }}>
                    <input
                      type="checkbox"
                      checked={departments.includes(dept)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setDepartments([...departments, dept]);
                        } else {
                          setDepartments(departments.filter(d => d !== dept));
                        }
                      }}
                      style={{
                        width: '18px',
                        height: '18px',
                        cursor: 'pointer'
                      }}
                    />
                    <span style={{ fontSize: '14px', color: '#333' }}>{dept}</span>
                  </label>
                ))}
              </div>
              <p style={{
                margin: '4px 0 0 0',
                fontSize: '12px',
                color: '#666'
              }}>
                Select which departments to process (default: Service & Parts)
              </p>
            </div>

            {/* Max Rows */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#333'
              }}>
                Max Rows to Fetch (from API)
              </label>
              <input
                type="number"
                value={maxRows}
                onChange={(e) => setMaxRows(e.target.value)}
                min="1"
                max="500"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
              <p style={{
                margin: '4px 0 0 0',
                fontSize: '12px',
                color: '#666'
              }}>
                Maximum number of templates to fetch from API (1-500)
              </p>
            </div>

            {/* Custom Limit */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#333'
              }}>
                Custom Processing Limit (Optional)
              </label>
              <input
                type="number"
                value={customLimit}
                onChange={(e) => setCustomLimit(e.target.value)}
                placeholder="Leave empty to process all"
                min="1"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
              <p style={{
                margin: '4px 0 0 0',
                fontSize: '12px',
                color: '#666'
              }}>
                Limit how many templates to process (leave empty for all)
              </p>
            </div>

            {/* Logo Media ID */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#d32f2f'
              }}>
                Logo Media ID (Required) <span style={{ color: '#d32f2f' }}>*</span>
              </label>
              <input
                type="text"
                value={logoMediaId}
                onChange={(e) => setLogoMediaId(e.target.value)}
                placeholder="Enter your store's logo Media ID..."
                required
                style={{
                  width: '100%',
                  padding: '10px',
                  border: logoMediaId ? '2px solid #4caf50' : '2px solid #ff9800',
                  borderRadius: '6px',
                  fontSize: '14px',
                  fontFamily: 'monospace',
                  backgroundColor: logoMediaId ? '#f1f8f4' : '#fff8e1'
                }}
              />
              <p style={{
                margin: '4px 0 0 0',
                fontSize: '12px',
                color: '#d32f2f',
                fontWeight: '500'
              }}>
                ⚠️ Required: Media ID of YOUR store's logo from Media Library
              </p>
              <p style={{
                margin: '4px 0 0 0',
                fontSize: '11px',
                color: '#666',
                fontStyle: 'italic'
              }}>
                📍 Find it: Media Library → Upload your logo → Copy the 24-character ID
              </p>
            </div>

            {/* Logo Width */}
            <div style={{ marginBottom: '20px' }}>
              <label style={{
                display: 'block',
                marginBottom: '8px',
                fontSize: '14px',
                fontWeight: '600',
                color: '#333'
              }}>
                Logo Width (px)
              </label>
              <input
                type="number"
                value={logoWidth}
                onChange={(e) => setLogoWidth(e.target.value)}
                min="50"
                max="500"
                style={{
                  width: '100%',
                  padding: '10px',
                  border: '2px solid #e0e0e0',
                  borderRadius: '6px',
                  fontSize: '14px'
                }}
              />
              <p style={{
                margin: '4px 0 0 0',
                fontSize: '12px',
                color: '#666'
              }}>
                Width of the logo in pixels (recommended: 160px)
              </p>
            </div>

            {/* Auto-Publish Toggle */}
            <div style={{ marginBottom: '16px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: 'pointer',
                padding: '12px',
                backgroundColor: autoPublish ? '#e8f5e9' : '#fff3e0',
                borderRadius: '6px',
                border: autoPublish ? '2px solid #4caf50' : '2px solid #ff9800'
              }}>
                <input
                  type="checkbox"
                  checked={autoPublish}
                  onChange={(e) => {
                    const newValue = e.target.checked;
                    setAutoPublish(newValue);
                    // When auto-publish is enabled, suggest closing tabs (user can override)
                    // When auto-publish is disabled, force tabs to stay open
                    if (!newValue) {
                      setKeepTabsOpen(true);
                    }
                  }}
                  style={{
                    width: '20px',
                    height: '20px',
                    cursor: 'pointer'
                  }}
                />
                <div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#333'
                  }}>
                    📤 Auto-Publish Templates (2-Click Workflow)
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#666'
                  }}>
                    {autoPublish
                      ? '✅ Will publish templates after adding logos'
                      : '⚠️ Templates will NOT be published - you must manually verify and publish'}
                  </div>
                </div>
              </label>
            </div>

            {/* Keep Tabs Open */}
            <div style={{ marginBottom: '24px' }}>
              <label style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                cursor: !autoPublish ? 'not-allowed' : 'pointer',
                padding: '12px',
                backgroundColor: keepTabsOpen ? '#e3f2fd' : '#f5f5f5',
                borderRadius: '6px',
                border: keepTabsOpen ? '2px solid #2196f3' : '2px solid transparent',
                opacity: !autoPublish ? 0.6 : 1
              }}>
                <input
                  type="checkbox"
                  checked={keepTabsOpen}
                  onChange={(e) => setKeepTabsOpen(e.target.checked)}
                  disabled={!autoPublish}
                  style={{
                    width: '20px',
                    height: '20px',
                    cursor: !autoPublish ? 'not-allowed' : 'pointer'
                  }}
                />
                <div>
                  <div style={{
                    fontSize: '14px',
                    fontWeight: '600',
                    color: '#333'
                  }}>
                    📂 Keep Tabs Open After Processing
                  </div>
                  <div style={{
                    fontSize: '12px',
                    color: '#666'
                  }}>
                    {!autoPublish
                      ? '🔒 Forced ON when auto-publish is disabled (for manual verification)'
                      : keepTabsOpen
                        ? '✅ Tabs will stay open for verification (even after publishing)'
                        : '❌ Tabs will close after publishing (recommended for bulk processing)'}
                  </div>
                </div>
              </label>
            </div>

            {/* Info Box */}
            <div style={{
              padding: '16px',
              backgroundColor: '#e8f5e9',
              border: '2px solid #4caf50',
              borderRadius: '8px',
              marginBottom: '24px'
            }}>
              <h4 style={{
                margin: '0 0 12px 0',
                fontSize: '14px',
                fontWeight: '600',
                color: '#2e7d32',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                ✨ FINAL VERSION - What this will do:
              </h4>
              <ul style={{
                margin: 0,
                paddingLeft: '20px',
                fontSize: '13px',
                color: '#333',
                lineHeight: '1.8'
              }}>
                <li><strong>Filter by departments:</strong> {departments.join(', ')}</li>
                <li><strong>4-layer logo detection:</strong> Warnings + Empty containers + Headers + Table-based</li>
                <li><strong>Smart replacement:</strong> Only replace logos WITH warnings (skip correct logos)</li>
                <li><strong>Logo insertion:</strong> Insert into empty Logo 1/2 containers & headers</li>
                <li><strong>Add headers:</strong> For templates without Logo 1/2 containers</li>
                <li><strong>Center align:</strong> All logos centered automatically</li>
                <li><strong>Resize logos:</strong> To {logoWidth}px width</li>
                <li><strong>Auto-publish:</strong> {autoPublish ? '✅ Enabled (2-click workflow)' : '❌ Disabled (manual verification required)'}</li>
                <li><strong>Tabs after processing:</strong> {
                  !autoPublish
                    ? '🔒 Kept open (forced - for manual verification & publishing)'
                    : keepTabsOpen
                      ? '📂 Kept open (for verification)'
                      : '✅ Closed automatically (bulk processing mode)'
                }</li>
                <li><strong>Excel report:</strong> Comprehensive statistics & detection log</li>
              </ul>
            </div>

            <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowSettings(false)}
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
                onClick={startLogoAddition}
                style={{
                  padding: '12px 24px',
                  fontSize: '14px',
                  fontWeight: '600',
                  backgroundColor: '#FF6B6B',
                  color: 'white',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer'
                }}
              >
                🚀 Start Addition
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

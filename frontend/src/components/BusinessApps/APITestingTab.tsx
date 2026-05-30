/**
 * API Testing Tab - Postman-like API testing tool
 * Supports: GET, POST, PUT, DELETE, PATCH, HEAD, OPTIONS
 * Features: Custom headers, request body, pre/post-request scripts
 */

import React, { useState } from 'react';
import { config } from '../../config';

interface APITestingTabProps {
  addNotification: (notification: any) => void;
}

interface HeaderRow {
  id: string;
  key: string;
  value: string;
  enabled: boolean;
}

// Whitelist of 29 Required Headers for Tekion API
// Only these headers will be accepted when users paste/add headers
const ALLOWED_HEADERS = [
  'accept',
  'accept-language',
  'applicationid',
  'clientid',
  'content-type',
  'dealerid',
  'dnt',
  'flattenedaecprogramsmap',
  'locale',
  'origin',
  'original-tenantid',
  'original-userid',
  'priority',
  'productids',
  'program',
  'roleid',
  'sec-ch-ua',
  'sec-ch-ua-mobile',
  'sec-ch-ua-platform',
  'sec-fetch-dest',
  'sec-fetch-mode',
  'sec-fetch-site',
  'subapplicationid',
  'tek-siteid',
  'tekion-api-token',
  'tenantname',
  'user-agent',
  'userid'
];

// Helper function to check if a header is allowed
const isAllowedHeader = (headerKey: string): boolean => {
  return ALLOWED_HEADERS.includes(headerKey.toLowerCase());
};

export const APITestingTab: React.FC<APITestingTabProps> = ({ addNotification }) => {
  // Request state
  const [method, setMethod] = useState<string>('GET');
  const [url, setUrl] = useState<string>('');
  const [headers, setHeaders] = useState<HeaderRow[]>([
    { id: '1', key: 'Content-Type', value: 'application/json', enabled: true }
  ]);
  const [body, setBody] = useState<string>('');
  const [preRequestScript, setPreRequestScript] = useState<string>('');
  const [postResponseScript, setPostResponseScript] = useState<string>('');
  
  // Response state
  const [response, setResponse] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  
  // UI state
  const [activeTab, setActiveTab] = useState<'headers' | 'body' | 'pre-script' | 'post-script'>('headers');
  const [responseTab, setResponseTab] = useState<'body' | 'headers'>('body');
  const [headerBulkEdit, setHeaderBulkEdit] = useState<boolean>(false);
  const [headerBulkText, setHeaderBulkText] = useState<string>('');

  const HTTP_METHODS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];

  // Add new header row
  const addHeader = () => {
    setHeaders([...headers, { id: Date.now().toString(), key: '', value: '', enabled: true }]);
  };

  // Update header with validation
  const updateHeader = (id: string, field: 'key' | 'value' | 'enabled', value: string | boolean) => {
    // If updating the key field, validate it's in the allowed list
    if (field === 'key' && typeof value === 'string' && value.trim()) {
      if (!isAllowedHeader(value.trim())) {
        addNotification({
          type: 'error',
          title: '❌ Invalid Header',
          message: `Header "${value}" is not in the allowed list. Only the ${ALLOWED_HEADERS.length} required Tekion API headers can be used.`,
          duration: 4000
        });
        return;
      }
    }
    setHeaders(headers.map(h => h.id === id ? { ...h, [field]: value } : h));
  };

  // Delete header
  const deleteHeader = (id: string) => {
    setHeaders(headers.filter(h => h.id !== id));
  };

  // Convert headers to bulk edit format
  const headersToBulkText = () => {
    return headers
      .filter(h => h.enabled && h.key)
      .map(h => `${h.key}: ${h.value}`)
      .join('\n');
  };

  /**
   * Smart header parser - extracts and filters headers from raw API data
   * Handles: Browser DevTools format, curl commands, Postman exports, mixed content
   * Filters: Only keeps the 29 allowed headers, ignores noise and unwanted headers
   *
   * Supported formats:
   * 1. DevTools: "accept: application/json"
   * 2. curl: -H 'accept: application/json'
   * 3. curl with continuations: curl 'url' \
   *                              -H 'header: value' \
   *                              --data-raw '{...}'
   */
  const parseAndFilterHeaders = (rawInput: string): { filtered: HeaderRow[]; totalParsed: number; filteredOut: number } => {
    const filtered: HeaderRow[] = [];
    let totalParsed = 0;

    // Step 1: Detect curl command format and extract headers using regex
    // Join line continuations first
    const joinedInput = rawInput.replace(/\\\s*\n\s*/g, ' ');

    // Check if it's a curl command (starts with 'curl' after joining)
    if (joinedInput.trim().startsWith('curl ')) {
      // Extract all -H or --header flags using regex
      // Matches: -H 'header: value' or -H "header: value" or --header 'header: value'
      const headerPattern = /(?:-H|--header)\s+(['"])((?:(?!\1).)*)\1/g;
      let match;

      while ((match = headerPattern.exec(joinedInput)) !== null) {
        const headerLine = match[2]; // The content between quotes
        const colonIndex = headerLine.indexOf(':');

        if (colonIndex > 0) {
          const key = headerLine.substring(0, colonIndex).trim();
          const value = headerLine.substring(colonIndex + 1).trim();

          if (key && value) {
            totalParsed++;
            if (isAllowedHeader(key)) {
              filtered.push({
                id: Date.now().toString() + filtered.length,
                key: key,
                value: value,
                enabled: true
              });
            }
          }
        }
      }

      const filteredOut = totalParsed - filtered.length;
      return { filtered, totalParsed, filteredOut };
    }

    // Step 2: Fall back to line-by-line parsing for DevTools/Postman format
    const lines = rawInput.split('\n');

    for (let line of lines) {
      let trimmedLine = line.trim();

      // Skip empty lines
      if (!trimmedLine) continue;

      // Skip curl command line itself
      if (trimmedLine.startsWith('curl ')) continue;

      // Skip HTTP method flag (-X)
      if (trimmedLine.match(/^-X\s+['"]?(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)/i)) continue;
      if (trimmedLine.match(/^--request\s+/i)) continue;

      // Skip cookie flags (-b, --cookie)
      if (trimmedLine.startsWith('-b ')) continue;
      if (trimmedLine.startsWith('--cookie ')) continue;

      // Skip body/data flags
      if (trimmedLine.match(/^--data-raw\s+/)) continue;
      if (trimmedLine.match(/^--data-binary\s+/)) continue;
      if (trimmedLine.match(/^--data-urlencode\s+/)) continue;
      if (trimmedLine.match(/^--data\s+/)) continue;
      if (trimmedLine.match(/^-d\s+/)) continue;

      // Skip form upload flags
      if (trimmedLine.match(/^-F\s+/)) continue;
      if (trimmedLine.match(/^--form\s+/)) continue;

      // Skip output flags
      if (trimmedLine.match(/^-o\s+/)) continue;
      if (trimmedLine.match(/^--output\s+/)) continue;
      if (trimmedLine.match(/^-O($|\s)/)) continue;

      // Skip other common curl flags
      if (trimmedLine.match(/^(-v|--verbose|--compressed|--location|-L|-i|--include|-s|--silent)($|\s)/)) continue;

      // Skip DevTools noise
      if (
        trimmedLine.toLowerCase().startsWith('general') ||
        trimmedLine.toLowerCase().startsWith('request url:') ||
        trimmedLine.toLowerCase().startsWith('request method:') ||
        trimmedLine.toLowerCase().startsWith('status code:') ||
        trimmedLine.toLowerCase().startsWith('remote address:') ||
        trimmedLine.toLowerCase().startsWith('referrer policy:') ||
        trimmedLine.toLowerCase().startsWith('request headers') ||
        trimmedLine.toLowerCase().startsWith('response headers') ||
        trimmedLine.startsWith('{') ||  // JSON body start
        trimmedLine.startsWith('[') ||  // JSON array start
        trimmedLine.startsWith('}') ||  // JSON body end
        trimmedLine.startsWith(']')     // JSON array end
      ) {
        continue;
      }

      // Step 3: Handle curl -H or --header format
      if (trimmedLine.startsWith('-H ') || trimmedLine.startsWith('--header ')) {
        // Remove -H or --header prefix
        const prefix = trimmedLine.startsWith('-H ') ? '-H ' : '--header ';
        trimmedLine = trimmedLine.substring(prefix.length).trim();

        // Remove surrounding quotes (single or double)
        if ((trimmedLine.startsWith("'") && trimmedLine.endsWith("'")) ||
            (trimmedLine.startsWith('"') && trimmedLine.endsWith('"'))) {
          trimmedLine = trimmedLine.substring(1, trimmedLine.length - 1);
        }
      }

      // Step 4: Parse as header (key: value)
      const colonIndex = trimmedLine.indexOf(':');
      if (colonIndex === -1 || colonIndex === 0) continue;

      const key = trimmedLine.substring(0, colonIndex).trim();
      const value = trimmedLine.substring(colonIndex + 1).trim();

      // Skip if key is empty or value is empty
      if (!key || !value) continue;

      // Count as parsed
      totalParsed++;

      // Step 5: Filter - only keep allowed headers (case-insensitive check)
      if (isAllowedHeader(key)) {
        filtered.push({
          id: Date.now().toString() + filtered.length,
          key: key,
          value: value,
          enabled: true
        });
      }
    }

    const filteredOut = totalParsed - filtered.length;
    return { filtered, totalParsed, filteredOut };
  };

  // Parse bulk edit text to headers with smart filtering
  const bulkTextToHeaders = () => {
    const { filtered: newHeaders, totalParsed, filteredOut } = parseAndFilterHeaders(headerBulkText);

    if (newHeaders.length === 0) {
      addNotification({
        type: 'error',
        title: '❌ No Valid Headers Found',
        message: 'Supported formats:\n\n1. DevTools: accept: application/json\n2. curl: -H \'accept: application/json\'\n3. Postman: key: value\n\nPaste any format and headers will be auto-extracted!',
        duration: 5000
      });
      return;
    }

    setHeaders(newHeaders);
    setHeaderBulkEdit(false);

    // Show success notification with filtering info
    if (filteredOut > 0) {
      addNotification({
        type: 'success',
        title: '✅ Headers Applied',
        message: `Applied ${newHeaders.length} headers (filtered out ${filteredOut} non-allowed headers)`,
        duration: 4000
      });
    } else {
      addNotification({
        type: 'success',
        title: '✅ Headers Applied',
        message: `Applied ${newHeaders.length} headers`,
        duration: 3000
      });
    }
  };

  // Send API request
  const sendRequest = async () => {
    if (!url.trim()) {
      addNotification({
        type: 'error',
        title: '❌ URL Required',
        message: 'Please enter a URL',
        duration: 3000
      });
      return;
    }

    setLoading(true);
    setResponse(null);

    try {
      // Build headers object (only enabled headers with keys)
      const requestHeaders: Record<string, string> = {};
      headers.forEach(h => {
        if (h.enabled && h.key.trim()) {
          requestHeaders[h.key] = h.value;
        }
      });

      // Execute pre-request script
      let processedBody = body;
      if (preRequestScript.trim()) {
        try {
          processedBody = executePrerequestScript(preRequestScript, body, requestHeaders);
        } catch (scriptError: any) {
          addNotification({
            type: 'warning',
            title: '⚠️ Pre-request Script Error',
            message: scriptError.message,
            duration: 5000
          });
        }
      }

      // Call backend proxy
      const response = await fetch(`${config.apiBaseUrl}/api/proxy-request`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url.trim(),
          method: method,
          headers: requestHeaders,
          body: processedBody || null,
          timeout: 30
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      setResponse(result);

      // Execute post-response script
      if (postResponseScript.trim()) {
        try {
          executePostresponseScript(postResponseScript, result);
        } catch (scriptError: any) {
          addNotification({
            type: 'warning',
            title: '⚠️ Post-response Script Error',
            message: scriptError.message,
            duration: 5000
          });
        }
      }

      addNotification({
        type: result.status >= 200 && result.status < 300 ? 'success' : 'warning',
        title: `${result.status} ${result.status_text}`,
        message: `Completed in ${result.time}ms`,
        duration: 5000
      });

    } catch (error: any) {
      addNotification({
        type: 'error',
        title: '❌ Request Failed',
        message: error.message || 'Unknown error',
        duration: 5000
      });
    } finally {
      setLoading(false);
    }
  };

  // Execute pre-request script
  const executePrerequestScript = (script: string, currentBody: string, currentHeaders: Record<string, string>): string => {
    const pm = {
      request: {
        url,
        method,
        headers: currentHeaders,
        body: currentBody
      },
      variables: {} as Record<string, any>,
      setVariable: function(key: string, value: any) {
        this.variables[key] = value;
      },
      getVariable: function(key: string) {
        return this.variables[key];
      }
    };

    // Execute script in sandbox
    const fn = new Function('pm', script);
    fn(pm);

    // Return potentially modified body
    return pm.request.body;
  };

  // Execute post-response script
  const executePostresponseScript = (script: string, responseData: any): void => {
    const pm = {
      response: responseData,
      variables: {} as Record<string, any>,
      setVariable: function(key: string, value: any) {
        this.variables[key] = value;
      },
      getVariable: function(key: string) {
        return this.variables[key];
      },
      test: function(name: string, fn: () => boolean) {
        console.log(`Test "${name}":`, fn() ? 'PASS' : 'FAIL');
      }
    };

    // Execute script in sandbox
    const fn = new Function('pm', script);
    fn(pm);
  };

  return (
    <div className="api-testing-container" style={{ padding: '20px' }}>
      <h2 style={{ marginTop: 0 }}>🌐 API Testing</h2>
      <p style={{ color: '#888', marginBottom: '20px' }}>
        Test any API with custom headers, body, and scripts. No CORS restrictions!
      </p>

      {/* Request Builder */}
      <div className="api-request-builder" style={{ marginBottom: '30px' }}>
        <div style={{ display: 'flex', gap: '10px', marginBottom: '15px' }}>
          <select
            value={method}
            onChange={(e) => setMethod(e.target.value)}
            style={{
              padding: '10px',
              fontSize: '14px',
              borderRadius: '4px',
              border: '1px solid #444',
              backgroundColor: '#2a2a2a',
              color: '#fff',
              minWidth: '120px'
            }}
          >
            {HTTP_METHODS.map(m => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>

          <input
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://api.example.com/endpoint"
            style={{
              flex: 1,
              padding: '10px',
              fontSize: '14px',
              borderRadius: '4px',
              border: '1px solid #444',
              backgroundColor: '#2a2a2a',
              color: '#fff'
            }}
          />

          <button
            onClick={sendRequest}
            disabled={loading || !url.trim()}
            style={{
              padding: '10px 30px',
              fontSize: '14px',
              fontWeight: 'bold',
              borderRadius: '4px',
              border: 'none',
              backgroundColor: loading ? '#555' : '#4a9eff',
              color: '#fff',
              cursor: loading || !url.trim() ? 'not-allowed' : 'pointer',
              minWidth: '100px'
            }}
          >
            {loading ? '⏳ Sending...' : '🚀 Send'}
          </button>
        </div>

        {/* Request Tabs */}
        <div style={{ marginBottom: '15px', borderBottom: '1px solid #444' }}>
          <div style={{ display: 'flex', gap: '5px' }}>
            {(['headers', 'body', 'pre-script', 'post-script'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                style={{
                  padding: '10px 20px',
                  border: 'none',
                  backgroundColor: activeTab === tab ? '#3a3a3a' : 'transparent',
                  color: activeTab === tab ? '#4a9eff' : '#888',
                  borderBottom: activeTab === tab ? '2px solid #4a9eff' : 'none',
                  cursor: 'pointer',
                  fontWeight: activeTab === tab ? 'bold' : 'normal'
                }}
              >
                {tab === 'headers' ? '📋 Headers' :
                 tab === 'body' ? '📝 Body' :
                 tab === 'pre-script' ? '⚙️ Pre-request' :
                 '🔍 Post-response'}
              </button>
            ))}
          </div>
        </div>

        {/* Request Tab Content */}
        <div style={{ backgroundColor: '#2a2a2a', padding: '15px', borderRadius: '4px', minHeight: '200px' }}>

          {/* Headers Tab */}
          {activeTab === 'headers' && (
            <div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '10px' }}>
                <h4 style={{ margin: 0 }}>Request Headers</h4>
                <div style={{ display: 'flex', gap: '10px' }}>
                  <button
                    onClick={() => {
                      if (headerBulkEdit) {
                        bulkTextToHeaders();
                      } else {
                        setHeaderBulkText(headersToBulkText());
                        setHeaderBulkEdit(true);
                      }
                    }}
                    style={{
                      padding: '5px 15px',
                      fontSize: '12px',
                      borderRadius: '4px',
                      border: '1px solid #4a9eff',
                      backgroundColor: 'transparent',
                      color: '#4a9eff',
                      cursor: 'pointer'
                    }}
                  >
                    {headerBulkEdit ? '✅ Apply Bulk Edit' : '📝 Bulk Edit'}
                  </button>
                  <button
                    onClick={addHeader}
                    style={{
                      padding: '5px 15px',
                      fontSize: '12px',
                      borderRadius: '4px',
                      border: '1px solid #4a9eff',
                      backgroundColor: 'transparent',
                      color: '#4a9eff',
                      cursor: 'pointer'
                    }}
                  >
                    ➕ Add Header
                  </button>
                </div>
              </div>

              {headerBulkEdit ? (
                <textarea
                  value={headerBulkText}
                  onChange={(e) => setHeaderBulkText(e.target.value)}
                  placeholder="Content-Type: application/json&#10;Authorization: Bearer token&#10;X-Custom-Header: value"
                  rows={10}
                  style={{
                    width: '100%',
                    padding: '10px',
                    fontFamily: 'monospace',
                    fontSize: '13px',
                    backgroundColor: '#1a1a1a',
                    color: '#fff',
                    border: '1px solid #444',
                    borderRadius: '4px',
                    resize: 'vertical'
                  }}
                />
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {headers.map(header => (
                    <div key={header.id} style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                      <input
                        type="checkbox"
                        checked={header.enabled}
                        onChange={(e) => updateHeader(header.id, 'enabled', e.target.checked)}
                        style={{ width: '20px', height: '20px' }}
                      />
                      <input
                        type="text"
                        value={header.key}
                        onChange={(e) => updateHeader(header.id, 'key', e.target.value)}
                        placeholder="Header name"
                        style={{
                          flex: 1,
                          padding: '8px',
                          backgroundColor: '#1a1a1a',
                          color: '#fff',
                          border: '1px solid #444',
                          borderRadius: '4px'
                        }}
                      />
                      <input
                        type="text"
                        value={header.value}
                        onChange={(e) => updateHeader(header.id, 'value', e.target.value)}
                        placeholder="Value"
                        style={{
                          flex: 2,
                          padding: '8px',
                          backgroundColor: '#1a1a1a',
                          color: '#fff',
                          border: '1px solid #444',
                          borderRadius: '4px'
                        }}
                      />
                      <button
                        onClick={() => deleteHeader(header.id)}
                        style={{
                          padding: '8px 12px',
                          backgroundColor: '#ff4444',
                          color: '#fff',
                          border: 'none',
                          borderRadius: '4px',
                          cursor: 'pointer'
                        }}
                      >
                        🗑️
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Body Tab */}
          {activeTab === 'body' && (
            <div>
              <h4 style={{ marginTop: 0 }}>Request Body</h4>
              <textarea
                value={body}
                onChange={(e) => setBody(e.target.value)}
                placeholder='{"key": "value"}'
                rows={12}
                style={{
                  width: '100%',
                  padding: '10px',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  backgroundColor: '#1a1a1a',
                  color: '#fff',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  resize: 'vertical'
                }}
              />
            </div>
          )}

          {/* Pre-request Script Tab */}
          {activeTab === 'pre-script' && (
            <div>
              <h4 style={{ marginTop: 0 }}>Pre-request Script</h4>
              <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>
                Executed before the request. Use <code>pm.request</code> to access/modify request data.
              </p>
              <textarea
                value={preRequestScript}
                onChange={(e) => setPreRequestScript(e.target.value)}
                placeholder={'// Example:\n// pm.request.headers[\'X-Timestamp\'] = Date.now();\n// pm.request.body = JSON.stringify({...JSON.parse(pm.request.body), extra: "field"});'}
                rows={12}
                style={{
                  width: '100%',
                  padding: '10px',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  backgroundColor: '#1a1a1a',
                  color: '#fff',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  resize: 'vertical'
                }}
              />
            </div>
          )}

          {/* Post-response Script Tab */}
          {activeTab === 'post-script' && (
            <div>
              <h4 style={{ marginTop: 0 }}>Post-response Script</h4>
              <p style={{ fontSize: '12px', color: '#888', marginBottom: '10px' }}>
                Executed after receiving response. Use <code>pm.response</code> and <code>pm.test()</code>.
              </p>
              <textarea
                value={postResponseScript}
                onChange={(e) => setPostResponseScript(e.target.value)}
                placeholder={'// Example:\n// pm.test("Status is 200", () => pm.response.status === 200);\n// pm.test("Has data", () => pm.response.json && pm.response.json.data);'}
                rows={12}
                style={{
                  width: '100%',
                  padding: '10px',
                  fontFamily: 'monospace',
                  fontSize: '13px',
                  backgroundColor: '#1a1a1a',
                  color: '#fff',
                  border: '1px solid #444',
                  borderRadius: '4px',
                  resize: 'vertical'
                }}
              />
            </div>
          )}
        </div>
      </div>

      {/* Response Viewer */}
      {response && (
        <div className="api-response-viewer">
          <h3 style={{ marginBottom: '15px' }}>Response</h3>

          {/* Response Summary */}
          <div style={{
            display: 'flex',
            gap: '20px',
            padding: '15px',
            backgroundColor: '#2a2a2a',
            borderRadius: '4px',
            marginBottom: '15px'
          }}>
            <div>
              <span style={{ color: '#888' }}>Status: </span>
              <span style={{
                fontWeight: 'bold',
                color: response.status >= 200 && response.status < 300 ? '#4ade80' :
                       response.status >= 400 ? '#f87171' : '#facc15'
              }}>
                {response.status} {response.status_text}
              </span>
            </div>
            <div>
              <span style={{ color: '#888' }}>Time: </span>
              <span style={{ fontWeight: 'bold' }}>{response.time}ms</span>
            </div>
            <div>
              <span style={{ color: '#888' }}>Size: </span>
              <span style={{ fontWeight: 'bold' }}>
                {response.size > 1024 * 1024
                  ? `${(response.size / (1024 * 1024)).toFixed(2)} MB`
                  : response.size > 1024
                  ? `${(response.size / 1024).toFixed(2)} KB`
                  : `${response.size} B`}
              </span>
            </div>
          </div>

          {/* Response Tabs */}
          <div style={{ marginBottom: '15px', borderBottom: '1px solid #444' }}>
            <div style={{ display: 'flex', gap: '5px' }}>
              {(['body', 'headers'] as const).map(tab => (
                <button
                  key={tab}
                  onClick={() => setResponseTab(tab)}
                  style={{
                    padding: '10px 20px',
                    border: 'none',
                    backgroundColor: responseTab === tab ? '#3a3a3a' : 'transparent',
                    color: responseTab === tab ? '#4a9eff' : '#888',
                    borderBottom: responseTab === tab ? '2px solid #4a9eff' : 'none',
                    cursor: 'pointer',
                    fontWeight: responseTab === tab ? 'bold' : 'normal'
                  }}
                >
                  {tab === 'body' ? '📄 Body' : '📋 Headers'}
                </button>
              ))}
            </div>
          </div>

          {/* Response Content */}
          <div style={{ backgroundColor: '#2a2a2a', padding: '15px', borderRadius: '4px' }}>
            {responseTab === 'body' && (
              <pre style={{
                margin: 0,
                padding: '15px',
                backgroundColor: '#1a1a1a',
                color: '#fff',
                borderRadius: '4px',
                overflowX: 'auto',
                maxHeight: '500px',
                overflowY: 'auto',
                fontFamily: 'monospace',
                fontSize: '13px',
                lineHeight: '1.5'
              }}>
                {response.json
                  ? JSON.stringify(response.json, null, 2)
                  : response.body}
              </pre>
            )}

            {responseTab === 'headers' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {Object.entries(response.headers).map(([key, value]) => (
                  <div key={key} style={{
                    display: 'flex',
                    gap: '10px',
                    padding: '8px',
                    backgroundColor: '#1a1a1a',
                    borderRadius: '4px'
                  }}>
                    <span style={{ fontWeight: 'bold', color: '#4a9eff', minWidth: '200px' }}>{key}:</span>
                    <span style={{ color: '#aaa', wordBreak: 'break-all' }}>{value as string}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* No Response Yet */}
      {!response && !loading && (
        <div style={{
          padding: '40px',
          textAlign: 'center',
          color: '#666',
          backgroundColor: '#2a2a2a',
          borderRadius: '4px'
        }}>
          <div style={{ fontSize: '48px', marginBottom: '10px' }}>🚀</div>
          <div>Enter a URL and click Send to test an API</div>
        </div>
      )}
    </div>
  );
};

/**
 * OEM ID Update Component
 * Bulk update OEM IDs for users in Tekion
 */

import React, { useState } from 'react';
import {
  OemUpdateHeaders,
  OemUpdateRow,
  OemTemplate,
  BatchProgress,
  TekionUser,
  ParsedCsvData
} from './types';
import {
  parseHeadersAuto,
  validateHeaders,
  formatHeadersForDisplay
} from './CurlParser';
import {
  parseCsvContent,
  readFileAsText,
  validateCsvData,
  extractUpdateRows
} from './CsvParser';

interface OemIdUpdateProps {
  addLog: (message: string) => void;
  clearLogs: () => void;
}

export const OemIdUpdate: React.FC<OemIdUpdateProps> = ({ addLog, clearLogs }) => {
  // ========================================
  // STATE
  // ========================================
  
  // Step 1: Headers
  const [headersInput, setHeadersInput] = useState('');
  const [extractedHeaders, setExtractedHeaders] = useState<Partial<OemUpdateHeaders> | null>(null);
  const [headersValid, setHeadersValid] = useState(false);
  
  // Step 2: CSV Upload
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [parsedCsv, setParsedCsv] = useState<ParsedCsvData | null>(null);
  const [csvValid, setCsvValid] = useState(false);
  
  // Step 3: Batch Processing
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState<BatchProgress>({
    total: 0,
    processed: 0,
    success: 0,
    failed: 0,
    created: 0,
    existing: 0,
    logs: []
  });
  
  const [updateRows, setUpdateRows] = useState<OemUpdateRow[]>([]);
  
  // ========================================
  // STEP 1: HEADER DETECTION
  // ========================================
  
  const handleDetectHeaders = () => {
    try {
      const headers = parseHeadersAuto(headersInput);
      const validation = validateHeaders(headers);
      
      if (!validation.valid) {
        const errorMsg = [
          ...validation.missing.map(m => `Missing required header: ${m}`),
          ...validation.errors
        ].join('\n');
        
        alert(`❌ Header validation failed:\n\n${errorMsg}`);
        setExtractedHeaders(null);
        setHeadersValid(false);
        return;
      }
      
      setExtractedHeaders(headers as OemUpdateHeaders);
      setHeadersValid(true);
      
      addLog('✅ Headers detected and validated');
      addLog(`   Dealer ID: ${headers.dealerid}`);
      addLog(`   Tenant: ${headers.tenantname || 'N/A'}`);
      
    } catch (error: any) {
      alert(`❌ Failed to parse headers: ${error.message}`);
      setExtractedHeaders(null);
      setHeadersValid(false);
    }
  };
  
  // ========================================
  // STEP 2: FILE UPLOAD
  // ========================================
  
  const handleFileSelect = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    try {
      setSelectedFile(file);
      addLog(`📄 Reading file: ${file.name}`);
      
      const content = await readFileAsText(file);
      const parsed = parseCsvContent(content);
      const validation = validateCsvData(parsed);
      
      if (!validation.valid) {
        alert(`❌ CSV validation failed:\n\n${validation.errors.join('\n')}`);
        setParsedCsv(null);
        setCsvValid(false);
        return;
      }
      
      setParsedCsv(parsed);
      setCsvValid(true);
      
      addLog(`✅ CSV parsed successfully`);
      addLog(`   Total rows: ${parsed.rows.length}`);
      addLog(`   Email column: "${parsed.emailColumn}"`);
      addLog(`   OEM ID column: "${parsed.oemIdColumn}"`);
      
      // Extract update rows
      const rows = extractUpdateRows(parsed);
      setUpdateRows(rows.map(r => ({ ...r, status: 'pending' })));
      
    } catch (error: any) {
      alert(`❌ Failed to parse CSV: ${error.message}`);
      setParsedCsv(null);
      setCsvValid(false);
    }
  };
  
  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
  };
  
  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();

    const file = e.dataTransfer.files[0];
    if (file) {
      // Simulate file input change
      const event = {
        target: {
          files: [file]
        }
      } as any;
      await handleFileSelect(event);
    }
  };

  // ========================================
  // API FUNCTIONS
  // ========================================

  /**
   * Fetch all users from Tekion
   */
  async function fetchAllUsers(headers: OemUpdateHeaders): Promise<TekionUser[]> {
    const baseUrl = 'https://preprodapp.tekioncloud.com';
    const endpoint = `${baseUrl}/api/userservice/u/v2/userandroles`;

    const allUsers: TekionUser[] = [];
    let currentIndex = 0;
    const pageSize = 250;

    while (true) {
      const payload = {
        filter: JSON.stringify({
          "dealerId": headers.dealerid,
          "includeGlobalUser": true
        }),
        pageInfo: {
          "currentIndex": currentIndex,
          "maxResult": pageSize
        }
      };

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: headers as any,
        body: JSON.stringify(payload)
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch users: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      const users = data.data?.users || [];
      allUsers.push(...users);

      if (users.length < pageSize) break;
      currentIndex += pageSize;
    }

    return allUsers;
  }

  /**
   * Extract OEM template from existing users
   */
  function getOemTemplate(users: TekionUser[], dealerId: string): OemTemplate {
    for (const user of users) {
      if (!user.oemMappings || user.oemMappings.length === 0) continue;

      for (const mapping of user.oemMappings) {
        if (mapping.dealerId === dealerId && mapping.oemDetails && mapping.oemDetails.length > 0) {
          const detail = mapping.oemDetails[0];
          return {
            dealerId: dealerId,
            oem: detail.oem,
            make: detail.makeOverrides?.[0]?.make || 'mercedesbenz',
            makeOverrideDisabled: detail.makeOverrideDisabled
          };
        }
      }
    }

    // Default template if none found
    return {
      dealerId: dealerId,
      oem: 'benz',
      make: 'mercedesbenz',
      makeOverrideDisabled: true
    };
  }

  /**
   * Update OEM ID for a single user
   */
  async function updateUserOem(
    userId: string,
    newOemId: string,
    template: OemTemplate,
    headers: OemUpdateHeaders
  ): Promise<{ scenario: 'CREATED' | 'EXISTING' | 'NEW'; oldOemId: string | null }> {
    const baseUrl = 'https://preprodapp.tekioncloud.com';
    const endpoint = `${baseUrl}/api/userservice/u/user-access-settings/${userId}`;

    // GET current user
    const getResponse = await fetch(endpoint, {
      method: 'GET',
      headers: headers as any
    });

    if (!getResponse.ok) {
      throw new Error(`GET failed: ${getResponse.status}`);
    }

    const getData = await getResponse.json();
    const user = getData.data?.user || {};

    const targetDealerId = headers.dealerid;

    // Find dealer mapping
    let dealerMapping = null;
    for (const mapping of (user.oemMappings || [])) {
      if (mapping.dealerId === targetDealerId) {
        dealerMapping = mapping;
        break;
      }
    }

    let oldOemId: string | null = null;
    let scenario: 'CREATED' | 'EXISTING' | 'NEW';

    if (dealerMapping) {
      // Found existing mapping
      oldOemId = dealerMapping.oemDetails[0]?.oemId || null;
      const hasComplexId = 'complexListId' in dealerMapping;

      if (hasComplexId) {
        // EXISTING: Preserve complexListId
        dealerMapping.oemDetails[0].oemId = newOemId;
        scenario = 'EXISTING';
      } else {
        // NEW: Remove complexListId
        dealerMapping.oemDetails[0].oemId = newOemId;
        delete dealerMapping.complexListId;
        delete dealerMapping.oemDetails[0].complexListId;
        if (dealerMapping.oemDetails[0].makeOverrides) {
          dealerMapping.oemDetails[0].makeOverrides.forEach((override: any) => {
            delete override.complexListId;
          });
        }
        scenario = 'NEW';
      }
    } else {
      // Not found: Create new mapping
      if (!user.oemMappings) {
        user.oemMappings = [];
      }

      user.oemMappings.push({
        dealerId: template.dealerId,
        oemDetails: [{
          oem: template.oem,
          oemId: newOemId,
          makeOverrideDisabled: template.makeOverrideDisabled,
          makeOverrides: [{
            make: template.make,
            oemId: null
          }]
        }]
      });

      oldOemId = null;
      scenario = 'CREATED';
    }

    // PUT updated user
    const putResponse = await fetch(endpoint, {
      method: 'PUT',
      headers: headers as any,
      body: JSON.stringify({ saveUserRequest: user })
    });

    if (!putResponse.ok) {
      throw new Error(`PUT failed: ${putResponse.status}`);
    }

    return { scenario, oldOemId };
  }

  // ========================================
  // STEP 3: BATCH UPDATE LOGIC
  // ========================================

  const handleStartBatchUpdate = async () => {
    if (!extractedHeaders || !csvValid || updateRows.length === 0) {
      alert('❌ Please complete Steps 1 and 2 first');
      return;
    }

    const confirmed = confirm(
      `🚀 Start batch update for ${updateRows.length} users?\n\n` +
      `Dealer ID: ${extractedHeaders.dealerid}\n` +
      `This will update OEM IDs in Tekion.\n\n` +
      `Continue?`
    );

    if (!confirmed) return;

    setIsProcessing(true);
    clearLogs();

    addLog('🚀 ========================================');
    addLog(`🚀 BATCH OEM ID UPDATE - DEALER ${extractedHeaders.dealerid}`);
    addLog('🚀 ========================================');
    addLog(`📋 Total rows: ${updateRows.length}`);

    // Reset progress
    const newProgress: BatchProgress = {
      total: updateRows.length,
      processed: 0,
      success: 0,
      failed: 0,
      created: 0,
      existing: 0,
      logs: []
    };
    setProgress(newProgress);

    try {
      // Step 1: Fetch all users
      addLog('📨 Fetching all users from Tekion...');
      const allUsers = await fetchAllUsers(extractedHeaders as OemUpdateHeaders);
      addLog(`✅ Fetched ${allUsers.length} users`);

      // Step 2: Extract OEM template
      addLog(`🔍 Extracting OEM template for dealer ${extractedHeaders.dealerid}...`);
      const template = getOemTemplate(allUsers, extractedHeaders.dealerid);
      addLog(`✅ Template: oem="${template.oem}", make="${template.make}"`);

      // Step 3: Create user map
      const userMap = new Map<string, TekionUser>();
      allUsers.forEach(u => {
        if (u.email) {
          userMap.set(u.email.toLowerCase(), u);
        }
      });

      // Step 4: Process each row
      addLog('\n⚙️ Starting batch update...\n');

      for (let i = 0; i < updateRows.length; i++) {
        const row = updateRows[i];
        const email = row.email.toLowerCase();
        const newOemId = row.oemId;

        addLog(`[${i + 1}/${updateRows.length}] ${row.email}`);

        const tekionUser = userMap.get(email);

        if (!tekionUser) {
          row.status = 'failed';
          row.error = 'Email not found in Tekion';
          newProgress.failed++;
          newProgress.processed++;
          addLog(`   ❌ Not found`);
          setProgress({ ...newProgress });
          continue;
        }

        if (!newOemId || newOemId.trim() === '') {
          row.status = 'failed';
          row.error = 'No OEM ID provided';
          newProgress.failed++;
          newProgress.processed++;
          addLog(`   ⚠️  No OEM ID`);
          setProgress({ ...newProgress });
          continue;
        }

        try {
          const result = await updateUserOem(
            tekionUser.id,
            newOemId,
            template,
            extractedHeaders as OemUpdateHeaders
          );

          row.status = 'success';
          row.scenario = result.scenario;
          row.oldOemId = result.oldOemId;
          newProgress.success++;
          newProgress.processed++;

          if (result.scenario === 'CREATED') {
            newProgress.created++;
            addLog(`   ✅ Created: [NONE] → ${newOemId}`);
          } else {
            newProgress.existing++;
            addLog(`   ✅ Updated (${result.scenario}): ${result.oldOemId || 'None'} → ${newOemId}`);
          }

        } catch (error: any) {
          row.status = 'failed';
          row.error = error.message;
          newProgress.failed++;
          newProgress.processed++;
          addLog(`   ❌ Error: ${error.message.substring(0, 50)}`);
        }

        setProgress({ ...newProgress });
        setUpdateRows([...updateRows]);

        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
      }

      // Final summary
      addLog('\n================================================================================');
      addLog('📊 SUMMARY');
      addLog('================================================================================');
      addLog(`Total: ${newProgress.total}`);
      addLog(`✅ Success: ${newProgress.success} (${((newProgress.success / newProgress.total) * 100).toFixed(1)}%)`);
      addLog(`   ├── Created: ${newProgress.created}`);
      addLog(`   └── Updated: ${newProgress.existing}`);
      addLog(`❌ Failed: ${newProgress.failed} (${((newProgress.failed / newProgress.total) * 100).toFixed(1)}%)`);
      addLog('================================================================================');

    } catch (error: any) {
      addLog(`\n❌ Fatal error: ${error.message}`);
      alert(`❌ Batch update failed: ${error.message}`);
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div style={{
      padding: '32px',
      maxWidth: '900px',
      margin: '0 auto'
    }}>
      {/* Header */}
      <div style={{
        marginBottom: '32px',
        borderBottom: '2px solid #FF9800',
        paddingBottom: '16px'
      }}>
        <h2 style={{
          margin: '0 0 8px 0',
          fontSize: '28px',
          color: '#FF9800',
          display: 'flex',
          alignItems: 'center',
          gap: '12px'
        }}>
          <span style={{ fontSize: '32px' }}>🔑</span>
          OEM ID Update
        </h2>
        <p style={{
          margin: 0,
          fontSize: '14px',
          color: '#666'
        }}>
          OEM ID Update for User Setup
        </p>
      </div>

      {/* Step 1: Headers Input */}
      <div style={{
        marginBottom: '24px',
        padding: '20px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        border: headersValid ? '2px solid #4CAF50' : '2px solid #ddd'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#333' }}>
          📋 Step 1: Paste cURL Command or Headers
        </h3>

        <textarea
          value={headersInput}
          onChange={(e) => setHeadersInput(e.target.value)}
          placeholder={`Paste cURL command or headers here:\n\ncurl 'https://...' -H 'dealerid: 7619' -H 'tekion-api-token: eyJ...'\n\nOR:\n\ndealerid:7619\ntekion-api-token:eyJ...\ntenantname:dreammotorgroupllc`}
          style={{
            width: '100%',
            minHeight: '120px',
            padding: '12px',
            fontFamily: 'monospace',
            fontSize: '13px',
            border: '1px solid #ddd',
            borderRadius: '4px',
            marginBottom: '12px',
            resize: 'vertical'
          }}
        />

        <button
          onClick={handleDetectHeaders}
          disabled={!headersInput.trim()}
          style={{
            padding: '10px 20px',
            backgroundColor: headersInput.trim() ? '#FF9800' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: '6px',
            cursor: headersInput.trim() ? 'pointer' : 'not-allowed',
            fontWeight: '600',
            fontSize: '14px'
          }}
        >
          🔍 Detect Headers
        </button>

        {extractedHeaders && headersValid && (
          <div style={{
            marginTop: '12px',
            padding: '12px',
            backgroundColor: '#E8F5E9',
            borderRadius: '4px',
            fontSize: '13px',
            fontFamily: 'monospace',
            whiteSpace: 'pre-wrap'
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#2E7D32' }}>
              ✅ Headers Detected:
            </div>
            {formatHeadersForDisplay(extractedHeaders)}
          </div>
        )}
      </div>

      {/* Step 2: CSV Upload */}
      <div style={{
        marginBottom: '24px',
        padding: '20px',
        backgroundColor: '#f5f5f5',
        borderRadius: '8px',
        border: csvValid ? '2px solid #4CAF50' : '2px solid #ddd'
      }}>
        <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#333' }}>
          📄 Step 2: Upload CSV/Excel File
        </h3>

        <div
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          style={{
            border: '2px dashed #FF9800',
            borderRadius: '8px',
            padding: '30px',
            textAlign: 'center',
            backgroundColor: 'white',
            cursor: 'pointer',
            marginBottom: '12px'
          }}
          onClick={() => document.getElementById('csv-file-input')?.click()}
        >
          <div style={{ fontSize: '48px', marginBottom: '12px' }}>📁</div>
          <p style={{ margin: '0 0 8px 0', fontSize: '16px', fontWeight: '600' }}>
            {selectedFile ? selectedFile.name : 'Drop CSV/Excel file here'}
          </p>
          <p style={{ margin: 0, fontSize: '13px', color: '#666' }}>
            or click to browse
          </p>
          <input
            id="csv-file-input"
            type="file"
            accept=".csv,.xlsx,.xls"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
        </div>

        {parsedCsv && csvValid && (
          <div style={{
            padding: '12px',
            backgroundColor: '#E8F5E9',
            borderRadius: '4px',
            fontSize: '13px'
          }}>
            <div style={{ fontWeight: 'bold', marginBottom: '8px', color: '#2E7D32' }}>
              ✅ CSV Parsed Successfully:
            </div>
            <div>Total rows: {parsedCsv.rows.length}</div>
            <div>Email column: "{parsedCsv.emailColumn}"</div>
            <div>OEM ID column: "{parsedCsv.oemIdColumn}"</div>
          </div>
        )}
      </div>

      {/* Step 3: Start Button */}
      <div style={{ marginBottom: '24px', textAlign: 'center' }}>
        <button
          onClick={handleStartBatchUpdate}
          disabled={!headersValid || !csvValid || isProcessing}
          style={{
            padding: '16px 32px',
            backgroundColor: (headersValid && csvValid && !isProcessing) ? '#FF9800' : '#ccc',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: (headersValid && csvValid && !isProcessing) ? 'pointer' : 'not-allowed',
            fontWeight: '600',
            fontSize: '16px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.2)'
          }}
        >
          {isProcessing ? '⏳ Processing...' : '🚀 Start Batch Update'}
        </button>
      </div>

      {/* Step 4: Progress */}
      {(isProcessing || progress.processed > 0) && (
        <div style={{
          marginBottom: '24px',
          padding: '20px',
          backgroundColor: '#f5f5f5',
          borderRadius: '8px',
          border: '2px solid #2196F3'
        }}>
          <h3 style={{ margin: '0 0 12px 0', fontSize: '18px', color: '#333' }}>
            📊 Progress: {progress.processed}/{progress.total} ({Math.round((progress.processed / progress.total) * 100)}%)
          </h3>

          <div style={{
            width: '100%',
            height: '24px',
            backgroundColor: '#ddd',
            borderRadius: '12px',
            overflow: 'hidden',
            marginBottom: '12px'
          }}>
            <div style={{
              width: `${(progress.processed / progress.total) * 100}%`,
              height: '100%',
              backgroundColor: '#2196F3',
              transition: 'width 0.3s ease'
            }} />
          </div>

          <div style={{ display: 'flex', gap: '20px', fontSize: '14px' }}>
            <div>
              <strong>✅ Success:</strong> {progress.success}
              {progress.success > 0 && (
                <span style={{ marginLeft: '8px', color: '#666' }}>
                  (Created: {progress.created}, Updated: {progress.existing})
                </span>
              )}
            </div>
            <div><strong>❌ Failed:</strong> {progress.failed}</div>
          </div>
        </div>
      )}
    </div>
  );
};

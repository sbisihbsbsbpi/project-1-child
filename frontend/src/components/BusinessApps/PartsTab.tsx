/**
 * Parts Tab - Parts Tiles Configuration UI
 */

import React, { useState, useEffect } from 'react';
import './PartsTab.css';

interface PartsTile {
  id: string;
  name: string;
  icon: string;
  description: string;
  category: string;
  method: 'POST' | 'PUT' | 'GET' | 'DELETE';
  url: string;
  preRequestScript?: string;
  body: any;
}

interface TileState {
  status: 'pending' | 'running' | 'success' | 'error';
  lastExecuted?: string;
  responseTime?: number;
  responseStatus?: number;
  responseStatusText?: string;
  responseBody?: string;
  responseSize?: string;
}

// Parts Tiles Configuration Data
const PARTS_TILES: PartsTile[] = [
  {
    id: 'pdf-config',
    name: 'PDF Configuration',
    icon: '📄',
    description: 'Configure PDF templates for invoices and quotes',
    category: 'Parts Module',
    method: 'POST',
    url: 'https://preprodapp.tekioncloud.com/api/partTrade/u/settings/part/general/pdfConfiguration',
    preRequestScript: `pm.environment.set("RETURN", "");
pm.environment.set("WARRANTY", "");`,
    body: {
      pdfRichTextAreas: [
        {
          fieldName: 'disclaimer',
          value: {
            blocks: [{
              key: 'disclaimer',
              text: '{{WARRANTY}}',
              type: 'unstyled',
              depth: 0,
              inlineStyleRanges: [{
                offset: 0,
                length: 2000,
                style: 'CUSTOM_FONT_SIZE_1rem'
              }],
              entityRanges: [],
              data: {
                blockStyle_lineHeight: 90
              }
            }],
            entityMap: {}
          },
          visible: true
        },
        {
          fieldName: 'returnTerms',
          value: {
            blocks: [{
              key: 'returnTerms',
              text: '{{RETURN}}',
              type: 'unstyled',
              depth: 0,
              inlineStyleRanges: [{
                offset: 0,
                length: 2000,
                style: 'CUSTOM_FONT_SIZE_1rem'
              }],
              entityRanges: [],
              data: {
                blockStyle_lineHeight: 90
              }
            }],
            entityMap: {}
          },
          visible: true
        }
      ],
      pdfType: '{{currentPdfType}}',
      useGeneralSettings: false
    }
  },
  {
    id: 'oem-makes',
    name: 'OEM & Makes',
    icon: '🏭',
    description: 'Configure OEM brands and manufacturer details',
    category: 'Dealer Config',
    method: 'PUT',
    url: 'https://preprodapp.tekioncloud.com/api/api-core/u/tenant/{{tenantname}}/dealer-master/{{dealerid}}',
    body: {
      oemDetails: [{
        displayName: 'General Motors',
        oemImageUrl: null,
        oem: 'gm',
        makeId: ['gmc', 'chevrolet'],
        makeDetails: [
          {
            make: 'gmc',
            makeId: 'gmc',
            displayName: 'Gmc',
            dealerCode: '548349',
            makeLogoUrl: null
          },
          {
            make: 'chevrolet',
            makeId: 'chevrolet',
            displayName: 'Chevrolet',
            dealerCode: '548349',
            makeLogoUrl: null
          }
        ],
        make: ['gmc', 'chevrolet']
      }],
      dealerCodeWithMake: [
        { dealerCode: '548349', make: 'gmc' },
        { dealerCode: '548349', make: 'chevrolet' }
      ]
    },
    preRequestScript: `// Get values directly from the request Headers tab
const tenantName = pm.request.headers.get('tenantname');
const dealerId = pm.request.headers.get('dealerid');

console.log('tenantname from header:', tenantName);
console.log('dealerid from header:', dealerId);

// Set them as variables to use in URL
pm.variables.set('tenantname', tenantName);
pm.variables.set('dealerid', dealerId);`
  },
  {
    id: 'general-settings',
    name: 'General Settings',
    icon: '⚙️',
    description: 'Tax regime configuration and business shifts',
    category: 'Dealer Config',
    method: 'PUT',
    url: 'https://preprodapp.tekioncloud.com/api/api-core/u/tenant/kellerchevroletinc/dealer-master/7713',
    body: {
      taxRegimeConfig: {
        taxRegimeType: 'SALES_TAX',
        defaultSplitType: 'AFTER_TAX',
        taxRegimes: [{
          taxType: 'SALES_TAX',
          taxPercentage: 8.75,
          coreSaleTaxable: true
        }]
      },
      shifts: [{ shiftNumber: 1, startTime: 25200000, endTime: 64800000 }]
    }
  },
  {
    id: 'manufacturer',
    name: 'Manufacturer',
    icon: '🏢',
    description: 'Configure manufacturer settings',
    category: 'Parts Module',
    method: 'POST',
    url: 'https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/manufacturer',
    body: {
      status: 'ACTIVE',
      brandCode: 'GM',
      subBrandCode: 'GM',
      oemCode: 'GM'
    }
  },
  {
    id: 'appt-reminder',
    name: 'Appointment Reminder',
    icon: '🔔',
    description: 'Configure appointment reminder notifications',
    category: 'Scheduling',
    method: 'PUT',
    url: 'https://preprodapp.tekioncloud.com/api/scheduling/u/settings/notification',
    body: {
      addedReminderSettings: [{
        reminderName: 'Appointment Reminder',
        remindBefore: 1,
        remindBeforeUnit: 'DAYS',
        time: { timeInHours: 10, timeInMinutes: 0 },
        textEnabled: true,
        emailEnabled: true
      }]
    }
  },
  {
    id: 'appt-notifications',
    name: 'Appointment Notifications',
    icon: '📧',
    description: 'Configure customer notification templates',
    category: 'Scheduling',
    method: 'PUT',
    url: 'https://preprodapp.tekioncloud.com/api/api-core/u/tenant/{{tenantname}}/dealer-master/{{dealerid}}',
    body: [
      {
        notificationType: 'APPOINTMENT_CONFIRMATION',
        optInText: true,
        optInEmail: true,
        sendNotificationToCustomer: true
      },
      {
        notificationType: 'APPOINTMENT_REMINDER',
        optInText: true,
        optInEmail: true
      }
    ]
  },
  {
    id: 'void-reason',
    name: 'Parts Void Reason',
    icon: '🚫',
    description: 'Configure void reason for sales orders (ID: 23)',
    category: 'Parts Module',
    method: 'PUT',
    url: 'https://preprodapp.tekioncloud.com/api/parts/proxy/u/settings/void-reason/23',
    body: {
      id: '23',
      active: true,
      detail: {
        countInLostSale: true,
        reasonCode: 'Customer Cancelled - with Lost Sale',
        languages: null
      },
      type: 'SALES_ORDER'
    }
  },
  {
    id: 'priority-code-sync',
    name: 'Sync Priority Codes',
    icon: '⚡',
    description: 'Auto-sync: ensures exactly 5 codes exist (SPAC, STK, KEY, OVN, CSO). Deletes unwanted, creates missing.',
    category: 'Parts Module',
    method: 'POST',
    url: 'http://localhost:8001/api/priority-code/sync',
    body: {}
  }
];

// OEM-Makes Mapping Data
const OEM_MAKES_DATA: Record<string, string[]> = {
  'subaru': ['subaru'],
  'kia': ['kia'],
  'fisker': ['karma'],
  'hyundai': ['hyundai', 'genesis'],
  'fca': ['chrysler', 'dodge', 'maserati', 'jeep', 'fiat', 'alfaromeo', 'ram'],
  'tesla': ['tesla'],
  'geelyandetika': ['lotus'],
  'czinger': ['czinger'],
  'ford': ['lincoln', 'mercury', 'ford'],
  'bmw': ['rollsroyce', 'mini', 'bmw'],
  'mazda': ['mazda'],
  'rimac': ['rimac'],
  'kenworth': ['kenworth'],
  'astonmartin': ['astonmartin'],
  'volkswagen': ['porsche', 'audi', 'bentley', 'lamborghini', 'volkswagen', 'bugatti'],
  'suzuki': ['suzuki'],
  'stellantis': ['lancia'],
  'benz': ['sprinter', 'metris', 'mercedesbenz', 'smart'],
  'pagani': ['pagani'],
  'mclaren': ['mclaren'],
  'gm': ['saturn', 'pontiac', 'hummer', 'chevrolet', 'buick', 'saab', 'cadillac', 'gmc', 'oldsmobile'],
  'ferrari': ['ferrari'],
  'mahindragroup': ['pininfarina'],
  'honda': ['acura', 'honda'],
  'renault_nissan_mitsubishi_alliance': ['mitsubishi', 'infiniti', 'nissan'],
  'tata': ['landrover', 'jaguar'],
  'koenigsegg': ['koenigsegg'],
  'hino': ['hino'],
  'peterbilt': ['peterbilt'],
  'toyota': ['toyota', 'scion', 'lexus'],
  'isuzu': ['isuzu'],
  'volvo': ['polestar', 'volvo']
};

// OEM Display Names
const OEM_DISPLAY_NAMES: Record<string, string> = {
  'subaru': 'Subaru',
  'kia': 'Kia',
  'fisker': 'Fisker',
  'hyundai': 'Hyundai',
  'fca': 'FCA (Stellantis)',
  'tesla': 'Tesla',
  'geelyandetika': 'Geely/Etika',
  'czinger': 'Czinger',
  'ford': 'Ford Motor Company',
  'bmw': 'BMW Group',
  'mazda': 'Mazda',
  'rimac': 'Rimac',
  'kenworth': 'Kenworth',
  'astonmartin': 'Aston Martin',
  'volkswagen': 'Volkswagen Group',
  'suzuki': 'Suzuki',
  'stellantis': 'Stellantis',
  'benz': 'Mercedes-Benz',
  'pagani': 'Pagani',
  'mclaren': 'McLaren',
  'gm': 'General Motors',
  'ferrari': 'Ferrari',
  'mahindragroup': 'Mahindra Group',
  'honda': 'Honda',
  'renault_nissan_mitsubishi_alliance': 'Renault-Nissan-Mitsubishi',
  'tata': 'Tata Motors',
  'koenigsegg': 'Koenigsegg',
  'hino': 'Hino',
  'peterbilt': 'Peterbilt',
  'toyota': 'Toyota Motor Corporation',
  'isuzu': 'Isuzu',
  'volvo': 'Volvo'
};

// BLACKLIST: Headers to REMOVE (only these 2)
// All other headers will be kept and forwarded to Tekion API
const BLOCKED_HEADERS = [
  'referer',
  'cookie'
];

// Helper function to check if a header should be blocked
const isBlockedHeader = (headerKey: string): boolean => {
  return BLOCKED_HEADERS.includes(headerKey.toLowerCase());
};

// Unified Headers (shared across ALL tiles)
// Based on actual Tekion API headers - keys are required, values are examples
// Note: ONLY 'referer' and 'cookie' are removed. All other headers are kept.
const UNIFIED_HEADERS: Record<string, string> = {
  'accept': 'application/json, text/plain, */*',
  'accept-language': 'en-GB,en;q=0.9',
  'applicationid': 'ARC_NA',
  'clientid': 'web',
  'content-type': 'application/json',
  'dealerid': '4',
  'dnt': '1',
  'flattenedaecprogramsmap': 'HMA::HMA_US_HYUNDAI_NEW',
  'locale': 'en_US',
  'origin': 'https://preprodapp.tekioncloud.com',
  'original-tenantid': 'techmotors',
  'original-userid': 'fe3a3333-c9ad-49fd-bef7-79eacaddc1d5',
  'priority': 'u=1, i',
  'productids': 'ARC',
  'program': 'DEFAULT',
  'roleid': '4_Controller',
  'sec-ch-ua': '"Google Chrome";v="147", "Not.A/Brand";v="8", "Chromium";v="147"',
  'sec-ch-ua-mobile': '?0',
  'sec-ch-ua-platform': '"macOS"',
  'sec-fetch-dest': 'empty',
  'sec-fetch-mode': 'cors',
  'sec-fetch-site': 'same-origin',
  'subapplicationid': 'US',
  'tek-siteid': '-1_4',
  'tekion-api-token': 'eyJhbGciOiJIUzI1NiJ9.eyJqdGkiOiJmZTNhMzMzMy1jOWFkLTQ5ZmQtYmVmNy03OWVhY2FkZGMxZDUiLCJpYXQiOjE3Nzc2NDc3MDQsInN1YiI6ImZlM2EzMzMzLWM5YWQtNDlmZC1iZWY3LTc5ZWFjYWRkYzFkNSIsImlzcyI6IkxvZ2luU2VydmljZSIsInVubG9ja0FjY291bnQiOmZhbHNlLCJub3VuY2UiOiI1YjUxYzIxYy0xMjRlLTQxMDktYWJiMS0zNmRiMmFjODllNTQiLCJvcmlnaW5hbFVzZXJJZCI6ImZlM2EzMzMzLWM5YWQtNDlmZC1iZWY3LTc5ZWFjYWRkYzFkNSIsIm9yaWdpbmFsVGVuYW50SWQiOiJ0ZWNobW90b3JzIiwidXNlcklkIjoiZmUzYTMzMzMtYzlhZC00OWZkLWJlZjctNzllYWNhZGRjMWQ1IiwiZW1haWwiOiJ0bHJlZGR5QHRla2lvbi5jb20iLCJleHAiOjE3Nzc2NTU0ODB9.pGU_uB_-0x7ijxRcSKjQ4ncxFQp8Ghy2oPZt6J0PX2U',
  'tenantname': 'techmotors',
  'tracestate': 'es=s:1',
  'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/147.0.0.0 Safari/537.36',
  'userid': 'fe3a3333-c9ad-49fd-bef7-79eacaddc1d5',
  'x-observe-rum-id': '00-58441366428656f83382cb21cbcfb044-67070cda1c0bf900-01'
};

interface PartsTabProps {
  addLog: (message: string) => void;
}

export const PartsTab: React.FC<PartsTabProps> = ({ addLog }) => {
  // Initialize active tiles from localStorage or defaults
  const [activeTiles, setActiveTiles] = useState<PartsTile[]>(() => {
    try {
      const stored = localStorage.getItem('parts-tab-active-tiles');
      if (stored) {
        const parsed = JSON.parse(stored);
        console.log('✅ Loaded active tiles from localStorage');
        return parsed;
      }
    } catch (e) {
      console.warn('⚠️ Failed to load active tiles from localStorage:', e);
    }
    return [...PARTS_TILES];
  });

  // Track deleted tiles for restoration
  const [deletedTileIds, setDeletedTileIds] = useState<string[]>(() => {
    try {
      const stored = localStorage.getItem('parts-tab-deleted-tiles');
      return stored ? JSON.parse(stored) : [];
    } catch {
      return [];
    }
  });

  // Manage Tiles modal state
  const [isManageTilesModalOpen, setIsManageTilesModalOpen] = useState(false);

  // Drag state for reordering
  const [draggedTileId, setDraggedTileId] = useState<string | null>(null);
  const [dragOverTileId, setDragOverTileId] = useState<string | null>(null);

  // Initialize selectedTileId from URL hash or default to first tile
  const getInitialTileId = (): string => {
    const hash = window.location.hash;
    // Parse hash format: #business-apps/parts/pdf-config
    const match = hash.match(/#business-apps\/parts\/([^/]+)/);
    if (match) {
      const tileIdFromUrl = match[1];
      // Validate that the tile exists in active tiles
      const tileExists = activeTiles.some(t => t.id === tileIdFromUrl);
      if (tileExists) {
        return tileIdFromUrl;
      }
    }
    return activeTiles[0]?.id || '';
  };

  const [selectedTileId, setSelectedTileId] = useState<string>(getInitialTileId());

  // Persist collapse state to localStorage
  const [isLeftPanelCollapsed, setIsLeftPanelCollapsed] = useState<boolean>(() => {
    try {
      const saved = localStorage.getItem('partsTabLeftPanelCollapsed');
      return saved ? JSON.parse(saved) : false;
    } catch {
      return false;
    }
  });

  const [tileStates, setTileStates] = useState<Record<string, TileState>>({});

  // Initialize unified headers with localStorage persistence
  const [unifiedHeaders, setUnifiedHeaders] = useState<Record<string, string>>(() => {
    try {
      const stored = localStorage.getItem('parts-unified-headers');
      if (stored) {
        const parsed = JSON.parse(stored);
        console.log('✅ Loaded unified headers from localStorage');
        return parsed;
      }
    } catch (e) {
      console.warn('⚠️ Failed to load headers from localStorage, using defaults:', e);
    }
    return UNIFIED_HEADERS;
  });

  const [activeTab, setActiveTab] = useState<'headers' | 'body' | 'pre-request'>('headers');
  const [isBulkEditMode, setIsBulkEditMode] = useState(false);
  const [bulkEditText, setBulkEditText] = useState('');

  // Initialize pre-request scripts from tile data
  const [preRequestScripts, setPreRequestScripts] = useState<Record<string, string>>(() => {
    const scripts: Record<string, string> = {};
    PARTS_TILES.forEach(tile => {
      if (tile.preRequestScript) {
        scripts[tile.id] = tile.preRequestScript;
      }
    });
    return scripts;
  });

  // Track saved pre-request scripts (for detecting unsaved changes)
  const [savedPreRequestScripts, setSavedPreRequestScripts] = useState<Record<string, string>>(() => {
    const scripts: Record<string, string> = {};
    PARTS_TILES.forEach(tile => {
      if (tile.preRequestScript) {
        scripts[tile.id] = tile.preRequestScript;
      }
    });
    return scripts;
  });

  // Track current editing script (temporary state before save)
  const [editingScript, setEditingScript] = useState<string>('');

  // Initialize tile bodies from tile data (editable bodies) with localStorage persistence
  const [tileBodies, setTileBodies] = useState<Record<string, any>>(() => {
    const bodies: Record<string, any> = {};

    // Try to load from localStorage first
    try {
      const stored = localStorage.getItem('parts-tab-tile-bodies');
      if (stored) {
        const parsed = JSON.parse(stored);
        // Merge with defaults (in case new tiles were added)
        PARTS_TILES.forEach(tile => {
          bodies[tile.id] = parsed[tile.id] || tile.body;
        });
        console.log('✅ Loaded tile bodies from localStorage');
        return bodies;
      }
    } catch (e) {
      console.warn('⚠️ Failed to load tile bodies from localStorage:', e);
    }

    // Fallback to defaults
    PARTS_TILES.forEach(tile => {
      bodies[tile.id] = tile.body;
    });
    return bodies;
  });

  // Track saved bodies (for detecting unsaved changes) - initialized from tileBodies
  const [savedTileBodies, setSavedTileBodies] = useState<Record<string, any>>(() => {
    return { ...tileBodies };
  });

  // Track current editing body (temporary state before save)
  const [editingBody, setEditingBody] = useState<string>('');

  // Initialize tile URLs from tile data (editable URLs)
  const [tileUrls, setTileUrls] = useState<Record<string, string>>(() => {
    const urls: Record<string, string> = {};
    PARTS_TILES.forEach(tile => {
      urls[tile.id] = tile.url;
    });
    return urls;
  });

  // PDF Configuration Editor Modal State
  const [isPdfModalOpen, setIsPdfModalOpen] = useState(false);
  const [warrantyText, setWarrantyText] = useState('');
  const [returnText, setReturnText] = useState('');

  // OEM & Makes Editor Modal State
  const [isOemMakesModalOpen, setIsOemMakesModalOpen] = useState(false);
  const [selectedMakes, setSelectedMakes] = useState<Record<string, string[]>>({});
  const [oemSearchQuery, setOemSearchQuery] = useState('');
  const [dealerCode, setDealerCode] = useState('548349');

  // Environment and local variables storage
  const [environmentVariables, setEnvironmentVariables] = useState<Record<string, any>>({});
  const [localVariables, setLocalVariables] = useState<Record<string, any>>({});

  const selectedTile = activeTiles.find(t => t.id === selectedTileId);

  // Add welcome log on component mount
  useEffect(() => {
    addLog('🎯 Parts Tab initialized');
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Only run once on mount - addLog is stable from props

  // Listen for URL hash changes (browser back/forward navigation)
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash;
      const match = hash.match(/#business-apps\/parts\/([^/]+)/);
      if (match) {
        const tileIdFromUrl = match[1];
        const tileExists = activeTiles.some(t => t.id === tileIdFromUrl);
        if (tileExists && tileIdFromUrl !== selectedTileId) {
          setSelectedTileId(tileIdFromUrl);
          console.log(`🔗 Hash changed to tile: ${tileIdFromUrl}`);
        }
      }
    };

    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, [selectedTileId]);

  // Load editing script when tile changes
  useEffect(() => {
    setEditingScript(preRequestScripts[selectedTileId] || '');
  }, [selectedTileId, preRequestScripts]);

  // Load editing body when tile changes
  useEffect(() => {
    const currentBody = tileBodies[selectedTileId];
    setEditingBody(currentBody ? JSON.stringify(currentBody, null, 2) : '{}');
  }, [selectedTileId, tileBodies]);

  // Check if current script has unsaved changes
  const hasUnsavedChanges = editingScript !== (savedPreRequestScripts[selectedTileId] || '');

  // Check if current body has unsaved changes
  const hasUnsavedBodyChanges = (() => {
    try {
      const currentSaved = savedTileBodies[selectedTileId];
      const currentEditing = JSON.parse(editingBody);
      return JSON.stringify(currentSaved) !== JSON.stringify(currentEditing);
    } catch {
      return false; // Invalid JSON, treat as no changes
    }
  })();

  // Save pre-request script
  const handleSavePreRequestScript = () => {
    setPreRequestScripts(prev => ({
      ...prev,
      [selectedTileId]: editingScript
    }));
    setSavedPreRequestScripts(prev => ({
      ...prev,
      [selectedTileId]: editingScript
    }));
    addLog(`💾 Parts Tab: Pre-request script saved for ${selectedTile?.name}`);
  };

  // Save body
  const handleSaveBody = () => {
    try {
      const parsedBody = JSON.parse(editingBody);
      setTileBodies(prev => ({
        ...prev,
        [selectedTileId]: parsedBody
      }));
      setSavedTileBodies(prev => ({
        ...prev,
        [selectedTileId]: parsedBody
      }));
      addLog(`💾 Parts Tab: Body saved for ${selectedTile?.name}`);
    } catch (error: any) {
      alert(`❌ Invalid JSON: ${error.message}`);
      addLog(`❌ Parts Tab: Failed to save body - Invalid JSON`);
    }
  };

  const getStatusInfo = (status: TileState['status']) => {
    const map = {
      pending: { class: 'status-pending', icon: '⏳', label: 'Pending' },
      running: { class: 'status-running', icon: '⚡', label: 'Running' },
      success: { class: 'status-success', icon: '✅', label: 'Success' },
      error: { class: 'status-error', icon: '❌', label: 'Failed' }
    };
    return map[status] || map.pending;
  };

  // Calculate stats
  const stats = {
    success: Object.values(tileStates).filter(s => s.status === 'success').length,
    pending: PARTS_TILES.length - Object.values(tileStates).filter(s => s.status === 'success' || s.status === 'error').length,
    error: Object.values(tileStates).filter(s => s.status === 'error').length
  };

  const handleTogglePanel = () => {
    const newCollapsedState = !isLeftPanelCollapsed;
    setIsLeftPanelCollapsed(newCollapsedState);
    // Persist to localStorage
    try {
      localStorage.setItem('partsTabLeftPanelCollapsed', JSON.stringify(newCollapsedState));
    } catch (error) {
      console.warn('Failed to save panel state to localStorage:', error);
    }
  };

  const handleSelectTile = (tileId: string) => {
    setSelectedTileId(tileId);
    setActiveTab('headers'); // Reset to headers tab when selecting new tile

    // Update URL hash to reflect selected tile
    const newHash = `#business-apps/parts/${tileId}`;
    window.history.pushState(null, '', `/main${newHash}`);
    console.log(`🔗 Parts tile changed: ${newHash}`);
  };

  // Tile Management Functions
  const handleDeleteTile = (tileId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent tile selection
    const tile = activeTiles.find(t => t.id === tileId);
    if (!tile) return;

    if (!confirm(`Delete "${tile.name}"?\n\nYou can restore it later from the Manage Tiles menu.`)) {
      return;
    }

    const updated = activeTiles.filter(t => t.id !== tileId);
    setActiveTiles(updated);
    localStorage.setItem('parts-tab-active-tiles', JSON.stringify(updated));

    // Track deleted tile
    const newDeletedIds = [...deletedTileIds, tileId];
    setDeletedTileIds(newDeletedIds);
    localStorage.setItem('parts-tab-deleted-tiles', JSON.stringify(newDeletedIds));

    // Select another tile if the deleted one was selected
    if (selectedTileId === tileId && updated.length > 0) {
      handleSelectTile(updated[0].id);
    }

    addLog(`🗑️ Parts Tab: Deleted tile "${tile.name}"`);
  };

  const handleRestoreTile = (tileId: string) => {
    const tileTemplate = PARTS_TILES.find(t => t.id === tileId);
    if (!tileTemplate) return;

    setActiveTiles(prev => [...prev, tileTemplate]);
    localStorage.setItem('parts-tab-active-tiles', JSON.stringify([...activeTiles, tileTemplate]));

    const newDeletedIds = deletedTileIds.filter(id => id !== tileId);
    setDeletedTileIds(newDeletedIds);
    localStorage.setItem('parts-tab-deleted-tiles', JSON.stringify(newDeletedIds));

    addLog(`✅ Parts Tab: Restored tile "${tileTemplate.name}"`);
  };

  const handleResetToDefaults = () => {
    if (!confirm('Reset all tiles to default configuration?\n\nThis will restore all deleted tiles and reset their order.')) {
      return;
    }

    setActiveTiles([...PARTS_TILES]);
    localStorage.setItem('parts-tab-active-tiles', JSON.stringify(PARTS_TILES));

    setDeletedTileIds([]);
    localStorage.setItem('parts-tab-deleted-tiles', JSON.stringify([]));

    addLog('🔄 Parts Tab: Reset tiles to defaults');
  };

  const handleExportToCode = () => {
    const code = `// Auto-generated Parts Tiles Configuration
// Generated: ${new Date().toLocaleString()}
// Copy this into PartsTab.tsx (lines 30-247) to update PARTS_TILES array

const PARTS_TILES: PartsTile[] = ${JSON.stringify(activeTiles, null, 2)};`;

    navigator.clipboard.writeText(code);
    alert(`✅ Tile configuration copied to clipboard!

📋 ${activeTiles.length} tiles exported

To apply changes:
1. Open: frontend/src/components/BusinessApps/PartsTab.tsx
2. Replace lines 30-247 with the clipboard content
3. Save the file

The frontend will auto-reload with your custom configuration.`);

    addLog(`📤 Parts Tab: Exported ${activeTiles.length} tiles to clipboard`);
  };

  // Drag and Drop handlers for reordering
  const handleDragStart = (e: React.DragEvent, tileId: string) => {
    setDraggedTileId(tileId);
    e.dataTransfer.effectAllowed = 'move';
  };

  const handleDragOver = (e: React.DragEvent, tileId: string) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
    setDragOverTileId(tileId);
  };

  const handleDragLeave = () => {
    setDragOverTileId(null);
  };

  const handleDrop = (e: React.DragEvent, dropTargetId: string) => {
    e.preventDefault();

    if (!draggedTileId || draggedTileId === dropTargetId) {
      setDraggedTileId(null);
      setDragOverTileId(null);
      return;
    }

    const draggedIndex = activeTiles.findIndex(t => t.id === draggedTileId);
    const targetIndex = activeTiles.findIndex(t => t.id === dropTargetId);

    if (draggedIndex === -1 || targetIndex === -1) {
      setDraggedTileId(null);
      setDragOverTileId(null);
      return;
    }

    const reordered = Array.from(activeTiles);
    const [removed] = reordered.splice(draggedIndex, 1);
    reordered.splice(targetIndex, 0, removed);

    setActiveTiles(reordered);
    localStorage.setItem('parts-tab-active-tiles', JSON.stringify(reordered));

    setDraggedTileId(null);
    setDragOverTileId(null);

    addLog(`🔄 Parts Tab: Reordered tiles`);
  };

  const handleDragEnd = () => {
    setDraggedTileId(null);
    setDragOverTileId(null);
  };

  // Replace {{variables}} in strings with actual values
  const replaceVariables = (text: string, variables: Record<string, any>): string => {
    return text.replace(/\{\{([^}]+)\}\}/g, (match, varName) => {
      const value = variables[varName.trim()];
      return value !== undefined ? String(value) : match;
    });
  };

  const handleExecuteTile = async (tileId: string) => {
    const tile = activeTiles.find(t => t.id === tileId);
    if (!tile) return;

    const requestId = crypto.randomUUID(); // Generate correlation ID
    addLog(`🚀 Parts Tab: Executing ${tile.name} (${requestId})`);

    // Create temporary storage for this execution
    let tempEnvironmentVars = { ...environmentVariables };
    let tempLocalVars = { ...localVariables };
    let tempHeaders = { ...unifiedHeaders };

    // Use the edited body instead of the original tile body
    const currentBody = tileBodies[tileId] || tile.body;

    // Execute pre-request script if exists
    const preRequestScript = preRequestScripts[tileId];
    if (preRequestScript && preRequestScript.trim()) {
      addLog(`📜 Parts Tab: Running pre-request script for ${tile.name}`);
      try {
        // Create a pm-like API for the script (Postman-compatible)
        const pm = {
          environment: {
            set: (key: string, value: any) => {
              tempEnvironmentVars[key] = value;
            },
            get: (key: string) => {
              const value = tempEnvironmentVars[key];
              return value;
            },
            unset: (key: string) => {
              delete tempEnvironmentVars[key];
            }
          },
          variables: {
            set: (key: string, value: any) => {
              tempLocalVars[key] = value;
            },
            get: (key: string) => {
              // Check local first, then environment, then headers (lowercase)
              if (tempLocalVars[key] !== undefined) {
                return tempLocalVars[key];
              }
              if (tempEnvironmentVars[key] !== undefined) {
                return tempEnvironmentVars[key];
              }
              // Check headers (lowercase)
              const headerValue = tempHeaders[key.toLowerCase()];
              if (headerValue !== undefined) {
                return headerValue;
              }
              return undefined;
            },
            replaceIn: (template: string) => {
              // Combine all variables for replacement (headers last = highest priority)
              const allVars = {
                ...tempEnvironmentVars,
                ...tempLocalVars,
                ...Object.fromEntries(
                  Object.entries(tempHeaders).map(([k, v]) => [k.toLowerCase(), v])
                )
              };
              const result = replaceVariables(template, allVars);
              return result;
            }
          },
          request: {
            headers: {
              get: (key: string) => {
                // Get header value (case-insensitive)
                return tempHeaders[key] || tempHeaders[key.toLowerCase()];
              },
              add: (header: { key: string; value: string }) => {
                tempHeaders[header.key] = header.value;
              },
              remove: (key: string) => {
                delete tempHeaders[key];
              }
            }
          },
          sendRequest: (url: string | any, callback?: Function) => {
            const requestUrl = typeof url === 'string' ? url : url.url;
            // Simulate async request (can be enhanced with actual fetch)
            setTimeout(() => {
              if (callback) {
                callback(null, { status: 200, body: 'Mock response' });
              }
            }, 100);
          }
        };

        // Execute the script in a safe context
        const scriptFunction = new Function('pm', 'console', preRequestScript);
        scriptFunction(pm, console);

        // Update state with modified variables and headers
        setEnvironmentVariables(tempEnvironmentVars);
        setLocalVariables(tempLocalVars);
        setUnifiedHeaders(tempHeaders);

        addLog(`✅ Parts Tab: Pre-request script executed for ${tile.name}`);
      } catch (error: any) {
        addLog(`❌ Parts Tab: Pre-request script error for ${tile.name}: ${error.message}`);
        alert(`❌ Pre-request script error: ${error.message}`);
        return; // Don't proceed if script fails
      }
    }

    // Set running state
    setTileStates(prev => ({
      ...prev,
      [tileId]: { ...prev[tileId], status: 'running' }
    }));

    const pdfTypes = tileId === 'pdf-config' ? [
      'SALES_ORDER_RETAIL_GENERAL_CUSTOMER',
      'SALES_ORDER_RETAIL_INVOICE_CUSTOMER',
      'SALES_ORDER_RETAIL_RETURN_CUSTOMER',
      'SALES_ORDER_INTERNAL_GENERAL_CUSTOMER',
      'SALES_ORDER_INTERNAL_INVOICE_CUSTOMER',
      'SALES_ORDER_INTERNAL_RETURN_CUSTOMER',
      'SALES_ORDER_WHOLESALE_GENERAL_CUSTOMER',
      'SALES_ORDER_WHOLESALE_INVOICE_CUSTOMER',
      'SALES_ORDER_WHOLESALE_RETURN_CUSTOMER'
    ] : [null];

    let overallSuccess = true;
    let allResponses: any[] = [];
    let lastResponseTime = 0;
    let lastResponseStatus = 200;
    let lastResponseStatusText = 'OK';
    let totalSize = 0;
    let anyError: any = null;

    for (const currentPdfType of pdfTypes) {
      if (currentPdfType) {
        tempLocalVars['currentPdfType'] = currentPdfType;
        addLog(`⏳ Parts Tab: Processing PDF Type: ${currentPdfType}`);
      }

      // Build variable map including headers (for URL and body replacement)
      const allVars = {
        ...tempEnvironmentVars,
        ...tempLocalVars,
        // Add headers as lowercase variables so they can be used in URLs
        ...Object.fromEntries(
          Object.entries(tempHeaders).map(([k, v]) => [k.toLowerCase(), v])
        )
      };
      addLog(`🔧 Parts Tab: Available variables - ${Object.keys(allVars).join(', ')}`);

      // Replace variables in URL
      const currentUrl = tileUrls[tileId] || tile.url;
      const processedUrl = replaceVariables(currentUrl, allVars);

      // Replace variables in body (use current edited body)
      let processedBody = currentBody;
      try {
        const bodyString = JSON.stringify(currentBody);
        const replacedBodyString = replaceVariables(bodyString, allVars);
        processedBody = JSON.parse(replacedBodyString);

        // Log what we're about to send
        if (currentPdfType) {
          addLog(`📤 Parts Tab: Sending payload with pdfType="${processedBody.pdfType}"`);
          addLog(`📝 Parts Tab: Warranty text: "${processedBody.pdfRichTextAreas?.[0]?.value?.blocks?.[0]?.text?.substring(0, 50)}..."`);
          addLog(`📝 Parts Tab: Return text: "${processedBody.pdfRichTextAreas?.[1]?.value?.blocks?.[0]?.text?.substring(0, 50)}..."`);
        }
      } catch (e) {
        console.warn('⚠️ Could not replace variables in body:', e);
        addLog(`⚠️ Parts Tab: Variable replacement failed - ${e}`);
      }

      const startTime = performance.now(); // Track performance

      // Make actual API call through backend proxy
      try {
        const typeLogSuffix = currentPdfType ? ` (${currentPdfType})` : '';
        addLog(`🌐 Parts Tab: Sending ${tile.method} request to ${tile.name}${typeLogSuffix}`);

        const response = await fetch('http://localhost:8001/api/proxy-request', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            url: processedUrl,
            method: tile.method,
            headers: tempHeaders,
            body: JSON.stringify(processedBody),
            pre_request_script: preRequestScript || undefined,
            timeout: 30
          })
        });

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }

        const result = await response.json();
        const duration = performance.now() - startTime;

        const isSuccess = result.status >= 200 && result.status < 300;
        if (!isSuccess) overallSuccess = false;

        const isResponseEmpty = !result.json && (!result.body || result.body.trim() === '');
        const responseDetail = isResponseEmpty ? ' (Empty Response Body)' : '';

        // Log detailed response information
        addLog(
          `${isSuccess ? '✅' : '❌'} Parts Tab: ${tile.name}${typeLogSuffix} - ${result.status} ${result.status_text} (${Math.round(duration)}ms)${responseDetail}`
        );

        if (result.json) {
          addLog(`📥 Parts Tab: Response JSON keys: ${Object.keys(result.json).join(', ')}`);
          addLog(`📥 Parts Tab: Response preview: ${JSON.stringify(result.json).substring(0, 100)}...`);
        } else if (result.body) {
          addLog(`📥 Parts Tab: Response body (text): ${result.body.substring(0, 100)}${result.body.length > 100 ? '...' : ''}`);
        } else {
          addLog(`📥 Parts Tab: Response is empty`);
        }

        allResponses.push(
          currentPdfType
            ? { pdfType: currentPdfType, response: isResponseEmpty ? "Empty Response (Success)" : (result.json || result.body || result) }
            : (isResponseEmpty ? "Empty Response (Success)" : (result.json || result.body || result))
        );

        lastResponseTime += duration;
        lastResponseStatus = result.status;
        lastResponseStatusText = result.status_text;
        totalSize += result.size || 0;

      } catch (error: any) {
        const duration = performance.now() - startTime;
        const typeLogSuffix = currentPdfType ? ` (${currentPdfType})` : '';
        addLog(`❌ Parts Tab: ${tile.name}${typeLogSuffix} request failed - ${error.message}`);

        overallSuccess = false;
        anyError = error;

        allResponses.push(
          currentPdfType
            ? { pdfType: currentPdfType, error: error.message || 'Request failed' }
            : { error: error.message || 'Request failed', details: 'Check console for more information' }
        );

        lastResponseStatus = 0;
        lastResponseStatusText = 'Network Error';
      }
    }

    if (anyError && pdfTypes.length === 1 && !pdfTypes[0]) {
      alert(`❌ Request failed: ${anyError.message}`);
    } else if (anyError) {
      alert(`❌ One or more requests failed. Check logs for details.`);
    }

    // Update state with real response
    setTileStates(prev => ({
      ...prev,
      [tileId]: {
        ...prev[tileId],
        status: overallSuccess ? 'success' : 'error',
        lastExecuted: new Date().toISOString(),
        responseTime: lastResponseTime,
        responseStatus: lastResponseStatus,
        responseStatusText: lastResponseStatusText,
        responseBody: JSON.stringify(allResponses.length === 1 && !pdfTypes[0] ? allResponses[0] : allResponses, null, 2),
        responseSize: (totalSize / 1024).toFixed(2)
      }
    }));
  };

  const handleToggleBulkEdit = () => {
    if (!isBulkEditMode) {
      // Entering bulk edit mode - populate textarea
      const text = Object.entries(unifiedHeaders)
        .map(([k, v]) => `${k}: ${v}`)
        .join('\n');
      setBulkEditText(text);
    }
    setIsBulkEditMode(!isBulkEditMode);
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
  const parseAndFilterHeaders = (rawInput: string): { filtered: Record<string, string>; totalParsed: number; filteredOut: number } => {
    const filtered: Record<string, string> = {};
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
            // BLACKLIST approach: Keep all headers EXCEPT blocked ones
            if (!isBlockedHeader(key)) {
              filtered[key] = value;
            }
          }
        }
      }

      const filteredOut = totalParsed - Object.keys(filtered).length;
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

      // Step 5: Filter - BLACKLIST approach: Keep all headers EXCEPT blocked ones
      if (!isBlockedHeader(key)) {
        filtered[key] = value;
      }
    }

    const filteredOut = totalParsed - Object.keys(filtered).length;
    return { filtered, totalParsed, filteredOut };
  };

  const handleSaveBulkEdit = () => {
    try {
      const { filtered: newHeaders, totalParsed, filteredOut } = parseAndFilterHeaders(bulkEditText);

      if (Object.keys(newHeaders).length === 0) {
        alert('❌ No valid headers found!\n\nSupported formats:\n\n1. DevTools: accept: application/json\n2. curl: -H \'accept: application/json\'\n3. Postman: key: value\n\nPaste any format and headers will be auto-extracted!');
        return;
      }

      // REPLACE old headers completely with new filtered headers
      setUnifiedHeaders(newHeaders);

      // Save to localStorage for persistence
      try {
        localStorage.setItem('parts-unified-headers', JSON.stringify(newHeaders));
        console.log('✅ Headers saved to localStorage');
      } catch (storageError) {
        console.warn('⚠️ Failed to save headers to localStorage:', storageError);
      }

      setIsBulkEditMode(false);

      // Show success message with filtering info
      const keptCount = Object.keys(newHeaders).length;
      const message = filteredOut > 0
        ? `✅ Applied ${keptCount} headers\n\n📊 Parsed: ${totalParsed} headers\n✅ Kept: ${keptCount} headers\n🚫 Blocked: ${filteredOut} headers (referer, cookie)`
        : `✅ Applied ${keptCount} headers`;

      alert(message);
      addLog(`📋 Parts Tab: Headers updated from paste (${keptCount} headers, ${filteredOut} filtered out)`);
    } catch (e: any) {
      alert('❌ Error parsing headers: ' + e.message);
      console.error('Header parsing error:', e);
    }
  };

  const handleUpdateHeaderKey = (oldKey: string, newKey: string) => {
    if (!newKey.trim() || newKey === oldKey) return;

    // Validate: check if new key is in the blocked list
    if (isBlockedHeader(newKey.trim())) {
      alert(`❌ Header "${newKey}" is blocked.\n\n🚫 Blocked headers: ${BLOCKED_HEADERS.join(', ')}\n\nThese headers are automatically removed for security/compatibility.`);
      return;
    }

    // Check if new key already exists
    if (unifiedHeaders[newKey] && newKey !== oldKey) {
      alert('❌ Header key already exists!');
      return;
    }

    const newHeaders = { ...unifiedHeaders };
    const value = newHeaders[oldKey];
    delete newHeaders[oldKey];
    newHeaders[newKey] = value;
    setUnifiedHeaders(newHeaders);

    // Save to localStorage
    try {
      localStorage.setItem('parts-unified-headers', JSON.stringify(newHeaders));
    } catch (e) {
      console.warn('⚠️ Failed to save to localStorage:', e);
    }
  };

  const handleUpdateHeaderValue = (key: string, value: string) => {
    const newHeaders = {
      ...unifiedHeaders,
      [key]: value
    };
    setUnifiedHeaders(newHeaders);

    // Save to localStorage
    try {
      localStorage.setItem('parts-unified-headers', JSON.stringify(newHeaders));
    } catch (e) {
      console.warn('⚠️ Failed to save to localStorage:', e);
    }
  };

  const handleDeleteHeader = (key: string) => {
    if (!window.confirm(`Delete header "${key}"?`)) return;

    const newHeaders = { ...unifiedHeaders };
    delete newHeaders[key];
    setUnifiedHeaders(newHeaders);

    // Save to localStorage
    try {
      localStorage.setItem('parts-unified-headers', JSON.stringify(newHeaders));
    } catch (e) {
      console.warn('⚠️ Failed to save to localStorage:', e);
    }
  };

  const handleAddHeader = () => {
    const key = prompt('Enter header key:');
    if (!key || !key.trim()) return;

    // Validate: check if key is in the blocked list
    if (isBlockedHeader(key.trim())) {
      alert(`❌ Header "${key}" is blocked.\n\n🚫 Blocked headers: ${BLOCKED_HEADERS.join(', ')}\n\nThese headers are automatically removed for security/compatibility.`);
      return;
    }

    if (unifiedHeaders[key.trim()]) {
      alert('❌ Header key already exists!');
      return;
    }

    const value = prompt('Enter header value:');
    if (value === null) return;

    const newHeaders = {
      ...unifiedHeaders,
      [key.trim()]: value.trim()
    };
    setUnifiedHeaders(newHeaders);

    // Save to localStorage
    try {
      localStorage.setItem('parts-unified-headers', JSON.stringify(newHeaders));
    } catch (e) {
      console.warn('⚠️ Failed to save to localStorage:', e);
    }

    addLog(`➕ Parts Tab: Added header ${key.trim()}`);
  };

  const handleResetHeaders = () => {
    if (!window.confirm('Reset all headers to default values?\n\nThis will affect all tiles.')) return;

    setUnifiedHeaders(UNIFIED_HEADERS);

    // Save to localStorage
    try {
      localStorage.setItem('parts-unified-headers', JSON.stringify(UNIFIED_HEADERS));
    } catch (e) {
      console.warn('⚠️ Failed to save to localStorage:', e);
    }

    alert('✅ Headers reset to default values!');
    addLog(`🔄 Parts Tab: Headers reset to default`);

  };

  const handleCopyBody = () => {
    navigator.clipboard.writeText(editingBody)
      .then(() => alert('✅ Body copied to clipboard!'))
      .catch(() => alert('❌ Failed to copy'));
  };

  const handlePrettifyBody = () => {
    try {
      const parsed = JSON.parse(editingBody);
      setEditingBody(JSON.stringify(parsed, null, 2));
    } catch (error: any) {
      alert(`❌ Invalid JSON: ${error.message}`);
    }
  };

  // PDF Configuration Editor Handlers
  const handleOpenPdfConfigEditor = () => {
    // Extract current WARRANTY and RETURN values from pre-request script if they exist
    const currentScript = preRequestScripts['pdf-config'] || '';

    // Parse existing values (simple regex extraction)
    const warrantyMatch = currentScript.match(/pm\.environment\.set\("WARRANTY",\s*"(.*)"\)/);
    const returnMatch = currentScript.match(/pm\.environment\.set\("RETURN",\s*"(.*)"\)/);

    // Unescape the values for editing - convert \\\\n back to actual newlines for natural editing
    const unescapeText = (text: string) => {
      return text
        .replace(/\\\\n/g, '\n')    // \\\\n → actual newline (reverse of our double escaping)
        .replace(/\\\\r/g, '\r')    // \\\\r → carriage return
        .replace(/\\"/g, '"')       // \" → "
        .replace(/\\'/g, "'")       // \' → '
        .replace(/\\\\\\\\/g, '\\'); // \\\\\\\\ → \ (8 backslashes to 1)
    };

    setWarrantyText(warrantyMatch ? unescapeText(warrantyMatch[1]) : '');
    setReturnText(returnMatch ? unescapeText(returnMatch[1]) : '');
    setIsPdfModalOpen(true);
  };

  const handleSavePdfConfig = () => {
    // Escape function: converts user text to JavaScript-safe strings
    // Convert actual newlines (Enter key) to \\\\n so they appear as \\n in the saved script
    // which then becomes \n when the variable is used, and \\n in the final JSON
    const escapeForJavaScript = (text: string): string => {
      return text
        .replace(/\\/g, '\\\\\\\\')   // Backslash → 4 backslashes (for double escaping)
        .replace(/\n/g, '\\\\n')      // Newline → \\\\n (so it shows as \\n in script, \n in variable)
        .replace(/\r/g, '\\\\r')      // Carriage return
        .replace(/"/g, '\\"')         // Double quote
        .replace(/'/g, "\\'");        // Single quote
    };

    const escapedWarranty = escapeForJavaScript(warrantyText);
    const escapedReturn = escapeForJavaScript(returnText);

    // Generate pre-request script
    const newScript = `pm.environment.set("RETURN", "${escapedReturn}");
pm.environment.set("WARRANTY", "${escapedWarranty}");`;

    // Update pre-request scripts state
    setPreRequestScripts(prev => ({
      ...prev,
      'pdf-config': newScript
    }));

    setIsPdfModalOpen(false);
    addLog(`✅ Parts Tab: PDF Configuration policies updated`);
  };

  const handleClosePdfModal = () => {
    setIsPdfModalOpen(false);
  };

  // OEM & Makes Editor Handlers
  const handleOpenOemMakesEditor = () => {
    const currentBody = tileBodies['oem-makes'];

    if (currentBody?.oemDetails) {
      const selected: Record<string, string[]> = {};
      currentBody.oemDetails.forEach((detail: any) => {
        selected[detail.oem] = detail.makeId || [];
      });
      setSelectedMakes(selected);
    }

    if (currentBody?.dealerCodeWithMake?.[0]?.dealerCode) {
      setDealerCode(currentBody.dealerCodeWithMake[0].dealerCode);
    }

    setOemSearchQuery('');
    setIsOemMakesModalOpen(true);
  };

  const handleToggleMake = (oem: string, make: string) => {
    setSelectedMakes(prev => {
      const currentMakes = prev[oem] || [];

      if (currentMakes.includes(make)) {
        // Deselect make
        const newMakes = currentMakes.filter(m => m !== make);
        if (newMakes.length === 0) {
          // No makes left, remove OEM
          const newState = { ...prev };
          delete newState[oem];
          return newState;
        }
        return { ...prev, [oem]: newMakes };
      } else {
        // Select make (auto-select OEM)
        return { ...prev, [oem]: [...currentMakes, make] };
      }
    });
  };

  const handleToggleOem = (oem: string) => {
    const currentMakes = selectedMakes[oem] || [];
    const allMakes = OEM_MAKES_DATA[oem];

    if (currentMakes.length === allMakes.length) {
      // All selected, deselect all
      const newState = { ...selectedMakes };
      delete newState[oem];
      setSelectedMakes(newState);
    } else {
      // Select all
      setSelectedMakes(prev => ({
        ...prev,
        [oem]: [...allMakes]
      }));
    }
  };

  const handleSelectAllOems = () => {
    const allSelected: Record<string, string[]> = {};
    Object.entries(OEM_MAKES_DATA).forEach(([oem, makes]) => {
      allSelected[oem] = [...makes];
    });
    setSelectedMakes(allSelected);
  };

  const handleSaveOemMakes = () => {
    const totalMakes = Object.values(selectedMakes).flat().length;

    if (totalMakes === 0) {
      alert('❌ Please select at least one make');
      return;
    }

    // Helper function to convert to title case
    const toTitleCase = (str: string): string => {
      return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    };

    // Generate oemDetails array with complete structure
    const oemDetails = Object.entries(selectedMakes).map(([oem, makes]) => {
      const oemLower = oem.toLowerCase();
      const makeIdArray = makes.map(m => m.toLowerCase());

      return {
        displayName: OEM_DISPLAY_NAMES[oemLower] || toTitleCase(oemLower),
        oemImageUrl: null,
        oem: oemLower,
        makeId: makeIdArray,
        makeDetails: makes.map(make => {
          const lowerMake = make.toLowerCase();
          return {
            make: lowerMake,
            makeId: lowerMake,
            displayName: toTitleCase(lowerMake),
            dealerCode: dealerCode.trim(),
            makeLogoUrl: null
          };
        }),
        make: makeIdArray // Duplicate of makeId (required by API)
      };
    });

    // Generate dealerCodeWithMake array
    const dealerCodeWithMake = Object.entries(selectedMakes)
      .flatMap(([oem, makes]) =>
        makes.map(make => ({
          dealerCode: dealerCode.trim(),
          make: make.toLowerCase()
        }))
      );

    const newBody = {
      oemDetails,
      dealerCodeWithMake
    };

    const updatedBodies = {
      ...tileBodies,
      'oem-makes': newBody
    };

    setTileBodies(updatedBodies);

    setSavedTileBodies(prev => ({
      ...prev,
      'oem-makes': newBody
    }));

    setEditingBody(JSON.stringify(newBody, null, 2));

    // Save to localStorage for persistence across reloads
    try {
      localStorage.setItem('parts-tab-tile-bodies', JSON.stringify(updatedBodies));
      console.log('✅ Saved OEM & Makes to localStorage');
    } catch (e) {
      console.warn('⚠️ Failed to save to localStorage:', e);
    }

    setIsOemMakesModalOpen(false);
    addLog(`✅ Parts Tab: OEM & Makes saved - ${oemDetails.length} OEMs, ${totalMakes} makes`);
  };

  const handleCloseOemMakesModal = () => {
    setIsOemMakesModalOpen(false);
  };

  return (
    <div className={`parts-app-container ${isLeftPanelCollapsed ? 'panel-collapsed' : ''}`}>
      {/* Left Panel: Tiles List */}
      <div className={`parts-left-panel ${isLeftPanelCollapsed ? 'collapsed' : ''}`}>
        <div className="parts-left-header">
          <div className="parts-left-header-content">
            <h1>🔧 Parts Tiles</h1>
            <p>Configuration Tasks</p>
          </div>
          <button
            className="parts-panel-toggle"
            onClick={handleTogglePanel}
            title="Toggle sidebar"
            aria-label="Toggle sidebar"
          >
            <svg width="20" height="20" viewBox="0 0 20 20" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
              <path d="M16.5 4C17.3284 4 18 4.67157 18 5.5V14.5C18 15.3284 17.3284 16 16.5 16H3.5C2.67157 16 2 15.3284 2 14.5V5.5C2 4.67157 2.67157 4 3.5 4H16.5ZM7 15H16.5C16.7761 15 17 14.7761 17 14.5V5.5C17 5.22386 16.7761 5 16.5 5H7V15ZM3.5 5C3.22386 5 3 5.22386 3 5.5V14.5C3 14.7761 3.22386 15 3.5 15H6V5H3.5Z" />
            </svg>
          </button>
        </div>

        <div className="parts-stats-bar">
          <div className="parts-stat-mini">
            <div className="parts-stat-mini-value">{stats.success}</div>
            <div className="parts-stat-mini-label">Success</div>
          </div>
          <div className="parts-stat-mini">
            <div className="parts-stat-mini-value">{stats.pending}</div>
            <div className="parts-stat-mini-label">Pending</div>
          </div>
          <div className="parts-stat-mini">
            <div className="parts-stat-mini-value">{stats.error}</div>
            <div className="parts-stat-mini-label">Failed</div>
          </div>
          <div className="parts-stat-mini">
            <button
              className="parts-btn-manage-tiles"
              onClick={() => setIsManageTilesModalOpen(true)}
              title="Manage tiles (delete, restore, reorder)"
            >
              ⚙️
            </button>
          </div>
        </div>

        <div className="parts-tiles-scroll">
          <div className="parts-tile-list">
            {activeTiles.map(tile => {
              const state = tileStates[tile.id] || { status: 'pending' };
              const statusInfo = getStatusInfo(state.status);
              const isActive = selectedTileId === tile.id;
              const isDragging = draggedTileId === tile.id;
              const isDragOver = dragOverTileId === tile.id;

              return (
                <div
                  key={tile.id}
                  className={`parts-tile-item ${isActive ? 'active' : ''} ${isDragging ? 'dragging' : ''} ${isDragOver ? 'drag-over' : ''}`}
                  onClick={() => handleSelectTile(tile.id)}
                  draggable
                  onDragStart={(e) => handleDragStart(e, tile.id)}
                  onDragOver={(e) => handleDragOver(e, tile.id)}
                  onDragLeave={handleDragLeave}
                  onDrop={(e) => handleDrop(e, tile.id)}
                  onDragEnd={handleDragEnd}
                >
                  <div className="parts-tile-drag-handle" title="Drag to reorder">
                    ⋮⋮
                  </div>
                  <div className="parts-tile-item-header">
                    <div className="parts-tile-icon">{tile.icon}</div>
                    <div className="parts-tile-info">
                      <div className="parts-tile-name">{tile.name}</div>
                      <div className="parts-tile-category">{tile.category}</div>
                    </div>
                  </div>
                  <div className="parts-tile-item-footer">
                    <span className="parts-badge-method">{tile.method}</span>
                    <span className={`parts-badge-status ${statusInfo.class}`}>{statusInfo.icon}</span>
                  </div>
                  <button
                    className="parts-tile-delete-btn"
                    onClick={(e) => handleDeleteTile(tile.id, e)}
                    title="Delete this tile"
                  >
                    🗑️
                  </button>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Right Panel: Request Configuration */}
      <div className="parts-right-panel">
        <div className="parts-right-header">
          <h2>{selectedTile?.icon} {selectedTile?.name || 'Parts Configuration'}</h2>
          <p>{selectedTile?.description || 'Select a tile from the left to view details'}</p>
        </div>

        <div className="parts-right-content">
          {selectedTile && (
            <>
              {/* Request Configuration Section */}
              <section className="parts-section">
                <div className="parts-section-header">
                  <h3 className="parts-section-title">📋 Request Configuration</h3>
                </div>

                {/* Method + URL + Execute */}
                <div className="parts-request-line">
                  <select
                    className={`parts-method-selector parts-method-${selectedTile.method.toLowerCase()}`}
                    disabled
                    value={selectedTile.method}
                  >
                    <option value={selectedTile.method}>{selectedTile.method}</option>
                  </select>
                  <input
                    type="text"
                    className="parts-url-input"
                    value={tileUrls[selectedTileId] || selectedTile.url}
                    onChange={(e) => {
                      setTileUrls(prev => ({
                        ...prev,
                        [selectedTileId]: e.target.value
                      }));
                    }}
                    placeholder="Enter URL with {{variables}}"
                  />
                  <button
                    className="parts-btn-execute"
                    onClick={() => handleExecuteTile(selectedTile.id)}
                  >
                    🚀 Execute
                  </button>
                </div>

                {/* Tabs: Headers and Body */}
                <div className="parts-request-tabs-container">
                  <div className="parts-request-tabs">
                    {/* PDF Config Editor Button - ONLY for pdf-config tile */}
                    {selectedTile.id === 'pdf-config' && (
                      <button
                        className="parts-btn-pdf-editor"
                        onClick={handleOpenPdfConfigEditor}
                      >
                        📝 Edit Policy
                      </button>
                    )}

                    {/* OEM Makes Editor Button - ONLY for oem-makes tile */}
                    {selectedTile.id === 'oem-makes' && (
                      <button
                        className="parts-btn-pdf-editor"
                        onClick={handleOpenOemMakesEditor}
                      >
                        🏭 Edit OEM & Makes
                      </button>
                    )}

                    <button
                      className={`parts-tab-btn ${activeTab === 'headers' ? 'active' : ''}`}
                      onClick={() => setActiveTab('headers')}
                    >
                      Headers
                    </button>
                    <button
                      className={`parts-tab-btn ${activeTab === 'body' ? 'active' : ''}`}
                      onClick={() => setActiveTab('body')}
                    >
                      Body
                    </button>
                    <button
                      className={`parts-tab-btn ${activeTab === 'pre-request' ? 'active' : ''}`}
                      onClick={() => setActiveTab('pre-request')}
                    >
                      Pre-request Script
                    </button>
                  </div>

                  <div className="parts-tab-content">
                    {/* Headers Tab */}
                    {activeTab === 'headers' && (
                      <div className="parts-tab-panel active">
                        <div className="parts-editor-toolbar">
                          <span style={{ color: '#999', fontSize: '13px' }}>
                            {Object.keys(unifiedHeaders).length} headers • Shared across all tiles
                          </span>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="parts-btn-icon" onClick={handleToggleBulkEdit}>
                              📝 Bulk Edit
                            </button>
                            <button className="parts-btn-icon" onClick={handleResetHeaders}>
                              🔄 Reset
                            </button>
                          </div>
                        </div>

                        {/* Key-Value Table (Postman style) */}
                        {!isBulkEditMode && (
                          <div className="parts-headers-table-container">
                            <table className="parts-headers-table">
                              <thead>
                                <tr>
                                  <th style={{ width: '35%' }}>KEY</th>
                                  <th style={{ width: '60%' }}>VALUE</th>
                                  <th style={{ width: '5%' }}></th>
                                </tr>
                              </thead>
                              <tbody>
                                {Object.entries(unifiedHeaders).map(([key, value]) => (
                                  <tr key={key}>
                                    <td>
                                      <input
                                        type="text"
                                        className="parts-header-input-key"
                                        value={key}
                                        onChange={(e) => handleUpdateHeaderKey(key, e.target.value)}
                                        onBlur={(e) => {
                                          if (e.target.value !== key) {
                                            handleUpdateHeaderKey(key, e.target.value);
                                          }
                                        }}
                                      />
                                    </td>
                                    <td>
                                      <input
                                        type="text"
                                        className="parts-header-input-value"
                                        value={value}
                                        onChange={(e) => handleUpdateHeaderValue(key, e.target.value)}
                                      />
                                    </td>
                                    <td>
                                      <button
                                        className="parts-btn-delete"
                                        onClick={() => handleDeleteHeader(key)}
                                        title="Delete"
                                      >
                                        ×
                                      </button>
                                    </td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                            <button className="parts-btn-add-header" onClick={handleAddHeader}>
                              + Add Header
                            </button>
                          </div>
                        )}

                        {/* Bulk Edit Textarea */}
                        {isBulkEditMode && (
                          <div className="parts-headers-bulk-container">
                            <textarea
                              className="parts-bulk-edit-textarea"
                              rows={15}
                              value={bulkEditText}
                              onChange={(e) => setBulkEditText(e.target.value)}
                            />
                            <div style={{ display: 'flex', gap: '8px', marginTop: '12px' }}>
                              <button className="parts-btn-secondary" onClick={handleSaveBulkEdit}>
                                💾 Save
                              </button>
                              <button className="parts-btn-secondary" onClick={handleToggleBulkEdit}>
                                Cancel
                              </button>
                            </div>
                          </div>
                        )}
                      </div>
                    )}

                    {/* Body Tab */}
                    {activeTab === 'body' && (
                      <div className="parts-tab-panel active">
                        <div className="parts-editor-toolbar">
                          <span style={{ color: '#4a9eff', fontWeight: 600 }}>
                            JSON Body
                            {hasUnsavedBodyChanges && <span style={{ color: '#ff9f43', marginLeft: '8px' }}>⚠️ Unsaved changes</span>}
                          </span>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="parts-btn-icon" onClick={handlePrettifyBody}>
                              🎨 Prettify
                            </button>
                            <button className="parts-btn-icon" onClick={handleCopyBody}>
                              📋 Copy
                            </button>
                            <button
                              className={`parts-save-btn ${hasUnsavedBodyChanges ? 'has-changes' : ''}`}
                              onClick={handleSaveBody}
                              disabled={!hasUnsavedBodyChanges}
                            >
                              💾 {hasUnsavedBodyChanges ? 'Save Changes' : 'Saved'}
                            </button>
                          </div>
                        </div>
                        <textarea
                          className="parts-json-editor"
                          rows={15}
                          value={editingBody}
                          onChange={(e) => setEditingBody(e.target.value)}
                          placeholder="Enter JSON body..."
                        />
                        <div className="parts-editor-footer">
                          <span className="char-count">
                            {editingBody.length} characters
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Pre-request Script Tab */}
                    {activeTab === 'pre-request' && (
                      <div className="parts-tab-panel active">
                        <div className="parts-editor-toolbar">
                          <span style={{ color: '#4a9eff', fontWeight: 600 }}>📜 JavaScript</span>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button
                              className="parts-btn-icon"
                              onClick={() => {
                                const formatted = editingScript;
                                alert('💡 Tip: Use Prettier or format manually');
                              }}
                            >
                              🎨 Beautify
                            </button>
                            <button
                              className="parts-btn-icon"
                              onClick={() => {
                                setEditingScript('');
                              }}
                            >
                              🗑️ Clear
                            </button>
                            <button
                              className={`parts-save-btn ${hasUnsavedChanges ? 'has-changes' : ''}`}
                              onClick={handleSavePreRequestScript}
                              disabled={!hasUnsavedChanges}
                            >
                              💾 {hasUnsavedChanges ? 'Save Changes' : 'Saved'}
                            </button>
                          </div>
                        </div>

                        <div className="parts-info-message" style={{ marginBottom: '12px' }}>
                          💡 This JavaScript code runs BEFORE the request is sent. Use it to set variables, modify headers, or add dynamic data.
                          {hasUnsavedChanges && <span style={{ color: '#ff9800', marginLeft: '12px' }}>⚠️ Unsaved changes</span>}
                        </div>

                        <textarea
                          className="parts-code-editor"
                          rows={18}
                          placeholder={`// Example: Set dynamic timestamp\npm.environment.set("timestamp", Date.now());\n\n// Example: Generate random ID\nconst randomId = Math.random().toString(36).substr(2, 9);\npm.variables.set("requestId", randomId);\n\n// Example: Modify headers\npm.request.headers.add({\n  key: "X-Request-ID",\n  value: randomId\n});\n\n// Example: Log to console\nconsole.log("Pre-request script executed at:", new Date().toISOString());\n\n// Example: Conditional logic\nif (pm.environment.get("environment") === "production") {\n  console.log("Running in production mode");\n}`}
                          value={editingScript}
                          onChange={(e) => setEditingScript(e.target.value)}
                        />

                        <details className="parts-help-section" style={{ marginTop: '16px' }}>
                          <summary style={{ cursor: 'pointer', color: '#4a9eff', fontWeight: 600, padding: '8px 0' }}>
                            💡 Available pm APIs
                          </summary>
                          <div style={{ padding: '12px', background: '#1a1a1a', borderRadius: '6px', marginTop: '8px' }}>
                            <code style={{ display: 'block', marginBottom: '8px', color: '#60a5fa' }}>
                              pm.environment.set(key, value) - Set environment variable
                            </code>
                            <code style={{ display: 'block', marginBottom: '8px', color: '#60a5fa' }}>
                              pm.environment.get(key) - Get environment variable
                            </code>
                            <code style={{ display: 'block', marginBottom: '8px', color: '#60a5fa' }}>
                              pm.variables.set(key, value) - Set local variable
                            </code>
                            <code style={{ display: 'block', marginBottom: '8px', color: '#60a5fa' }}>
                              pm.variables.get(key) - Get variable
                            </code>
                            <code style={{ display: 'block', marginBottom: '8px', color: '#60a5fa' }}>
                              pm.request.headers.add({`{key, value}`}) - Add request header
                            </code>
                            <code style={{ display: 'block', marginBottom: '8px', color: '#60a5fa' }}>
                              pm.sendRequest(url, callback) - Send async HTTP request
                            </code>
                            <code style={{ display: 'block', color: '#60a5fa' }}>
                              console.log(...) - Log output to console
                            </code>
                          </div>
                        </details>
                      </div>
                    )}
                  </div>
                </div>
              </section>

              {/* Response Section (shown after execution) */}
              {tileStates[selectedTile.id]?.lastExecuted && (
                <section className="parts-section parts-response-section">
                  <div className="parts-section-header">
                    <h3 className="parts-section-title">📊 Response</h3>
                    <div className="parts-response-meta">
                      <span className={`parts-status-badge parts-status-${tileStates[selectedTile.id].responseStatus || 200}`}>
                        {tileStates[selectedTile.id].responseStatus || 200} {tileStates[selectedTile.id].responseStatusText || 'OK'}
                      </span>
                      <span className="parts-time-badge">
                        ⏱️ {tileStates[selectedTile.id].responseTime || 0}ms
                      </span>
                      <span className="parts-size-badge">
                        📦 {tileStates[selectedTile.id].responseSize || '0.0'} KB
                      </span>
                      <button
                        className="parts-copy-btn"
                        onClick={() => {
                          const responseText = tileStates[selectedTile.id].responseBody || '{}';
                          navigator.clipboard.writeText(responseText);
                          addLog(`📋 Parts Tab: Response copied to clipboard (${responseText.length} characters)`);
                        }}
                        title="Copy response to clipboard"
                      >
                        📋 Copy Response
                      </button>
                    </div>
                  </div>

                  <div className="parts-response-body">
                    <pre className="parts-json-response">
                      {tileStates[selectedTile.id].responseBody || '{}'}
                    </pre>
                  </div>
                </section>
              )}
            </>
          )}
        </div>
      </div>

      {/* PDF Configuration Editor Modal */}
      {isPdfModalOpen && (
        <div className="parts-modal-overlay" onClick={handleClosePdfModal}>
          <div className="parts-modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="parts-modal-header">
              <h3>📝 Edit Warranty & Return Policy</h3>
              <button className="parts-modal-close" onClick={handleClosePdfModal}>×</button>
            </div>

            <div className="parts-modal-body">
              <div className="parts-modal-field">
                <label className="parts-modal-label">
                  Warranty Text
                  <span className="parts-modal-hint">💡 Press Enter for line breaks - they'll be converted to \n automatically</span>
                </label>
                <textarea
                  className="parts-modal-textarea"
                  rows={8}
                  value={warrantyText}
                  onChange={(e) => setWarrantyText(e.target.value)}
                  placeholder="Any warranties on the products sold hereby are those made by the manufacturer.&#10;&#10;The Seller hereby expressly disclaims all warranties..."
                />
              </div>

              <div className="parts-modal-field">
                <label className="parts-modal-label">
                  Return Policy Text
                  <span className="parts-modal-hint">💡 Press Enter for line breaks - they'll be converted to \n automatically</span>
                </label>
                <textarea
                  className="parts-modal-textarea"
                  rows={8}
                  value={returnText}
                  onChange={(e) => setReturnText(e.target.value)}
                  placeholder="NO RETURNS ON ELECTRICAL OR SPECIAL ORDER ITEMS&#10;NO REFUNDS AFTER 15 DAYS&#10;All sales are final."
                />
              </div>
            </div>

            <div className="parts-modal-footer">
              <button className="parts-btn-modal-cancel" onClick={handleClosePdfModal}>
                Cancel
              </button>
              <button className="parts-btn-modal-save" onClick={handleSavePdfConfig}>
                💾 Save & Update Script
              </button>
            </div>
          </div>
        </div>
      )}

      {/* OEM & Makes Editor Modal */}
      {isOemMakesModalOpen && (
        <div className="parts-modal-overlay" onClick={handleCloseOemMakesModal}>
          <div className="parts-modal-content oem-makes-modal" onClick={(e) => e.stopPropagation()}>
            <div className="parts-modal-header">
              <h3>🏭 Select OEM & Makes</h3>
              <button className="parts-modal-close" onClick={handleCloseOemMakesModal}>×</button>
            </div>

            <div className="parts-modal-body">
              {/* Search Bar */}
              <input
                type="text"
                className="oem-search-input"
                placeholder="🔍 Search OEM or Make..."
                value={oemSearchQuery}
                onChange={(e) => setOemSearchQuery(e.target.value)}
              />

              {/* Dealer Code Input */}
              <div className="oem-dealer-code-field">
                <label>Dealer Code:</label>
                <input
                  type="text"
                  value={dealerCode}
                  onChange={(e) => setDealerCode(e.target.value)}
                  placeholder="548349"
                />
              </div>

              {/* OEM Groups */}
              <div className="oem-groups-container">
                {(() => {
                  const filteredAndSorted = Object.entries(OEM_MAKES_DATA)
                    .filter(([oem, makes]) => {
                      const query = oemSearchQuery.toLowerCase();
                      return oem.toLowerCase().includes(query) ||
                             makes.some(make => make.toLowerCase().includes(query));
                    })
                    .sort(([oemA], [oemB]) => {
                      const hasSelectionA = (selectedMakes[oemA]?.length || 0) > 0;
                      const hasSelectionB = (selectedMakes[oemB]?.length || 0) > 0;

                      // Selected OEMs first
                      if (hasSelectionA && !hasSelectionB) return -1;
                      if (!hasSelectionA && hasSelectionB) return 1;

                      // Within same group (selected or unselected), sort alphabetically by display name
                      const nameA = OEM_DISPLAY_NAMES[oemA] || oemA;
                      const nameB = OEM_DISPLAY_NAMES[oemB] || oemB;
                      return nameA.localeCompare(nameB);
                    });

                  const selectedCount = filteredAndSorted.filter(([oem]) =>
                    (selectedMakes[oem]?.length || 0) > 0
                  ).length;

                  return filteredAndSorted.map(([oem, makes], index) => {
                    const selected = selectedMakes[oem] || [];
                    const allSelected = selected.length === makes.length;
                    const someSelected = selected.length > 0 && !allSelected;
                    const isFirstUnselected = index === selectedCount && selectedCount > 0;

                    return (
                      <React.Fragment key={oem}>
                        {/* Separator between selected and unselected */}
                        {isFirstUnselected && (
                          <div className="oem-separator">
                            <span>Other OEMs</span>
                          </div>
                        )}
                        <div className="oem-group">
                        {/* OEM Header Checkbox */}
                        <div className="oem-header" onClick={() => handleToggleOem(oem)}>
                          <input
                            type="checkbox"
                            checked={allSelected}
                            ref={el => {
                              if (el) el.indeterminate = someSelected;
                            }}
                            onChange={() => handleToggleOem(oem)}
                            onClick={(e) => e.stopPropagation()}
                          />
                          <strong>{OEM_DISPLAY_NAMES[oem] || oem.toUpperCase()}</strong>
                          <span className="oem-count">
                            ({selected.length}/{makes.length} makes)
                          </span>
                        </div>

                        {/* Makes Checkboxes */}
                        <div className="makes-grid">
                          {makes.map(make => (
                            <label key={make} className="make-checkbox">
                              <input
                                type="checkbox"
                                checked={selected.includes(make)}
                                onChange={() => handleToggleMake(oem, make)}
                              />
                              <span>{make.charAt(0).toUpperCase() + make.slice(1)}</span>
                            </label>
                          ))}
                        </div>
                      </div>
                      </React.Fragment>
                    );
                  });
                })()}
              </div>

              {/* Summary */}
              <div className="oem-selection-summary">
                Selected: {Object.values(selectedMakes).flat().length} makes from {Object.keys(selectedMakes).length} OEMs
              </div>
            </div>

            <div className="parts-modal-footer">
              <button className="parts-btn-modal-cancel" onClick={() => setSelectedMakes({})}>
                Clear All
              </button>
              <button className="parts-btn-modal-cancel" onClick={handleSelectAllOems}>
                Select All
              </button>
              <button className="parts-btn-modal-cancel" onClick={handleCloseOemMakesModal}>
                Cancel
              </button>
              <button className="parts-btn-modal-save" onClick={handleSaveOemMakes}>
                💾 Save & Apply
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Manage Tiles Modal */}
      {isManageTilesModalOpen && (
        <div className="parts-modal-overlay" onClick={() => setIsManageTilesModalOpen(false)}>
          <div className="parts-modal-content parts-manage-tiles-modal" onClick={(e) => e.stopPropagation()}>
            <div className="parts-modal-header">
              <h2>⚙️ Manage Parts Tiles</h2>
              <button className="parts-modal-close" onClick={() => setIsManageTilesModalOpen(false)}>×</button>
            </div>

            <div className="parts-modal-body">
              {/* Stats */}
              <div className="manage-tiles-stats">
                <div className="manage-tiles-stat">
                  <span className="manage-tiles-stat-label">Active Tiles:</span>
                  <span className="manage-tiles-stat-value">{activeTiles.length}/{PARTS_TILES.length}</span>
                </div>
                <div className="manage-tiles-stat">
                  <span className="manage-tiles-stat-label">Deleted:</span>
                  <span className="manage-tiles-stat-value">{deletedTileIds.length}</span>
                </div>
              </div>

              {/* Deleted Tiles Section */}
              {deletedTileIds.length > 0 && (
                <div className="manage-tiles-section">
                  <h3 className="manage-tiles-section-title">🗑️ Deleted Tiles ({deletedTileIds.length})</h3>
                  <div className="manage-tiles-list">
                    {deletedTileIds.map(tileId => {
                      const tile = PARTS_TILES.find(t => t.id === tileId);
                      if (!tile) return null;

                      return (
                        <div key={tileId} className="manage-tiles-item">
                          <span className="manage-tiles-item-icon">{tile.icon}</span>
                          <div className="manage-tiles-item-info">
                            <div className="manage-tiles-item-name">{tile.name}</div>
                            <div className="manage-tiles-item-category">{tile.category}</div>
                          </div>
                          <button
                            className="manage-tiles-restore-btn"
                            onClick={() => handleRestoreTile(tileId)}
                          >
                            ↩️ Restore
                          </button>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Info */}
              <div className="manage-tiles-info">
                <p>💡 <strong>Tips:</strong></p>
                <ul>
                  <li><strong>Drag & Drop:</strong> Reorder tiles in the main list</li>
                  <li><strong>Delete:</strong> Click the 🗑️ button on any tile</li>
                  <li><strong>Restore:</strong> Use the buttons above to restore deleted tiles</li>
                  <li><strong>Export:</strong> Save your configuration as code to make it permanent</li>
                </ul>
              </div>
            </div>

            <div className="parts-modal-footer">
              <button className="parts-btn-modal-cancel" onClick={handleResetToDefaults}>
                🔄 Reset to Defaults
              </button>
              <button className="parts-btn-modal-save" onClick={handleExportToCode}>
                📤 Export to Code
              </button>
              <button className="parts-btn-modal-save" onClick={() => setIsManageTilesModalOpen(false)}>
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

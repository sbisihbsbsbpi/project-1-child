/**
 * CSV/Excel Parser
 * Handles file upload and column detection
 */

import { ParsedCsvData } from './types';

/**
 * Parse CSV file content
 */
export function parseCsvContent(content: string): ParsedCsvData {
  const lines = content.trim().split('\n');
  
  if (lines.length === 0) {
    throw new Error('CSV file is empty');
  }
  
  // Parse header row
  const headers = parseCSVLine(lines[0]);
  
  // Parse data rows
  const rows: any[] = [];
  for (let i = 1; i < lines.length; i++) {
    if (lines[i].trim()) {
      const values = parseCSVLine(lines[i]);
      const row: any = {};
      headers.forEach((header, index) => {
        row[header] = values[index] || '';
      });
      rows.push(row);
    }
  }
  
  // Auto-detect columns
  const emailColumn = detectEmailColumn(headers);
  const oemIdColumn = detectOemIdColumn(headers);
  
  return {
    headers,
    rows,
    emailColumn,
    oemIdColumn
  };
}

/**
 * Parse a single CSV line (handles quoted values)
 */
function parseCSVLine(line: string): string[] {
  const result: string[] = [];
  let current = '';
  let inQuotes = false;
  
  for (let i = 0; i < line.length; i++) {
    const char = line[i];
    
    if (char === '"') {
      inQuotes = !inQuotes;
    } else if (char === ',' && !inQuotes) {
      result.push(current.trim());
      current = '';
    } else {
      current += char;
    }
  }
  
  result.push(current.trim());
  return result;
}

/**
 * Detect email column from headers
 */
function detectEmailColumn(headers: string[]): string | null {
  const emailPatterns = ['email', 'e-mail', 'mail', 'user', 'username', 'user_email'];
  
  for (const header of headers) {
    const normalized = header.toLowerCase().trim();
    if (emailPatterns.some(pattern => normalized.includes(pattern))) {
      return header;
    }
  }
  
  return null;
}

/**
 * Detect OEM ID column from headers
 */
function detectOemIdColumn(headers: string[]): string | null {
  const oemIdPatterns = ['oemid', 'oem_id', 'oem-id', 'id', 'oemId'];
  
  for (const header of headers) {
    const normalized = header.toLowerCase().trim();
    if (oemIdPatterns.some(pattern => normalized === pattern.toLowerCase())) {
      return header;
    }
  }
  
  return null;
}

/**
 * Read file as text
 */
export function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    
    reader.onload = (e) => {
      const content = e.target?.result as string;
      resolve(content);
    };
    
    reader.onerror = () => {
      reject(new Error('Failed to read file'));
    };
    
    reader.readAsText(file);
  });
}

/**
 * Validate CSV data
 */
export function validateCsvData(data: ParsedCsvData): {
  valid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (!data.emailColumn) {
    errors.push('Could not detect email column. Please ensure your CSV has a column named "email"');
  }
  
  if (!data.oemIdColumn) {
    errors.push('Could not detect OEM ID column. Please ensure your CSV has a column named "oemId"');
  }
  
  if (data.rows.length === 0) {
    errors.push('CSV file has no data rows');
  }
  
  if (data.rows.length > 1000) {
    errors.push(`CSV has ${data.rows.length} rows. Maximum supported is 1000. Please split into smaller batches.`);
  }
  
  return {
    valid: errors.length === 0,
    errors
  };
}

/**
 * Extract update rows from parsed CSV
 */
export function extractUpdateRows(data: ParsedCsvData): Array<{ email: string; oemId: string }> {
  if (!data.emailColumn || !data.oemIdColumn) {
    return [];
  }
  
  return data.rows
    .filter(row => row[data.emailColumn!] && row[data.oemIdColumn!])
    .map(row => ({
      email: row[data.emailColumn!].trim(),
      oemId: row[data.oemIdColumn!].trim()
    }));
}

/**
 * cURL Command Parser
 * Extracts headers from cURL commands or raw header text
 */

import { OemUpdateHeaders } from './types';

/**
 * Parse a cURL command and extract headers
 */
export function parseCurlCommand(curlText: string): Partial<OemUpdateHeaders> {
  const headers: Record<string, string> = {};
  
  // Match -H 'header: value' or --header "header: value" patterns
  const headerRegex = /(?:-H|--header)\s+['"]([^:]+):\s*([^'"]+)['"]/g;
  let match;
  
  while ((match = headerRegex.exec(curlText)) !== null) {
    const headerName = match[1].toLowerCase().trim();
    const headerValue = match[2].trim();
    headers[headerName] = headerValue;
  }
  
  return headers;
}

/**
 * Parse raw headers text (one per line)
 * Format: "header-name:value" or "header-name: value"
 */
export function parseHeadersText(headersText: string): Partial<OemUpdateHeaders> {
  const headers: Record<string, string> = {};
  const lines = headersText.split('\n');
  
  for (const line of lines) {
    const trimmedLine = line.trim();
    if (!trimmedLine) continue;
    
    const colonIndex = trimmedLine.indexOf(':');
    if (colonIndex === -1) continue;
    
    const headerName = trimmedLine.substring(0, colonIndex).toLowerCase().trim();
    const headerValue = trimmedLine.substring(colonIndex + 1).trim();
    
    if (headerName && headerValue) {
      headers[headerName] = headerValue;
    }
  }
  
  return headers;
}

/**
 * Auto-detect format and parse
 */
export function parseHeadersAuto(input: string): Partial<OemUpdateHeaders> {
  input = input.trim();
  
  // Check if it looks like a cURL command
  if (input.startsWith('curl ') || input.includes('-H ') || input.includes('--header')) {
    return parseCurlCommand(input);
  }
  
  // Otherwise, treat as raw headers
  return parseHeadersText(input);
}

/**
 * Validate that required headers are present
 */
export function validateHeaders(headers: Partial<OemUpdateHeaders>): {
  valid: boolean;
  missing: string[];
  errors: string[];
} {
  const required = ['dealerid', 'tekion-api-token'];
  const missing: string[] = [];
  const errors: string[] = [];
  
  for (const field of required) {
    if (!headers[field as keyof OemUpdateHeaders]) {
      missing.push(field);
    }
  }
  
  // Additional validation
  if (headers.dealerid && !/^\d+$/.test(headers.dealerid)) {
    errors.push('dealerid must be a numeric value');
  }
  
  if (headers['tekion-api-token'] && !headers['tekion-api-token'].startsWith('eyJ')) {
    errors.push('tekion-api-token appears to be invalid (should start with "eyJ")');
  }
  
  return {
    valid: missing.length === 0 && errors.length === 0,
    missing,
    errors
  };
}

/**
 * Format headers for display
 */
export function formatHeadersForDisplay(headers: Partial<OemUpdateHeaders>): string {
  const lines: string[] = [];
  
  // Show important headers first
  const priority = ['dealerid', 'tekion-api-token', 'tenantname', 'userid'];
  
  for (const key of priority) {
    if (headers[key as keyof OemUpdateHeaders]) {
      const value = headers[key as keyof OemUpdateHeaders];
      // Truncate token for display
      if (key === 'tekion-api-token' && value && value.length > 50) {
        lines.push(`${key}: ${value.substring(0, 30)}...${value.substring(value.length - 10)}`);
      } else {
        lines.push(`${key}: ${value}`);
      }
    }
  }
  
  // Show count of other headers
  const otherCount = Object.keys(headers).length - priority.filter(k => headers[k as keyof OemUpdateHeaders]).length;
  if (otherCount > 0) {
    lines.push(`... and ${otherCount} more headers`);
  }
  
  return lines.join('\n');
}

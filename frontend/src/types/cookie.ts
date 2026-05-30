/**
 * 🍪 Cookie Type Definitions
 * 
 * TypeScript interfaces for cookie management, security auditing, and browser cookie extraction.
 * 
 * @module types/cookie
 * @author AI Assistant
 * @date 2026-03-06
 */

/**
 * Standard HTTP Cookie structure
 */
export interface Cookie {
  /** Cookie name */
  name: string;
  
  /** Cookie value */
  value: string;
  
  /** Domain the cookie belongs to */
  domain: string;
  
  /** Path scope of the cookie */
  path?: string;
  
  /** Expiration date/time (ISO string or timestamp) */
  expires?: string | number;
  
  /** Whether cookie is HTTP-only (not accessible via JavaScript) */
  httpOnly?: boolean;
  
  /** Whether cookie requires HTTPS */
  secure?: boolean;
  
  /** SameSite attribute for CSRF protection */
  sameSite?: 'Strict' | 'Lax' | 'None';
  
  /** Cookie size in bytes (optional metadata) */
  size?: number;
  
  /** Session cookie flag */
  session?: boolean;
}

/**
 * Security audit issue
 */
export interface SecurityIssue {
  /** Severity level */
  severity: 'high' | 'medium' | 'low';
  
  /** Issue description */
  message: string;
  
  /** Related cookie name (if applicable) */
  cookie?: string;
  
  /** Issue type/category */
  type?: string;
}

/**
 * Security audit warning
 */
export interface SecurityWarning {
  /** Warning type/category */
  type: string;
  
  /** Warning message */
  message: string;
  
  /** Related cookie name (if applicable) */
  cookie?: string;
  
  /** Severity level */
  severity?: 'high' | 'medium' | 'low';
}

/**
 * Security audit recommendation
 */
export interface SecurityRecommendation {
  /** Priority level */
  priority: 'high' | 'medium' | 'low';
  
  /** Recommendation message */
  message: string;
  
  /** Related cookie name (if applicable) */
  cookie?: string;
  
  /** Action to take */
  action?: string;
}

/**
 * Complete security audit report
 */
export interface SecurityAuditReport {
  /** List of security issues found */
  issues: SecurityIssue[];
  
  /** List of warnings */
  warnings: SecurityWarning[];
  
  /** List of recommendations */
  recommendations: SecurityRecommendation[];
  
  /** Overall security score (0-100) */
  score?: number;
  
  /** Audit timestamp */
  timestamp?: string;
}

/**
 * HAR (HTTP Archive) format cookie
 */
export interface HARCookie {
  name: string;
  value: string;
  path?: string;
  domain?: string;
  expires?: string;
  httpOnly?: boolean;
  secure?: boolean;
  sameSite?: string;
}

/**
 * Browser cookie extraction status
 */
export interface CookieImportStatus {
  /** Playwright cookie status */
  playwright?: {
    exists: boolean;
    cookie_count: number;
    extracted_at?: string;
  };
  
  /** Camoufox cookie status */
  camoufox?: {
    exists: boolean;
    cookie_count: number;
    size_mb?: number;
  };
}

/**
 * Cookie export format options
 */
export type CookieExportFormat = 'json' | 'netscape' | 'har' | 'curl' | 'playwright';

/**
 * Cookie import format options
 */
export type CookieImportFormat = 'json' | 'netscape' | 'har';


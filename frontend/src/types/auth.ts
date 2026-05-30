/**
 * 🔐 Authentication Type Definitions
 * 
 * Type definitions for authentication and authorization functionality.
 * 
 * @module types/auth
 * @author AI Assistant
 * @date 2025-11-03
 */

/**
 * Cookie data structure
 */
export interface Cookie {
  /** Cookie name */
  name: string;
  
  /** Cookie value */
  value: string;
  
  /** Cookie domain */
  domain: string;
  
  /** Cookie path */
  path?: string;
  
  /** Expiration timestamp (Unix epoch) */
  expires?: number;
  
  /** HTTP only flag */
  httpOnly?: boolean;
  
  /** Secure flag */
  secure?: boolean;
  
  /** SameSite policy */
  sameSite?: 'Strict' | 'Lax' | 'None';
}

/**
 * LocalStorage item structure
 */
export interface LocalStorageItem {
  /** Item key */
  name: string;
  
  /** Item value (JSON string) */
  value: string;
}

/**
 * Authentication state status
 */
export interface AuthStateStatus {
  /** Whether auth state file exists */
  exists: boolean;
  
  /** Number of cookies saved */
  cookie_count?: number;
  
  /** Number of localStorage items saved */
  localStorage_count?: number;
  
  /** List of cookies */
  cookies?: Cookie[];
  
  /** List of localStorage items */
  localStorage_items?: LocalStorageItem[];
}

/**
 * Authentication settings
 */
export interface AuthSettings {
  /** Raw cookie string (Netscape format) */
  cookies: string;
  
  /** Raw localStorage data (JSON string) */
  localStorageData: string;
  
  /** Login URL for manual authentication */
  loginUrl: string;
}

/**
 * Login modal state
 */
export interface LoginModalState {
  /** Whether modal is visible */
  isOpen: boolean;
  
  /** Login URL */
  url: string;
  
  /** Whether login is in progress */
  isLoading: boolean;
}

/**
 * Default auth settings
 */
export const DEFAULT_AUTH_SETTINGS: AuthSettings = {
  cookies: '',
  localStorageData: '',
  loginUrl: 'https://preprodapp.tekioncloud.com/home',
};


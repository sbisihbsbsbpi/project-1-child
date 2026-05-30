/**
 * 📁 Session Type Definitions
 * 
 * Type definitions for session management functionality.
 * Sessions allow saving and loading capture configurations.
 * 
 * @module types/session
 * @author AI Assistant
 * @date 2025-11-03
 */

import type { CaptureSettings, NamingSettings } from './capture';
import type { AuthSettings } from './auth';

/**
 * Session data structure
 * 
 * A session saves all settings and URLs for a specific capture scenario.
 * Users can create multiple sessions for different projects/clients.
 */
export interface Session {
  /** Unique session identifier */
  id: string;
  
  /** Session name (user-defined) */
  name: string;
  
  /** Session description */
  description?: string;
  
  /** Creation timestamp */
  createdAt: string;
  
  /** Last modified timestamp */
  updatedAt: string;
  
  /** Capture settings for this session */
  captureSettings: CaptureSettings;
  
  /** File naming settings for this session */
  namingSettings: NamingSettings;
  
  /** Authentication settings for this session */
  authSettings?: AuthSettings;
  
  /** List of URLs to capture */
  urls: string[];
  
  /** Session tags for organization */
  tags?: string[];
  
  /** Session color for visual identification */
  color?: string;
}

/**
 * Session creation input
 */
export interface CreateSessionInput {
  /** Session name (required) */
  name: string;
  
  /** Session description (optional) */
  description?: string;
  
  /** Initial capture settings (optional, uses current if not provided) */
  captureSettings?: Partial<CaptureSettings>;
  
  /** Initial naming settings (optional, uses current if not provided) */
  namingSettings?: Partial<NamingSettings>;
  
  /** Initial auth settings (optional, uses current if not provided) */
  authSettings?: Partial<AuthSettings>;
  
  /** Initial URLs (optional, uses current if not provided) */
  urls?: string[];
  
  /** Session tags (optional) */
  tags?: string[];
  
  /** Session color (optional) */
  color?: string;
}

/**
 * Session update input
 */
export interface UpdateSessionInput {
  /** Session ID to update */
  id: string;
  
  /** New session name (optional) */
  name?: string;
  
  /** New session description (optional) */
  description?: string;
  
  /** Updated capture settings (optional) */
  captureSettings?: Partial<CaptureSettings>;
  
  /** Updated naming settings (optional) */
  namingSettings?: Partial<NamingSettings>;
  
  /** Updated auth settings (optional) */
  authSettings?: Partial<AuthSettings>;
  
  /** Updated URLs (optional) */
  urls?: string[];
  
  /** Updated tags (optional) */
  tags?: string[];
  
  /** Updated color (optional) */
  color?: string;
}

/**
 * Session filter options
 */
export interface SessionFilter {
  /** Filter by name (partial match) */
  name?: string;
  
  /** Filter by tags (any match) */
  tags?: string[];
  
  /** Filter by creation date range */
  createdAfter?: string;
  createdBefore?: string;
  
  /** Filter by update date range */
  updatedAfter?: string;
  updatedBefore?: string;
}

/**
 * Session sort options
 */
export type SessionSortField = 'name' | 'createdAt' | 'updatedAt';
export type SessionSortOrder = 'asc' | 'desc';

export interface SessionSort {
  field: SessionSortField;
  order: SessionSortOrder;
}


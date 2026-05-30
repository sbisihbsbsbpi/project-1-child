/**
 * 🔗 URL Management Type Definitions
 * 
 * Type definitions for URL folder and URL item management.
 * 
 * @module types/url
 * @author AI Assistant
 * @date 2025-11-03
 */

/**
 * URL item within a folder
 */
export interface URLItem {
  /** Unique identifier for this URL */
  id: number;
  
  /** The actual URL string */
  url: string;
  
  /** When this URL was added */
  addedAt: string;
  
  /** Optional notes about this URL */
  notes?: string;
  
  /** Whether this URL is enabled for capture */
  enabled?: boolean;
}

/**
 * URL folder containing multiple URLs
 */
export interface URLFolder {
  /** Unique folder identifier */
  id: string;
  
  /** Folder name */
  name: string;
  
  /** Folder description */
  description?: string;
  
  /** List of URLs in this folder */
  urls: URLItem[];
  
  /** When this folder was created */
  createdAt: string;
  
  /** When this folder was last modified */
  updatedAt: string;
  
  /** Folder color for visual identification */
  color?: string;
  
  /** Folder icon (emoji or icon name) */
  icon?: string;
  
  /** Whether folder is collapsed in UI */
  collapsed?: boolean;
}

/**
 * URL folder creation input
 */
export interface CreateURLFolderInput {
  /** Folder name (required) */
  name: string;
  
  /** Folder description (optional) */
  description?: string;
  
  /** Initial URLs (optional) */
  urls?: string[];
  
  /** Folder color (optional) */
  color?: string;
  
  /** Folder icon (optional) */
  icon?: string;
}

/**
 * URL folder update input
 */
export interface UpdateURLFolderInput {
  /** Folder ID to update */
  id: string;
  
  /** New folder name (optional) */
  name?: string;
  
  /** New folder description (optional) */
  description?: string;
  
  /** New folder color (optional) */
  color?: string;
  
  /** New folder icon (optional) */
  icon?: string;
}

/**
 * URL sort options
 */
export type URLSortField = 'date' | 'alpha';
export type URLSortOrder = 'asc' | 'desc';

export interface URLSort {
  field: URLSortField;
  order: URLSortOrder;
}

/**
 * Combined sort type for backward compatibility
 */
export type URLSortType = 'date-desc' | 'date-asc' | 'alpha-asc' | 'alpha-desc';

/**
 * URL search/filter options
 */
export interface URLFilter {
  /** Search query (partial match on URL) */
  query?: string;
  
  /** Filter by enabled status */
  enabled?: boolean;
  
  /** Filter by date range */
  addedAfter?: string;
  addedBefore?: string;
}

/**
 * URL bulk operation types
 */
export type URLBulkOperation = 
  | 'delete'
  | 'enable'
  | 'disable'
  | 'move'
  | 'copy'
  | 'export';

/**
 * URL bulk operation input
 */
export interface URLBulkOperationInput {
  /** Folder ID containing the URLs */
  folderId: string;
  
  /** URL IDs to operate on */
  urlIds: number[];
  
  /** Operation to perform */
  operation: URLBulkOperation;
  
  /** Target folder ID (for move/copy operations) */
  targetFolderId?: string;
}


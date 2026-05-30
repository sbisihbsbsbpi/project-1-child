/**
 * 📦 Type Definitions - Main Export
 * 
 * Central export point for all TypeScript type definitions used throughout the application.
 * 
 * @module types
 * @author AI Assistant
 * @date 2025-11-03
 */

// Re-export all types from individual modules
export * from './capture';
export * from './auth';
export * from './session';
export * from './url';

/**
 * Common utility types used across the application
 */

/** Generic API response wrapper */
export interface APIResponse<T = any> {
  status: 'success' | 'error';
  message?: string;
  data?: T;
  error?: string;
}

/** Generic pagination metadata */
export interface PaginationMeta {
  current: number;
  total: number;
  hasMore: boolean;
}

/** Generic sort order */
export type SortOrder = 'asc' | 'desc';

/** Generic filter function */
export type FilterFn<T> = (item: T) => boolean;

/** Generic comparator function for sorting */
export type CompareFn<T> = (a: T, b: T) => number;


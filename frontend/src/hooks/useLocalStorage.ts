/**
 * 💾 Simple localStorage Hook
 * 
 * A simple, type-safe localStorage hook without debouncing.
 * Use this for values that change infrequently.
 * For frequently changing values, use useDebouncedLocalStorage instead.
 * 
 * @module hooks/useLocalStorage
 * @author AI Assistant
 * @date 2025-11-03
 * 
 * @example
 * ```tsx
 * // Simple string value
 * const [name, setName] = useLocalStorage('user-name', 'John');
 * 
 * // Complex object
 * const [settings, setSettings] = useLocalStorage('app-settings', {
 *   theme: 'dark',
 *   language: 'en'
 * });
 * ```
 */

import { useState, useEffect } from 'react';

/**
 * Simple localStorage hook with type safety
 * 
 * @template T - Type of the stored value
 * @param key - localStorage key
 * @param defaultValue - Default value if key doesn't exist
 * @returns Tuple of [value, setValue] similar to useState
 */
export function useLocalStorage<T>(
  key: string,
  defaultValue: T
): [T, React.Dispatch<React.SetStateAction<T>>] {
  // Read initial value from localStorage
  const [value, setValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key);
      if (item === null) {
        return defaultValue;
      }
      
      // Try to parse as JSON
      try {
        return JSON.parse(item) as T;
      } catch {
        // If parsing fails, return as-is (for plain strings)
        return item as T;
      }
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  });

  // Save to localStorage whenever value changes
  useEffect(() => {
    try {
      const valueToStore = typeof value === 'string' 
        ? value 
        : JSON.stringify(value);
      
      localStorage.setItem(key, valueToStore);
    } catch (error) {
      console.error(`Error writing localStorage key "${key}":`, error);
    }
  }, [key, value]);

  return [value, setValue];
}

/**
 * localStorage hook with custom serializer/deserializer
 * 
 * Use this when you need custom serialization logic (e.g., Date objects, Map, Set)
 * 
 * @template T - Type of the stored value
 * @param key - localStorage key
 * @param defaultValue - Default value if key doesn't exist
 * @param serializer - Custom serialization function
 * @param deserializer - Custom deserialization function
 * @returns Tuple of [value, setValue] similar to useState
 * 
 * @example
 * ```tsx
 * const [date, setDate] = useLocalStorageWithSerializer(
 *   'last-visit',
 *   new Date(),
 *   (date) => date.toISOString(),
 *   (str) => new Date(str)
 * );
 * ```
 */
export function useLocalStorageWithSerializer<T>(
  key: string,
  defaultValue: T,
  serializer: (value: T) => string,
  deserializer: (value: string) => T
): [T, React.Dispatch<React.SetStateAction<T>>] {
  // Read initial value from localStorage
  const [value, setValue] = useState<T>(() => {
    try {
      const item = localStorage.getItem(key);
      if (item === null) {
        return defaultValue;
      }
      return deserializer(item);
    } catch (error) {
      console.error(`Error reading localStorage key "${key}":`, error);
      return defaultValue;
    }
  });

  // Save to localStorage whenever value changes
  useEffect(() => {
    try {
      const serialized = serializer(value);
      localStorage.setItem(key, serialized);
    } catch (error) {
      console.error(`Error writing localStorage key "${key}":`, error);
    }
  }, [key, value, serializer]);

  return [value, setValue];
}

/**
 * Hook to remove a localStorage item
 * 
 * @param key - localStorage key to remove
 * @returns Function to remove the item
 * 
 * @example
 * ```tsx
 * const removeAuthToken = useLocalStorageRemove('auth-token');
 * 
 * // Later...
 * removeAuthToken(); // Removes 'auth-token' from localStorage
 * ```
 */
export function useLocalStorageRemove(key: string): () => void {
  return () => {
    try {
      localStorage.removeItem(key);
    } catch (error) {
      console.error(`Error removing localStorage key "${key}":`, error);
    }
  };
}

/**
 * Hook to clear all localStorage items with a specific prefix
 * 
 * @param prefix - Prefix to match (e.g., 'screenshot-')
 * @returns Function to clear matching items
 * 
 * @example
 * ```tsx
 * const clearScreenshotData = useLocalStorageClearPrefix('screenshot-');
 * 
 * // Later...
 * clearScreenshotData(); // Removes all keys starting with 'screenshot-'
 * ```
 */
export function useLocalStorageClearPrefix(prefix: string): () => void {
  return () => {
    try {
      const keys = Object.keys(localStorage);
      keys.forEach(key => {
        if (key.startsWith(prefix)) {
          localStorage.removeItem(key);
        }
      });
    } catch (error) {
      console.error(`Error clearing localStorage with prefix "${prefix}":`, error);
    }
  };
}


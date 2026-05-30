/**
 * ✅ FIXED: Centralized configuration for frontend
 * Uses environment variables instead of hardcoded values
 */

export const config = {
  // Backend API base URL
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8001",

  // Request timeout (5 minutes)
  requestTimeout: 300000,

  // WebSocket reconnect settings
  wsReconnectDelay: 3000,
  wsMaxReconnectAttempts: 5,
} as const;

/**
 * Helper function to build API URLs
 */
export const apiUrl = (path: string): string => {
  // Remove leading slash if present
  const cleanPath = path.startsWith("/") ? path.slice(1) : path;
  return `${config.apiBaseUrl}/${cleanPath}`;
};

export default config;

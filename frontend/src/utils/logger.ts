/**
 * Centralized logging utility using loglevel
 * 
 * Features:
 * - Automatic dev/prod switching
 * - Log levels: debug, info, warn, error
 * - Timestamp formatting
 * - Clean, professional output
 * 
 * Usage:
 * ```typescript
 * import log from './utils/logger';
 * 
 * log.debug('Debug message');
 * log.info('Info message');
 * log.warn('Warning message');
 * log.error('Error message', error);
 * ```
 */

import log from 'loglevel';

// Configure log level based on environment
if (import.meta.env.DEV) {
  log.setLevel('debug'); // Show all logs in development
} else {
  log.setLevel('warn'); // Only warnings and errors in production
}

// Custom formatting with timestamps and log levels
const originalFactory = log.methodFactory;

log.methodFactory = function (methodName, logLevel, loggerName) {
  const rawMethod = originalFactory(methodName, logLevel, loggerName);
  
  return function (...args) {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0]; // HH:MM:SS format
    const level = methodName.toUpperCase().padEnd(5, ' '); // Align log levels
    const prefix = `[${timestamp}] [${level}]`;
    
    // Call the original method with our prefix
    rawMethod(prefix, ...args);
  };
};

// Apply the custom factory
log.setLevel(log.getLevel());

export default log;


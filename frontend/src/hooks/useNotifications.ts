/**
 * 🔔 Notifications Hook
 *
 * Custom hook for managing toast notifications with queue, auto-dismiss, and history.
 *
 * @module hooks/useNotifications
 * @author AI Assistant
 * @date 2025-11-14
 *
 * @example
 * ```tsx
 * const { notifications, addNotification, removeNotification, clearAll } = useNotifications();
 *
 * // Add success notification
 * addNotification({
 *   type: 'success',
 *   title: 'Success!',
 *   message: 'Screenshot captured',
 *   duration: 5000
 * });
 * ```
 */

import { useState, useCallback, useRef } from "react";
import {
  ToastNotification,
  NotificationOptions,
  NotificationType,
} from "../types/notification";

interface UseNotificationsReturn {
  notifications: ToastNotification[];
  history: ToastNotification[];
  addNotification: (options: NotificationOptions) => string;
  removeNotification: (id: string) => void;
  clearAll: () => void;
  clearHistory: () => void;
}

/**
 * Default notification durations by type (in milliseconds)
 */
const DEFAULT_DURATIONS: Record<NotificationType, number> = {
  success: 5000,
  error: 7000,
  warning: 6000,
  info: 5000,
};

/**
 * Auto-detect notification type from message content
 */
const detectType = (message: string): NotificationType => {
  const lowerMessage = message.toLowerCase();

  if (
    message.includes("✅") ||
    lowerMessage.includes("success") ||
    lowerMessage.includes("complete")
  ) {
    return "success";
  } else if (
    message.includes("❌") ||
    lowerMessage.includes("error") ||
    lowerMessage.includes("failed")
  ) {
    return "error";
  } else if (message.includes("⚠️") || lowerMessage.includes("warning")) {
    return "warning";
  } else {
    return "info";
  }
};

/**
 * Auto-generate title based on type
 */
const generateTitle = (type: NotificationType): string => {
  switch (type) {
    case "success":
      return "✅ Success";
    case "error":
      return "❌ Error";
    case "warning":
      return "⚠️ Warning";
    case "info":
    default:
      return "ℹ️ Information";
  }
};

/**
 * Generate random screen position for toast
 * Ensures toasts appear within viewport bounds with padding
 */
const generateRandomPosition = (
  existingPositions: Array<{ top: number; left: number }>
): { top: number; left: number } => {
  // Get viewport dimensions
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;

  // Toast dimensions (approximate)
  const toastWidth = 420;
  const toastHeight = 120;

  // Add padding from edges
  const padding = 20;

  // Calculate safe ranges
  const maxLeft = Math.max(padding, viewportWidth - toastWidth - padding);
  const maxTop = Math.max(padding, viewportHeight - toastHeight - padding);

  // Try to find a non-overlapping position (max 10 attempts)
  let attempts = 0;
  let position: { top: number; left: number };

  do {
    // Generate random position within safe range
    const left = Math.random() * maxLeft;
    const top = Math.random() * maxTop;
    position = { top, left };

    // Check if overlaps with existing toasts
    const overlaps = existingPositions.some((existing) => {
      const horizontalOverlap = !(
        position.left + toastWidth < existing.left ||
        position.left > existing.left + toastWidth
      );
      const verticalOverlap = !(
        position.top + toastHeight < existing.top ||
        position.top > existing.top + toastHeight
      );
      return horizontalOverlap && verticalOverlap;
    });

    if (!overlaps) {
      return position;
    }

    attempts++;
  } while (attempts < 10);

  // If we couldn't find a non-overlapping position after 10 attempts, just use the last one
  return position!;
};

/**
 * Custom hook for managing notifications
 */
export const useNotifications = (): UseNotificationsReturn => {
  const [notifications, setNotifications] = useState<ToastNotification[]>([]);
  const [history, setHistory] = useState<ToastNotification[]>([]);
  const notificationIdCounter = useRef(0);

  // ✅ Removed misleading log - this runs on every render, not just mount

  /**
   * Add a new notification
   */
  const addNotification = useCallback(
    (options: NotificationOptions): string => {
      const id = `notification-${Date.now()}-${notificationIdCounter.current++}`;

      // Auto-detect type if not provided
      const type = options.type || detectType(options.message);

      // Auto-generate title if not provided
      const title = options.title || generateTitle(type);

      // Use default duration if not provided
      const duration =
        options.duration !== undefined
          ? options.duration
          : DEFAULT_DURATIONS[type];

      // Get existing positions to avoid overlaps
      const existingPositions = notifications
        .filter((n) => n.position)
        .map((n) => n.position!);

      // Generate random position
      const position = generateRandomPosition(existingPositions);

      const notification: ToastNotification = {
        id,
        type,
        title,
        message: options.message,
        icon: options.icon,
        duration,
        dismissible: options.dismissible !== false,
        timestamp: new Date(),
        visible: true,
        position, // ✅ Add random position
      };

      setNotifications((prev) => [notification, ...prev]); // Add to beginning (newest first)

      setHistory((prev) => {
        const newHistory = [notification, ...prev];
        // Keep only last 100 notifications in history
        if (newHistory.length > 100) {
          console.log(
            `🔔 History limit reached, trimming to 100 notifications`
          );
          return newHistory.slice(0, 100);
        }
        return newHistory;
      });

      return id;
    },
    [notifications]
  );

  /**
   * Remove a notification by ID
   */
  const removeNotification = useCallback((id: string) => {
    setNotifications((prev) => prev.filter((n) => n.id !== id));
  }, []);

  /**
   * Clear all active notifications
   */
  const clearAll = useCallback(() => {
    setNotifications([]);
  }, []);

  /**
   * Clear notification history
   */
  const clearHistory = useCallback(() => {
    console.log(`🔔 Clearing notification history (${history.length} items)`);
    setHistory([]);
  }, [history.length]);

  return {
    notifications,
    history,
    addNotification,
    removeNotification,
    clearAll,
    clearHistory,
  };
};

export default useNotifications;

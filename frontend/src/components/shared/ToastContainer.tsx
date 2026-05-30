/**
 * 🍞 Toast Container Component
 *
 * Container for managing and displaying multiple toast notifications.
 * Handles stacking, positioning, and z-index management.
 *
 * @module components/shared/ToastContainer
 * @author AI Assistant
 * @date 2025-11-14
 *
 * @example
 * ```tsx
 * <ToastContainer
 *   notifications={notifications}
 *   onDismiss={removeNotification}
 *   position="top-right"
 *   maxVisible={5}
 * />
 * ```
 */

import React from "react";
import { ToastNotification } from "../../types/notification";
import Toast from "./Toast";

interface ToastContainerProps {
  notifications: ToastNotification[];
  onDismiss: (id: string) => void;
  position?: "top-right" | "top-left" | "bottom-right" | "bottom-left";
  maxVisible?: number;
}

/**
 * Toast container component
 */
export const ToastContainer: React.FC<ToastContainerProps> = ({
  notifications,
  onDismiss,
  position = "top-right",
  maxVisible = 5,
}) => {
  // ✅ Removed misleading log - this runs on every render, not just when notifications change

  // Limit visible notifications
  const visibleNotifications = notifications.slice(0, maxVisible);

  if (visibleNotifications.length < notifications.length) {
    console.log(
      `🍞 ToastContainer: Hiding ${
        notifications.length - visibleNotifications.length
      } notifications (exceeds max)`
    );
  }

  const positionClass = (() => {
    switch (position) {
      case "top-left":
        return "toast-container-top-left";
      case "bottom-right":
        return "toast-container-bottom-right";
      case "bottom-left":
        return "toast-container-bottom-left";
      case "top-right":
      default:
        return "toast-container-top-right";
    }
  })();

  return (
    <div
      aria-live="polite"
      aria-atomic="false"
      role="region"
      aria-label="Notifications"
      className={`toast-container ${positionClass}`}
    >
      {visibleNotifications.map((notification) => (
        <Toast
          key={notification.id}
          notification={notification}
          onDismiss={onDismiss}
        />
      ))}
    </div>
  );
};

export default ToastContainer;

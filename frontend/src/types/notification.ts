/**
 * 🔔 Notification Type Definitions
 *
 * Type definitions for the toast notification system.
 *
 * @module types/notification
 * @author AI Assistant
 * @date 2025-11-14
 */

/**
 * Notification type (determines color and icon)
 */
export type NotificationType = "success" | "error" | "warning" | "info";

/**
 * Toast notification interface
 */
export interface ToastNotification {
  /** Unique identifier */
  id: string;

  /** Notification type (success/error/warning/info) */
  type: NotificationType;

  /** Notification title */
  title: string;

  /** Notification message/body */
  message: string;

  /** Custom icon (optional, defaults based on type) */
  icon?: string;

  /** Auto-dismiss duration in milliseconds (0 = no auto-dismiss) */
  duration?: number;

  /** Whether notification can be manually dismissed */
  dismissible?: boolean;

  /** Timestamp when notification was created */
  timestamp: Date;

  /** Whether notification is currently visible */
  visible?: boolean;

  /** Random position on screen (optional) */
  position?: {
    top: number;
    left: number;
  };
}

/**
 * WebSocket message types
 */
export interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

/**
 * Progress update message
 */
export interface ProgressMessage extends WebSocketMessage {
  type: "progress";
  current: number;
  total: number;
  url: string;
  status: string;
  request_id?: string;
}

/**
 * URL configuration detected message
 */
export interface URLConfigDetectedMessage extends WebSocketMessage {
  type: "url_config_detected";
  config_name: string;
  url: string;
  actions_count: number;
}

/**
 * URL configuration action message
 */
export interface URLConfigActionMessage extends WebSocketMessage {
  type: "url_config_action";
  action_index: number;
  total_actions: number;
  action_type: string;
  description: string;
}

/**
 * Form processing message
 */
export interface FormProcessingMessage extends WebSocketMessage {
  type: "form_processing";
  form_index: number;
  total_forms: number;
  form_name: string;
  status: string;
}

/**
 * Segment progress message
 */
export interface SegmentProgressMessage extends WebSocketMessage {
  type: "segment_progress";
  segment_index: number;
  total_segments: number;
  url: string;
}

/**
 * Screenshot result message
 */
export interface ScreenshotResultMessage extends WebSocketMessage {
  type: "result";
  url: string;
  status: "success" | "error";
  message?: string;
}

/**
 * Notification history filter
 */
export interface NotificationFilter {
  type?: NotificationType;
  dateRange?: {
    start: Date;
    end: Date;
  };
  searchQuery?: string;
}

/**
 * Notification options for creating new notifications
 */
export interface NotificationOptions {
  type?: NotificationType;
  title?: string;
  message: string;
  icon?: string;
  duration?: number;
  dismissible?: boolean;
}

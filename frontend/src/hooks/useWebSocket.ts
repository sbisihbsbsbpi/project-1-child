/**
 * 🔌 WebSocket Hook
 * 
 * Custom hook for managing WebSocket connection with auto-reconnect and message handling.
 * 
 * @module hooks/useWebSocket
 * @author AI Assistant
 * @date 2025-11-14
 * 
 * @example
 * ```tsx
 * const { isConnected, lastMessage, sendMessage } = useWebSocket({
 *   url: 'ws://127.0.0.1:8000/ws',
 *   onMessage: (message) => console.log('Received:', message),
 *   autoReconnect: true
 * });
 * ```
 */

import { useState, useEffect, useRef, useCallback } from 'react';
import { WebSocketMessage } from '../types/notification';
import config from '../config';

interface UseWebSocketOptions {
  url?: string;
  onMessage?: (message: WebSocketMessage) => void;
  onOpen?: () => void;
  onClose?: () => void;
  onError?: (error: Event) => void;
  autoReconnect?: boolean;
  reconnectDelay?: number;
  maxReconnectAttempts?: number;
  pingInterval?: number;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: WebSocketMessage | null;
  sendMessage: (message: any) => void;
  reconnect: () => void;
  disconnect: () => void;
}

/**
 * Custom hook for WebSocket connection
 */
export const useWebSocket = (options: UseWebSocketOptions = {}): UseWebSocketReturn => {
  const {
    url = `ws://${config.apiBaseUrl.replace('http://', '').replace('https://', '')}/ws`,
    onMessage,
    onOpen,
    onClose,
    onError,
    autoReconnect = true,
    reconnectDelay = config.wsReconnectDelay || 3000,
    maxReconnectAttempts = config.wsMaxReconnectAttempts || 5,
    pingInterval = 30000, // 30 seconds
  } = options;

  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<WebSocketMessage | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const pingIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const shouldReconnectRef = useRef(true);

  // ✅ Removed misleading log - this runs on every render, not just mount

  /**
   * Send a message through WebSocket
   */
  const sendMessage = useCallback((message: any) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      const messageStr = typeof message === 'string' ? message : JSON.stringify(message);
      console.log(`🔌 WebSocket: Sending message: ${messageStr.substring(0, 100)}...`);
      wsRef.current.send(messageStr);
    } else {
      console.warn('🔌 WebSocket: Cannot send message - not connected');
    }
  }, []);

  /**
   * Start ping/pong keep-alive
   */
  const startPing = useCallback(() => {
    console.log(`🔌 WebSocket: Starting ping interval (${pingInterval}ms)`);
    
    if (pingIntervalRef.current) {
      clearInterval(pingIntervalRef.current);
    }

    pingIntervalRef.current = setInterval(() => {
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        console.log('🔌 WebSocket: Sending ping');
        sendMessage('ping');
      }
    }, pingInterval);
  }, [pingInterval, sendMessage]);

  /**
   * Stop ping/pong keep-alive
   */
  const stopPing = useCallback(() => {
    if (pingIntervalRef.current) {
      console.log('🔌 WebSocket: Stopping ping interval');
      clearInterval(pingIntervalRef.current);
      pingIntervalRef.current = null;
    }
  }, []);

  /**
   * Connect to WebSocket
   */
  const connect = useCallback(() => {
    console.log(`🔌 WebSocket: Attempting to connect to ${url}`);
    console.log(`🔌 WebSocket: Reconnect attempts: ${reconnectAttemptsRef.current}/${maxReconnectAttempts}`);

    try {
      const ws = new WebSocket(url);
      wsRef.current = ws;

      ws.onopen = () => {
        console.log('🔌 WebSocket: ✅ Connected successfully!');
        setIsConnected(true);
        reconnectAttemptsRef.current = 0;
        startPing();
        onOpen?.();
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          console.log(`🔌 WebSocket: 📨 Received message: ${message.type || 'unknown'}`);
          setLastMessage(message);
          onMessage?.(message);
        } catch (error) {
          console.log(`🔌 WebSocket: 📨 Received text: ${event.data}`);
          // Handle non-JSON messages (like "pong")
        }
      };

      ws.onerror = (error) => {
        console.error('🔌 WebSocket: ❌ Error occurred:', error);
        onError?.(error);
      };

      ws.onclose = () => {
        console.log('🔌 WebSocket: 🔌 Connection closed');
        setIsConnected(false);
        stopPing();
        onClose?.();

        // Auto-reconnect logic
        if (shouldReconnectRef.current && autoReconnect && reconnectAttemptsRef.current < maxReconnectAttempts) {
          reconnectAttemptsRef.current++;
          console.log(`🔌 WebSocket: 🔄 Reconnecting in ${reconnectDelay}ms (attempt ${reconnectAttemptsRef.current}/${maxReconnectAttempts})`);
          
          reconnectTimeoutRef.current = setTimeout(() => {
            connect();
          }, reconnectDelay);
        } else if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
          console.error('🔌 WebSocket: ❌ Max reconnect attempts reached');
        }
      };
    } catch (error) {
      console.error('🔌 WebSocket: ❌ Failed to create WebSocket:', error);
    }
  }, [url, autoReconnect, reconnectDelay, maxReconnectAttempts, onMessage, onOpen, onClose, onError, startPing, stopPing]);

  /**
   * Disconnect from WebSocket
   */
  const disconnect = useCallback(() => {
    console.log('🔌 WebSocket: Disconnecting...');
    shouldReconnectRef.current = false;
    stopPing();
    
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
  }, [stopPing]);

  /**
   * Manually reconnect
   */
  const reconnect = useCallback(() => {
    console.log('🔌 WebSocket: Manual reconnect requested');
    disconnect();
    shouldReconnectRef.current = true;
    reconnectAttemptsRef.current = 0;
    setTimeout(() => connect(), 100);
  }, [connect, disconnect]);

  // Connect on mount - ONLY ONCE
  useEffect(() => {
    console.log('🔌 WebSocket: Component mounted - connecting');
    connect();

    return () => {
      console.log('🔌 WebSocket: Component unmounting - cleanup');
      shouldReconnectRef.current = false;
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // ✅ FIX: Empty deps - connect only on mount, not when callbacks change

  return {
    isConnected,
    lastMessage,
    sendMessage,
    reconnect,
    disconnect,
  };
};

export default useWebSocket;


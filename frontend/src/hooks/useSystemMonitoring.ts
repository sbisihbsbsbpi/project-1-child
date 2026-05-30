/**
 * ✅ FIXED (Bug #14): Extract system monitoring logic from App.tsx
 * 
 * This hook handles system resource monitoring, reducing App.tsx complexity.
 */

import { useState, useEffect, useCallback } from 'react';
import config from '../config';
import log from '../utils/logger';

interface SystemUsageState {
  backend_rss_mb?: number | null;
  backend_cpu_percent?: number | null;
  system_ram_total_mb?: number | null;
  system_ram_used_mb?: number | null;
  system_ram_percent?: number | null;
  system_cpu_percent?: number | null;
  browser_rss_mb?: number | null;
  browser_cpu_percent?: number | null;
  status?: string;
  message?: string;
  timestamp?: string;
}

export function useSystemMonitoring(pollingInterval: number = 2000) {
  const [systemUsage, setSystemUsage] = useState<SystemUsageState | null>(null);
  const [isMonitoring, setIsMonitoring] = useState(false);

  const fetchSystemUsage = useCallback(async () => {
    try {
	      const res = await fetch(`${config.apiBaseUrl}/api/system/usage`);
	      if (res.ok) {
	        const data = await res.json();
	        setSystemUsage(data);
	      } else {
	        // Backend responded but not with a healthy payload
	        setSystemUsage({
	          status: "error",
	          message: `Backend responded with status ${res.status}`,
	          timestamp: new Date().toISOString(),
	        });
	      }
    } catch (err) {
      log.debug('Failed to fetch system usage', { error: err });
	      // Mark status as error so the UI shows backend as unavailable
	      setSystemUsage({
	        status: "error",
	        message: 'Backend unreachable',
	        timestamp: new Date().toISOString(),
	      });
    }
  }, []);

  useEffect(() => {
    if (!isMonitoring) {
      return;
    }

    let cancelled = false;
    let timeoutId: NodeJS.Timeout | null = null;

    const poll = async () => {
      if (cancelled) return;

      await fetchSystemUsage();

      if (!cancelled) {
        timeoutId = setTimeout(poll, pollingInterval);
      }
    };

    poll();

    return () => {
      cancelled = true;
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, [isMonitoring, pollingInterval, fetchSystemUsage]);

  const startMonitoring = useCallback(() => {
    setIsMonitoring(true);
  }, []);

  const stopMonitoring = useCallback(() => {
    setIsMonitoring(false);
    setSystemUsage(null);
  }, []);

  return {
    systemUsage,
    isMonitoring,
    startMonitoring,
    stopMonitoring,
    fetchSystemUsage,
  };
}


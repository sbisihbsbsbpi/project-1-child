import React from 'react';
import UrlStatusTable from '../UrlStatusTable';
import PerformanceMetrics from '../PerformanceMetrics';

interface RollingModeStats {
  totalUrls: number;
  completed: number;
  failed: number;
  active: number;
  avgTimePerUrl: number;
  estimatedTimeRemaining: number;
}

interface UrlStatus {
  url: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  startTime?: number;
  endTime?: number;
  duration?: number;
  screenshotCount?: number;
  error?: string;
  textBoxName: string;
}

interface PerformanceMetrics {
  throughput: number;
  successRate: number;
  avgScreenshotsPerUrl: number;
  totalScreenshots: number;
  peakConcurrency: number;
  startTime: number;
  elapsedTime: number;
}

interface LogsTabProps {
  logs: string[];
  copyLogs: () => void;
  clearLogs: () => void;
  rollingModeStats?: RollingModeStats;
  enableRollingMode?: boolean;
  urlStatuses?: Map<string, UrlStatus>;
  performanceMetrics?: PerformanceMetrics;
}

const LogsTabComponent: React.FC<LogsTabProps> = ({
  logs,
  copyLogs,
  clearLogs,
  rollingModeStats,
  enableRollingMode = false,
  urlStatuses,
  performanceMetrics
}) => {
  console.log("🎨 LogsTab rendering, logs.length =", logs.length);

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="tab-content">
      <div className="logs-section">
        <div className="logs-header">
          <h2>⏱️ Logs ({logs.length})</h2>
          <div className="logs-buttons">
            <button onClick={() => {
              console.log("📋 Copy Logs button clicked");
              copyLogs();
            }} className="copy-logs-btn">
              📋 Copy Logs
            </button>
            <button onClick={() => {
              console.log("🗑️ Clear Logs button clicked in LogsTab");
              clearLogs();
            }} className="clear-logs-btn">
              🗑️ Clear Logs
            </button>
          </div>
        </div>

        {/* ✅ NEW (Phase 4): Performance Metrics */}
        {enableRollingMode && performanceMetrics && performanceMetrics.startTime > 0 && (
          <PerformanceMetrics metrics={performanceMetrics} />
        )}

        {/* ✅ NEW (Phase 3): Rolling Mode Progress Display */}
        {enableRollingMode && rollingModeStats && rollingModeStats.totalUrls > 0 && (
          <div className="rolling-mode-progress">
            <div className="progress-header">
              <h3>🔄 Rolling Parallelization Progress</h3>
            </div>

            <div className="progress-stats">
              <div className="stat-item">
                <span className="stat-label">Total URLs:</span>
                <span className="stat-value">{rollingModeStats.totalUrls}</span>
              </div>
              <div className="stat-item success">
                <span className="stat-label">✅ Completed:</span>
                <span className="stat-value">{rollingModeStats.completed}</span>
              </div>
              {rollingModeStats.failed > 0 && (
                <div className="stat-item error">
                  <span className="stat-label">❌ Failed:</span>
                  <span className="stat-value">{rollingModeStats.failed}</span>
                </div>
              )}
              <div className="stat-item">
                <span className="stat-label">⏳ Remaining:</span>
                <span className="stat-value">
                  {rollingModeStats.totalUrls - rollingModeStats.completed - rollingModeStats.failed}
                </span>
              </div>
            </div>

            <div className="progress-bar-container">
              <div className="progress-bar">
                <div
                  className="progress-fill success"
                  style={{
                    width: `${(rollingModeStats.completed / rollingModeStats.totalUrls) * 100}%`
                  }}
                />
                {rollingModeStats.failed > 0 && (
                  <div
                    className="progress-fill error"
                    style={{
                      width: `${(rollingModeStats.failed / rollingModeStats.totalUrls) * 100}%`,
                      left: `${(rollingModeStats.completed / rollingModeStats.totalUrls) * 100}%`
                    }}
                  />
                )}
              </div>
              <div className="progress-text">
                {rollingModeStats.completed + rollingModeStats.failed}/{rollingModeStats.totalUrls} URLs
                ({((rollingModeStats.completed + rollingModeStats.failed) / rollingModeStats.totalUrls * 100).toFixed(1)}%)
              </div>
            </div>

            {rollingModeStats.avgTimePerUrl > 0 && (
              <div className="progress-timing">
                <div className="timing-item">
                  <span className="timing-label">Avg Time/URL:</span>
                  <span className="timing-value">{formatTime(rollingModeStats.avgTimePerUrl)}</span>
                </div>
                {rollingModeStats.estimatedTimeRemaining > 0 && (
                  <div className="timing-item">
                    <span className="timing-label">Est. Remaining:</span>
                    <span className="timing-value">{formatTime(rollingModeStats.estimatedTimeRemaining)}</span>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ✅ NEW (Phase 4): URL Status Table */}
        {enableRollingMode && urlStatuses && urlStatuses.size > 0 && (
          <UrlStatusTable urlStatuses={urlStatuses} showAll={false} />
        )}

        <div className="logs-container">
          {logs.length > 0 ? (
            logs.map((log, index) => (
              <div key={index} className="log-entry">
                {log}
              </div>
            ))
          ) : (
            <div className="log-entry">
              No logs yet. Start capturing to see logs.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

// ✅ Memoize to prevent unnecessary re-renders
export const LogsTab = React.memo(LogsTabComponent);


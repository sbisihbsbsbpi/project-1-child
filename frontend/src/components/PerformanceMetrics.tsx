import React, { useState, useEffect } from 'react';

interface PerformanceMetricsProps {
  metrics: {
    throughput: number;
    successRate: number;
    avgScreenshotsPerUrl: number;
    totalScreenshots: number;
    peakConcurrency: number;
    startTime: number;
    elapsedTime: number;
  };
}

const PerformanceMetrics: React.FC<PerformanceMetricsProps> = ({ metrics }) => {
  const [currentTime, setCurrentTime] = useState(Date.now());

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatTime = (seconds: number): string => {
    if (seconds < 60) return `${seconds.toFixed(0)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    if (mins < 60) return `${mins}m ${secs}s`;
    const hours = Math.floor(mins / 60);
    const remainingMins = mins % 60;
    return `${hours}h ${remainingMins}m`;
  };

  const getSuccessRateClass = (rate: number): string => {
    if (rate >= 95) return 'excellent';
    if (rate >= 80) return 'good';
    if (rate >= 60) return 'fair';
    return 'poor';
  };

  const getThroughputClass = (throughput: number): string => {
    if (throughput >= 5) return 'excellent';
    if (throughput >= 3) return 'good';
    if (throughput >= 1) return 'fair';
    return 'poor';
  };

  const elapsedTime = metrics.startTime > 0 
    ? (currentTime - metrics.startTime) / 1000 
    : metrics.elapsedTime;

  return (
    <div className="performance-metrics-container">
      <div className="metrics-header">
        <h3>📊 Performance Metrics</h3>
        <div className="elapsed-time">
          ⏱️ {formatTime(elapsedTime)}
        </div>
      </div>

      <div className="metrics-grid">
        <div className={`metric-card ${getThroughputClass(metrics.throughput)}`}>
          <div className="metric-icon">🚀</div>
          <div className="metric-content">
            <div className="metric-label">Throughput</div>
            <div className="metric-value">{metrics.throughput.toFixed(1)}</div>
            <div className="metric-unit">URLs/min</div>
          </div>
        </div>

        <div className={`metric-card ${getSuccessRateClass(metrics.successRate)}`}>
          <div className="metric-icon">✅</div>
          <div className="metric-content">
            <div className="metric-label">Success Rate</div>
            <div className="metric-value">{metrics.successRate.toFixed(1)}%</div>
            <div className="metric-unit">completion</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">📸</div>
          <div className="metric-content">
            <div className="metric-label">Screenshots</div>
            <div className="metric-value">{metrics.totalScreenshots}</div>
            <div className="metric-unit">
              {metrics.avgScreenshotsPerUrl > 0 
                ? `${metrics.avgScreenshotsPerUrl.toFixed(1)} avg/URL` 
                : 'total'}
            </div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon">⚡</div>
          <div className="metric-content">
            <div className="metric-label">Peak Concurrency</div>
            <div className="metric-value">{metrics.peakConcurrency}</div>
            <div className="metric-unit">simultaneous</div>
          </div>
        </div>
      </div>

      <div className="metrics-insights">
        {metrics.throughput > 0 && (
          <div className="insight">
            {metrics.throughput >= 5 ? (
              <span className="insight-good">🎉 Excellent throughput! Processing at peak efficiency.</span>
            ) : metrics.throughput >= 3 ? (
              <span className="insight-good">👍 Good throughput. System performing well.</span>
            ) : metrics.throughput >= 1 ? (
              <span className="insight-fair">⚠️ Moderate throughput. Consider checking network or page complexity.</span>
            ) : (
              <span className="insight-poor">⚠️ Low throughput. URLs may be complex or network slow.</span>
            )}
          </div>
        )}
        
        {metrics.successRate > 0 && metrics.successRate < 100 && (
          <div className="insight">
            {metrics.successRate >= 95 ? (
              <span className="insight-good">✨ Excellent success rate!</span>
            ) : metrics.successRate >= 80 ? (
              <span className="insight-fair">💡 Some failures detected. Check logs for details.</span>
            ) : (
              <span className="insight-poor">⚠️ High failure rate. Review timeout settings and URL validity.</span>
            )}
          </div>
        )}

        {metrics.peakConcurrency > 0 && (
          <div className="insight">
            <span className="insight-info">
              🔄 Peak concurrency: {metrics.peakConcurrency} URLs processed simultaneously
            </span>
          </div>
        )}
      </div>
    </div>
  );
};

export default PerformanceMetrics;


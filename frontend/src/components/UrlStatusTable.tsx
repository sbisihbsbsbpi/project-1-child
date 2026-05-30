import React, { useState, useEffect } from 'react';

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

interface UrlStatusTableProps {
  urlStatuses: Map<string, UrlStatus>;
  showAll?: boolean;
}

const UrlStatusTable: React.FC<UrlStatusTableProps> = ({ urlStatuses, showAll: showAllProp = false }) => {
  const [currentTime, setCurrentTime] = useState(Date.now());
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'active' | 'completed' | 'failed'>('all');
  const [sortBy, setSortBy] = useState<'url' | 'status' | 'duration' | 'screenshots'>('status');
  const [showAll, setShowAll] = useState(showAllProp);

  // Update current time every second for elapsed time display
  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentTime(Date.now());
    }, 1000);
    return () => clearInterval(interval);
  }, []);

  const formatDuration = (seconds?: number): string => {
    if (!seconds) return '-';
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  const getElapsedTime = (status: UrlStatus): string => {
    if (status.status === 'pending') return '-';
    if (status.status === 'active' && status.startTime) {
      const elapsed = (currentTime - status.startTime) / 1000;
      return formatDuration(elapsed);
    }
    if (status.duration) return formatDuration(status.duration);
    return '-';
  };

  const getStatusIcon = (status: string): string => {
    switch (status) {
      case 'pending': return '⏳';
      case 'active': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const getStatusClass = (status: string): string => {
    switch (status) {
      case 'pending': return 'status-pending';
      case 'active': return 'status-active';
      case 'completed': return 'status-completed';
      case 'failed': return 'status-failed';
      default: return '';
    }
  };

  // Convert Map to Array and filter
  const statusArray = Array.from(urlStatuses.values());
  const filteredStatuses = filterStatus === 'all' 
    ? statusArray 
    : statusArray.filter(s => s.status === filterStatus);

  // Sort
  const sortedStatuses = [...filteredStatuses].sort((a, b) => {
    switch (sortBy) {
      case 'url':
        return a.url.localeCompare(b.url);
      case 'status':
        const statusOrder = { pending: 0, active: 1, completed: 2, failed: 3 };
        return statusOrder[a.status] - statusOrder[b.status];
      case 'duration':
        return (b.duration || 0) - (a.duration || 0);
      case 'screenshots':
        return (b.screenshotCount || 0) - (a.screenshotCount || 0);
      default:
        return 0;
    }
  });

  // Limit display if not showing all
  const displayStatuses = showAll ? sortedStatuses : sortedStatuses.slice(0, 10);

  const stats = {
    pending: statusArray.filter(s => s.status === 'pending').length,
    active: statusArray.filter(s => s.status === 'active').length,
    completed: statusArray.filter(s => s.status === 'completed').length,
    failed: statusArray.filter(s => s.status === 'failed').length,
  };

  return (
    <div className="url-status-table-container">
      <div className="url-status-header">
        <h3>📋 URL Status Tracker</h3>
        <div className="url-status-stats">
          <span className="stat-badge pending">⏳ {stats.pending}</span>
          <span className="stat-badge active">🔄 {stats.active}</span>
          <span className="stat-badge completed">✅ {stats.completed}</span>
          {stats.failed > 0 && <span className="stat-badge failed">❌ {stats.failed}</span>}
        </div>
      </div>

      <div className="url-status-controls">
        <div className="filter-group">
          <label>Filter:</label>
          <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value as any)}>
            <option value="all">All ({statusArray.length})</option>
            <option value="pending">Pending ({stats.pending})</option>
            <option value="active">Active ({stats.active})</option>
            <option value="completed">Completed ({stats.completed})</option>
            <option value="failed">Failed ({stats.failed})</option>
          </select>
        </div>
        <div className="sort-group">
          <label>Sort by:</label>
          <select value={sortBy} onChange={(e) => setSortBy(e.target.value as any)}>
            <option value="status">Status</option>
            <option value="url">URL</option>
            <option value="duration">Duration</option>
            <option value="screenshots">Screenshots</option>
          </select>
        </div>
      </div>

      <div className="url-status-table-wrapper">
        <table className="url-status-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>URL</th>
              <th>Text Box</th>
              <th>Time</th>
              <th>Screenshots</th>
            </tr>
          </thead>
          <tbody>
            {displayStatuses.map((status, index) => (
              <tr key={index} className={getStatusClass(status.status)}>
                <td className="status-cell">
                  <span className="status-icon">{getStatusIcon(status.status)}</span>
                  <span className="status-text">{status.status}</span>
                </td>
                <td className="url-cell" title={status.url}>
                  {status.url.length > 60 ? status.url.substring(0, 57) + '...' : status.url}
                </td>
                <td className="textbox-cell">{status.textBoxName}</td>
                <td className="time-cell">{getElapsedTime(status)}</td>
                <td className="screenshots-cell">{status.screenshotCount || '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {!showAll && sortedStatuses.length > 10 && (
        <div className="url-status-footer">
          <span>Showing 10 of {sortedStatuses.length} URLs</span>
          <button
            onClick={() => setShowAll(true)}
            style={{
              marginLeft: '10px',
              padding: '4px 12px',
              background: '#667eea',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Show All {sortedStatuses.length}
          </button>
        </div>
      )}
      {showAll && sortedStatuses.length > 10 && (
        <div className="url-status-footer">
          <span>Showing all {sortedStatuses.length} URLs</span>
          <button
            onClick={() => setShowAll(false)}
            style={{
              marginLeft: '10px',
              padding: '4px 12px',
              background: '#6b7280',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px'
            }}
          >
            Show Less
          </button>
        </div>
      )}
    </div>
  );
};

export default UrlStatusTable;


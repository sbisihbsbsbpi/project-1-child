import React from 'react';

interface Screenshot {
  filename: string;
  path: string;
  url: string;
  timestamp: string;
  quality_score?: number;
  segments?: number;
}

interface Session {
  id: string;
  name: string;
  defaultName: string;
  timestamp: string;
  screenshots: Screenshot[];
  urls: string[];
  duration: number;
  settings: {
    captureMode: string;
    useStealth: boolean;
    useRealBrowser: boolean;
  };
}

interface SessionsTabProps {
  sessions: Session[];
  selectedSessions: Set<string>;
  isDeletingSession: boolean;
  editingSessionId: string | null;
  editingSessionName: string;
  sessionNameError: string;
  formatTimestamp: (timestamp: string) => string;
  deselectAllSessions: () => void;
  selectAllSessions: () => void;
  deleteSelectedSessions: () => void;
  toggleSessionSelection: (id: string) => void;
  setEditingSessionName: (name: string) => void;
  handleSessionNameKeyDown: (e: React.KeyboardEvent, id: string) => void;
  saveSessionName: (id: string) => void;
  cancelEditingSession: () => void;
  startEditingSession: (id: string) => void;
	  // New: generate Word document(s) for the currently-selected sessions
	  onCreateDocsFromSelected: () => void;
	  isCreatingDocs: boolean;
}

	const SessionsTabComponent: React.FC<SessionsTabProps> = ({
  sessions,
  selectedSessions,
  isDeletingSession,
  editingSessionId,
  editingSessionName,
  sessionNameError,
  formatTimestamp,
  deselectAllSessions,
  selectAllSessions,
  deleteSelectedSessions,
  toggleSessionSelection,
  setEditingSessionName,
  handleSessionNameKeyDown,
  saveSessionName,
  cancelEditingSession,
	  startEditingSession,
	  onCreateDocsFromSelected,
	  isCreatingDocs,
}) => {
  return (
    <div className="tab-content">
      <div className="sessions-section">
        <div className="sessions-header">
          <h2>🗂️ Session History</h2>
          <div className="sessions-actions">
            {sessions.length > 0 && (
              <>
                <button
                  onClick={() => {
                    if (selectedSessions.size === sessions.length) {
                      deselectAllSessions();
                    } else {
                      selectAllSessions();
                    }
                  }}
                  className="session-action-btn"
                >
                  {selectedSessions.size === sessions.length
                    ? "☐ Deselect All"
                    : "☑ Select All"}
                </button>
                {selectedSessions.size > 0 && (
                  <button
                    onClick={deleteSelectedSessions}
                    className="session-action-btn delete-btn"
                    disabled={isDeletingSession}
                    title={
                      isDeletingSession
                        ? "Deletion in progress..."
                        : "Delete selected sessions"
                    }
                  >
                    {isDeletingSession
                      ? "⏳ Deleting..."
                      : `🗑️ Delete Selected (${selectedSessions.size})`}
                  </button>
                )}
              </>
            )}
          </div>
        </div>

	        <div className="sessions-container">
	          {sessions.length === 0 ? (
	            <div className="no-sessions">
	              <p>🗂️ No sessions yet.</p>
	              <p>Capture screenshots to create your first session!</p>
	            </div>
	          ) : (
		            sessions.map((session) => {
		              const screenshotCount = Array.isArray(session.screenshots)
		                ? session.screenshots.length
		                : 0;
		              const hasLocation =
		                screenshotCount > 0 &&
		                typeof session.screenshots[0]?.path === "string" &&
		                session.screenshots[0].path.length > 0;
		              const sessionLocation = hasLocation
		                ? session.screenshots[0].path.split("/").slice(0, -1).join("/")
		                : null;
		              const durationSeconds =
		                typeof session.duration === "number"
		                  ? Math.round(session.duration / 1000)
		                  : 0;
		              const captureMode = session.settings?.captureMode ?? "Unknown";
		              const useStealth = !!session.settings?.useStealth;
		              const useRealBrowser = !!session.settings?.useRealBrowser;
		
		              return (
		                <div key={session.id} className="session-card">
	                <div className="session-card-header">
                  <input
                    type="checkbox"
                    className="session-checkbox"
                    checked={selectedSessions.has(session.id)}
                    onChange={() => toggleSessionSelection(session.id)}
                  />

                  {editingSessionId === session.id ? (
                    <div className="session-name-edit">
                      <input
                        type="text"
                        className="session-name-input"
                        value={editingSessionName}
                        onChange={(e) => setEditingSessionName(e.target.value)}
                        onKeyDown={(e) => handleSessionNameKeyDown(e, session.id)}
                        onBlur={() => saveSessionName(session.id)}
                        autoFocus
                      />
                      <button
                        className="session-name-save"
                        onClick={() => saveSessionName(session.id)}
                        title="Save"
                      >
                        ✓
                      </button>
                      <button
                        className="session-name-cancel"
                        onClick={cancelEditingSession}
                        title="Cancel"
                      >
                        ✗
                      </button>
                      {sessionNameError && (
                        <span className="session-name-error">
                          {sessionNameError}
                        </span>
                      )}
                    </div>
                  ) : (
                    <div className="session-name-display">
                      <h3 className="session-name">{session.name}</h3>
                      <button
                        className="session-name-edit-btn"
                        onClick={() => startEditingSession(session.id)}
                        title="Rename session"
                      >
                        ✏️
                      </button>
                    </div>
                  )}
                </div>

	                <div className="session-info">
	                  <span className="session-stat">
	                    📅 Created: {formatTimestamp(session.timestamp)}
	                  </span>
	                  <span className="session-stat">
	                    📊 Total segments: {screenshotCount}
	                  </span>
	                  <span className="session-stat">
	                    📸 Screenshots: {screenshotCount}
	                  </span>
	                  <span className="session-stat">
	                    ⏱️ Duration: {durationSeconds}s
	                  </span>
	                </div>
	
	                {sessionLocation && (
	                  <div className="session-location">
	                    <span
	                      className="session-stat"
	                      style={{ fontSize: "13px", color: "#888" }}
	                    >
	                      📁 Location:{" "}
	                      {sessionLocation}
	                    </span>
	                  </div>
	                )}
	
		                <div className="session-settings">
		                  <span className="session-setting">
		                    📸 {captureMode}
		                  </span>
		                  {useStealth && (
		                    <span className="session-setting">🥷 Stealth</span>
		                  )}
		                  {useRealBrowser && (
		                    <span className="session-setting">🌐 Real Browser</span>
		                  )}
		                </div>
		              </div>
		              );
		            })
          )}
        </div>

	        {selectedSessions.size > 0 && (
          <div className="sessions-footer">
            <p>
              📊 Selected: {selectedSessions.size} session(s) |{" "}
	              {sessions
	                .filter((s) => selectedSessions.has(s.id))
	                .reduce(
	                  (sum, s) =>
	                    sum +
	                    (Array.isArray(s.screenshots)
	                      ? s.screenshots.length
	                      : 0),
	                  0
	                )}{" "}
	              screenshot(s)
	            </p>
	            <button
	              className="create-doc-btn"
	              onClick={onCreateDocsFromSelected}
	              disabled={isCreatingDocs}
	              title={
	                isCreatingDocs
	                  ? "Generating Word document(s) from selected sessions..."
	                  : "Create Word document(s) from selected sessions"
	              }
	            >
	              {isCreatingDocs
	                ? "📄 Generating Word Doc(s)..."
	                : "📄 Create Word Doc from Selected"}
	            </button>
          </div>
        )}
      </div>
    </div>
  );
};

// ✅ Memoize to prevent unnecessary re-renders when props haven't changed
export const SessionsTab = React.memo(SessionsTabComponent);


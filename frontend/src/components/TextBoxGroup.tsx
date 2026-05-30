import React, { memo } from 'react';

/**
 * Individual Text Box component for batch URL processing
 * 
 * Extracted from App.tsx monolith to improve:
 * - Performance: React.memo prevents unnecessary re-renders
 * - Maintainability: Single responsibility principle
 * - Testability: Can be unit tested in isolation
 * - Cognitive architecture: Component structure matches user mental model
 */

export interface TextBox {
  id: string;
  sessionName: string;
  urls: string;
  batchTimeout?: number;
  batchTimeoutUnit?: string;
  selected?: boolean;
}

interface UrlFolder {
  id?: string;
  name: string;
  urls: string[];
  createdAt?: string;
}

interface TextBoxGroupProps {
  textBox: TextBox;
  index: number;
  isCollapsed: boolean;
  loading: boolean;
  urlFolders: UrlFolder[];
  timeoutError: string | null;
  totalTextBoxes: number;
  
  // Stable callbacks (wrapped in useCallback in parent)
  onToggleCollapse: (id: string) => void;
  onToggleSelection: (id: string) => void;
  onUpdateField: (id: string, field: keyof TextBox, value: any) => void;
  onLoadFolder: (id: string, folderName: string) => void;
  onRemove: (id: string) => void;
  onTimeoutChange: (id: string, value: string) => void;
  onTimeoutBlur: (id: string, value: string) => void;
  onTimeoutUnitChange: (id: string, unit: string) => void;
  getTimeoutDisplayValue: (textBox: TextBox) => number | string;
  detectFolderMention: (text: string) => string | null;
  addLog: (message: string) => void;
}

const TextBoxGroupComponent: React.FC<TextBoxGroupProps> = ({
  textBox,
  index,
  isCollapsed,
  loading,
  urlFolders,
  timeoutError,
  totalTextBoxes,
  onToggleCollapse,
  onToggleSelection,
  onUpdateField,
  onLoadFolder,
  onRemove,
  onTimeoutChange,
  onTimeoutBlur,
  onTimeoutUnitChange,
  getTimeoutDisplayValue,
  detectFolderMention,
  addLog,
}) => {
  return (
    <div
      className={`textbox-group ${
        textBox.selected === false ? 'textbox-unselected' : ''
      }`}
    >
      <div
        className="textbox-header"
        onClick={() => onToggleCollapse(textBox.id)}
        style={{ cursor: 'pointer' }}
      >
        <div className="textbox-header-left">
          <span className="textbox-toggle-icon">
            {isCollapsed ? '▶' : '▼'}
          </span>
          <h3>Text box {index + 1}</h3>
        </div>
      </div>

      {!isCollapsed && (
        <>
          <div className="textbox-header-inline">
            {/* Checkbox for text box selection */}
            <div className="textbox-checkbox-container">
              <input
                type="checkbox"
                className="textbox-checkbox"
                checked={textBox.selected !== false}
                onChange={() => onToggleSelection(textBox.id)}
                disabled={loading}
                title={
                  textBox.selected !== false
                    ? 'Uncheck to skip this text box during capture'
                    : 'Check to include this text box in capture'
                }
              />
            </div>

            <div className="textbox-title-and-input">
              <label className="textbox-inline-label">
                <strong>Session name (for Word document):</strong>
              </label>
              <input
                type="text"
                className="session-name-input-field-inline"
                placeholder="e.g., Accounting, Parts, Service"
                value={textBox.sessionName}
                onChange={(e) =>
                  onUpdateField(textBox.id, 'sessionName', e.target.value)
                }
                disabled={loading}
              />
            </div>

            {/* Folder dropdown */}
            <div
              className="textbox-title-and-input"
              style={{
                marginLeft: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <label className="textbox-inline-label">
                <strong>Folder:</strong>
              </label>
              <select
                className="session-name-input-field-inline"
                disabled={loading || urlFolders.length === 0}
                defaultValue=""
                onChange={(e) => {
                  const value = e.target.value;
                  if (!value) return;
                  onLoadFolder(textBox.id, value);
                }}
              >
                {urlFolders.length === 0 ? (
                  <option value="">No folders yet</option>
                ) : (
                  <>
                    <option value="">Select folder</option>
                    {urlFolders.map((folder) => (
                      <option key={folder.name} value={folder.name}>
                        {folder.name}
                      </option>
                    ))}
                  </>
                )}
              </select>
            </div>

            {/* Batch timeout input with unit selector */}
            <div
              className="textbox-title-and-input"
              style={{
                marginLeft: '20px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
              }}
            >
              <label className="textbox-inline-label">
                <strong>Batch timeout:</strong>
              </label>
              <input
                type="number"
                className="session-name-input-field-inline"
                placeholder=""
                step="any"
                min="0"
                value={getTimeoutDisplayValue(textBox)}
                onChange={(e) => onTimeoutChange(textBox.id, e.target.value)}
                onBlur={(e) => onTimeoutBlur(textBox.id, e.target.value)}
                disabled={loading}
                style={{ width: '80px' }}
              />

              {/* Unit selector dropdown */}
              <select
                id={`timeout-unit-${textBox.id}`}
                className="session-name-input-field-inline"
                value={textBox.batchTimeoutUnit || 'seconds'}
                onChange={(e) => onTimeoutUnitChange(textBox.id, e.target.value)}
                disabled={loading}
                style={{ width: '100px' }}
              >
                <option value="seconds">seconds</option>
                <option value="minutes">minutes</option>
                <option value="hours">hours</option>
              </select>

              {/* Inline validation error display */}
              {timeoutError && (
                <span
                  className="error"
                  style={{
                    fontSize: '12px',
                    marginLeft: '8px',
                    whiteSpace: 'nowrap',
                  }}
                >
                  ⚠️ {timeoutError}
                </span>
              )}
            </div>

            <button
              className="remove-textbox-btn"
              onClick={() => onRemove(textBox.id)}
              disabled={loading || totalTextBoxes <= 1}
              title="Remove this text box"
            >
              Remove
            </button>
          </div>

          {/* URLs textarea with line numbers */}
          <div className="textbox-urls">
            <label>
              <strong>URLs (one per line):</strong>
            </label>
            <div className="textarea-wrapper">
              {/* Textarea */}
              <textarea
                className="textbox-urls-textarea"
                placeholder="https://example.com&#10;https://google.com"
                value={textBox.urls}
                onChange={(e) => {
                  onUpdateField(textBox.id, 'urls', e.target.value);
                  // Auto-resize textarea
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
                onScroll={(e) => {
                  const lineNumbers = document.getElementById(
                    `line-numbers-${textBox.id}`
                  );
                  if (lineNumbers) {
                    lineNumbers.scrollTop = e.currentTarget.scrollTop;
                  }
                }}
                onFocus={(e) => {
                  // Expand on focus
                  e.target.style.height = 'auto';
                  e.target.style.height = e.target.scrollHeight + 'px';
                }}
                onBlur={(e) => {
                  // Shrink to minimum on blur if content is small
                  const lineCount = textBox.urls.split('\n').length;
                  const minRows = 6;
                  if (lineCount <= minRows) {
                    e.target.style.height = 'auto';
                  }
                }}
                rows={6}
                disabled={loading}
                style={{
                  backgroundImage: `linear-gradient(transparent 0px, transparent 7px, transparent 8px, transparent 19.5px),
                    repeating-linear-gradient(
                      transparent,
                      transparent 19.5px,
                      #e5e7eb 19.5px,
                      #e5e7eb 20px
                    )`,
                  backgroundAttachment: 'local',
                  backgroundPosition: '60px 8px',
                  lineHeight: '19.5px',
                  minHeight: '135px',
                  overflow: 'hidden',
                }}
              />
              {/* Line numbers - sequential S.No for URLs only */}
              <div
                className="line-numbers-hardcoded"
                id={`line-numbers-${textBox.id}`}
                style={{
                  position: 'absolute',
                  left: '1px',
                  top: '1px',
                  bottom: '1px',
                  width: '50px',
                  padding: '8px 0',
                  paddingLeft: '8px',
                  fontFamily: '"Courier New", monospace',
                  fontSize: '13px',
                  lineHeight: '19.5px',
                  color: 'rgba(0, 0, 0, 0.5)',
                  userSelect: 'none',
                  pointerEvents: 'none',
                  zIndex: 10,
                  textAlign: 'right',
                  borderRight: '1px solid rgba(0, 0, 0, 0.1)',
                  background: 'rgba(249, 250, 251, 0.9)',
                  overflow: 'hidden',
                  borderTopLeftRadius: '3px',
                  borderBottomLeftRadius: '3px',
                  boxSizing: 'border-box',
                }}
              >
                {(() => {
                  const lines = textBox.urls.split('\n');
                  let sno = 0;
                  return lines.map((line, lineIndex) => {
                    const hasUrl = line.trim() !== '';
                    if (hasUrl) sno++;
                    return (
                      <div
                        key={lineIndex}
                        style={{
                          height: '19.5px',
                          lineHeight: '19.5px',
                          paddingRight: '8px',
                          fontWeight: 600,
                          fontSize: '13px',
                          textAlign: 'right',
                        }}
                      >
                        {hasUrl ? sno : ''}
                      </div>
                    );
                  });
                })()}
              </div>
            </div>

            {/* Folder mention detection */}
            {(() => {
              const mentionedFolder = detectFolderMention(textBox.urls);
              if (mentionedFolder && urlFolders.length > 0) {
                const folder = urlFolders.find(
                  (f) =>
                    f.name.toLowerCase() === mentionedFolder.toLowerCase()
                );
                if (folder) {
                  return (
                    <div className="folder-mention-hint">
                      <p>
                        Detected folder:{' '}
                        <strong>@{mentionedFolder}</strong>
                      </p>
                      <button
                        className="load-folder-btn"
                        onClick={() => {
                          // Load URLs into this specific text box
                          onUpdateField(
                            textBox.id,
                            'urls',
                            folder.urls.join('\n')
                          );
                          addLog(
                            `✅ Loaded ${folder.urls.length} URL(s) from folder "${folder.name}" into Text Box`
                          );
                        }}
                        disabled={loading}
                      >
                        Load {folder.urls.length} URL(s) from "{folder.name}"
                      </button>
                    </div>
                  );
                } else {
                  return (
                    <div className="folder-mention-hint error">
                      <p>
                        Folder <strong>@{mentionedFolder}</strong> not found
                      </p>
                    </div>
                  );
                }
              }

              // Show available folders hint if there are folders
              if (urlFolders.length > 0 && !textBox.urls.trim()) {
                return (
                  <div className="folder-hint">
                    <p>
                      Tip: Type <strong>@foldername</strong> to load saved URLs
                    </p>
                    <p className="available-folders">
                      Available folders:{' '}
                      {urlFolders.map((f) => `@${f.name}`).join(', ')}
                    </p>
                  </div>
                );
              }
              return null;
            })()}
          </div>
        </>
      )}
    </div>
  );
};

// Memoize to prevent unnecessary re-renders when parent state changes
export const TextBoxGroup = memo(TextBoxGroupComponent);

TextBoxGroup.displayName = 'TextBoxGroup';

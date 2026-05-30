import React from 'react';

interface UrlFolder {
  id: string;
  name: string;
  urls: string[];
  createdAt: string;
}

interface UrlsTabProps {
  urlFolders: UrlFolder[];
  newFolderName: string;
  setNewFolderName: (name: string) => void;
  expandedFolders: Set<string>;
  editingFolderId: string | null;
  editingFolderName: string;
  setEditingFolderName: (name: string) => void;
  removeDuplicateUrls: () => void;
  createFolder: () => void;
  toggleFolderExpanded: (id: string) => void;
  startEditingFolder: (id: string, name: string) => void;
  saveFolderName: (id: string) => void;
  cancelEditingFolder: () => void;
  deleteFolder: (id: string) => void;
  loadUrlsFromFolder: (folder: UrlFolder) => void;
  addUrlToFolder: (folderId: string, url: string) => void;
  removeUrlFromFolder: (folderId: string, url: string) => void;
}

const UrlsTabComponent: React.FC<UrlsTabProps> = ({
  urlFolders,
  newFolderName,
  setNewFolderName,
  expandedFolders,
  editingFolderId,
  editingFolderName,
  setEditingFolderName,
  removeDuplicateUrls,
  createFolder,
  toggleFolderExpanded,
  startEditingFolder,
  saveFolderName,
  cancelEditingFolder,
  deleteFolder,
  loadUrlsFromFolder,
  addUrlToFolder,
  removeUrlFromFolder,
}) => {
  const [newUrlInputs, setNewUrlInputs] = React.useState<Record<string, string>>({});

  return (
    <div className="tab-content">
      <div className="urls-section">
        <div className="urls-header">
          <h2>📁 URL Library</h2>
          <div className="urls-header-actions">
            <button
              onClick={removeDuplicateUrls}
              className="clean-duplicates-btn"
              title="Remove duplicate URLs from all folders"
            >
              🧹 Clean Duplicates
            </button>
            <div className="new-folder-form">
              <input
                type="text"
                className="new-folder-input"
                placeholder="New folder name..."
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    createFolder();
                  }
                }}
              />
              <button onClick={createFolder} className="create-folder-btn">
                + New Folder
              </button>
            </div>
          </div>
        </div>

        <div className="folders-container">
          {urlFolders.length === 0 ? (
            <div className="no-folders">
              <p>📁 No folders yet.</p>
              <p>Create your first folder to organize URLs!</p>
            </div>
          ) : (
            urlFolders.map((folder) => (
              <div key={folder.id} className="folder-card">
                <div className="folder-header">
                  <button
                    className="folder-expand-btn"
                    onClick={() => toggleFolderExpanded(folder.id)}
                  >
                    {expandedFolders.has(folder.id) ? "▼" : "▶"}
                  </button>

                  {editingFolderId === folder.id ? (
                    <div className="folder-name-edit">
                      <input
                        type="text"
                        className="folder-name-input"
                        value={editingFolderName}
                        onChange={(e) => setEditingFolderName(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            saveFolderName(folder.id);
                          } else if (e.key === "Escape") {
                            cancelEditingFolder();
                          }
                        }}
                        onBlur={() => saveFolderName(folder.id)}
                        autoFocus
                      />
                      <button
                        className="folder-name-save"
                        onClick={() => saveFolderName(folder.id)}
                        title="Save"
                      >
                        ✓
                      </button>
                      <button
                        className="folder-name-cancel"
                        onClick={cancelEditingFolder}
                        title="Cancel"
                      >
                        ✗
                      </button>
                    </div>
                  ) : (
                    <div className="folder-name-display">
                      <h3 className="folder-name">{folder.name}</h3>
                      <span className="folder-count">({folder.urls.length} URLs)</span>
                      <button
                        className="folder-name-edit-btn"
                        onClick={() => startEditingFolder(folder.id, folder.name)}
                        title="Rename folder"
                      >
                        ✏️
                      </button>
                    </div>
                  )}

                  <div className="folder-actions">
                    <button
                      className="load-folder-btn"
                      onClick={() => loadUrlsFromFolder(folder)}
                      title="Load URLs into main input"
                    >
                      📥 Load
                    </button>
                    <button
                      className="delete-folder-btn"
                      onClick={() => deleteFolder(folder.id)}
                      title="Delete folder"
                    >
                      🗑️
                    </button>
                  </div>
                </div>

                {expandedFolders.has(folder.id) && (
                  <div className="folder-content">
                    <div className="folder-urls">
                      {folder.urls.length === 0 ? (
                        <p className="no-urls">No URLs in this folder yet.</p>
                      ) : (
                        folder.urls.map((url, index) => (
                          <div key={index} className="url-item">
                            <span className="url-text">{url}</span>
                            <button
                              className="remove-url-btn"
                              onClick={() => removeUrlFromFolder(folder.id, url)}
                              title="Remove URL"
                            >
                              ✕
                            </button>
                          </div>
                        ))
                      )}
                    </div>

                    <div className="add-url-form">
                      <input
                        type="text"
                        className="add-url-input"
                        placeholder="Add URL to folder..."
                        value={newUrlInputs[folder.id] || ''}
                        onChange={(e) =>
                          setNewUrlInputs({ ...newUrlInputs, [folder.id]: e.target.value })
                        }
                        onKeyDown={(e) => {
                          if (e.key === "Enter") {
                            e.preventDefault();
                            const url = newUrlInputs[folder.id]?.trim();
                            if (url) {
                              addUrlToFolder(folder.id, url);
                              setNewUrlInputs({ ...newUrlInputs, [folder.id]: '' });
                            }
                          }
                        }}
                      />
                      <button
                        className="add-url-btn"
                        onClick={() => {
                          const url = newUrlInputs[folder.id]?.trim();
                          if (url) {
                            addUrlToFolder(folder.id, url);
                            setNewUrlInputs({ ...newUrlInputs, [folder.id]: '' });
                          }
                        }}
                      >
                        ✨ Add URLs to Folder
                      </button>
                    </div>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
};

// ✅ Memoize to prevent unnecessary re-renders
export const UrlsTab = React.memo(UrlsTabComponent);


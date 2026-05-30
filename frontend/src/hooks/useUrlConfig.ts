/**
 * ✅ FIXED (Bug #14): URL configuration state hook
 * 
 * Manages URL-specific click configurations and editor state.
 */

import { useState } from 'react';

interface UrlClickAction {
  type: "click";
  text: string;
  wait_after_ms: number;
}

interface UrlClickConfig {
  id: string;
  url_pattern: string;
  actions: UrlClickAction[];
}

export function useUrlConfig() {
  const [urlConfigs, setUrlConfigs] = useState<UrlClickConfig[]>([]);
  const [showUrlConfigEditor, setShowUrlConfigEditor] = useState(false);
  const [editingUrlConfigId, setEditingUrlConfigId] = useState<string | null>(null);
  const [urlConfigForm, setUrlConfigForm] = useState<UrlClickConfig>({
    id: "",
    url_pattern: "",
    actions: [],
  });

  const openEditor = (config?: UrlClickConfig) => {
    if (config) {
      setEditingUrlConfigId(config.id);
      setUrlConfigForm(config);
    } else {
      setEditingUrlConfigId(null);
      setUrlConfigForm({
        id: `config-${Date.now()}`,
        url_pattern: "",
        actions: [],
      });
    }
    setShowUrlConfigEditor(true);
  };

  const closeEditor = () => {
    setShowUrlConfigEditor(false);
    setEditingUrlConfigId(null);
    setUrlConfigForm({
      id: "",
      url_pattern: "",
      actions: [],
    });
  };

  const addConfig = (config: UrlClickConfig) => {
    setUrlConfigs([...urlConfigs, config]);
  };

  const updateConfig = (id: string, config: UrlClickConfig) => {
    setUrlConfigs(urlConfigs.map(c => c.id === id ? config : c));
  };

  const deleteConfig = (id: string) => {
    setUrlConfigs(urlConfigs.filter(c => c.id !== id));
  };

  const saveCurrentConfig = () => {
    if (editingUrlConfigId) {
      updateConfig(editingUrlConfigId, urlConfigForm);
    } else {
      addConfig(urlConfigForm);
    }
    closeEditor();
  };

  const addAction = (action: UrlClickAction) => {
    setUrlConfigForm({
      ...urlConfigForm,
      actions: [...urlConfigForm.actions, action],
    });
  };

  const removeAction = (index: number) => {
    setUrlConfigForm({
      ...urlConfigForm,
      actions: urlConfigForm.actions.filter((_, i) => i !== index),
    });
  };

  const updateAction = (index: number, action: UrlClickAction) => {
    setUrlConfigForm({
      ...urlConfigForm,
      actions: urlConfigForm.actions.map((a, i) => i === index ? action : a),
    });
  };

  return {
    // Config list
    urlConfigs,
    setUrlConfigs,
    
    // Editor state
    showUrlConfigEditor,
    setShowUrlConfigEditor,
    editingUrlConfigId,
    setEditingUrlConfigId,
    urlConfigForm,
    setUrlConfigForm,
    
    // Helper functions
    openEditor,
    closeEditor,
    addConfig,
    updateConfig,
    deleteConfig,
    saveCurrentConfig,
    
    // Action management
    addAction,
    removeAction,
    updateAction,
  };
}


/**
 * ✅ FIXED (Bug #14): Word editor state management hook
 * 
 * Manages word transformation editor state and logic.
 */

import { useState } from 'react';

interface WordTransformation {
  word: string;
  replacement: string;
  type: "remove" | "space" | "custom";
}

export function useWordEditor() {
  const [wordInput, setWordInput] = useState("");
  const [showWordEditor, setShowWordEditor] = useState(false);
  const [editingWordIndex, setEditingWordIndex] = useState<number | null>(null);
  const [editorWord, setEditorWord] = useState("");
  const [editorReplacement, setEditorReplacement] = useState("");
  const [editorType, setEditorType] = useState<"remove" | "space" | "custom">("space");

  const openEditor = (word?: WordTransformation, index?: number) => {
    if (word && index !== undefined) {
      setEditingWordIndex(index);
      setEditorWord(word.word);
      setEditorReplacement(word.replacement);
      setEditorType(word.type);
    } else {
      setEditingWordIndex(null);
      setEditorWord("");
      setEditorReplacement("");
      setEditorType("space");
    }
    setShowWordEditor(true);
  };

  const closeEditor = () => {
    setShowWordEditor(false);
    setEditingWordIndex(null);
    setEditorWord("");
    setEditorReplacement("");
    setEditorType("space");
  };

  const resetInput = () => {
    setWordInput("");
  };

  return {
    // Input state
    wordInput,
    setWordInput,
    resetInput,
    
    // Editor modal state
    showWordEditor,
    setShowWordEditor,
    editingWordIndex,
    setEditingWordIndex,
    editorWord,
    setEditorWord,
    editorReplacement,
    setEditorReplacement,
    editorType,
    setEditorType,
    
    // Helper functions
    openEditor,
    closeEditor,
  };
}


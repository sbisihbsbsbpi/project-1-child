/**
 * ✅ FIXED (Bug #14): Cookie management state hook
 *
 * Manages cookie extraction, analysis, and export state.
 */

import { useState } from 'react';

interface CookieImportStatus {
  playwright?: {
    exists: boolean;
    cookie_count: number;
    extracted_at?: string;
  };
  camoufox?: {
    exists: boolean;
    cookie_count: number;
    size_mb?: number;
  };
}

export function useCookieManagement() {
  const [cookieImportStatus, setCookieImportStatus] = useState<CookieImportStatus>({});
  
  const [_availableBrowsers, _setAvailableBrowsers] = useState<string[]>([]);
  const [isExtractingCookies, setIsExtractingCookies] = useState(false);
  const [cookieAnalysis, setCookieAnalysis] = useState<any>(null);
  const [isAnalyzingCookies, setIsAnalyzingCookies] = useState(false);
  const [_selectedCookie, _setSelectedCookie] = useState<any>(null);
  const [showCookieEditor, setShowCookieEditor] = useState(false);
  const [editingCookie, setEditingCookie] = useState<any>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportType, setExportType] = useState<"curl" | "playwright">("curl");

  const clearCookieStatus = () => {
    setCookieImportStatus({});
  };

  const startExtraction = () => {
    setIsExtractingCookies(true);
  };

  const completeExtraction = () => {
    setIsExtractingCookies(false);
  };

  const startAnalysis = () => {
    setIsAnalyzingCookies(true);
  };

  const completeAnalysis = (analysis: any) => {
    setCookieAnalysis(analysis);
    setIsAnalyzingCookies(false);
  };

  const clearAnalysis = () => {
    setCookieAnalysis(null);
    setIsAnalyzingCookies(false);
  };

  const openCookieEditor = (cookie: any) => {
    setEditingCookie(cookie);
    setShowCookieEditor(true);
  };

  const closeCookieEditor = () => {
    setEditingCookie(null);
    setShowCookieEditor(false);
  };

  const openExportModal = (type: "curl" | "playwright" = "curl") => {
    setExportType(type);
    setShowExportModal(true);
  };

  const closeExportModal = () => {
    setShowExportModal(false);
  };

  return {
    // Import state
    cookieImportStatus,
    setCookieImportStatus,
    clearCookieStatus,

    // Browser detection (reserved)
    _availableBrowsers,
    _setAvailableBrowsers,

    // Extraction state
    isExtractingCookies,
    setIsExtractingCookies,
    startExtraction,
    completeExtraction,

    // Analysis state
    cookieAnalysis,
    setCookieAnalysis,
    isAnalyzingCookies,
    setIsAnalyzingCookies,
    startAnalysis,
    completeAnalysis,
    clearAnalysis,

    // Cookie selection (reserved)
    _selectedCookie,
    _setSelectedCookie,

    // Editor state
    showCookieEditor,
    setShowCookieEditor,
    editingCookie,
    setEditingCookie,
    openCookieEditor,
    closeCookieEditor,

    // Export state
    showExportModal,
    setShowExportModal,
    exportType,
    setExportType,
    openExportModal,
    closeExportModal,
  };
}


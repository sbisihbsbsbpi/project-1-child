/**
 * ✅ FIXED (Bug #14): Authentication flow state hook
 *
 * Manages authentication state, login modal, and custom dialogs.
 */

import { useState } from 'react';

interface AuthStateStatus {
  exists: boolean;
  cookie_count?: number;
  localStorage_count?: number;
  cookies?: Array<{ name: string; domain: string; expires?: number }>;
  localStorage_items?: Array<{ name: string; value: string }>;
}

interface CustomDialog {
  isOpen: boolean;
  title: string;
  message: string;
  onConfirm?: () => void;
  onCancel?: () => void;
  confirmText?: string;
  cancelText?: string;
}

export function useAuthFlow() {
  const [authStateStatus, setAuthStateStatus] = useState<AuthStateStatus>({
    exists: false,
  });
  
  const [isLoginInProgress, setIsLoginInProgress] = useState(false);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginUrl, setLoginUrl] = useState("https://example.com/login");
  const [_showAuthPreview, _setShowAuthPreview] = useState(false); // Reserved for future use
  
  const [customDialog, setCustomDialog] = useState<CustomDialog>({
    isOpen: false,
    title: "",
    message: "",
  });

  const startLogin = (url?: string) => {
    if (url) setLoginUrl(url);
    setIsLoginInProgress(true);
    setShowLoginModal(true);
  };

  const completeLogin = () => {
    setIsLoginInProgress(false);
    setShowLoginModal(false);
  };

  const cancelLogin = () => {
    setIsLoginInProgress(false);
    setShowLoginModal(false);
  };

  const logout = () => {
    setAuthStateStatus({
      exists: false,
    });
  };

  const showDialog = (
    title: string,
    message: string,
    onConfirm?: () => void,
    onCancel?: () => void,
    confirmText: string = "OK",
    cancelText: string = "Cancel"
  ) => {
    setCustomDialog({
      isOpen: true,
      title,
      message,
      onConfirm,
      onCancel,
      confirmText,
      cancelText,
    });
  };

  const closeDialog = () => {
    setCustomDialog({
      isOpen: false,
      title: "",
      message: "",
    });
  };

  return {
    // Auth status
    authStateStatus,
    setAuthStateStatus,

    // Login flow
    isLoginInProgress,
    setIsLoginInProgress,
    showLoginModal,
    setShowLoginModal,
    loginUrl,
    setLoginUrl,
    startLogin,
    completeLogin,
    cancelLogin,
    logout,

    // Auth preview (reserved)
    _showAuthPreview,
    _setShowAuthPreview,

    // Custom dialog
    customDialog,
    setCustomDialog,
    showDialog,
    closeDialog,
  };
}


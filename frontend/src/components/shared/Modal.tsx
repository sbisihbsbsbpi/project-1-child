/**
 * 🪟 Modal Component
 * 
 * Reusable modal dialog component with overlay, animations, and keyboard support.
 * 
 * @module components/shared/Modal
 * @author AI Assistant
 * @date 2025-11-03
 * 
 * @example
 * ```tsx
 * <Modal
 *   isOpen={showModal}
 *   onClose={() => setShowModal(false)}
 *   title="Confirm Delete"
 * >
 *   <p>Are you sure you want to delete this item?</p>
 *   <ButtonGroup>
 *     <Button variant="secondary" onClick={() => setShowModal(false)}>
 *       Cancel
 *     </Button>
 *     <Button variant="danger" onClick={handleDelete}>
 *       Delete
 *     </Button>
 *   </ButtonGroup>
 * </Modal>
 * ```
 */

import React, { useEffect, useCallback } from 'react';

/**
 * Modal size types
 */
export type ModalSize = 'small' | 'medium' | 'large' | 'fullscreen';

/**
 * Modal component props
 */
export interface ModalProps {
  /** Whether modal is visible */
  isOpen: boolean;
  
  /** Callback when modal should close */
  onClose: () => void;
  
  /** Modal title */
  title?: string;
  
  /** Modal description/subtitle */
  description?: string;
  
  /** Modal size (default: 'medium') */
  size?: ModalSize;
  
  /** Modal content */
  children: React.ReactNode;
  
  /** Footer content (buttons, etc.) */
  footer?: React.ReactNode;
  
  /** Whether clicking overlay closes modal (default: true) */
  closeOnOverlayClick?: boolean;
  
  /** Whether pressing Escape closes modal (default: true) */
  closeOnEscape?: boolean;
  
  /** Whether to show close button (default: true) */
  showCloseButton?: boolean;
  
  /** Additional CSS classes for modal content */
  className?: string;
  
  /** Additional CSS classes for overlay */
  overlayClassName?: string;
}

/**
 * Modal component
 */
export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  size = 'medium',
  children,
  footer,
  closeOnOverlayClick = true,
  closeOnEscape = true,
  showCloseButton = true,
  className = '',
  overlayClassName = '',
}) => {
  // Handle escape key
  const handleEscape = useCallback(
    (event: KeyboardEvent) => {
      if (closeOnEscape && event.key === 'Escape') {
        onClose();
      }
    },
    [closeOnEscape, onClose]
  );

  // Add/remove escape key listener
  useEffect(() => {
    if (isOpen) {
      document.addEventListener('keydown', handleEscape);
      // Prevent body scroll when modal is open
      document.body.style.overflow = 'hidden';
    }

    return () => {
      document.removeEventListener('keydown', handleEscape);
      document.body.style.overflow = '';
    };
  }, [isOpen, handleEscape]);

  // Don't render if not open
  if (!isOpen) {
    return null;
  }

  // Handle overlay click
  const handleOverlayClick = (e: React.MouseEvent<HTMLDivElement>) => {
    if (closeOnOverlayClick && e.target === e.currentTarget) {
      onClose();
    }
  };

  // Build CSS classes
  const overlayClasses = ['modal-overlay', overlayClassName]
    .filter(Boolean)
    .join(' ');

  const contentClasses = ['modal-content', `modal-${size}`, className]
    .filter(Boolean)
    .join(' ');

  return (
    <div className={overlayClasses} onClick={handleOverlayClick}>
      <div className={contentClasses} onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        {(title || showCloseButton) && (
          <div className="modal-header">
            <div className="modal-title-section">
              {title && <h2 className="modal-title">{title}</h2>}
              {description && <p className="modal-description">{description}</p>}
            </div>
            {showCloseButton && (
              <button
                className="modal-close-btn"
                onClick={onClose}
                aria-label="Close modal"
                title="Close (Esc)"
              >
                ✕
              </button>
            )}
          </div>
        )}

        {/* Body */}
        <div className="modal-body">{children}</div>

        {/* Footer */}
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>
  );
};

/**
 * Confirmation modal component
 * 
 * Simplified modal for yes/no confirmations
 * 
 * @example
 * ```tsx
 * <ConfirmModal
 *   isOpen={showConfirm}
 *   onClose={() => setShowConfirm(false)}
 *   onConfirm={handleDelete}
 *   title="Delete Item"
 *   message="Are you sure you want to delete this item? This action cannot be undone."
 *   confirmText="Delete"
 *   confirmVariant="danger"
 * />
 * ```
 */
export interface ConfirmModalProps {
  /** Whether modal is visible */
  isOpen: boolean;
  
  /** Callback when modal should close */
  onClose: () => void;
  
  /** Callback when user confirms */
  onConfirm: () => void;
  
  /** Modal title */
  title: string;
  
  /** Confirmation message */
  message: string;
  
  /** Confirm button text (default: 'Confirm') */
  confirmText?: string;
  
  /** Cancel button text (default: 'Cancel') */
  cancelText?: string;
  
  /** Confirm button variant (default: 'primary') */
  confirmVariant?: 'primary' | 'danger' | 'warning';
  
  /** Whether confirm action is loading */
  loading?: boolean;
}

export const ConfirmModal: React.FC<ConfirmModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  confirmVariant = 'primary',
  loading = false,
}) => {
  const handleConfirm = () => {
    onConfirm();
    if (!loading) {
      onClose();
    }
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="small"
      closeOnOverlayClick={!loading}
      closeOnEscape={!loading}
    >
      <p className="confirm-message">{message}</p>
      <div className="modal-actions">
        <button
          className="modal-btn modal-btn-secondary"
          onClick={onClose}
          disabled={loading}
        >
          {cancelText}
        </button>
        <button
          className={`modal-btn modal-btn-${confirmVariant}`}
          onClick={handleConfirm}
          disabled={loading}
        >
          {loading ? '⏳ Processing...' : confirmText}
        </button>
      </div>
    </Modal>
  );
};

// Export default
export default Modal;


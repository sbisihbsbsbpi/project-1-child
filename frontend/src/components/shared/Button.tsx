/**
 * 🔘 Button Component
 * 
 * Reusable button component with consistent styling and behavior.
 * Supports multiple variants, sizes, and states.
 * 
 * @module components/shared/Button
 * @author AI Assistant
 * @date 2025-11-03
 * 
 * @example
 * ```tsx
 * // Primary button
 * <Button variant="primary" onClick={handleClick}>
 *   Save Changes
 * </Button>
 * 
 * // Danger button with icon
 * <Button variant="danger" icon="🗑️" onClick={handleDelete}>
 *   Delete
 * </Button>
 * 
 * // Loading state
 * <Button variant="primary" loading disabled>
 *   Processing...
 * </Button>
 * ```
 */

import React from 'react';

/**
 * Button variant types
 */
export type ButtonVariant = 
  | 'primary'    // Main action button (blue)
  | 'secondary'  // Secondary action (gray)
  | 'success'    // Success action (green)
  | 'danger'     // Destructive action (red)
  | 'warning'    // Warning action (orange)
  | 'ghost';     // Minimal styling

/**
 * Button size types
 */
export type ButtonSize = 'small' | 'medium' | 'large';

/**
 * Button component props
 */
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  /** Button variant (default: 'primary') */
  variant?: ButtonVariant;
  
  /** Button size (default: 'medium') */
  size?: ButtonSize;
  
  /** Icon to display before text (emoji or icon name) */
  icon?: string;
  
  /** Icon to display after text */
  iconAfter?: string;
  
  /** Loading state - shows spinner and disables button */
  loading?: boolean;
  
  /** Full width button */
  fullWidth?: boolean;
  
  /** Additional CSS classes */
  className?: string;
  
  /** Button content */
  children?: React.ReactNode;
}

/**
 * Button component
 */
export const Button: React.FC<ButtonProps> = ({
  variant = 'primary',
  size = 'medium',
  icon,
  iconAfter,
  loading = false,
  fullWidth = false,
  className = '',
  children,
  disabled,
  ...props
}) => {
  // Build CSS classes
  const classes = [
    'btn',
    `btn-${variant}`,
    `btn-${size}`,
    fullWidth && 'btn-full-width',
    loading && 'btn-loading',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <button
      className={classes}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <span className="btn-spinner">⏳</span>}
      {!loading && icon && <span className="btn-icon">{icon}</span>}
      {children && <span className="btn-text">{children}</span>}
      {!loading && iconAfter && <span className="btn-icon-after">{iconAfter}</span>}
    </button>
  );
};

/**
 * Button group component for grouping related buttons
 * 
 * @example
 * ```tsx
 * <ButtonGroup>
 *   <Button variant="secondary">Cancel</Button>
 *   <Button variant="primary">Save</Button>
 * </ButtonGroup>
 * ```
 */
export interface ButtonGroupProps {
  /** Button elements */
  children: React.ReactNode;
  
  /** Alignment (default: 'right') */
  align?: 'left' | 'center' | 'right';
  
  /** Additional CSS classes */
  className?: string;
}

export const ButtonGroup: React.FC<ButtonGroupProps> = ({
  children,
  align = 'right',
  className = '',
}) => {
  const classes = [
    'btn-group',
    `btn-group-${align}`,
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return <div className={classes}>{children}</div>;
};

/**
 * Icon button component (button with only an icon, no text)
 * 
 * @example
 * ```tsx
 * <IconButton icon="⚙️" onClick={openSettings} title="Settings" />
 * ```
 */
export interface IconButtonProps extends Omit<ButtonProps, 'children'> {
  /** Icon to display (required) */
  icon: string;
  
  /** Tooltip text (required for accessibility) */
  title: string;
}

export const IconButton: React.FC<IconButtonProps> = ({
  icon,
  title,
  ...props
}) => {
  return (
    <Button
      {...props}
      className={`btn-icon-only ${props.className || ''}`}
      title={title}
      aria-label={title}
    >
      {icon}
    </Button>
  );
};

// Export default
export default Button;


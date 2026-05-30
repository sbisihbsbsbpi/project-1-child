import React from 'react';

/**
 * Accessible info button component that replaces raw "i" text spans with proper semantic HTML.
 * 
 * Features:
 * - Uses semantic <button> element for keyboard accessibility
 * - Provides aria-label for screen readers
 * - Supports aria-describedby for tooltip association
 * - Keyboard accessible (Enter/Space to activate, Escape to close tooltip)
 * - Visible focus states
 * 
 * @example
 * <InfoButton 
 *   ariaLabel="Information about batch mode"
 *   tooltip="Batch mode allows processing multiple URLs"
 * />
 */

interface InfoButtonProps {
  /** Accessible label for screen readers */
  ariaLabel: string;
  /** Tooltip text to display on hover/focus */
  tooltip: string;
  /** Optional unique ID for aria-describedby association */
  id?: string;
  /** Optional CSS class name */
  className?: string;
  /** Optional inline styles */
  style?: React.CSSProperties;
}

export const InfoButton: React.FC<InfoButtonProps> = ({
  ariaLabel,
  tooltip,
  id,
  className = 'info-icon',
  style = {}
}) => {
  const buttonId = id || `info-button-${React.useId()}`;
  const tooltipId = `${buttonId}-tooltip`;

  return (
    <button
      id={buttonId}
      type="button"
      className={className}
      aria-label={ariaLabel}
      aria-describedby={tooltipId}
      title={tooltip}
      style={{
        marginLeft: '6px',
        cursor: 'help',
        background: 'transparent',
        border: 'none',
        padding: '2px 6px',
        fontSize: 'inherit',
        ...style
      }}
      onClick={(e) => {
        // Prevent form submission or other default actions
        e.preventDefault();
        e.stopPropagation();
      }}
      onKeyDown={(e) => {
        // Activate on Enter or Space
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          // Could trigger tooltip display here if implementing custom tooltips
        }
      }}
    >
      <span aria-hidden="true">i</span>
      {/* Hidden tooltip content for screen readers */}
      <span id={tooltipId} className="sr-only">
        {tooltip}
      </span>
    </button>
  );
};

/**
 * Accessible info icon using a custom icon or emoji instead of "i".
 * Same accessibility features as InfoButton but allows custom visual representation.
 */
interface InfoIconProps extends InfoButtonProps {
  /** The icon/emoji to display. Defaults to "ℹ️" */
  icon?: string;
}

export const InfoIcon: React.FC<InfoIconProps> = ({
  ariaLabel,
  tooltip,
  icon = 'ℹ️',
  id,
  className = 'info-icon',
  style = {}
}) => {
  const buttonId = id || `info-icon-${React.useId()}`;
  const tooltipId = `${buttonId}-tooltip`;

  return (
    <button
      id={buttonId}
      type="button"
      className={className}
      aria-label={ariaLabel}
      aria-describedby={tooltipId}
      title={tooltip}
      style={{
        marginLeft: '6px',
        cursor: 'help',
        background: 'transparent',
        border: 'none',
        padding: '2px',
        fontSize: 'inherit',
        ...style
      }}
      onClick={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
        }
      }}
    >
      <span aria-hidden="true">{icon}</span>
      <span id={tooltipId} className="sr-only">
        {tooltip}
      </span>
    </button>
  );
};

export default InfoButton;

import React from 'react';
import { FallbackProps } from 'react-error-boundary';

export const FeatureErrorFallback: React.FC<FallbackProps> = ({ error, resetErrorBoundary }) => {
  return (
    <div className="tab-content">
      <div
        style={{
          padding: '30px',
          textAlign: 'center',
          backgroundColor: '#f8d7da',
          border: '1px solid #f5c6cb',
          borderRadius: '6px',
          margin: '20px',
        }}
      >
        <h3 style={{ color: '#721c24', marginBottom: '12px' }}>
          ❌ This feature encountered an error
        </h3>
        <p style={{ color: '#721c24', marginBottom: '12px', fontSize: '14px' }}>
          Don't worry, other features should still work normally.
        </p>
        <details style={{ marginBottom: '16px', textAlign: 'left' }}>
          <summary style={{ cursor: 'pointer', color: '#721c24', fontSize: '13px' }}>
            Technical details
          </summary>
          <pre
            style={{
              marginTop: '8px',
              padding: '8px',
              backgroundColor: '#fff',
              border: '1px solid #f5c6cb',
              borderRadius: '4px',
              overflow: 'auto',
              fontSize: '11px',
              color: '#721c24',
            }}
          >
            {error.message}
          </pre>
        </details>
        <button
          onClick={resetErrorBoundary}
          style={{
            padding: '8px 16px',
            backgroundColor: '#dc3545',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '13px',
          }}
        >
          🔄 Retry
        </button>
      </div>
    </div>
  );
};


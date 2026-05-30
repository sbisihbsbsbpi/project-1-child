import React from 'react';
import { FallbackProps } from 'react-error-boundary';

export const ErrorFallback: React.FC<FallbackProps> = ({ error, resetErrorBoundary }) => {
  return (
    <div
      style={{
        padding: '40px',
        textAlign: 'center',
        backgroundColor: '#fff3cd',
        border: '2px solid #ffc107',
        borderRadius: '8px',
        margin: '20px',
      }}
    >
      <h2 style={{ color: '#856404', marginBottom: '16px' }}>
        ⚠️ Something went wrong
      </h2>
      <p style={{ color: '#856404', marginBottom: '16px' }}>
        The application encountered an unexpected error.
      </p>
      <details style={{ marginBottom: '20px', textAlign: 'left' }}>
        <summary style={{ cursor: 'pointer', color: '#856404', fontWeight: 'bold' }}>
          Error details
        </summary>
        <pre
          style={{
            marginTop: '10px',
            padding: '10px',
            backgroundColor: '#f8f9fa',
            border: '1px solid #dee2e6',
            borderRadius: '4px',
            overflow: 'auto',
            fontSize: '12px',
            color: '#212529',
          }}
        >
          {error.message}
          {'\n\n'}
          {error.stack}
        </pre>
      </details>
      <button
        onClick={resetErrorBoundary}
        style={{
          padding: '10px 20px',
          backgroundColor: '#ffc107',
          color: '#212529',
          border: 'none',
          borderRadius: '4px',
          cursor: 'pointer',
          fontSize: '14px',
          fontWeight: '500',
        }}
      >
        🔄 Try again
      </button>
    </div>
  );
};


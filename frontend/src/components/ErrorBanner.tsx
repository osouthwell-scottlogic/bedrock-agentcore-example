import { useState } from 'react';
import { Alert } from './ui/Alert';
import { Button } from './ui/Button';
import styles from './ErrorBanner.module.css';

export interface UiError {
  message: string;
  errorCode?: string;
  requestId?: string;
  details?: unknown;
}

interface ErrorBannerProps {
  error: UiError | null;
  onDismiss?: () => void;
  header?: string;
}

const stringifyDetails = (details: unknown): string => {
  try {
    return JSON.stringify(details, null, 2);
  } catch {
    return String(details);
  }
};

export function ErrorBanner({ error, onDismiss, header }: ErrorBannerProps) {
  const [expanded, setExpanded] = useState(false);

  if (!error) return null;

  const { message, errorCode, requestId, details } = error;
  const hasDetails = details !== undefined && details !== null && details !== '';

  return (
    <Alert
      type="error"
      onDismiss={onDismiss}
      header={header || 'An error occurred'}
    >
      <div className={styles.content}>
        <div className={styles.message}>{message}</div>
        {errorCode && (
          <div className={styles.meta}>Error code: {errorCode}</div>
        )}
        {requestId && (
          <div className={styles.meta}>
            Request ID: {requestId}{' '}
            <Button
              variant="link"
              onClick={() => navigator.clipboard.writeText(requestId)}
            >
              Copy
            </Button>
          </div>
        )}
        {hasDetails && (
          <details className={styles.details}>
            <summary className={styles.summary}>
              {expanded ? 'Hide details' : 'Show details'}
            </summary>
            <pre className={styles.pre}>
              {stringifyDetails(details)}
            </pre>
          </details>
        )}
      </div>
    </Alert>
  );
}

export default ErrorBanner;

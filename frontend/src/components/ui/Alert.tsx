import { ReactNode } from 'react';
import { CloseIcon } from '../icons/Close';
import styles from './Alert.module.css';

interface AlertProps {
  children: ReactNode;
  type?: 'error' | 'info' | 'success';
  onDismiss?: () => void;
  header?: string;
}

export function Alert({ children, type = 'info', onDismiss, header }: AlertProps) {
  return (
    <div className={`${styles.alert} ${styles[type]}`} role="alert">
      <div className={styles.content}>
        {header && <div className={styles.header}>{header}</div>}
        <div className={styles.body}>{children}</div>
      </div>
      {onDismiss && (
        <button 
          className={styles.dismiss} 
          onClick={onDismiss}
          aria-label="Dismiss alert"
        >
          <CloseIcon size={16} />
        </button>
      )}
    </div>
  );
}

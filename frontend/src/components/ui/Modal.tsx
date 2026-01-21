import { ReactNode, useEffect } from 'react';
import { CloseIcon } from '../icons/Close';
import styles from './Modal.module.css';

interface ModalProps {
  visible: boolean;
  onDismiss: () => void;
  header: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Modal({ visible, onDismiss, header, children, footer }: ModalProps) {
  useEffect(() => {
    if (visible) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [visible]);

  if (!visible) return null;

  return (
    <div className={styles.overlay} onClick={onDismiss}>
      <div 
        className={styles.modal} 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-header"
      >
        <div className={styles.header}>
          <h2 id="modal-header" className={styles.title}>{header}</h2>
          <button 
            className={styles.close} 
            onClick={onDismiss}
            aria-label="Close modal"
          >
            <CloseIcon />
          </button>
        </div>
        <div className={styles.body}>{children}</div>
        {footer && <div className={styles.footer}>{footer}</div>}
      </div>
    </div>
  );
}

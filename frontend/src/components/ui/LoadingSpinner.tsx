import styles from './LoadingSpinner.module.css';

interface LoadingSpinnerProps {
  size?: number;
  text?: string;
}

export function LoadingSpinner({ size = 24, text }: LoadingSpinnerProps) {
  return (
    <div className={styles.wrapper}>
      <div 
        className={styles.spinner} 
        style={{ width: size, height: size }}
        role="status"
        aria-label={text || 'Loading'}
      />
      {text && <span className={styles.text}>{text}</span>}
    </div>
  );
}

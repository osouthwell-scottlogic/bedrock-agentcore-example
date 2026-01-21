import { CSSProperties, ReactNode } from 'react';
import styles from './IconButton.module.css';

interface IconButtonProps {
  children: ReactNode;
  onClick?: () => void;
  disabled?: boolean;
  ariaLabel: string;
  className?: string;
  style?: CSSProperties;
}

export function IconButton({
  children,
  onClick,
  disabled = false,
  ariaLabel,
  className = '',
  style,
}: IconButtonProps) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={disabled}
      className={`${styles.iconButton} ${className}`}
      style={style}
      aria-label={ariaLabel}
      title={ariaLabel}
    >
      {children}
    </button>
  );
}

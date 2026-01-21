import { ChangeEvent, CSSProperties, KeyboardEvent } from 'react';
import styles from './Textarea.module.css';

interface TextareaProps {
  value: string;
  onChange: (value: string) => void;
  onKeyDown?: (e: KeyboardEvent<HTMLTextAreaElement>) => void;
  placeholder?: string;
  disabled?: boolean;
  rows?: number;
  id?: string;
  name?: string;
  className?: string;
  style?: CSSProperties;
  ariaLabel?: string;
}

export function Textarea({
  value,
  onChange,
  onKeyDown,
  placeholder,
  disabled = false,
  rows = 3,
  id,
  name,
  className = '',
  style,
  ariaLabel,
}: TextareaProps) {
  const handleChange = (e: ChangeEvent<HTMLTextAreaElement>) => {
    onChange(e.target.value);
  };

  return (
    <textarea
      value={value}
      onChange={handleChange}
      onKeyDown={onKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      rows={rows}
      id={id}
      name={name}
      className={`${styles.textarea} ${className}`}
      style={style}
      aria-label={ariaLabel}
    />
   );
}

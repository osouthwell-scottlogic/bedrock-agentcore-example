import { ChangeEvent, CSSProperties } from 'react';
import styles from './Input.module.css';

interface InputProps {
  value: string;
  onChange: (value: string) => void;
  type?: 'text' | 'email' | 'password';
  placeholder?: string;
  disabled?: boolean;
  required?: boolean;
  id?: string;
  name?: string;
  className?: string;
  style?: CSSProperties;
  ariaLabel?: string;
}

export function Input({
  value,
  onChange,
  type = 'text',
  placeholder,
  disabled = false,
  required = false,
  id,
  name,
  className = '',
  style,
  ariaLabel,
}: InputProps) {
  const handleChange = (e: ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  return (
    <input
      type={type}
      value={value}
      onChange={handleChange}
      placeholder={placeholder}
      disabled={disabled}
      required={required}
      id={id}
      name={name}
      className={`${styles.input} ${className}`}
      style={style}
      aria-label={ariaLabel}
    />
  );
}

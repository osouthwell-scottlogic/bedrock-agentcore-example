/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
import { KeyboardEvent } from 'react';
import { Textarea } from '../ui/Textarea';
import { IconButton } from '../ui/IconButton';
import { SendIcon } from '../icons/Send';
import styles from './ChatInput.module.css';

export interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
}

export function ChatInput({ value, onChange, onSend, disabled }: ChatInputProps) {
  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !disabled) {
        onSend();
      }
    }
  };

  return (
    <div className={styles.wrapper}>
      <Textarea
        value={value}
        onChange={onChange}
        onKeyDown={handleKeyDown}
        placeholder="Ask about bonds, customers, or market data..."
        disabled={disabled}
        rows={2}
        ariaLabel="Message input"
      />
      <IconButton
        onClick={onSend}
        disabled={disabled || !value.trim()}
        ariaLabel="Send message"
      >
        <SendIcon />
      </IconButton>
    </div>
  );
}

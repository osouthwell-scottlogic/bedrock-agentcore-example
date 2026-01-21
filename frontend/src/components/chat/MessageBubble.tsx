/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
import { MarkdownRenderer } from './MarkdownRenderer';
import { messageBubbleStyles } from '../../styles/components';

export interface MessageBubbleProps {
  type: 'user' | 'agent';
  content: string;
}

export function MessageBubble({ type, content }: MessageBubbleProps) {
  const isUser = type === 'user';

  if (isUser) {
    return (
      <div css={css(messageBubbleStyles.userBubble)}>
        <MarkdownRenderer content={content} variant="user" />
      </div>
    );
  }

  return (
    <div css={css(messageBubbleStyles.agentBubble)}>
      <MarkdownRenderer content={content} variant="agent" />
    </div>
  );
}

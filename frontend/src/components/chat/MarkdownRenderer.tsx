/** @jsxImportSource @emotion/react */
import { css } from '@emotion/react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import '../../markdown.css';
import { markdownStyles } from '../../styles/components';

export interface MarkdownRendererProps {
  content: string;
  variant: 'user' | 'agent';
}

export function MarkdownRenderer({ content, variant }: MarkdownRendererProps) {
  const isUser = variant === 'user';

  return (
    <div css={css([markdownStyles.wrapper, isUser && markdownStyles.wrapperUser])}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          code({ node, inline, className, children, ...props }: any) {
            return inline ? (
              <code
                css={css(isUser ? markdownStyles.inlineCodeUser : markdownStyles.inlineCodeAgent)}
                {...props}
              >
                {children}
              </code>
            ) : (
              <code
                css={css(isUser ? markdownStyles.blockCodeUser : markdownStyles.blockCode)}
                {...props}
              >
                {children}
              </code>
            );
          },
          a({ node, children, ...props }: any) {
            return (
              <a
                css={css(markdownStyles.link)}
                {...props}
                target="_blank"
                rel="noopener noreferrer"
              >
                {children}
              </a>
            );
          },
          ul({ node, children, ...props }: any) {
            return (
              <ul css={css(markdownStyles.list)} {...props}>
                {children}
              </ul>
            );
          },
          ol({ node, children, ...props }: any) {
            return (
              <ol css={css(markdownStyles.list)} {...props}>
                {children}
              </ol>
            );
          },
          p({ node, children, ...props }: any) {
            return (
              <p css={css(markdownStyles.paragraph)} {...props}>
                {children}
              </p>
            );
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}

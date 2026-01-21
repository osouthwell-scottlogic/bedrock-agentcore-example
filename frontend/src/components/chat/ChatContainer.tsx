import { ChatMessage } from "./ChatMessage";
import { Message } from "../../hooks/useChatMessages";
import { LoadingSpinner } from "../ui/LoadingSpinner";
import { chatContainerStyles, chatFooterOverlayStyles } from "../../styles/components";
import { ReactNode, useEffect, useRef } from "react";

export interface ChatContainerProps {
  messages: Message[];
  loading: boolean;
  children?: ReactNode;
  footerChildren?: ReactNode;
}

export function ChatContainer({ messages, loading, children, footerChildren }: ChatContainerProps) {
  const scrollContainerRef = useRef<HTMLDivElement | null>(null);
  const isAtBottomRef = useRef<boolean>(true);

  const updateIsAtBottom = () => {
    const el = scrollContainerRef.current;
    if (!el) return;
    const threshold = 40; // px tolerance for "near bottom"
    const atBottom = el.scrollTop + el.clientHeight >= el.scrollHeight - threshold;
    isAtBottomRef.current = atBottom;
  };

  // Keep container at the bottom when new items come in, but only if already at/near bottom
  useEffect(() => {
    const el = scrollContainerRef.current;
    if (!el) return;
    if (isAtBottomRef.current) {
      // Scroll to bottom after layout updates
      requestAnimationFrame(() => {
        el.scrollTop = el.scrollHeight;
      });
    }
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div style={chatContainerStyles.wrapper}>
        <div style={chatContainerStyles.contentWrapper}>
          <div style={chatContainerStyles.emptyState}>
            <div style={chatContainerStyles.emptyStateContent}>
              <h2 style={chatContainerStyles.emptyStateTitle}>
                Bank X Financial Assistant
              </h2>
              <p style={chatContainerStyles.emptyStateSubtitle}>
                Ask me about bond products, customer portfolios, or market
                research
              </p>
            </div>
          </div>
          {footerChildren && (
            <div style={chatFooterOverlayStyles.wrapper}>{footerChildren}</div>
          )}
          {children}
        </div>
      </div>
    );
  }

  return (
    <div style={chatContainerStyles.outerWrapper}>
      {/* Fixed header - does not scroll */}
      <div style={chatContainerStyles.headerWithMessages}>
        <h2 style={chatContainerStyles.headerTitleWithMessages}>
          Bank X Financial Assistant
        </h2>
      </div>

      {/* Scrollable messages area */}
      <div
        style={chatContainerStyles.messagesScrollContainer}
        ref={scrollContainerRef}
        onScroll={updateIsAtBottom}
      >
        <div style={chatContainerStyles.messagesWrapper}>
          {messages.map((message, index) => (
            <ChatMessage
              key={index}
              message={message}
              messageIndex={index}
              isLast={index === messages.length - 1 && !loading}
            />
          ))}
          {loading && (
            <div style={chatContainerStyles.loadingIndicator}>
              <LoadingSpinner text="Processing your request..." />
            </div>
          )}
          {children}
        </div>
        {/* Sticky bottom suggestions inside scroll container */}
        {footerChildren && (
          <div style={chatFooterOverlayStyles.wrapper}>{footerChildren}</div>
        )}
      </div>
    </div>
  );
}

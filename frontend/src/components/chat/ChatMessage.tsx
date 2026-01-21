import { MessageAvatar } from "./MessageAvatar";
import { MessageBubble } from "./MessageBubble";
import { Message } from "../../hooks/useChatMessages";
import { chatMessageStyles } from "../../styles/components";

export interface ChatMessageProps {
  message: Message;
  messageIndex: number;
  isLast?: boolean;
}

export function ChatMessage({ message, isLast }: ChatMessageProps) {
  const isUser = message.type === "user";

  return (
    <div
      style={{
        ...chatMessageStyles.wrapper,
        ...(isUser
          ? chatMessageStyles.wrapperUser
          : chatMessageStyles.wrapperAgent),
        ...(isLast && chatMessageStyles.wrapperLast),
      }}
    >
      {!isUser && (
        <div style={chatMessageStyles.avatarWrapper}>
          <MessageAvatar type="agent" />
        </div>
      )}
      <div
        style={{
          ...chatMessageStyles.contentWrapper,
          ...(isUser
            ? chatMessageStyles.contentWrapperUser
            : chatMessageStyles.contentWrapperAgent),
        }}
      >
        <MessageBubble type={message.type} content={message.content} />
      </div>
      {isUser && (
        <div style={chatMessageStyles.avatarWrapper}>
          <MessageAvatar type="user" />
        </div>
      )}
    </div>
  );
}

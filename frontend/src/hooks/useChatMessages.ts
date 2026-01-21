import { useState } from 'react';
import { invokeAgent } from '../agentcore';
import { HttpError } from '../lib/fetchJson';
import { UiError } from '../components/ErrorBanner';
import { parseAgentResponse } from '../lib/responseParser';

export interface Message {
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
}

export interface UseChatMessagesReturn {
  messages: Message[];
  loading: boolean;
  error: UiError | null;
  prompt: string;
  setPrompt: (prompt: string) => void;
  setError: (error: UiError | null) => void;
  handleSendMessage: (user: any, isLocalDev: boolean, onAuthRequired: () => void, onMessageSent: (messages: Message[]) => void) => Promise<void>;
  resetMessages: () => void;
}

export function useChatMessages(): UseChatMessagesReturn {
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<UiError | null>(null);

  const handleSendMessage = async (
    user: any,
    isLocalDev: boolean,
    onAuthRequired: () => void,
    onMessageSent: (messages: Message[]) => void
  ) => {
    if (!isLocalDev && !user) {
      onAuthRequired();
      return;
    }

    if (!prompt.trim()) {
      setError({ message: 'Please enter a prompt' });
      return;
    }

    const userMessage: Message = {
      type: 'user',
      content: prompt,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError(null);
    const currentPrompt = prompt;
    setPrompt('');

    const streamingMessageIndex = messages.length + 1;
    setMessages(prev => [...prev, {
      type: 'agent',
      content: '',
      timestamp: new Date()
    }]);

    try {
      let streamedContent = '';

      // Build conversation history from previous messages (excluding the current user message)
      const conversationHistory = messages.map(msg => ({
        role: msg.type === 'user' ? 'user' : 'assistant',
        content: msg.content
      }));

      const data = await invokeAgent({
        prompt: currentPrompt,
        conversationHistory,
        onChunk: (chunk: string) => {
          streamedContent += chunk;

          setMessages(prev => {
            const updated = [...prev];
            updated[streamingMessageIndex] = {
              type: 'agent',
              content: streamedContent,
              timestamp: new Date()
            };
            return updated;
          });
        }
      });

      const finalContent = parseAgentResponse(data.response || streamedContent);
      const finalMessages = [...messages, userMessage, {
        type: 'agent',
        content: finalContent,
        timestamp: new Date()
      }] as Message[];
      
      setMessages(prev => {
        const updated = [...prev];
        updated[streamingMessageIndex] = {
          type: 'agent',
          content: finalContent,
          timestamp: new Date()
        };
        return updated;
      });

      onMessageSent(finalMessages);
    } catch (err: any) {
      if (err instanceof HttpError) {
        setError({
          message: err.message,
          errorCode: err.errorCode,
          requestId: err.requestId,
          details: err.details,
        });
      } else {
        setError({ message: err?.message || 'Unexpected error' });
      }
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  const resetMessages = () => {
    setMessages([]);
  };

  return {
    messages,
    loading,
    error,
    prompt,
    setPrompt,
    setError,
    handleSendMessage,
    resetMessages,
  };
}

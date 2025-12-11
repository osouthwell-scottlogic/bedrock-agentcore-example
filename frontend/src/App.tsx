import { useState, useEffect } from 'react';
import AppLayout from '@cloudscape-design/components/app-layout';
import TopNavigation from '@cloudscape-design/components/top-navigation';
import ContentLayout from '@cloudscape-design/components/content-layout';
import Container from '@cloudscape-design/components/container';
import SpaceBetween from '@cloudscape-design/components/space-between';
import Box from '@cloudscape-design/components/box';
import ButtonGroup from '@cloudscape-design/components/button-group';
import Grid from '@cloudscape-design/components/grid';
import StatusIndicator from '@cloudscape-design/components/status-indicator';
import ChatBubble from '@cloudscape-design/chat-components/chat-bubble';
import Avatar from '@cloudscape-design/chat-components/avatar';
import SupportPromptGroup from '@cloudscape-design/chat-components/support-prompt-group';
import PromptInput from '@cloudscape-design/components/prompt-input';
import Alert from '@cloudscape-design/components/alert';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { invokeAgent } from './agentcore';
import './markdown.css';

interface AuthUser {
  email: string;
}

interface Message {
  type: 'user' | 'agent';
  content: string;
  timestamp: Date;
  feedback?: 'helpful' | 'not-helpful';
  feedbackSubmitting?: boolean;
}

interface MessageFeedback {
  [messageIndex: number]: {
    feedback?: 'helpful' | 'not-helpful';
    submitting?: boolean;
    showCopySuccess?: boolean;
  };
}

function App() {
  const isLocalDev = (import.meta as any).env.VITE_LOCAL_DEV === 'true';

  // All hooks declared at the top level to maintain consistent order
  const [prompt, setPrompt] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [user, setUser] = useState<AuthUser | null>(null);
  const [showAuthModal, setShowAuthModal] = useState(false);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [messageFeedback, setMessageFeedback] = useState<MessageFeedback>({});
  const [showSupportPrompts, setShowSupportPrompts] = useState(true);
  const [AuthModalComponent, setAuthModalComponent] = useState<any>(null);
  const [dynamicPrompts, setDynamicPrompts] = useState<Array<{id: string, text: string}>>([]);
  const [loadingPrompts, setLoadingPrompts] = useState(false);

  // Authentication effect
  useEffect(() => {
    if (isLocalDev) {
      // Skip authentication in local development mode
      setCheckingAuth(false);
      setUser({ email: 'local-dev@example.com' } as AuthUser);
      // Generate initial dynamic prompts
      generateInitialPrompts();
    } else {
      checkAuth();
    }
  }, [isLocalDev]);

  // Generate initial prompts on startup
  const generateInitialPrompts = async () => {
    setLoadingPrompts(true);
    try {
      const suggestionPrompt = `You are helping a user get started with Bank X Financial Assistant. Suggest 4 brief, actionable prompts they might want to try first.

Available capabilities:
- list_available_bonds: Show all 4 bond products
- get_customer_profile: View customer details  
- get_product_details: Get detailed bond information
- search_market_data: Research market trends
- send_email: Email qualified customers about bonds
- get_recent_emails: View sent email history

Respond ONLY with a JSON array of 4 short prompts (each 3-8 words), like:
["Show all available bonds", "View customer portfolios", "Email about Government Bond Y", "Check recent emails"]`;

      let suggestionResponse = '';
      
      await invokeAgent({
        prompt: suggestionPrompt,
        onChunk: (chunk: string) => {
          suggestionResponse += chunk;
        }
      });

      const cleanedResponse = cleanResponse(suggestionResponse);
      const jsonMatch = cleanedResponse.match(/\[[\s\S]*\]/);
      
      if (jsonMatch) {
        const suggestions = JSON.parse(jsonMatch[0]);
        if (Array.isArray(suggestions) && suggestions.length > 0) {
          const formattedPrompts = suggestions.slice(0, 4).map((text: string, idx: number) => ({
            id: `initial-${idx}`,
            text: text
          }));
          setDynamicPrompts(formattedPrompts);
        }
      }
    } catch (err) {
      console.error('Error generating initial prompts:', err);
    } finally {
      setLoadingPrompts(false);
    }
  };

  // AuthModal loading effect
  useEffect(() => {
    if (!isLocalDev && showAuthModal && !AuthModalComponent) {
      import('./AuthModal').then(module => {
        setAuthModalComponent(() => module.default);
      });
    }
  }, [showAuthModal, AuthModalComponent, isLocalDev]);

  const checkAuth = async () => {
    if (isLocalDev) return;

    try {
      const { getCurrentUser } = await import('./auth');
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      // Generate initial prompts after auth
      generateInitialPrompts();
    } catch (err) {
      setUser(null);
    } finally {
      setCheckingAuth(false);
    }
  };

  const handleSignOut = async () => {
    if (isLocalDev) return;

    try {
      const { signOut } = await import('./auth');
      signOut();
    } catch (err) {
      console.error('Error signing out:', err);
    }
    setUser(null);
    setMessages([]);
  };

  const handleAuthSuccess = async () => {
    setShowAuthModal(false);
    await checkAuth();
  };

  const handleFeedback = async (messageIndex: number, feedbackType: 'helpful' | 'not-helpful') => {
    // Set submitting state
    setMessageFeedback(prev => ({
      ...prev,
      [messageIndex]: { ...prev[messageIndex], submitting: true }
    }));

    // Simulate feedback submission (you can add actual API call here)
    await new Promise(resolve => setTimeout(resolve, 500));

    // Set feedback submitted
    setMessageFeedback(prev => ({
      ...prev,
      [messageIndex]: { feedback: feedbackType, submitting: false }
    }));
  };

  const handleCopy = async (messageIndex: number, content: string) => {
    try {
      await navigator.clipboard.writeText(content);

      // Show success indicator
      setMessageFeedback(prev => ({
        ...prev,
        [messageIndex]: { ...prev[messageIndex], showCopySuccess: true }
      }));

      // Hide success indicator after 2 seconds
      setTimeout(() => {
        setMessageFeedback(prev => ({
          ...prev,
          [messageIndex]: { ...prev[messageIndex], showCopySuccess: false }
        }));
      }, 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const cleanResponse = (response: string): string => {
    // Remove surrounding quotes if present
    let cleaned = response.trim();
    if ((cleaned.startsWith('"') && cleaned.endsWith('"')) ||
      (cleaned.startsWith("'") && cleaned.endsWith("'"))) {
      cleaned = cleaned.slice(1, -1);
    }
    // Replace literal \n with actual newlines
    cleaned = cleaned.replace(/\\n/g, '\n');
    // Replace literal \t with actual tabs
    cleaned = cleaned.replace(/\\t/g, '\t');
    return cleaned;
  };

  const handleSupportPromptClick = (promptText: string) => {
    // Fill the prompt input with the selected text
    setPrompt(promptText);
    // Hide support prompts after selection
    setShowSupportPrompts(false);
    // Clear dynamic prompts so new ones are generated after response
    setDynamicPrompts([]);
  };

  const handleSendMessage = async () => {
    if (!isLocalDev && !user) {
      setShowAuthModal(true);
      return;
    }

    if (!prompt.trim()) {
      setError('Please enter a prompt');
      return;
    }

    // Hide support prompts when sending a message
    setShowSupportPrompts(false);

    const userMessage: Message = {
      type: 'user',
      content: prompt,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setLoading(true);
    setError('');
    const currentPrompt = prompt;
    setPrompt('');

    // Add a placeholder message for the streaming response
    const streamingMessageIndex = messages.length + 1;
    setMessages(prev => [...prev, {
      type: 'agent',
      content: '',
      timestamp: new Date()
    }]);

    try {
      let streamedContent = '';

      const data = await invokeAgent({
        prompt: currentPrompt,
        onChunk: (chunk: string) => {
          // Accumulate the streamed content
          streamedContent += chunk;

          // Update the last message with the streamed content
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

      // Update with the final cleaned response
      const finalContent = cleanResponse(data.response || streamedContent);
      setMessages(prev => {
        const updated = [...prev];
        updated[streamingMessageIndex] = {
          type: 'agent',
          content: finalContent,
          timestamp: new Date()
        };
        return updated;
      });

      // Show support prompts and generate dynamic suggestions after agent responds
      setShowSupportPrompts(true);
      await generateDynamicPrompts([...messages, {
        type: 'agent',
        content: finalContent,
        timestamp: new Date()
      }]);
    } catch (err: any) {
      setError(err.message);
      // Remove the placeholder message on error
      setMessages(prev => prev.slice(0, -1));
    } finally {
      setLoading(false);
    }
  };

  // Generate dynamic prompts using the agent
  const generateDynamicPrompts = async (conversationHistory: Message[]) => {
    if (!isLocalDev && !user) return;
    
    setLoadingPrompts(true);
    
    try {
      // Build conversation summary for context
      const recentMessages = conversationHistory.slice(-4); // Last 4 messages
      const conversationSummary = recentMessages.map(m => 
        `${m.type === 'user' ? 'User' : 'Assistant'}: ${m.content.substring(0, 200)}${m.content.length > 200 ? '...' : ''}`
      ).join('\n');

      const suggestionPrompt = `Based on this conversation history, suggest 3-4 brief, actionable follow-up prompts the user might want to try next. Consider the available tools and natural conversation flow.

Available capabilities:
- list_available_bonds: Show all bond products
- get_customer_profile: View customer details
- get_product_details: Get bond information
- search_market_data: Research market trends
- send_email: Email customers about bonds (requires approval)
- get_recent_emails: View sent email history

Recent conversation:
${conversationSummary}

Respond ONLY with a JSON array of 3-4 short prompts (each 3-8 words), like:
["View customer portfolios", "Email about Corporate Bond A", "Research municipal bond trends"]`;

      let suggestionResponse = '';
      
      await invokeAgent({
        prompt: suggestionPrompt,
        onChunk: (chunk: string) => {
          suggestionResponse += chunk;
        }
      });

      // Parse the response to extract suggestions
      const cleanedResponse = cleanResponse(suggestionResponse);
      
      // Try to extract JSON array from response
      const jsonMatch = cleanedResponse.match(/\[[\s\S]*\]/);
      if (jsonMatch) {
        const suggestions = JSON.parse(jsonMatch[0]);
        if (Array.isArray(suggestions) && suggestions.length > 0) {
          const formattedPrompts = suggestions.slice(0, 4).map((text: string, idx: number) => ({
            id: `dynamic-${idx}-${Date.now()}`,
            text: text
          }));
          setDynamicPrompts(formattedPrompts);
        }
      } else {
        // Fallback to static prompts if parsing fails
        setDynamicPrompts([]);
      }
    } catch (err) {
      console.error('Error generating dynamic prompts:', err);
      setDynamicPrompts([]);
    } finally {
      setLoadingPrompts(false);
    }
  };

  // Get contextual support prompts based on conversation
  const getSupportPrompts = () => {
    // If we have dynamic prompts, use them
    if (dynamicPrompts.length > 0) {
      return dynamicPrompts;
    }

    // Initial prompts when no messages
    if (messages.length === 0) {
      return [
        { id: 'show-bonds', text: 'Show all available bond products' },
        { id: 'email-gov-bond', text: 'Email customers about Government Bond Y' },
        { id: 'email-corp-bond', text: 'Email customers about Corporate Bond A' },
        { id: 'recent-emails', text: 'Show recently sent emails' }
      ];
    }

    // Fallback static prompts
    return [
      { id: 'show-bonds-default', text: 'Show all bond products' },
      { id: 'email-default', text: 'Email customers about a bond' },
      { id: 'recent-default', text: 'Show recently sent emails' }
    ];
  };

  if (checkingAuth) {
    return (
      <>
        <TopNavigation
          identity={{
            href: "#",
            title: "Bank X Financial Assistant"
          }}
          utilities={[
            {
              type: "button",
              text: user ? `${user.email} | Sign Out` : "Sign In",
              iconName: user ? "user-profile" : "lock-private",
              onClick: () => {
                if (user) {
                  handleSignOut();
                } else {
                  setShowAuthModal(true);
                }
              }
            }
          ]}
          i18nStrings={{
            overflowMenuTriggerText: "More",
            overflowMenuTitleText: "All"
          }}
        />
        <AppLayout
          navigationHide={true}
          toolsHide={true}
          disableContentPaddings
          contentType="default"
          content={
            <ContentLayout defaultPadding>
              <Box textAlign="center" padding="xxl">
                Loading...
              </Box>
            </ContentLayout>
          }
        />
      </>
    );
  }

  return (
    <>
      {!isLocalDev && AuthModalComponent && (
        <AuthModalComponent
          visible={showAuthModal}
          onDismiss={() => setShowAuthModal(false)}
          onSuccess={handleAuthSuccess}
        />
      )}
      <TopNavigation
        identity={{
          href: "#",
          title: isLocalDev
            ? "Bank X Financial Assistant (Local Dev)"
            : "Bank X Financial Assistant"
        }}
        utilities={isLocalDev ? [
          {
            type: "button",
            text: "Local Development",
            iconName: "settings"
          }
        ] : [
          {
            type: "button",
            text: user ? `${user.email} | Sign Out` : "Sign In",
            iconName: user ? "user-profile" : "lock-private",
            onClick: () => {
              if (user) {
                handleSignOut();
              } else {
                setShowAuthModal(true);
              }
            }
          }
        ]}
        i18nStrings={{
          overflowMenuTriggerText: "More",
          overflowMenuTitleText: "All"
        }}
      />
      <AppLayout
        navigationHide={true}
        toolsHide={true}
        disableContentPaddings
        contentType="default"
        content={
          <ContentLayout defaultPadding>
            <Grid
              gridDefinition={[
                { colspan: { default: 12, xs: 1, s: 2 } },
                { colspan: { default: 12, xs: 10, s: 8 } },
                { colspan: { default: 12, xs: 1, s: 2 } }
              ]}
            >
              <div />
              <SpaceBetween size="l">
                {error && (
                  <Alert type="error" dismissible onDismiss={() => setError('')}>
                    {error}
                  </Alert>
                )}

                <Container>
                  <div role="region" aria-label="Chat">
                    <SpaceBetween size="m">
                      {messages.length === 0 ? (
                        <Box textAlign="center" padding={{ vertical: 'xxl' }} color="text-body-secondary">
                          Start a conversation with the generative AI assistant by typing a message below
                        </Box>
                      ) : (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                          {messages.map((message, index) => {
                            const feedback = messageFeedback[index];
                            const isAgent = message.type === 'agent';

                            return (
                              <div key={index} style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                                {isAgent && (
                                  <Avatar
                                    ariaLabel="Generative AI assistant"
                                    tooltipText="Generative AI assistant"
                                    iconName="gen-ai"
                                    color="gen-ai"
                                  />
                                )}
                                <div style={{ flex: 1 }}>
                                  <ChatBubble
                                    type={message.type === 'user' ? 'outgoing' : 'incoming'}
                                    ariaLabel={`${message.type === 'user' ? 'User' : 'Generative AI assistant'} message`}
                                    avatar={message.type === 'user' ? <div /> : undefined}
                                  >
                                    <ReactMarkdown
                                      remarkPlugins={[remarkGfm]}
                                      components={{
                                        // Style code blocks
                                        code: ({ className, children }: any) => {
                                          const inline = !className;
                                          return inline ? (
                                            <code style={{
                                              backgroundColor: '#f4f4f4',
                                              padding: '2px 6px',
                                              borderRadius: '3px',
                                              fontFamily: 'monospace',
                                              fontSize: '0.9em'
                                            }}>
                                              {children}
                                            </code>
                                          ) : (
                                            <pre style={{
                                              backgroundColor: '#f4f4f4',
                                              padding: '12px',
                                              borderRadius: '6px',
                                              overflow: 'auto',
                                              fontFamily: 'monospace',
                                              fontSize: '0.9em'
                                            }}>
                                              <code className={className}>
                                                {children}
                                              </code>
                                            </pre>
                                          );
                                        },
                                        // Style links
                                        a: ({ children, href }: any) => (
                                          <a href={href} style={{ color: '#0972d3' }} target="_blank" rel="noopener noreferrer">
                                            {children}
                                          </a>
                                        ),
                                        // Style lists
                                        ul: ({ children }: any) => (
                                          <ul style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '8px' }}>
                                            {children}
                                          </ul>
                                        ),
                                        ol: ({ children }: any) => (
                                          <ol style={{ marginLeft: '20px', marginTop: '8px', marginBottom: '8px' }}>
                                            {children}
                                          </ol>
                                        ),
                                        // Style paragraphs
                                        p: ({ children }: any) => (
                                          <p style={{ marginTop: '8px', marginBottom: '8px' }}>
                                            {children}
                                          </p>
                                        ),
                                      }}
                                    >
                                      {message.content}
                                    </ReactMarkdown>
                                  </ChatBubble>

                                  {isAgent && (
                                    <div style={{ marginTop: '8px' }}>
                                      <ButtonGroup
                                        variant="icon"
                                        ariaLabel="Message actions"
                                        items={[
                                          {
                                            type: 'icon-button',
                                            id: 'thumbs-up',
                                            iconName: feedback?.feedback === 'helpful' ? 'thumbs-up-filled' : 'thumbs-up',
                                            text: 'Helpful',
                                            disabled: feedback?.submitting || !!feedback?.feedback,
                                            loading: feedback?.submitting && feedback?.feedback !== 'not-helpful',
                                            disabledReason: feedback?.feedback === 'helpful'
                                              ? '"Helpful" feedback has been submitted.'
                                              : feedback?.feedback === 'not-helpful'
                                                ? '"Helpful" option is unavailable after "not helpful" feedback submitted.'
                                                : undefined,
                                          },
                                          {
                                            type: 'icon-button',
                                            id: 'thumbs-down',
                                            iconName: feedback?.feedback === 'not-helpful' ? 'thumbs-down-filled' : 'thumbs-down',
                                            text: 'Not helpful',
                                            disabled: feedback?.submitting || !!feedback?.feedback,
                                            loading: feedback?.submitting && feedback?.feedback !== 'helpful',
                                            disabledReason: feedback?.feedback === 'not-helpful'
                                              ? '"Not helpful" feedback has been submitted.'
                                              : feedback?.feedback === 'helpful'
                                                ? '"Not helpful" option is unavailable after "helpful" feedback submitted.'
                                                : undefined,
                                          },
                                          {
                                            type: 'icon-button',
                                            id: 'copy',
                                            iconName: 'copy',
                                            text: 'Copy',
                                            popoverFeedback: feedback?.showCopySuccess ? (
                                              <StatusIndicator type="success">
                                                Copied
                                              </StatusIndicator>
                                            ) : undefined,
                                          }
                                        ]}
                                        onItemClick={({ detail }) => {
                                          if (detail.id === 'thumbs-up') {
                                            handleFeedback(index, 'helpful');
                                          } else if (detail.id === 'thumbs-down') {
                                            handleFeedback(index, 'not-helpful');
                                          } else if (detail.id === 'copy') {
                                            handleCopy(index, message.content);
                                          }
                                        }}
                                      />
                                      {feedback?.feedback && (
                                        <Box margin={{ top: 'xs' }} color="text-status-info" fontSize="body-s">
                                          Feedback submitted
                                        </Box>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </div>
                            );
                          })}
                          {loading && (
                            <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-start' }}>
                              <Avatar
                                ariaLabel="Generative AI assistant"
                                tooltipText="Generative AI assistant"
                                iconName="gen-ai"
                                color="gen-ai"
                                loading={true}
                              />
                              <Box color="text-body-secondary">
                                Generating a response
                              </Box>
                            </div>
                          )}
                        </div>
                      )}

                      {showSupportPrompts && !loading && (
                        <>
                          {loadingPrompts ? (
                            <Box textAlign="center" padding="s" color="text-body-secondary">
                              <StatusIndicator type="loading">Generating suggestions...</StatusIndicator>
                            </Box>
                          ) : (
                            <SupportPromptGroup
                              onItemClick={({ detail }) => handleSupportPromptClick(
                                getSupportPrompts().find(p => p.id === detail.id)?.text || ''
                              )}
                              ariaLabel="Suggested prompts"
                              alignment="horizontal"
                              items={getSupportPrompts()}
                            />
                          )}
                        </>
                      )}

                      <PromptInput
                        value={prompt}
                        onChange={({ detail }) => setPrompt(detail.value)}
                        onAction={handleSendMessage}
                        placeholder="Ask a question..."
                        actionButtonAriaLabel="Send message"
                        actionButtonIconName="send"
                        disabled={loading}
                      />
                    </SpaceBetween>
                  </div>
                </Container>
              </SpaceBetween>
              <div />
            </Grid>
          </ContentLayout>
        }
      />
    </>
  );
}

export default App;

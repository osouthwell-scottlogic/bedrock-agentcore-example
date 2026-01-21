import { useState, useEffect } from 'react';
import { ErrorBanner } from './components/ErrorBanner';
import { Header } from './components/Header';
import { ChatContainer } from './components/chat/ChatContainer';
import { PromptSuggestions } from './components/chat/PromptSuggestions';
import { ChatInput } from './components/chat/ChatInput';
import { useAuth } from './hooks/useAuth';
import { useChatMessages } from './hooks/useChatMessages';
import { useDynamicPrompts } from './hooks/useDynamicPrompts';
import './styles/theme.css';
import './markdown.css';
import styles from './App.module.css';

function App() {
  const isLocalDev = (import.meta as any).env.VITE_LOCAL_DEV === 'true';
  
  // Custom hooks
  const auth = useAuth(isLocalDev);
  const chat = useChatMessages();
  const prompts = useDynamicPrompts(isLocalDev, auth.user);
  
  // UI state
  const [showSupportPrompts, setShowSupportPrompts] = useState(true);
  const [AuthModalComponent, setAuthModalComponent] = useState<any>(null);

  // Initialize prompts on auth
  useEffect(() => {
    if (auth.user && !auth.checkingAuth) {
      prompts.generateInitialPrompts();
    }
  }, [auth.user, auth.checkingAuth]);

  // Load AuthModal component lazily
  useEffect(() => {
    if (!isLocalDev && auth.showAuthModal && !AuthModalComponent) {
      import('./AuthModal').then(module => {
        setAuthModalComponent(() => module.default);
      });
    }
  }, [auth.showAuthModal, AuthModalComponent, isLocalDev]);

  const handleSupportPromptClick = (promptText: string) => {
    chat.setPrompt(promptText);
    setShowSupportPrompts(false);
    prompts.clearDynamicPrompts();
  };

  const handleSendMessage = async () => {
    setShowSupportPrompts(false);
    
    await chat.handleSendMessage(
      auth.user,
      isLocalDev,
      () => auth.setShowAuthModal(true),
      (messages) => {
        setShowSupportPrompts(true);
        prompts.generateDynamicPrompts(messages);
      }
    );
  };

  const handleSignOutWithReset = async () => {
    await auth.handleSignOut();
    chat.resetMessages();
  };

  const getSupportPrompts = () => {
    if (prompts.dynamicPrompts.length > 0) {
      return prompts.dynamicPrompts;
    }

    if (chat.messages.length === 0) {
      return [
        { id: 'show-bonds', text: 'Show all available bond products' },
        { id: 'email-gov-bond', text: 'Email customers about Government Bond Y' },
        { id: 'email-corp-bond', text: 'Email customers about Corporate Bond A' },
        { id: 'recent-emails', text: 'Show recently sent emails' }
      ];
    }

    return [
      { id: 'show-bonds-default', text: 'Show all bond products' },
      { id: 'email-default', text: 'Email customers about a bond' },
      { id: 'recent-default', text: 'Show recently sent emails' }
    ];
  };

  if (auth.checkingAuth) {
    return (
      <div className={styles.appContainer}>
        <Header
          isLocalDev={isLocalDev}
          user={auth.user}
          onSignOut={handleSignOutWithReset}
          onSignIn={() => auth.setShowAuthModal(true)}
        />
        <div className={styles.loadingContainer}>
          Loading...
        </div>
      </div>
    );
  }

  return (
    <div className={styles.appContainer}>
      {!isLocalDev && AuthModalComponent && (
        <AuthModalComponent
          visible={auth.showAuthModal}
          onDismiss={() => auth.setShowAuthModal(false)}
          onSuccess={auth.handleAuthSuccess}
        />
      )}
      
      <Header
        isLocalDev={isLocalDev}
        user={auth.user}
        onSignOut={handleSignOutWithReset}
        onSignIn={() => auth.setShowAuthModal(true)}
      />
      
      <main className={styles.mainContent}>
        <div className={styles.chatColumn}>
          {chat.error && (
            <ErrorBanner
              error={chat.error}
              onDismiss={() => chat.setError(null)}
              header="Agent invocation error"
            />
          )}

          <div className={styles.chatContainer}>
            <ChatContainer
              messages={chat.messages}
              loading={chat.loading}
              footerChildren={
                <PromptSuggestions
                  prompts={getSupportPrompts()}
                  loading={prompts.loadingPrompts}
                  visible={showSupportPrompts && !chat.loading}
                  onPromptClick={handleSupportPromptClick}
                />
              }
            />

            <div className={styles.chatFooter}>
              <ChatInput
                value={chat.prompt}
                onChange={chat.setPrompt}
                onSend={handleSendMessage}
                disabled={chat.loading}
              />
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;

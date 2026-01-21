import { useState, useEffect } from 'react';

interface AuthUser {
  email: string;
}

export interface UseAuthReturn {
  user: AuthUser | null;
  checkingAuth: boolean;
  showAuthModal: boolean;
  setShowAuthModal: (show: boolean) => void;
  checkAuth: () => Promise<void>;
  handleSignOut: () => Promise<void>;
  handleAuthSuccess: () => Promise<void>;
}

export function useAuth(isLocalDev: boolean): UseAuthReturn {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);
  const [showAuthModal, setShowAuthModal] = useState(false);

  const checkAuth = async () => {
    if (isLocalDev) return;

    try {
      const { getCurrentUser } = await import('../auth');
      const currentUser = await getCurrentUser();
      setUser(currentUser);
    } catch (err) {
      setUser(null);
    } finally {
      setCheckingAuth(false);
    }
  };

  const handleSignOut = async () => {
    if (isLocalDev) return;

    try {
      const { signOut } = await import('../auth');
      signOut();
    } catch (err) {
      console.error('Error signing out:', err);
    }
    setUser(null);
  };

  const handleAuthSuccess = async () => {
    setShowAuthModal(false);
    await checkAuth();
  };

  useEffect(() => {
    if (isLocalDev) {
      setCheckingAuth(false);
      setUser({ email: 'local-dev@example.com' } as AuthUser);
    } else {
      checkAuth();
    }
  }, [isLocalDev]);

  return {
    user,
    checkingAuth,
    showAuthModal,
    setShowAuthModal,
    checkAuth,
    handleSignOut,
    handleAuthSuccess,
  };
}

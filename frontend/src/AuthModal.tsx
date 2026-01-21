import { useState } from 'react';
import { Modal } from './components/ui/Modal';
import { Alert } from './components/ui/Alert';
import { Button } from './components/ui/Button';
import { Input } from './components/ui/Input';
import { ErrorBanner, UiError } from './components/ErrorBanner';
import { signUp, signIn, confirmSignUp } from './auth';
import styles from './AuthModal.module.css';

interface AuthModalProps {
  visible: boolean;
  onDismiss: () => void;
  onSuccess: () => void;
}

type AuthMode = 'signin' | 'signup' | 'confirm';

export default function AuthModal({ visible, onDismiss, onSuccess }: AuthModalProps) {
  const [mode, setMode] = useState<AuthMode>('signin');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmCode, setConfirmCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<UiError | null>(null);

  const handleSignIn = async () => {
    if (!email || !password) {
      setError({ message: 'Email and password are required' });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await signIn(email, password);
      onSuccess();
      resetForm();
    } catch (err: any) {
      setError({ message: err.message || 'Failed to sign in' });
    } finally {
      setLoading(false);
    }
  };

  const handleSignUp = async () => {
    if (!email || !password) {
      setError({ message: 'Email and password are required' });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await signUp(email, password);
      setMode('confirm');
      setError(null);
    } catch (err: any) {
      setError({ message: err.message || 'Failed to sign up' });
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async () => {
    if (!confirmCode) {
      setError({ message: 'Verification code is required' });
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await confirmSignUp(email, confirmCode);
      await signIn(email, password);
      onSuccess();
      resetForm();
    } catch (err: any) {
      setError({ message: err.message || 'Failed to confirm account' });
    } finally {
      setLoading(false);
    }
  };

  const resetForm = () => {
    setEmail('');
    setPassword('');
    setConfirmCode('');
    setMode('signin');
    setError(null);
  };

  const handleDismiss = () => {
    resetForm();
    onDismiss();
  };

  return (
    <Modal
      visible={visible}
      onDismiss={handleDismiss}
      header={mode === 'signin' ? 'Sign In' : mode === 'signup' ? 'Sign Up' : 'Confirm Account'}
      footer={
        <div className={styles.footer}>
          <Button variant="link" onClick={handleDismiss}>
            Cancel
          </Button>
          <Button
            variant="primary"
            onClick={mode === 'signin' ? handleSignIn : mode === 'signup' ? handleSignUp : handleConfirm}
            disabled={loading}
          >
            {mode === 'signin' ? 'Sign In' : mode === 'signup' ? 'Sign Up' : 'Confirm'}
          </Button>
        </div>
      }
    >
      <div className={styles.content}>
        <ErrorBanner error={error} onDismiss={() => setError(null)} />

        {mode === 'confirm' ? (
          <>
            <Alert type="info">
              A verification code has been sent to {email}. Please enter it below.
            </Alert>
            <div className={styles.field}>
              <label className={styles.label}>Verification Code</label>
              <Input
                value={confirmCode}
                onChange={setConfirmCode}
                placeholder="Enter 6-digit code"
                required
              />
            </div>
          </>
        ) : (
          <>
            <div className={styles.field}>
              <label className={styles.label}>Email</label>
              <Input
                value={email}
                onChange={setEmail}
                type="email"
                placeholder="your@email.com"
                required
              />
            </div>

            <div className={styles.field}>
              <label className={styles.label}>Password</label>
              <Input
                value={password}
                onChange={setPassword}
                type="password"
                placeholder="Enter password"
                required
              />
            </div>

            <div className={styles.switchMode}>
              {mode === 'signin' ? (
                <>
                  Don't have an account?{' '}
                  <Button variant="link" onClick={() => setMode('signup')}>
                    Sign up
                  </Button>
                </>
              ) : (
                <>
                  Already have an account?{' '}
                  <Button variant="link" onClick={() => setMode('signin')}>
                    Sign in
                  </Button>
                </>
              )}
            </div>
          </>
        )}
      </div>
    </Modal>
  );
}

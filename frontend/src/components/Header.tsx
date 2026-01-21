import { Button } from './ui/Button';
import styles from './Header.module.css';

export interface HeaderProps {
  isLocalDev: boolean;
  user?: { email: string } | null;
  onSignOut: () => void;
  onSignIn: () => void;
}

export function Header({ isLocalDev, user, onSignOut, onSignIn }: HeaderProps) {
  return (
    <header className={styles.header}>
      <div className={styles.container}>
        <h1 className={styles.logo}>
          {isLocalDev ? 'Bank X Financial Assistant (Local Dev)' : 'Bank X Financial Assistant'}
        </h1>
        <div className={styles.actions}>
          {isLocalDev ? (
            <div className={styles.badge}>Local Development</div>
          ) : (
            <Button
              onClick={user ? onSignOut : onSignIn}
              variant="secondary"
            >
              {user ? `${user.email} | Sign Out` : 'Sign In'}
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}

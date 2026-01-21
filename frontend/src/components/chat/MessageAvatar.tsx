import { UserIcon } from '../icons/User';
import { BotIcon } from '../icons/Bot';
import styles from './MessageAvatar.module.css';

export interface MessageAvatarProps {
  type: 'user' | 'agent';
}

export function MessageAvatar({ type }: MessageAvatarProps) {
  return (
    <div 
      className={`${styles.avatar} ${type === 'user' ? styles.user : styles.agent}`}
      aria-label={type === 'user' ? 'User avatar' : 'Agent avatar'}
      title={type === 'user' ? 'You' : 'Bank X Assistant'}
    >
      {type === 'user' ? <UserIcon size={20} /> : <BotIcon size={20} />}
    </div>
  );
}

/**
 * TopNavigation component extracted from App.tsx
 * Handles both loading state and authenticated state navigation
 */

import TopNavigation from '@cloudscape-design/components/top-navigation';

export interface NavigationProps {
  isLocalDev: boolean;
  isLoading?: boolean;
  user?: { email: string } | null;
  onSignOut: () => void;
  onSignIn: () => void;
}

export function Navigation({
  isLocalDev,
  isLoading = false,
  user = null,
  onSignOut,
  onSignIn,
}: NavigationProps) {
  return (
    <TopNavigation
      identity={{
        href: "#",
        title: isLoading || isLocalDev
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
              onSignOut();
            } else {
              onSignIn();
            }
          }
        }
      ]}
      i18nStrings={{
        overflowMenuTriggerText: "More",
        overflowMenuTitleText: "All"
      }}
    />
  );
}

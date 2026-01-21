/**
 * Reusable component styles built with design tokens
 */

import {
  colors,
  spacing,
  typography,
  animations,
  transitions,
  borderRadius,
  shadows,
  gradients,
  glass,
} from "./tokens";

export const chatContainerStyles = {
  // Outer wrapper for the entire chat area with header
  outerWrapper: {
    display: "flex" as const,
    flexDirection: "column" as const,
    flex: 1,
    width: "100%" as const,
    overflow: "hidden" as const,
    minHeight: 0,
    position: "relative" as const,
  },
  // Empty state wrapper (used when no messages)
  wrapper: {
    display: "flex" as const,
    flexDirection: "column" as const,
    flex: 1,
    width: "100%" as const,
    overflow: "hidden" as const,
    minHeight: 0,
  },
  contentWrapper: {
    display: "flex" as const,
    flexDirection: "column" as const,
    width: "100%" as const,
    minHeight: "100%" as const,
  },
  emptyState: {
    display: "flex" as const,
    alignItems: "center" as const,
    justifyContent: "center" as const,
    flex: 1,
    paddingTop: spacing.l,
  },
  emptyStateContent: {
    textAlign: "center" as const,
    position: "relative" as const,
    padding: `${spacing.xl} ${spacing.l}`,
    width: "100%",
  },
  emptyStateTitle: {
    position: "relative" as const,
    zIndex: 1,
    ...typography.headingLarge,
    color: colors.textDark,
    marginBottom: spacing.l,
    animation: animations.fadeInUpSlow,
  },
  emptyStateSubtitle: {
    position: "relative" as const,
    zIndex: 1,
    ...typography.bodyLarge,
    color: colors.textLight,
    animation: animations.fadeInUpVerySlow,
    padding: `0 ${spacing.m}`,
  },
  // Fixed header that stays at top
  headerWithMessages: {
    textAlign: "center" as const,
    position: "relative" as const,
    padding: `${spacing.m} ${spacing.l}`,
    width: "100%",
    flexShrink: 0,
    borderBottom: `1px solid rgba(0, 0, 0, 0.05)`,
  },
  headerTitleWithMessages: {
    position: "relative" as const,
    zIndex: 1,
    ...typography.headingLarge,
    color: colors.textDark,
    marginBottom: 0,
  },
  // Scrollable container for messages
  messagesScrollContainer: {
    flex: 1,
    flexGrow: 1,
    overflowX: "hidden" as const,
    overflowY: "auto" as const,
    minHeight: 0,
    maxHeight: "100%",
  },
  messagesWrapper: {
    scrollBehavior: "smooth" as const,
    display: "flex" as const,
    flexDirection: "column" as const,
    gap: spacing.m,
    width: "100%" as const,
    padding: `${spacing.xl} 0 0 0`,
  },
  loadingIndicator: {
    display: "flex" as const,
    justifyContent: "center" as const,
    padding: spacing.l,
    animation: animations.fadeInUp,
  },
  loadingText: {
    color: colors.textDark,
    fontWeight: 500,
  },
};

// Overlay area anchored at the bottom of the chat container
export const chatFooterOverlayStyles = {
  wrapper: {
    position: "sticky" as const,
    bottom: 0,
    zIndex: 1,
    backgroundColor: "transparent",
    pointerEvents: "auto" as const,
    padding: `${spacing.xs} ${spacing.m}`,
    width: "100%",
  },
};

export const chatMessageStyles = {
  wrapper: {
    display: "flex" as const,
    gap: spacing.m,
    marginBottom: spacing.m,
    alignItems: "flex-start" as const,
    padding: `0 ${spacing.m}`,
  },
  wrapperUser: {
    justifyContent: "flex-end" as const,
  },
  wrapperAgent: {
    justifyContent: "flex-start" as const,
  },
  wrapperLast: {
    marginBottom: 0,
  },
  contentWrapper: {
    flex: 1,
    maxWidth: "70%",
    minWidth: 0,
    display: "flex" as const,
    flexDirection: "column" as const,
  },
  contentWrapperUser: {
    alignItems: "flex-end" as const,
  },
  contentWrapperAgent: {
    alignItems: "flex-start" as const,
  },
  avatarWrapper: {
    flexShrink: 0,
    width: "40px",
  },
};

export const messageBubbleStyles = {
  userBubble: {
    padding: spacing.m,
    borderRadius: borderRadius.lg,
    background: "#01cdfe",
    color: colors.textDark,
    fontSize: "0.95rem",
    lineHeight: 1.45,
    wordWrap: "break-word" as const,
    overflowWrap: "break-word" as const,
    // Shadow tinted to match the cyan bubble
    boxShadow: "0 4px 16px rgba(1, 205, 254, 0.35)",
    transition: transitions.normal,
    maxWidth: "100%",
    animation: animations.fadeInUp,
  },
  agentBubbleWrapper: {
    animation: animations.fadeInUp,
  },
  agentBubble: {
    padding: spacing.s,
    borderRadius: borderRadius.lg,
    backgroundColor: "#f5f5f5",
    color: colors.textDark,
    wordWrap: "break-word" as const,
    overflowWrap: "break-word" as const,
    fontSize: "0.95rem",
    lineHeight: 1.45,
  },
};

export const promptSuggestionsStyles = {
  wrapper: {
    display: "flex" as const,
    flexDirection: "column" as const,
    gap: spacing.xs,
    padding: `${spacing.s} 0`,
    animation: animations.fadeInUp,
    width: "100%",
    maxWidth: "1200px",
    alignSelf: "center" as const,
    backgroundColor: "transparent",
  },
  loadingWrapper: {
    display: "flex" as const,
    justifyContent: "center" as const,
    padding: spacing.m,
  },
  grid: {
    display: "grid" as const,
    gridTemplateColumns: "repeat(auto-fit, minmax(160px, 1fr))" as const,
    gap: spacing.xs,
    padding: `0 ${spacing.s}`,
    width: "100%",
  },
  buttonBase: {
    padding: `${spacing.xs} ${spacing.s}`,
    borderRadius: borderRadius.sm,
    border: `1px solid ${colors.border}`,
    backgroundColor: colors.whiteGlass,
    cursor: "pointer" as const,
    transition: `all ${transitions.fast}`,
    textAlign: "left" as const,
    fontSize: "0.9rem",
    fontWeight: 500,
    color: colors.textDark,
    lineHeight: "1.4",
    maxWidth: "none",
    backdropFilter: `blur(${glass.solid.blur})`,
    WebkitBackdropFilter: `blur(${glass.solid.blur})`,
    "&:hover": {
      backgroundColor: colors.backgroundHover,
      borderColor: colors.borderHover,
      transform: "translateY(-2px)",
      boxShadow: shadows.medium,
    },
  },
};

export const chatInputStyles = {
  wrapper: {
    padding: spacing.m,
    background: colors.whiteGlass,
    borderRadius: borderRadius.xl,
    backdropFilter: `blur(${glass.solid.blur})`,
    WebkitBackdropFilter: `blur(${glass.solid.blur})`,
    boxShadow: `0 -4px 16px rgba(0, 0, 0, 0.1)`,
    transition: `all ${transitions.normal}`,
  },
};

export const messageAvatarStyles = {
  wrapper: {
    flexShrink: 0,
    transition: `transform ${transitions.fast}`,
  },
};

export const markdownStyles = {
  wrapper: {
    wordWrap: "break-word" as const,
    overflowWrap: "break-word" as const,
  },
  wrapperUser: {
    color: colors.textDark,
  },
  inlineCodeUser: {
    background: colors.codeUserBg,
    color: colors.textDark,
    padding: "2px 6px",
    borderRadius: borderRadius.sm,
    fontFamily: "Monaco, Menlo, Ubuntu Mono, monospace",
    fontSize: "0.9em",
    border: "none",
  },
  inlineCodeAgent: {
    background: colors.codeAgentBg,
    padding: "2px 6px",
    borderRadius: borderRadius.sm,
    fontFamily: "Monaco, Menlo, Ubuntu Mono, monospace",
    fontSize: "0.9em",
    border: `1px solid ${colors.codeAgentBorder}`,
  },
  blockCode: {
    background: colors.codeAgentBg,
    padding: spacing.s,
    borderRadius: borderRadius.md,
    fontFamily: "Monaco, Menlo, Ubuntu Mono, monospace",
    fontSize: "0.9em",
    overflowX: "auto" as const,
    border: `1px solid ${colors.codeAgentBorder}`,
    margin: `${spacing.s} 0`,
  },
  blockCodeUser: {
    background: colors.codeUserBg,
    padding: spacing.s,
    borderRadius: borderRadius.md,
    fontFamily: "Monaco, Menlo, Ubuntu Mono, monospace",
    fontSize: "0.9em",
    overflowX: "auto" as const,
    border: "none",
    margin: `${spacing.s} 0`,
  },
  link: {
    color: colors.cyan,
    textDecoration: "none" as const,
    transition: `color ${transitions.fast}`,
    borderBottom: "1px solid transparent",
    "&:hover": {
      borderBottomColor: colors.cyan,
    },
  },
  list: {
    margin: `${spacing.s} 0`,
    paddingLeft: spacing.l,
  },
  paragraph: {
    margin: `${spacing.s} 0`,
    lineHeight: 1.45,
  },
};

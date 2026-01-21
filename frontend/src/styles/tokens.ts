/**
 * Design tokens for consistent styling across the app
 */

export const colors = {
  // Primary colors
  primary: '#01cdfe',
  dark: '#2c3e50',
  
  // Vaporwave accent colors
  purple: '#b967ff',
  pink: '#ff71ce',
  cyan: '#01cdfe',
  
  // Text colors
  textDark: '#2c3e50',
  textLight: '#cccccc',
  textMuted: '#999999',
  
  // UI colors
  background: '#ffffff',
  backgroundHover: '#f0f0f0',
  border: '#e0e0e0',
  borderHover: '#01cdfe',
  success: '#01cdfe',
  
  // Glass effect colors
  whiteGlass: 'rgba(255, 255, 255, 0.95)',
  whiteSemi: 'rgba(255, 255, 255, 0.9)',
  whiteLight: 'rgba(255, 255, 255, 0.25)',
  
  // Code block backgrounds
  codeUserBg: 'rgba(255, 255, 255, 0.25)',
  codeAgentBg: 'rgba(1, 205, 254, 0.1)',
  codeAgentBorder: 'rgba(1, 205, 254, 0.3)',
};

export const spacing = {
  xs: '4px',
  s: '8px',
  m: '16px',
  l: '24px',
  xl: '32px',
  xxl: '48px',
};

export const typography = {
  headingLarge: {
    fontSize: '2.5rem',
    fontWeight: 600,
    lineHeight: '1.3',
  },
  headingMedium: {
    fontSize: '1.5rem',
    fontWeight: 600,
    lineHeight: '1.4',
  },
  bodyLarge: {
    fontSize: '1.2rem',
    fontWeight: 500,
    lineHeight: '1.6',
  },
  bodyRegular: {
    fontSize: '1rem',
    fontWeight: 400,
    lineHeight: '1.5',
  },
  small: {
    fontSize: '0.875rem',
    fontWeight: 400,
    lineHeight: '1.4',
  },
};

export const animations = {
  fadeInUp: 'fadeInUp 0.4s ease-out',
  fadeInUpSlow: 'fadeInUp 0.6s ease-out',
  fadeInUpVerySlow: 'fadeInUp 0.8s ease-out',
  fadeIn: 'fadeIn 0.3s ease-in-out',
};

export const transitions = {
  fast: '0.15s ease-in-out',
  normal: '0.3s ease-in-out',
  slow: '0.5s ease-out',
};

export const borderRadius = {
  sm: '4px',
  md: '8px',
  lg: '12px',
  xl: '16px',
};

export const shadows = {
  subtle: '0 2px 8px rgba(0, 0, 0, 0.08)',
  medium: '0 4px 16px rgba(0, 0, 0, 0.1)',
  glow: '0 4px 16px rgba(185, 103, 255, 0.4)',
  card: '0 8px 24px rgba(0, 0, 0, 0.12)',
};

export const glass = {
  solid: {
    opacity: 0.95,
    blur: '10px',
  },
  semi: {
    opacity: 0.9,
    blur: '20px',
  },
  light: {
    opacity: 0.8,
    blur: '30px',
  },
};

export const gradients = {
  primary: 'linear-gradient(135deg, #d99ff7 0%, #ff99e0 100%)',
  message: 'linear-gradient(135deg, #01cdfe 0%, #b967ff 100%)',
  accent: 'linear-gradient(135deg, #ff71ce 0%, #01cdfe 100%)',
};

export const zIndex = {
  base: 1,
  content: 10,
  overlay: 100,
  modal: 1000,
};

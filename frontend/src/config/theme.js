/**
 * Theme Configuration
 * Color palette for Dark Mode and Light Mode
 */

export const themeColors = {
  dark: {
    background: {
      primary: '#0F1419', // deep charcoal
      secondary: '#1A1F2E', // chat container
      tertiary: '#16181D', // sidebar
    },
    text: {
      primary: '#F3F4F6',
      secondary: '#9CA3AF',
      disabled: '#6B7280',
    },
    accent: {
      primary: '#8B5CF6', // vibrant purple
      secondary: '#3B82F6', // electric blue
      success: '#10B981',
      error: '#EF4444',
      warning: '#F59E0B',
    },
    interactive: {
      botBubble: '#2D3748', // with subtle gradient
      userBubble: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
      inputBg: '#1A1F2E',
      inputBorder: '#374151',
      hover: '#374151',
    },
    gradients: {
      hero: 'linear-gradient(135deg, #667EEA 0%, #764BA2 100%)',
      button: 'linear-gradient(135deg, #8B5CF6 0%, #3B82F6 100%)',
      glow: 'rgba(139, 92, 246, 0.3)',
    },
  },
  light: {
    background: {
      primary: '#F8FAFC',
      secondary: '#FFFFFF', // chat container
      tertiary: '#F1F5F9', // sidebar
    },
    text: {
      primary: '#0F172A',
      secondary: '#64748B',
      disabled: '#CBD5E1',
    },
    accent: {
      primary: '#6366F1',
      secondary: '#3B82F6',
      success: '#10B981',
      error: '#EF4444',
      warning: '#F59E0B',
    },
    interactive: {
      botBubble: '#F1F5F9',
      userBubble: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
      inputBg: '#FFFFFF',
      inputBorder: '#E2E8F0',
      hover: '#F1F5F9',
    },
    gradients: {
      hero: 'linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)',
      button: 'linear-gradient(135deg, #6366F1 0%, #3B82F6 100%)',
      glow: 'rgba(99, 102, 241, 0.2)',
    },
  },
}

/**
 * Get theme colors based on current mode
 */
export const getThemeColors = (isDark) => {
  return isDark ? themeColors.dark : themeColors.light
}

/**
 * CSS Variables for dynamic theming
 */
export const generateThemeCSS = (isDark) => {
  const colors = getThemeColors(isDark)
  
  return {
    '--bg-primary': colors.background.primary,
    '--bg-secondary': colors.background.secondary,
    '--bg-tertiary': colors.background.tertiary,
    '--text-primary': colors.text.primary,
    '--text-secondary': colors.text.secondary,
    '--text-disabled': colors.text.disabled,
    '--accent-primary': colors.accent.primary,
    '--accent-secondary': colors.accent.secondary,
    '--accent-success': colors.accent.success,
    '--accent-error': colors.accent.error,
    '--accent-warning': colors.accent.warning,
    '--bot-bubble': colors.interactive.botBubble,
    '--user-bubble': colors.interactive.userBubble,
    '--input-bg': colors.interactive.inputBg,
    '--input-border': colors.interactive.inputBorder,
    '--hover': colors.interactive.hover,
    '--gradient-hero': colors.gradients.hero,
    '--gradient-button': colors.gradients.button,
    '--glow-effect': colors.gradients.glow,
  }
}


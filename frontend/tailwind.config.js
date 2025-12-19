/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // Light Mode Colors
        primary: {
          DEFAULT: '#2563EB', // Light mode primary accent
          50: '#EFF6FF',
          100: '#DBEAFE',
          200: '#BFDBFE',
          300: '#93C5FD',
          400: '#60A5FA',
          500: '#3B82F6',
          600: '#2563EB',
          700: '#1D4ED8',
          800: '#1E40AF',
          900: '#1E3A8A',
        },
        // Dark Mode Colors (will be applied via CSS variables)
        'theme-bg': {
          primary: 'var(--bg-primary)',
          secondary: 'var(--bg-secondary)',
          tertiary: 'var(--bg-tertiary)',
        },
        'theme-text': {
          primary: 'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          disabled: 'var(--text-disabled)',
        },
        'theme-accent': {
          primary: 'var(--accent-primary)',
          secondary: 'var(--accent-secondary)',
          success: 'var(--accent-success)',
          error: 'var(--accent-error)',
          warning: 'var(--accent-warning)',
        },
        'theme-interactive': {
          botBubble: 'var(--bot-bubble)',
          userBubble: 'var(--user-bubble)',
          inputBg: 'var(--input-bg)',
          inputBorder: 'var(--input-border)',
          hover: 'var(--hover)',
        },
      },
      backgroundImage: {
        'gradient-hero': 'var(--gradient-hero)',
        'gradient-button': 'var(--gradient-button)',
      },
    },
  },
  plugins: [],
}


import type { Config } from 'tailwindcss'

const config: Config = {
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary Colors
        'primary-brand': '#2D3748',
        'primary-accent': '#4299E1',
        'primary-success': '#48BB78',
        'primary-warning': '#ED8936',
        'primary-error': '#F56565',
        
        // Neutral Colors
        'neutral-50': '#F7FAFC',
        'neutral-100': '#EDF2F7',
        'neutral-200': '#E2E8F0',
        'neutral-300': '#CBD5E0',
        'neutral-400': '#A0AEC0',
        'neutral-500': '#718096',
        'neutral-600': '#4A5568',
        'neutral-700': '#2D3748',
        'neutral-800': '#1A202C',
        'neutral-900': '#171923',
        
        // Chat Specific
        'user-message-bg': '#4299E1',
        'user-message-text': '#FFFFFF',
        'assistant-message-bg': '#F7FAFC',
        'assistant-message-text': '#2D3748',
        'reasoning-bg': '#EDF2F7',
        'reasoning-border': '#E2E8F0',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Menlo', 'Monaco', 'monospace'],
      },
      spacing: {
        '18': '4.5rem',
        '88': '22rem',
      },
      animation: {
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
}

export default config
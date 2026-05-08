/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        foundry: {
          bg: '#ffffff',
          'bg-secondary': '#ffffff',
          card: '#ffffff',
          border: '#e5e7eb',
          text: '#111827',
          'text-dim': '#6b7280',
          accent: '#2563eb',
          green: '#16a34a',
          amber: '#d97706',
          red: '#dc2626',
          purple: '#7c3aed',
        },
        geist: {
          bg: '#ffffff',
          'bg-subtle': '#fafafa',
          'bg-muted': '#f5f5f5',
          border: '#ededed',
          'border-strong': '#e5e5e5',
          fg: '#0a0a0a',
          'fg-muted': '#525252',
          'fg-subtle': '#8a8a8a',
          accent: '#2563eb',
          'accent-soft': '#eff6ff',
          success: '#10b981',
          warning: '#f59e0b',
          danger: '#ef4444',
          violet: '#8b5cf6',
        },
      },
      fontFamily: {
        sans: ['Inter', 'ui-sans-serif', 'system-ui', '-apple-system', 'Segoe UI', 'Roboto', 'Helvetica Neue', 'Arial', 'sans-serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};

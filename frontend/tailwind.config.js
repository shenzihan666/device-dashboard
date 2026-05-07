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
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};

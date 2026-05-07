/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {
      colors: {
        foundry: {
          bg: '#0d1117',
          'bg-secondary': '#11161e',
          card: '#161b22',
          border: '#1d242e',
          text: '#e6edf3',
          'text-dim': '#7d8590',
          accent: '#00d4ff',
          green: '#3fb950',
          amber: '#d29922',
          red: '#f85149',
          purple: '#7c5cff',
        },
      },
      fontFamily: {
        mono: ['ui-monospace', 'SFMono-Regular', 'SF Mono', 'Menlo', 'Consolas', 'monospace'],
      },
    },
  },
  plugins: [],
};

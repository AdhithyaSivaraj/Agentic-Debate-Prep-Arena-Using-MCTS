/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Background layers
        bg: {
          0: "var(--bg-0)",
          1: "var(--bg-1)",
          2: "var(--bg-2)",
        },
        // Text
        ink: {
          DEFAULT: "var(--ink)",
          muted: "var(--ink-muted)",
          faint: "var(--ink-faint)",
        },
        // Agent A (violet/blue default)
        agentA: {
          primary: "var(--a-primary)",
          dim:     "var(--a-dim)",
          border:  "var(--a-border)",
        },
        // Agent B (amber/gold default)
        agentB: {
          primary: "var(--b-primary)",
          dim:     "var(--b-dim)",
          border:  "var(--b-border)",
        },
        // Status
        contra: "var(--contra)",
        ok:     "var(--ok)",
        // Arena aliases (for old code compatibility)
        arena: {
          bg:      "var(--bg-0)",
          surface: "var(--bg-1)",
          text:    "var(--ink-muted)",
          muted:   "var(--ink-faint)",
          border:  "var(--border)",
        },
      },
      fontFamily: {
        serif: ['Fraunces', 'Georgia', 'serif'],
        sans:  ['Inter', 'DM Sans', '-apple-system', 'sans-serif'],
        mono:  ['JetBrains Mono', 'Fira Code', 'Consolas', 'monospace'],
      },
      fontSize: {
        display: ['clamp(46px,8.5vw,104px)', { lineHeight: '0.95', letterSpacing: '-0.02em' }],
        case:    ['clamp(18px,2.5vw,26px)',   { lineHeight: '1.25' }],
      },
      backdropBlur: {
        arena: '16px',
      },
      animation: {
        shimmer: 'shimmer 1.5s linear infinite',
        livePulse: 'livePulse 1.8s ease-in-out infinite',
      },
    },
  },
  plugins: [],
};

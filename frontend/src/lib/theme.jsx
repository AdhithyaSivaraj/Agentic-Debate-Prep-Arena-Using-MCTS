import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { flushSync } from 'react-dom';

// Swatch colours are fixed per theme so the switcher previews each one, whatever is active.
export const THEMES = [
  { id: 'brief',    label: 'Brief',    swatch: { bg: '#f2ede3', a: '#1f3d66', b: '#8c2f25' } },
  { id: 'ledger',   label: 'Ledger',   swatch: { bg: '#ffffff', a: '#1f3cff', b: '#ff4d00' } },
  { id: 'nocturne', label: 'Nocturne', swatch: { bg: '#0e1116', a: '#8db1d8', b: '#d6a55c' } },
];
const DEFAULT_THEME = 'brief';

function readStoredTheme() {
  try {
    const stored = localStorage.getItem('da-theme');
    return THEMES.some(t => t.id === stored) ? stored : DEFAULT_THEME;
  } catch {
    return DEFAULT_THEME;
  }
}

const ThemeContext = createContext({ theme: DEFAULT_THEME, setTheme: () => {}, themes: THEMES });

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(readStoredTheme);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    try { localStorage.setItem('da-theme', theme); } catch { /* storage unavailable */ }
  }, [theme]);

  // Switch with a circular reveal expanding from the click point (View Transitions API when available).
  const setTheme = useCallback((next, origin) => {
    const apply = () => {
      document.documentElement.setAttribute('data-theme', next);
      setThemeState(next);
    };
    const reduced = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches;
    if (!document.startViewTransition || reduced || !origin) {
      apply();
      return;
    }
    const { x, y } = origin;
    const radius = Math.hypot(Math.max(x, window.innerWidth - x), Math.max(y, window.innerHeight - y));
    const transition = document.startViewTransition(() => flushSync(apply));
    transition.ready.then(() => {
      document.documentElement.animate(
        { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${radius}px at ${x}px ${y}px)`] },
        { duration: 650, easing: 'cubic-bezier(0.2, 0.8, 0.2, 1)', pseudoElement: '::view-transition-new(root)' },
      );
    });
  }, []);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

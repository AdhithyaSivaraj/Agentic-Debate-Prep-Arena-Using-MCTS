import React, { createContext, useContext, useState, useEffect } from 'react';

const THEMES = ['obsidian', 'academic', 'terminal'];
const THEME_LABELS = {
  obsidian: 'Obsidian',
  academic: 'Academic',
  terminal: 'Terminal',
};

const ThemeContext = createContext({ theme: 'obsidian', setTheme: () => {}, themes: THEMES, labels: THEME_LABELS });

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(() => {
    return localStorage.getItem('da-theme') || 'obsidian';
  });

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('da-theme', theme);
  }, [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme, themes: THEMES, labels: THEME_LABELS }}>
      {children}
    </ThemeContext.Provider>
  );
}

export function useTheme() {
  return useContext(ThemeContext);
}

import React from 'react';
import { useTheme } from '../lib/theme';

export default function ThemeSwitcher() {
  const { theme, setTheme, themes, labels } = useTheme();

  return (
    <div className="theme-selector" role="toolbar" aria-label="Color Theme">
      {themes.map(t => (
        <button
          key={t}
          className={`theme-opt ${theme === t ? 'active' : ''}`}
          onClick={() => setTheme(t)}
          aria-label={`${labels[t]} theme`}
        >
          {labels[t]}
        </button>
      ))}
    </div>
  );
}

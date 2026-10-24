import React from 'react';
import { useTheme } from '../lib/theme';

export default function ThemeSwitcher() {
  const { theme, setTheme, themes } = useTheme();

  return (
    <div className="theme-selector" role="radiogroup" aria-label="Theme">
      {themes.map(t => (
        <button
          key={t.id}
          role="radio"
          aria-checked={theme === t.id}
          className={`theme-opt ${theme === t.id ? 'active' : ''}`}
          onClick={e => theme !== t.id && setTheme(t.id, { x: e.clientX, y: e.clientY })}
          title={`${t.label} theme`}
        >
          <span
            className="theme-swatch"
            style={{ '--sw-bg': t.swatch.bg, '--sw-a': t.swatch.a, '--sw-b': t.swatch.b }}
          />
          <span className="label">{t.label}</span>
        </button>
      ))}
    </div>
  );
}

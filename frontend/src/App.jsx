import React from 'react';
import DebateArena from './components/DebateArena';
import { ThemeProvider } from './lib/theme';

export default function App() {
  return (
    <ThemeProvider>
      <DebateArena />
    </ThemeProvider>
  );
}

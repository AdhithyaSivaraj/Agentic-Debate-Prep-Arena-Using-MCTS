import React, { useEffect, useState } from 'react';
import { createPortal } from 'react-dom';

/**
 * Honest loading state: says what the backend is actually doing and how long it has taken.
 * The backend reports no intermediate progress, so the bar is indeterminate.
 */
export default function WorkingOverlay({ kicker, title, topic, now, note }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const started = Date.now();
    const id = setInterval(() => setElapsed((Date.now() - started) / 1000), 100);
    return () => clearInterval(id);
  }, []);

  return createPortal(
    <div className="modal-overlay" role="status" aria-live="polite">
      <div className="working">
        <div className="working-kicker">{kicker}</div>
        <div className="working-title">{title}</div>
        {topic && <div className="working-topic">“{topic}”</div>}
        <div className="working-now">
          <span>{now}</span>
          <span className="elapsed">{elapsed.toFixed(1)}s</span>
        </div>
        <div className="working-track"><span /></div>
        {note && <div className="working-note">{note}</div>}
      </div>
    </div>,
    document.body
  );
}

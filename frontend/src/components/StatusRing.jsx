import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';

/**
 * StatusRing component displaying agent states: idle | thinking | speaking | done
 * - size: "lg" (28px in header) | "sm" (12px on spine)
 * - state: "idle" | "thinking" | "speaking" | "done"
 * - agent: "a" | "b"
 */
export const StatusRing = forwardRef(function StatusRing(
  { size = 'lg', state = 'idle', agent = 'a', className = '' },
  ref
) {
  const [pulse, setPulse] = useState(false);
  const [isSettling, setIsSettling] = useState(false);

  // Expose ring.pulse() JS hook for timing during typing streaming
  useImperativeHandle(ref, () => ({
    pulse: () => {
      setPulse(true);
      setTimeout(() => setPulse(false), 120);
    },
  }));

  // Trigger one-shot settle animation (scale 1 -> 1.18 -> 1 over 380ms) when entering 'done' state
  useEffect(() => {
    if (state === 'done') {
      setIsSettling(true);
      const timer = setTimeout(() => setIsSettling(false), 380);
      return () => clearTimeout(timer);
    }
  }, [state]);

  return (
    <span
      className={`status-ring ${size} ${pulse ? 'ring-pulse' : ''} ${isSettling ? 'settling' : ''} ${className}`}
      data-state={state}
      data-agent={agent}
      aria-label={`Agent ${agent.toUpperCase()} status: ${state}`}
    >
      <span className="ring-core" />
    </span>
  );
});

export default StatusRing;

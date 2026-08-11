import React, { useState, useEffect, useImperativeHandle, forwardRef } from 'react';


export const StatusRing = forwardRef(function StatusRing(
  { size = 'lg', state = 'idle', agent = 'a', className = '' },
  ref
) {
  const [pulse, setPulse] = useState(false);
  const [isSettling, setIsSettling] = useState(false);

  
  useImperativeHandle(ref, () => ({
    pulse: () => {
      setPulse(true);
      setTimeout(() => setPulse(false), 120);
    },
  }));

  
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

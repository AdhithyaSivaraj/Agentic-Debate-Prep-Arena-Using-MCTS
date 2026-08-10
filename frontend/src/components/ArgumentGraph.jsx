import { useEffect, useRef } from 'react';

const N = 56;

export default function ArgumentGraph({ opacity = 0.65 }) {
  const canvasRef = useRef(null);
  const animRef   = useRef(null);
  const nodesRef  = useRef([]);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx    = canvas.getContext('2d');

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
      nodesRef.current = Array.from({ length: N }, () => ({
        x:  Math.random() * canvas.width,
        y:  Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r:  Math.random() * 1.8 + 1.0,
      }));
    };

    resize();
    window.addEventListener('resize', resize);

    const step = () => {
      const { width, height } = canvas;
      ctx.clearRect(0, 0, width, height);

      // Read current theme colors from CSS variables
      const computed = getComputedStyle(document.documentElement);
      const edgeColor = computed.getPropertyValue('--graph-edge').trim() || '167, 139, 250';
      const nodeColor = computed.getPropertyValue('--graph-node').trim() || '240, 236, 255';

      // Move nodes
      for (const n of nodesRef.current) {
        n.x += n.vx;
        n.y += n.vy;
        if (n.x < 0 || n.x > width)  n.vx *= -1;
        if (n.y < 0 || n.y > height) n.vy *= -1;
      }

      // Draw connecting edges
      const nodes = nodesRef.current;
      for (let i = 0; i < N; i++) {
        for (let j = i + 1; j < N; j++) {
          const dx = nodes[i].x - nodes[j].x;
          const dy = nodes[i].y - nodes[j].y;
          const d  = Math.sqrt(dx * dx + dy * dy);
          if (d < 185) {
            const alpha = (1 - d / 185) * 0.45;
            ctx.strokeStyle = `rgba(${edgeColor}, ${alpha})`;
            ctx.lineWidth   = 1.2;
            ctx.beginPath();
            ctx.moveTo(nodes[i].x, nodes[i].y);
            ctx.lineTo(nodes[j].x, nodes[j].y);
            ctx.stroke();
          }
        }
      }

      // Draw glowing nodes
      for (const n of nodes) {
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${nodeColor}, 0.75)`;
        ctx.fill();

        // Subtle glow halo
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r * 2.5, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(${edgeColor}, 0.15)`;
        ctx.fill();
      }

      animRef.current = requestAnimationFrame(step);
    };

    step();

    return () => {
      window.removeEventListener('resize', resize);
      cancelAnimationFrame(animRef.current);
    };
  }, []);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        opacity,
        pointerEvents: 'none',
        transition: 'opacity 0.5s ease',
      }}
    />
  );
}

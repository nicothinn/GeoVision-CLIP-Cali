"use client";

import { useEffect, useRef } from "react";

export interface DataStreamBackgroundProps {
  /** Opacity of the canvas (0–1). Default 0.95 */
  opacity?: number;
  /** Number of blobs. Default 6 */
  blobCount?: number;
}

/**
 * Canvas 2D background with a lava-lamp / metaball effect.
 *
 * Multiple soft Gaussian blobs drift around the screen, blending where they
 * overlap to create organic, fluid-like shapes.  Colours flow through a
 * heat-map gradient (blue → cyan → green → yellow → orange → red).
 *
 * Zero dependencies, zero WebGL, zero runtime errors.
 */
export function DataStreamBackground({
  opacity = 0.95,
  blobCount = 6,
}: DataStreamBackgroundProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const mouseRef = useRef({ x: -1000, y: -1000 });

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let w = 0;
    let h = 0;

    // ── Blob definition ────────────────────────────────────────────
    interface Blob {
      x: number;
      y: number;
      radius: number;
      speed: number;
      angle: number;
      orbitRadiusX: number;
      orbitRadiusY: number;
      phase: number;
    }

    const blobs: Blob[] = [];

    function initBlobs() {
      blobs.length = 0;
      for (let i = 0; i < blobCount; i++) {
        blobs.push({
          x: Math.random() * w,
          y: Math.random() * h,
          radius: Math.min(w, h) * (0.18 + Math.random() * 0.22), // 18-40% of screen
          speed: 0.15 + Math.random() * 0.35,
          angle: Math.random() * Math.PI * 2,
          orbitRadiusX: w * (0.25 + Math.random() * 0.35),
          orbitRadiusY: h * (0.2 + Math.random() * 0.3),
          phase: Math.random() * Math.PI * 2,
        });
      }
    }

    // ── Resize ────────────────────────────────────────────────────
    function resize() {
      w = window.innerWidth;
      h = window.innerHeight;
      const dpr = Math.min(window.devicePixelRatio, 2);
      canvas!.width = w * dpr;
      canvas!.height = h * dpr;
      canvas!.style.width = w + "px";
      canvas!.style.height = h + "px";
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
      initBlobs();
    }

    resize();
    window.addEventListener("resize", resize);

    // ── Mouse ─────────────────────────────────────────────────────
    function onMouse(e: MouseEvent) {
      mouseRef.current.x = e.clientX;
      mouseRef.current.y = e.clientY;
    }
    function onMouseLeave() {
      mouseRef.current.x = -1000;
      mouseRef.current.y = -1000;
    }
    window.addEventListener("mousemove", onMouse);
    window.addEventListener("mouseleave", onMouseLeave);

    // ── Heat-map colour ───────────────────────────────────────────
    //  0.0  →  deep blue
    //  0.2  →  cyan
    //  0.4  →  green
    //  0.6  →  yellow
    //  0.8  →  orange
    //  1.0  →  red
    function heatColor(value: number): string {
      const v = Math.min(1, Math.max(0, value));
      const hue = 240 - v * 240;   // 240° (blue) → 0° (red)
      const sat = 90 + v * 10;     // 90–100%
      const lig = 45 + v * 25;     // 45–70%
      return `hsl(${hue}, ${sat}%, ${lig}%)`;
    }

    // ── Draw loop ─────────────────────────────────────────────────
    let animId: number;

    function draw(time: number) {
      animId = requestAnimationFrame(draw);
      const t = time * 0.001;

      const mx = mouseRef.current.x;
      const my = mouseRef.current.y;

      // Update blob positions (smooth orbital motion + drift)
      for (const blob of blobs) {
        blob.x =
          w * 0.5 +
          Math.cos(t * blob.speed + blob.phase) * blob.orbitRadiusX +
          Math.sin(t * blob.speed * 0.7 + blob.phase * 1.3) * blob.orbitRadiusX * 0.3;
        blob.y =
          h * 0.5 +
          Math.sin(t * blob.speed * 0.85 + blob.phase * 1.7) * blob.orbitRadiusY +
          Math.cos(t * blob.speed * 0.6 + blob.phase * 0.9) * blob.orbitRadiusY * 0.25;
      }

      // Mouse acts as an extra blob
      const mouseBlob = { x: mx, y: my, radius: 120, influence: 0 };
      const mouseDist = Math.sqrt(
        (mx - w * 0.5) ** 2 + (my - h * 0.5) ** 2,
      );
      const mouseActive = mouseDist < Math.max(w, h) * 0.6;

      // Grid resolution: lower = smoother but slower
      const step = 14; // px between sample points
      const cols = Math.ceil(w / step);
      const rows = Math.ceil(h / step);

      ctx!.clearRect(0, 0, w, h);

      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const px = c * step + step / 2;
          const py = r * step + step / 2;

          // Sum Gaussian influences from all blobs
          let sum = 0;
          for (const blob of blobs) {
            const dx = px - blob.x;
            const dy = py - blob.y;
            const distSq = dx * dx + dy * dy;
            const radiusSq = blob.radius * blob.radius;
            // Gaussian falloff: e^(-dist² / (2r²))
            sum += Math.exp(-distSq / (radiusSq * 0.5));
          }

          // Mouse influence
          if (mouseActive) {
            const mdx = px - mouseBlob.x;
            const mdy = py - mouseBlob.y;
            const mDistSq = mdx * mdx + mdy * mdy;
            const mRadiusSq = mouseBlob.radius * mouseBlob.radius;
            sum += Math.exp(-mDistSq / (mRadiusSq * 0.5)) * 0.6;
          }

          // Normalise to [0, 1] with a soft curve
          const value = Math.min(1, sum * 0.45);

          // Skip nearly-invisible cells for performance
          if (value < 0.02) continue;

          const size = step * 1.1;
          const alpha = Math.min(1, value * 1.1 + 0.15);

          ctx!.fillStyle = heatColor(value);
          ctx!.globalAlpha = alpha * opacity;

          // Draw soft circles (metaball look)
          ctx!.beginPath();
          ctx!.arc(px, py, size * 0.55, 0, Math.PI * 2);
          ctx!.fill();
        }
      }

      ctx!.globalAlpha = 1;
    }

    animId = requestAnimationFrame(draw);

    // ── Cleanup ───────────────────────────────────────────────────
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMouse);
      window.removeEventListener("mouseleave", onMouseLeave);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <canvas
      ref={canvasRef}
      className="absolute inset-0 w-full h-full"
      style={{ opacity: 1 }}
      aria-hidden="true"
    />
  );
}

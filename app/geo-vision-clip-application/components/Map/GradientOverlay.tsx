"use client";
import { useEffect, useRef } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import { getColorForValue, CONTAMINANT_META } from "@/lib/constants";

interface GridData {
  lats: number[][];
  lons: number[][];
  values: number[][];
  variances: number[][];
}

interface GradientOverlayProps {
  data: GridData;
  contaminant: string;
}

function hexToRgb(hex: string) {
  const r = parseInt(hex.slice(1, 3), 16);
  const g = parseInt(hex.slice(3, 5), 16);
  const b = parseInt(hex.slice(5, 7), 16);
  return { r, g, b };
}

export function GradientOverlay({ data, contaminant }: GradientOverlayProps) {
  const map = useMap();
  const overlayRef = useRef<L.ImageOverlay | null>(null);
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    if (!data || !map) return;

    const { lats, lons, values, variances } = data;
    const rows = lats.length;
    const cols = lats[0]?.length ?? 0;
    if (!rows || !cols) return;

    const meta = CONTAMINANT_META[contaminant] ?? CONTAMINANT_META.NO2;
    const minVal = meta.min;
    const maxVal = meta.max;

    // Find actual bounds for opacity normalization
    let maxVar = 0;
    let minVar = Infinity;
    for (const row of variances) {
      for (const v of row) {
        if (v > maxVar) maxVar = v;
        if (v < minVar) minVar = v;
      }
    }

    // Create canvas
    const canvas = document.createElement("canvas");
    canvas.width = cols;
    canvas.height = rows;
    canvasRef.current = canvas;
    const ctx = canvas.getContext("2d")!;

    for (let i = 0; i < rows; i++) {
      for (let j = 0; j < cols; j++) {
        const val = values[i][j];
        const variance = variances[i][j];
        const color = getColorForValue(val, minVal, maxVal);
        const { r, g, b } = hexToRgb(color);
        // Uncertainty layer: lower opacity where σ² is high
        const uncertainty = (variance - minVar) / (maxVar - minVar + 1e-9);
        const alpha = Math.round((0.85 - uncertainty * 0.45) * 255);

        ctx.fillStyle = `rgba(${r},${g},${b},${alpha / 255})`;
        ctx.fillRect(j, i, 1, 1);
      }
    }

    // Determine geographic bounds
    const allLats = lats.flat();
    const allLons = lons.flat();
    const minLat = Math.min(...allLats);
    const maxLat = Math.max(...allLats);
    const minLon = Math.min(...allLons);
    const maxLon = Math.max(...allLons);

    const bounds: L.LatLngBoundsExpression = [
      [minLat, minLon],
      [maxLat, maxLon],
    ];

    const url = canvas.toDataURL();

    if (overlayRef.current) {
      overlayRef.current.remove();
    }

    const overlay = L.imageOverlay(url, bounds, {
      opacity: 1,
      interactive: false,
      className: "gradient-overlay",
    });
    overlay.addTo(map);
    overlayRef.current = overlay;

    return () => {
      overlay.remove();
      overlayRef.current = null;
    };
  }, [data, contaminant, map]);

  return null;
}

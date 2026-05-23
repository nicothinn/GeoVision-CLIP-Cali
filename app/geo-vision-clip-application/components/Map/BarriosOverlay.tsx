"use client";

import { useMemo } from "react";
import { GeoJSON } from "react-leaflet";
import L from "leaflet";
import type { PathOptions } from "leaflet";
import type { Layer } from "leaflet";
import {
  type BarriosCollection,
  type ComunasCollection,
} from "@/lib/geo/barrios";

interface BarriosOverlayProps {
  barrios: BarriosCollection;
  comunas: ComunasCollection;
  theme: "dark" | "light";
}

function escapeHtml(text: string): string {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

export function BarriosOverlay({ barrios, comunas, theme }: BarriosOverlayProps) {
  const isDark = theme === "dark";

  const comunaStyle = useMemo<PathOptions>(
    () => ({
      color: isDark ? "#94a3b8" : "#64748b",
      weight: 2,
      opacity: 0.85,
      fillColor: isDark ? "#334155" : "#cbd5e1",
      fillOpacity: 0.06,
    }),
    [isDark]
  );

  const barrioStyle = useMemo<PathOptions>(
    () => ({
      color: isDark ? "#64748b" : "#94a3b8",
      weight: 1,
      opacity: 0.7,
      fillColor: isDark ? "#475569" : "#e2e8f0",
      fillOpacity: 0.08,
    }),
    [isDark]
  );

  const tooltipClass = isDark
    ? "barrio-tooltip barrio-tooltip--dark"
    : "barrio-tooltip barrio-tooltip--light";

  return (
    <>
      <GeoJSON
        key={`comunas-${theme}`}
        data={comunas}
        style={() => comunaStyle}
        interactive
        onEachFeature={(feature, layer) => {
          const comuna = String(
            (feature.properties as { comuna?: string })?.comuna ?? ""
          );
          if (!comuna) return;
          layer.bindTooltip(escapeHtml(comuna), {
            sticky: true,
            direction: "top",
            className: tooltipClass,
          });
        }}
      />
      <GeoJSON
        key={`barrios-${theme}`}
        data={barrios}
        style={() => barrioStyle}
        interactive
        onEachFeature={(feature, layer) => {
          const props = feature.properties as {
            barrio?: string;
            comuna?: string;
          };
          const barrio = String(props?.barrio ?? "");
          const comuna = String(props?.comuna ?? "");
          if (!barrio) return;
          const html = `<strong>${escapeHtml(barrio)}</strong><br/><span class="barrio-tooltip__comuna">Comuna: ${escapeHtml(comuna)}</span>`;
          layer.bindTooltip(html, {
            sticky: true,
            direction: "top",
            className: tooltipClass,
          });
          layer.on("mouseover", function (this: Layer) {
            const path = this as L.Path;
            if (path.setStyle) {
              path.setStyle({
                fillOpacity: isDark ? 0.18 : 0.22,
                weight: 1.5,
              });
            }
          });
          layer.on("mouseout", function (this: Layer) {
            const path = this as L.Path;
            if (path.setStyle) {
              path.setStyle(barrioStyle);
            }
          });
        }}
      />
    </>
  );
}

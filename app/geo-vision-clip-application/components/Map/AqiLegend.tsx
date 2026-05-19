"use client";
import { useEffect } from "react";
import { useMap } from "react-leaflet";
import L from "leaflet";
import { AQI_SCALE } from "@/lib/constants";

interface AqiLegendProps {
  theme: "dark" | "light";
}

export function AqiLegend({ theme }: AqiLegendProps) {
  const map = useMap();

  useEffect(() => {
    const control = new L.Control({ position: "bottomright" });

    control.onAdd = () => {
      const div = L.DomUtil.create("div");
      const bg = theme === "dark"
        ? "background:rgba(15,23,42,0.85);border:1px solid rgba(51,65,85,0.5);"
        : "background:rgba(255,255,255,0.9);border:1px solid rgba(226,232,240,0.8);";

      div.innerHTML = `
        <div style="${bg}padding:10px 12px;border-radius:10px;backdrop-filter:blur(12px);min-width:120px;">
          <div style="font-family:'Inter',sans-serif;font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.05em;color:${theme === "dark" ? "#94a3b8" : "#64748b"};margin-bottom:8px;">Índice AQI</div>
          ${AQI_SCALE.map((step) => `
            <div style="display:flex;align-items:center;gap:6px;margin-bottom:5px;">
              <div style="width:12px;height:12px;border-radius:50%;background:${step.color};flex-shrink:0;"></div>
              <span style="font-family:'Inter',sans-serif;font-size:11px;color:${theme === "dark" ? "#f1f5f9" : "#0f172a"};">${step.label}</span>
            </div>
          `).join("")}
        </div>
      `;
      return div;
    };

    control.addTo(map);

    return () => {
      control.remove();
    };
  }, [map, theme]);

  return null;
}

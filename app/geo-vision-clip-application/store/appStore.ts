"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { Contaminant, Horizon } from "@/lib/constants";

interface AppState {
  theme: "dark" | "light";
  contaminant: Contaminant;
  horizon: Horizon;
  selectedPoint: { lat: number; lon: number } | null;
  horizonIndex: number;
  playing: boolean;
  showBarriosLayers: boolean;

  toggleTheme: () => void;
  setShowBarriosLayers: (v: boolean) => void;
  setContaminant: (c: Contaminant) => void;
  setHorizon: (h: Horizon) => void;
  setHorizonIndex: (i: number) => void;
  setPoint: (lat: number, lon: number) => void;
  clearPoint: () => void;
  togglePlaying: () => void;
}

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      theme: "dark",
      contaminant: "NO2",
      horizon: "T+1",
      selectedPoint: null,
      horizonIndex: 0,
      playing: false,
      showBarriosLayers: true,

      toggleTheme: () =>
        set((s) => ({ theme: s.theme === "dark" ? "light" : "dark" })),
      setShowBarriosLayers: (v) => set({ showBarriosLayers: v }),
      setContaminant: (c) => set({ contaminant: c }),
      setHorizon: (h) => set({ horizon: h }),
      setHorizonIndex: (i) => {
        const HORIZONS = ["T+1", "T+3", "T+7"] as const;
        set({ horizonIndex: i, horizon: HORIZONS[i] });
      },
      setPoint: (lat, lon) => set({ selectedPoint: { lat, lon } }),
      clearPoint: () => set({ selectedPoint: null }),
      togglePlaying: () => set((s) => ({ playing: !s.playing })),
    }),
    {
      name: "geovision-store",
      partialize: (state) => ({
        theme: state.theme,
        contaminant: state.contaminant,
        horizon: state.horizon,
      }),
    }
  )
);

"use client";
import { useEffect, useRef } from "react";
import { Play, Pause, SkipForward } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { HORIZONS } from "@/lib/constants";

export function HorizonSlider() {
  const { theme, horizonIndex, setHorizonIndex, playing, togglePlaying } = useAppStore();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isDark = theme === "dark";

  useEffect(() => {
    if (playing) {
      intervalRef.current = setInterval(() => {
        setHorizonIndex((horizonIndex + 1) % HORIZONS.length);
      }, 1800);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [playing, horizonIndex, setHorizonIndex]);

  const handleNext = () => {
    setHorizonIndex((horizonIndex + 1) % HORIZONS.length);
  };

  return (
    <div
      className={`flex items-center gap-4 px-6 py-3 border-t ${
        isDark
          ? "bg-slate-900/90 border-slate-800 backdrop-blur-md"
          : "bg-white/90 border-slate-200 backdrop-blur-md"
      }`}
    >
      {/* Play/Pause */}
      <button
        onClick={togglePlaying}
        aria-label={playing ? "Pausar animación" : "Reproducir animación"}
        className={`flex items-center justify-center w-8 h-8 rounded-full transition-all ${
          isDark
            ? "bg-slate-800 text-emerald-400 hover:bg-emerald-500 hover:text-white"
            : "bg-slate-100 text-emerald-600 hover:bg-emerald-500 hover:text-white"
        }`}
      >
        {playing ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
      </button>

      {/* Skip */}
      <button
        onClick={handleNext}
        aria-label="Siguiente horizonte"
        className={`flex items-center justify-center w-8 h-8 rounded-full transition-all ${
          isDark
            ? "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
            : "bg-slate-100 text-slate-500 hover:bg-slate-200"
        }`}
      >
        <SkipForward className="w-4 h-4" />
      </button>

      {/* Range */}
      <input
        type="range"
        min={0}
        max={HORIZONS.length - 1}
        value={horizonIndex}
        onChange={(e) => setHorizonIndex(parseInt(e.target.value))}
        className="flex-1 h-1.5 rounded-full cursor-pointer"
        aria-label="Horizonte de predicción"
      />

      {/* Horizon pills */}
      <div className="flex gap-2">
        {HORIZONS.map((h, i) => (
          <button
            key={h}
            onClick={() => setHorizonIndex(i)}
            aria-pressed={horizonIndex === i}
            className={`px-3 py-1 rounded-full text-xs font-mono transition-all ${
              horizonIndex === i
                ? "bg-emerald-500 text-white shadow-md shadow-emerald-500/30"
                : isDark
                ? "bg-slate-800 text-slate-400 hover:bg-slate-700 hover:text-slate-200"
                : "bg-slate-100 text-slate-500 hover:bg-slate-200"
            }`}
          >
            {h}
          </button>
        ))}
      </div>
    </div>
  );
}

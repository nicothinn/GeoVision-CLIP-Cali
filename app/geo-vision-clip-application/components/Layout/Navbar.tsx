"use client";
import { Globe, Sun, Moon } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { CONTAMINANTS } from "@/lib/constants";
import type { Contaminant } from "@/lib/constants";

export function Navbar() {
  const { theme, toggleTheme, contaminant, setContaminant } = useAppStore();

  const isDark = theme === "dark";

  return (
    <header
      className={`flex items-center justify-between px-4 h-14 border-b shrink-0 z-50 ${
        isDark
          ? "bg-slate-900 border-slate-800"
          : "bg-white border-slate-200"
      }`}
    >
      {/* Brand */}
      <div className="flex items-center gap-2">
        <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-emerald-500/20">
          <Globe className="w-4 h-4 text-emerald-500" />
        </div>
        <div>
          <span className={`font-semibold text-sm ${isDark ? "text-slate-100" : "text-slate-900"}`}>
            GeoVision-CLIP
          </span>
          <span className="text-xs text-emerald-500 ml-1.5 font-mono">Cali</span>
        </div>
      </div>

      {/* Contaminant pills */}
      <nav className="flex items-center gap-1" aria-label="Selector de contaminante">
        {CONTAMINANTS.map((c) => (
          <button
            key={c}
            onClick={() => setContaminant(c as Contaminant)}
            aria-pressed={contaminant === c}
            className={`px-3 py-1.5 rounded-full text-xs font-mono font-semibold transition-all ${
              contaminant === c
                ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30"
                : isDark
                ? "bg-slate-800 text-slate-400 hover:text-slate-200 hover:bg-slate-700"
                : "bg-slate-100 text-slate-500 hover:text-slate-700 hover:bg-slate-200"
            }`}
          >
            {c === "NO2" ? "NO₂" : c === "SO2" ? "SO₂" : "O₃"}
          </button>
        ))}
      </nav>

      {/* Right controls */}
      <div className="flex items-center gap-2">
        <span className={`text-xs font-mono hidden sm:block ${isDark ? "text-slate-500" : "text-slate-400"}`}>
          v1.0 · DAGMA × CLIP
        </span>
        <button
          onClick={toggleTheme}
          aria-label={isDark ? "Cambiar a modo claro" : "Cambiar a modo oscuro"}
          className={`flex items-center justify-center w-8 h-8 rounded-lg transition-all ${
            isDark
              ? "bg-slate-800 text-amber-400 hover:bg-slate-700"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          {isDark ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
        </button>
      </div>
    </header>
  );
}

"use client";
import { useRef } from "react";
import dynamic from "next/dynamic";
import { Globe, ChevronDown, Wind, Activity, Satellite } from "lucide-react";
import { useAppStore } from "@/store/appStore";
import { useScrollReveal } from "@/hooks/useScrollReveal";
import { CONTAMINANTS } from "@/lib/constants";
import type { Contaminant } from "@/lib/constants";

// Dynamic import — Canvas 2D (no WebGL, no SSR needed for window access)
const DataStreamBackground = dynamic(
  () =>
    import("@/components/Hero/DataStreamBackground").then(
      (mod) => mod.DataStreamBackground,
    ),
  { ssr: false },
);

interface HeroSectionProps {
  onScrollToMap: () => void;
}

const STATS = [
  { label: "Estaciones DAGMA", value: "9", unit: "activas" },
  { label: "Cobertura", value: "520", unit: "km²" },
  { label: "Horizontes", value: "3", unit: "T+1 · T+3 · T+7" },
  { label: "Contaminantes", value: "3", unit: "NO₂ · SO₂ · O₃" },
];

export function HeroSection({ onScrollToMap }: HeroSectionProps) {
  const { theme, toggleTheme, contaminant, setContaminant } = useAppStore();
  const isDark = theme === "dark";

  const { ref: titleRef, visible: titleVisible } = useScrollReveal(0.05);
  const { ref: statsRef, visible: statsVisible } = useScrollReveal(0.1);

  return (
    <section className="relative w-full min-h-screen flex flex-col overflow-hidden bg-slate-950">
      {/* Canvas data-stream background (zero-dependency, no WebGL) */}
      <div className="absolute inset-0 z-0" aria-hidden="true">
        <DataStreamBackground opacity={0.85} density={1.0} />
        {/* Dark gradient overlay */}
        <div className="absolute inset-0 hero-video-overlay" />
        {/* Subtle grid pattern */}
        <div
          className="absolute inset-0 opacity-5"
          style={{
            backgroundImage: `linear-gradient(rgba(16,185,129,0.3) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(16,185,129,0.3) 1px, transparent 1px)`,
            backgroundSize: "60px 60px",
          }}
        />
      </div>

      {/* Fixed navbar */}
      <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 md:px-10 py-4 bg-slate-950/70 backdrop-blur-md border-b border-white/5">
        <div className="flex items-center gap-3">
          <div className="flex items-center justify-center w-9 h-9 rounded-xl bg-emerald-500/20 border border-emerald-500/30">
            <Globe className="w-4 h-4 text-emerald-400" />
          </div>
          <div>
            <span className="font-semibold text-slate-100 text-sm tracking-tight">
              GeoVision-CLIP
            </span>
            <span className="text-xs text-emerald-400 ml-2 font-mono">Cali</span>
          </div>
        </div>

        {/* Contaminant pills */}
        <nav className="hidden sm:flex items-center gap-1.5" aria-label="Selector de contaminante">
          {CONTAMINANTS.map((c) => (
            <button
              key={c}
              onClick={() => setContaminant(c as Contaminant)}
              aria-pressed={contaminant === c}
              className={`px-3 py-1.5 rounded-full text-xs font-mono font-semibold transition-all ${
                contaminant === c
                  ? "bg-emerald-500 text-white shadow-lg shadow-emerald-500/30"
                  : "bg-slate-800/70 text-slate-400 hover:text-slate-200 hover:bg-slate-700/70 border border-slate-700/50"
              }`}
            >
              {c === "NO2" ? "NO₂" : c === "SO2" ? "SO₂" : "O₃"}
            </button>
          ))}
        </nav>

        <button
          onClick={toggleTheme}
          className="text-xs font-mono text-slate-500 hover:text-emerald-400 transition-colors px-3 py-1.5 rounded-lg border border-slate-800/60 hover:border-emerald-500/30"
          aria-label="Cambiar tema"
        >
          {isDark ? "Modo claro" : "Modo oscuro"}
        </button>
      </header>

      {/* Main hero content */}
      <div className="relative z-10 flex flex-col items-center justify-center flex-1 text-center px-6 py-20">
        {/* Badge */}
        <div
          ref={titleRef as React.RefObject<HTMLDivElement>}
          className={`reveal ${titleVisible ? "visible" : ""} inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 mb-8`}
        >
          <Satellite className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-xs font-mono text-emerald-400 tracking-wider">
            Plataforma de monitoreo geoespacial · DAGMA × CLIP
          </span>
        </div>

        <h1
          className={`reveal reveal-delay-1 ${titleVisible ? "visible" : ""} text-4xl sm:text-6xl md:text-7xl font-bold text-slate-50 leading-tight tracking-tight text-balance max-w-4xl mb-6`}
        >
          Prediccion de{" "}
          <span className="text-emerald-400">calidad del aire</span>{" "}
          en tiempo real
        </h1>

        <p
          className={`reveal reveal-delay-2 ${titleVisible ? "visible" : ""} text-base sm:text-lg text-slate-400 leading-relaxed max-w-2xl mb-10 text-pretty`}
        >
          Modelos de deep learning entrenados con datos de las 9 estaciones DAGMA
          de Cali. Predicciones espaciales de NO₂, SO₂ y O₃ con horizontes de
          1, 3 y 7 dias y cuantificacion de incertidumbre.
        </p>

        {/* Feature chips */}
        <div
          className={`reveal reveal-delay-3 ${titleVisible ? "visible" : ""} flex flex-wrap items-center justify-center gap-3 mb-12`}
        >
          {[
            { icon: <Wind className="w-3.5 h-3.5" />, label: "GeoVision-CLIP" },
            { icon: <Activity className="w-3.5 h-3.5" />, label: "SAE Sparse Autoencoder" },
            { icon: <Satellite className="w-3.5 h-3.5" />, label: "Kriging espacial" },
          ].map(({ icon, label }) => (
            <div
              key={label}
              className="flex items-center gap-2 px-4 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-slate-300 text-sm"
            >
              <span className="text-emerald-400">{icon}</span>
              {label}
            </div>
          ))}
        </div>

        {/* CTA */}
        <div
          className={`reveal reveal-delay-4 ${titleVisible ? "visible" : ""} flex items-center gap-4`}
        >
          <button
            onClick={onScrollToMap}
            className="px-6 py-3 rounded-full bg-emerald-500 hover:bg-emerald-400 text-white font-semibold text-sm transition-all shadow-lg shadow-emerald-500/30 hover:shadow-emerald-500/50 hover:-translate-y-0.5"
          >
            Explorar el mapa
          </button>
          <button
            onClick={onScrollToMap}
            className="px-6 py-3 rounded-full bg-slate-800/70 hover:bg-slate-700/70 text-slate-300 font-semibold text-sm transition-all border border-slate-700/50"
          >
            Ver analisis
          </button>
        </div>
      </div>

      {/* Stats row */}
      <div
        ref={statsRef as React.RefObject<HTMLDivElement>}
        className={`reveal ${statsVisible ? "visible" : ""} relative z-10 grid grid-cols-2 md:grid-cols-4 gap-px bg-slate-800/30 border-t border-slate-800/50`}
      >
        {STATS.map(({ label, value, unit }, i) => (
          <div
            key={label}
            className={`reveal reveal-delay-${i + 1} ${statsVisible ? "visible" : ""} flex flex-col items-center py-8 px-4 bg-slate-950/80`}
          >
            <span className={`mono-value text-3xl md:text-4xl font-bold text-emerald-400 stat-glow`}>
              {value}
            </span>
            <span className="text-xs font-mono text-slate-600 mt-1">{unit}</span>
            <span className="text-xs text-slate-500 mt-1 text-center">{label}</span>
          </div>
        ))}
      </div>

      {/* Scroll indicator */}
      <button
        onClick={onScrollToMap}
        aria-label="Desplazarse al mapa"
        className="absolute bottom-28 left-1/2 -translate-x-1/2 z-20 flex flex-col items-center gap-2 text-slate-600 hover:text-emerald-400 transition-colors"
      >
        <span className="text-xs font-mono tracking-widest uppercase">Scroll</span>
        <ChevronDown className="w-5 h-5 scroll-bounce" />
      </button>
    </section>
  );
}

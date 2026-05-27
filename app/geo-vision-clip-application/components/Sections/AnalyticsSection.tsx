"use client";
import { useScrollReveal } from "@/hooks/useScrollReveal";
import { useAppStore } from "@/store/appStore";
import { GridMaps } from "@/components/Dashboard/GridMaps";
import { KPICards } from "@/components/Dashboard/KPICards";
import { ValidationTable } from "@/components/Sidebar/ValidationTable";
import { TimeSeriesChart } from "@/components/Dashboard/TimeSeriesChart";
import { CONTAMINANT_META } from "@/lib/constants";
import { BarChart3, Grid, TrendingUp } from "lucide-react";

export function AnalyticsSection() {
  const { theme, contaminant } = useAppStore();
  const isDark = theme === "dark";

  const { ref: headerRef, visible: headerVisible } = useScrollReveal(0.05);
  const { ref: gridRef, visible: gridVisible } = useScrollReveal(0.05);
  const { ref: bottomRef, visible: bottomVisible } = useScrollReveal(0.05);

  const meta = CONTAMINANT_META[contaminant];

  return (
    <section
      id="analisis"
      className={`w-full pb-24 ${isDark ? "bg-slate-950" : "bg-slate-100"}`}
    >
      {/* Top divider */}
      <div className={`w-full h-px ${isDark ? "bg-slate-800" : "bg-slate-200"}`} />

      {/* Section header */}
      <div
        ref={headerRef as React.RefObject<HTMLDivElement>}
        className={`reveal ${headerVisible ? "visible" : ""} px-6 md:px-10 pt-16 pb-8`}
      >
        <div className="flex items-center gap-3 mb-3">
          <div className="section-divider w-8" />
          <span className={`text-xs font-mono uppercase tracking-widest ${isDark ? "text-emerald-500" : "text-emerald-600"}`}>
            Vista analitica
          </span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4">
          <div>
            <h2 className={`text-2xl sm:text-3xl font-bold text-balance ${isDark ? "text-slate-100" : "text-slate-900"}`}>
              Analisis multidimensional 3 x 3
            </h2>
            <p className={`mt-2 text-sm leading-relaxed max-w-xl ${isDark ? "text-slate-400" : "text-slate-500"}`}>
              Cada celda combina un contaminante (NO₂, SO₂, O₃) con un
              horizonte temporal (T+1, T+3, T+7). El gradiente de color refleja
              la concentracion predicha interpolada sobre la ciudad.
            </p>
          </div>
          <div className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-mono shrink-0 ${
            isDark ? "bg-slate-800 text-emerald-400" : "bg-white border border-slate-200 text-emerald-600"
          }`}>
            <Grid className="w-4 h-4" />
            3 contaminantes × 3 horizontes
          </div>
        </div>
      </div>

      {/* 3x3 Grid maps */}
      <div
        ref={gridRef as React.RefObject<HTMLDivElement>}
        className={`reveal ${gridVisible ? "visible" : ""} px-4 md:px-10`}
      >
        <GridMaps />
      </div>

      {/* Bottom analytics row: Time series + Validation + KPIs */}
      <div
        ref={bottomRef as React.RefObject<HTMLDivElement>}
        className={`reveal ${bottomVisible ? "visible" : ""} px-4 md:px-10 mt-12`}
      >
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">

          {/* Time Series Chart */}
          <div className={`lg:col-span-2 rounded-2xl p-5 ${isDark ? "bg-slate-900 border border-slate-800" : "bg-white border border-slate-200"}`}>
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="w-4 h-4 text-emerald-500" />
              <span className={`text-sm font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                Serie temporal — {contaminant === "NO2" ? "NO₂" : contaminant === "SO2" ? "SO₂" : "O₃"}
              </span>
              <span className={`ml-auto text-xs font-mono ${isDark ? "text-slate-600" : "text-slate-400"}`}>
                8 dias · {meta.unit}
              </span>
            </div>
            <TimeSeriesChart contaminant={contaminant} unit={meta.unit} />
          </div>

          {/* Validation Table */}
          <div className={`rounded-2xl p-5 ${isDark ? "bg-slate-900 border border-slate-800" : "bg-white border border-slate-200"}`}>
            <div className="flex items-center gap-2 mb-4">
              <BarChart3 className="w-4 h-4 text-emerald-500" />
              <span className={`text-sm font-semibold ${isDark ? "text-slate-300" : "text-slate-700"}`}>
                Metricas de validacion
              </span>
            </div>
            <ValidationTable />
          </div>
        </div>

        {/* KPI cards row */}
        <div className="mt-6">
          <KPICards />
        </div>
      </div>

      {/* Footer */}
      <div className={`px-6 md:px-10 mt-16 pt-8 border-t flex flex-col sm:flex-row items-center justify-between gap-4 ${
        isDark ? "border-slate-800" : "border-slate-200"
      }`}>
        <div className="flex items-center gap-2">
          <div className="w-5 h-5 rounded-md bg-emerald-500/20 flex items-center justify-center">
            <div className="w-2 h-2 rounded-full bg-emerald-500" />
          </div>
          <span className={`text-xs font-mono ${isDark ? "text-slate-600" : "text-slate-400"}`}>
            GeoVision-CLIP Cali — v1.0 · DAGMA × CLIP · Modelo entrenado 2019-2023
          </span>
        </div>
        <span className={`text-xs font-mono ${isDark ? "text-slate-700" : "text-slate-300"}`}>
          Universidad Autónoma de Occidente · Analítica de datos e IA
        </span>
      </div>
    </section>
  );
}

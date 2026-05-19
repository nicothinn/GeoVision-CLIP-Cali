"use client";
import { Download, FileSpreadsheet } from "lucide-react";
import { useAppStore } from "@/store/appStore";

interface DownloadButtonsProps {
  lat: number;
  lon: number;
  contaminant: string;
}

export function DownloadButtons({ lat, lon, contaminant }: DownloadButtonsProps) {
  const { theme } = useAppStore();
  const isDark = theme === "dark";

  const download = (format: "csv" | "geotiff") => {
    const url = `/api/download/${format}?lat=${lat}&lon=${lon}&contaminant=${contaminant}`;
    const link = document.createElement("a");
    link.href = url;
    link.download = `geovision_${contaminant}_${lat.toFixed(4)}_${lon.toFixed(4)}.${format === "csv" ? "csv" : "tif"}`;
    link.click();
  };

  return (
    <div className={`rounded-xl p-3 ${isDark ? "bg-slate-800" : "bg-white border border-slate-200"}`}>
      <div className={`text-xs font-semibold mb-2 ${isDark ? "text-slate-400" : "text-slate-600"}`}>
        Descargar datos
      </div>
      <div className="flex gap-2">
        <button
          onClick={() => download("csv")}
          className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium bg-emerald-500 text-white hover:bg-emerald-600 transition-all"
        >
          <FileSpreadsheet className="w-3.5 h-3.5" />
          CSV
        </button>
        <button
          onClick={() => download("geotiff")}
          className={`flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium transition-all ${
            isDark
              ? "bg-slate-700 text-slate-300 hover:bg-slate-600"
              : "bg-slate-100 text-slate-600 hover:bg-slate-200"
          }`}
        >
          <Download className="w-3.5 h-3.5" />
          GeoTIFF
        </button>
      </div>
    </div>
  );
}

"use client";
import dynamic from "next/dynamic";
import { Loader2 } from "lucide-react";

const CaliMapInner = dynamic(() => import("./CaliMapInner"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-full bg-slate-900 rounded-xl">
      <div className="flex flex-col items-center gap-3">
        <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
        <span className="text-slate-400 text-sm font-mono">Cargando mapa...</span>
      </div>
    </div>
  ),
});

export { CaliMapInner as default };
export function CaliMap(props: Parameters<typeof CaliMapInner>[0]) {
  return <CaliMapInner {...props} />;
}

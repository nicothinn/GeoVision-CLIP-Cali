"use client";
import { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";
import { HeroSection } from "@/components/Sections/HeroSection";
import { MapSection } from "@/components/Sections/MapSection";
import { AnalyticsSection } from "@/components/Sections/AnalyticsSection";

export default function GeoVisionPage() {
  const [mounted, setMounted] = useState(false);
  const mapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const scrollToMap = () => {
    mapRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  if (!mounted) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-950">
        <div className="flex flex-col items-center gap-4">
          <Loader2 className="w-10 h-10 text-emerald-500 animate-spin" />
          <span className="text-slate-400 font-mono text-sm">Cargando GeoVision-CLIP...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-950 overflow-x-hidden">
      {/* Section 1: Hero with video background */}
      <HeroSection onScrollToMap={scrollToMap} />

      {/* Section 2: Interactive map + controls */}
      <div ref={mapRef}>
        <MapSection />
      </div>

      {/* Section 3: 3x3 grid + analytics */}
      <AnalyticsSection />
    </div>
  );
}

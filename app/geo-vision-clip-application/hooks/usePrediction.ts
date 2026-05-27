"use client";
import { useQuery } from "@tanstack/react-query";

interface PredictionParams {
  lat: number | null;
  lon: number | null;
  radiusKm: number;
  contaminant: string;
  horizon: string;
}

export function usePrediction({ lat, lon, radiusKm, contaminant, horizon }: PredictionParams) {
  return useQuery({
    queryKey: ["prediction", lat, lon, radiusKm, contaminant, horizon],
    queryFn: async () => {
      const res = await fetch("/api/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ lat, lon, radius_km: radiusKm, contaminant, horizon }),
      });
      if (!res.ok) throw new Error("Prediction failed");
      return res.json();
    },
    enabled: lat !== null && lon !== null,
    staleTime: 5 * 60 * 1000,
  });
}

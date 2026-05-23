"use client";

import { useQuery } from "@tanstack/react-query";
import { loadMcBarriosLayers } from "@/lib/geo/barrios";

export function useBarriosGeo(enabled = true) {
  return useQuery({
    queryKey: ["mc-barrios-geo"],
    queryFn: loadMcBarriosLayers,
    staleTime: Infinity,
    enabled,
  });
}

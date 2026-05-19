"use client";
import { useQuery } from "@tanstack/react-query";

export function useStations() {
  return useQuery({
    queryKey: ["stations"],
    queryFn: async () => {
      const res = await fetch("/api/stations");
      if (!res.ok) throw new Error("Failed to fetch stations");
      return res.json();
    },
    staleTime: 10 * 60 * 1000,
  });
}

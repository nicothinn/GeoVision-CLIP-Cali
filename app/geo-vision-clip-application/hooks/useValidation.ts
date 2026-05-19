"use client";
import { useQuery } from "@tanstack/react-query";

export function useValidation() {
  return useQuery({
    queryKey: ["validation"],
    queryFn: async () => {
      const res = await fetch("/api/validate");
      if (!res.ok) throw new Error("Failed to fetch validation data");
      return res.json();
    },
    staleTime: 30 * 60 * 1000,
  });
}

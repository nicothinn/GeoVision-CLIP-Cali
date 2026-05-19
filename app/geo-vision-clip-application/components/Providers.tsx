"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { useAppStore } from "@/store/appStore";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, staleTime: 5 * 60 * 1000 } },
});

function ThemeApplier({ children }: { children: React.ReactNode }) {
  const theme = useAppStore((s) => s.theme);

  useEffect(() => {
    const root = document.documentElement;
    if (theme === "dark") {
      root.classList.add("dark");
      root.style.backgroundColor = "#0f172a";
    } else {
      root.classList.remove("dark");
      root.style.backgroundColor = "#f8fafc";
    }
  }, [theme]);

  return <>{children}</>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => queryClient);
  return (
    <QueryClientProvider client={client}>
      <ThemeApplier>{children}</ThemeApplier>
    </QueryClientProvider>
  );
}

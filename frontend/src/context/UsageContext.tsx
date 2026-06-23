"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { getUsage } from "@/services/api";
import type { UsageQuota, UsageResponse } from "@/types/api";

type UsageContextValue = {
  usage: UsageResponse | null;
  isLoading: boolean;
  error: string | null;
  refreshUsage: () => Promise<void>;
  updateQuota: (quota: UsageQuota | null) => void;
};

const UsageContext = createContext<UsageContextValue | null>(null);

export function UsageProvider({ children }: { children: ReactNode }) {
  const [usage, setUsage] = useState<UsageResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refreshUsage = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      setUsage(await getUsage());
    } catch (refreshError) {
      setError(refreshError instanceof Error ? refreshError.message : "Usage information unavailable.");
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      void refreshUsage();
    }, 0);
    return () => window.clearTimeout(timer);
  }, [refreshUsage]);

  const updateQuota = useCallback(
    (quota: UsageQuota | null) => {
      if (!quota) {
        return;
      }
      if (!usage) {
        void refreshUsage();
        return;
      }
      setUsage((current) => (current ? { ...current, ...quota } : current));
    },
    [refreshUsage, usage],
  );

  const value = useMemo(
    () => ({ usage, isLoading, error, refreshUsage, updateQuota }),
    [error, isLoading, refreshUsage, updateQuota, usage],
  );

  return <UsageContext.Provider value={value}>{children}</UsageContext.Provider>;
}

export function useUsage() {
  const context = useContext(UsageContext);
  if (!context) {
    throw new Error("useUsage must be used within UsageProvider");
  }
  return context;
}

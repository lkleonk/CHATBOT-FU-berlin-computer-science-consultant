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

import { getDegrees } from "@/services/api";
import type { DegreeInfo } from "@/types/api";

export const DEGREE_STORAGE_KEY = "fu-consultant-degree";
export const DEFAULT_DEGREE_ID = "msc_informatik";

// Shown until GET /api/degrees answers; keep in sync with the backend registry.
const FALLBACK_DEGREES: DegreeInfo[] = [
  {
    id: DEFAULT_DEGREE_ID,
    display_name: "M.Sc. Informatik",
    regulation: "2014 Studien- und Pruefungsordnung",
  },
  {
    id: "msc_data_science",
    display_name: "M.Sc. Data Science",
    regulation: "2021 Studien- und Pruefungsordnung (FU-Mitteilungen 18/2021)",
  },
];

type DegreeContextValue = {
  /** Chosen degree id, or null until the user has picked one. */
  degreeId: string | null;
  /** Chosen degree id with the default applied; safe for API calls. */
  effectiveDegreeId: string;
  degrees: DegreeInfo[];
  degreesLoaded: boolean;
  selectDegree: (degreeId: string) => void;
};

const DegreeContext = createContext<DegreeContextValue | null>(null);

export function DegreeProvider({ children }: { children: ReactNode }) {
  const [degreeId, setDegreeId] = useState<string | null>(null);
  const [degrees, setDegrees] = useState<DegreeInfo[]>(FALLBACK_DEGREES);
  const [degreesLoaded, setDegreesLoaded] = useState(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      setDegreeId(window.localStorage.getItem(DEGREE_STORAGE_KEY));
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    let cancelled = false;
    const timer = window.setTimeout(async () => {
      try {
        const fetched = await getDegrees();
        if (!cancelled && fetched.length > 0) {
          setDegrees(fetched);
        }
      } catch {
        // Keep the fallback list; the backend list is only for display options.
      } finally {
        if (!cancelled) {
          setDegreesLoaded(true);
        }
      }
    }, 0);
    return () => {
      cancelled = true;
      window.clearTimeout(timer);
    };
  }, []);

  const selectDegree = useCallback((nextDegreeId: string) => {
    window.localStorage.setItem(DEGREE_STORAGE_KEY, nextDegreeId);
    setDegreeId(nextDegreeId);
  }, []);

  const value = useMemo(
    () => ({
      degreeId,
      effectiveDegreeId: degreeId ?? DEFAULT_DEGREE_ID,
      degrees,
      degreesLoaded,
      selectDegree,
    }),
    [degreeId, degrees, degreesLoaded, selectDegree],
  );

  return <DegreeContext.Provider value={value}>{children}</DegreeContext.Provider>;
}

export function useDegree() {
  const context = useContext(DegreeContext);
  if (!context) {
    throw new Error("useDegree must be used within DegreeProvider");
  }
  return context;
}

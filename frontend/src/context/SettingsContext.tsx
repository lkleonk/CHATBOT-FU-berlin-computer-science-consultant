"use client";

import { ThemeProvider } from "@mui/material/styles";
import {
  createContext,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";

import { createAppTheme } from "@/theme/theme";

type SettingsContextValue = {
  darkMode: boolean;
  toggleDarkMode: () => void;
};

const SettingsContext = createContext<SettingsContextValue | null>(null);
const DARK_MODE_STORAGE_KEY = "fu-consultant-dark-mode";

export function SettingsProvider({ children }: { children: ReactNode }) {
  const [darkMode, setDarkMode] = useState(false);
  const hasReadStoredSettings = useRef(false);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      const storedValue = window.localStorage.getItem(DARK_MODE_STORAGE_KEY);
      if (storedValue !== null) {
        setDarkMode(storedValue === "true");
      }
      hasReadStoredSettings.current = true;
    }, 0);

    return () => window.clearTimeout(timer);
  }, []);

  useEffect(() => {
    if (!hasReadStoredSettings.current) {
      return;
    }
    window.localStorage.setItem(DARK_MODE_STORAGE_KEY, String(darkMode));
  }, [darkMode]);

  const value = useMemo(
    () => ({
      darkMode,
      toggleDarkMode: () => setDarkMode((current) => !current),
    }),
    [darkMode],
  );

  const theme = useMemo(() => createAppTheme(darkMode), [darkMode]);

  return (
    <SettingsContext.Provider value={value}>
      <ThemeProvider theme={theme}>
        {children}
      </ThemeProvider>
    </SettingsContext.Provider>
  );
}

export function useSettings() {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error("useSettings must be used within SettingsProvider");
  }
  return context;
}

"use client";

import { createContext, useContext, useEffect, useState, type ReactNode } from "react";

export type Theme = "dark" | "light" | "midnight" | "oled";

const THEME_KEY = "medfree.theme";
const defaultTheme: Theme = "dark";

const ThemeContext = createContext<{ theme: Theme; setTheme: (t: Theme) => void }>({
  theme: defaultTheme,
  setTheme: () => {},
});

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(defaultTheme);

  useEffect(() => {
    const stored = (localStorage.getItem(THEME_KEY) as Theme) || defaultTheme;
    setThemeState(stored);
    document.documentElement.setAttribute("data-theme", stored);
  }, []);

  const setTheme = (t: Theme) => {
    setThemeState(t);
    localStorage.setItem(THEME_KEY, t);
    document.documentElement.setAttribute("data-theme", t);
  };

  return <ThemeContext.Provider value={{ theme, setTheme }}>{children}</ThemeContext.Provider>;
}

export const useTheme = () => useContext(ThemeContext);

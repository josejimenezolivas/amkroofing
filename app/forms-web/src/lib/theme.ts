import { useEffect, useState } from "react";

export type Theme = "light" | "dark";
export type ThemeChoice = Theme | "system";

const KEY = "amk-forms-theme-choice";
// Saved "dark" on every first visit back when dark was the default, so only "light" there was picked by hand.
const OLD_KEY = "amk-forms-theme";
const systemLight = matchMedia("(prefers-color-scheme: light)");

const stored = (): ThemeChoice => {
  const value = localStorage.getItem(KEY);
  if (value === "light" || value === "dark") return value;
  return value === null && localStorage.getItem(OLD_KEY) === "light" ? "light" : "system";
};

/** The theme the editor will open in, for painting the loading screen before it mounts. */
export function storedTheme(): Theme {
  const choice = stored();
  return choice === "system" ? (systemLight.matches ? "light" : "dark") : choice;
}

/** The editor's colour theme: the system's unless this browser picked light or dark. */
export function useTheme() {
  const [choice, setChoice] = useState(stored);
  const [prefersLight, setPrefersLight] = useState(systemLight.matches);

  useEffect(() => localStorage.setItem(KEY, choice), [choice]);

  useEffect(() => {
    const onChange = () => setPrefersLight(systemLight.matches);
    systemLight.addEventListener("change", onChange);
    return () => systemLight.removeEventListener("change", onChange);
  }, []);

  const theme: Theme = choice === "system" ? (prefersLight ? "light" : "dark") : choice;
  return { choice, setChoice, theme };
}

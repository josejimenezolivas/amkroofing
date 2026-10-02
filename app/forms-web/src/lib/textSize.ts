import { useEffect, useState } from "react";

export type TextSize = "system" | "standard" | "larger";

const KEY = "amk-forms-text-size";
const LARGER = 1.3;
/** From here up the chrome also gets bigger icons and tap targets, a wider sidebar, and a zoomed-in page on phones. */
const LARGE_FROM = 1.2;
/** Dynamic Type's accessibility sizes reach about 3x; the toolbar and sidebar stop fitting past this. */
const MAX = 1.75;

const stored = (): TextSize => {
  const value = localStorage.getItem(KEY);
  return value === "standard" || value === "larger" ? value : "system";
};

/**
 * The device's text size relative to its default. iOS reports Dynamic Type
 * through -apple-system-body (17px at the default size); Android's font scale
 * and desktop browsers' font-size setting come through `medium` (16px by
 * default), Android only with <meta name="text-scale"> in index.html.
 */
function systemScale(): number {
  const dynamicType = CSS.supports("font", "-apple-system-body") && matchMedia("(pointer: coarse)").matches;
  const probe = document.createElement("span");
  probe.style.cssText = `position:absolute;visibility:hidden;font:${dynamicType ? "-apple-system-body" : "medium sans-serif"}`;
  document.documentElement.append(probe);
  const px = parseFloat(getComputedStyle(probe).fontSize);
  probe.remove();
  return px / (dynamicType ? 17 : 16) || 1;
}

const scaleFor = (choice: TextSize, system: number): number => {
  const scale = choice === "standard" ? 1 : choice === "larger" ? Math.max(LARGER, system) : system;
  return Math.min(Math.max(scale, 1), MAX);
};

/** --text-scale multiplies every size in the chrome; `data-text="large"` switches on the bigger controls. */
const apply = (scale: number) => {
  const root = document.documentElement;
  root.style.setProperty("--text-scale", String(scale));
  if (scale >= LARGE_FROM) root.dataset.text = "large";
  else delete root.dataset.text;
};

// Before the first paint, so the sign-in page and the loading placeholder are already the right size.
apply(scaleFor(stored(), systemScale()));

/** Text size: the phone's own setting unless this browser picked Standard or Larger. */
export function useTextSize() {
  const [choice, setChoice] = useState(stored);
  const [system, setSystem] = useState(systemScale);

  useEffect(() => localStorage.setItem(KEY, choice), [choice]);

  useEffect(() => {
    // People change the phone's text size in Settings, with the browser in the background.
    const remeasure = () => setSystem(systemScale());
    document.addEventListener("visibilitychange", remeasure);
    addEventListener("resize", remeasure);
    return () => {
      document.removeEventListener("visibilitychange", remeasure);
      removeEventListener("resize", remeasure);
    };
  }, []);

  const scale = scaleFor(choice, system);
  useEffect(() => apply(scale), [scale]);

  return { choice, setChoice, large: scale >= LARGE_FROM };
}

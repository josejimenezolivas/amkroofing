import { useEffect, useState } from "react";

const KEY = "amk-forms-large-text";

const stored = (): boolean => localStorage.getItem(KEY) === "1";

/** `data-text="large"` on <html> sets --text-scale, which every size in the chrome is multiplied by. */
const apply = (large: boolean) => {
  if (large) document.documentElement.dataset.text = "large";
  else delete document.documentElement.dataset.text;
};

// Before the first paint, so the sign-in page and the loading placeholder are already large.
apply(stored());

/** Larger text for people who find the default sizes hard to read. Remembered per browser. */
export function useLargeText() {
  const [large, setLarge] = useState(stored);

  useEffect(() => {
    apply(large);
    if (large) localStorage.setItem(KEY, "1");
    else localStorage.removeItem(KEY);
  }, [large]);

  return { large, setLarge };
}

import { cx } from "../lib/cx";

export const NEW_DOCUMENT = "M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.4 2.6a2 2 0 0 1 2.8 2.8L12 14.6l-4 1 1-4Z";
export const MENU = "M4 7h16M4 12h16M4 17h16";

/** A 24px line icon drawn with the current text colour. */
export const Icon = ({ className, d }: { className?: string; d: string }) => (
  <svg className={cx("icon", className)} viewBox="0 0 24 24" aria-hidden="true">
    <path d={d} fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

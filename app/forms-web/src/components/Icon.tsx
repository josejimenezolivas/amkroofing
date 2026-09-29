import { cx } from "../lib/cx";

/** A 24px line icon drawn with the current text colour. */
export const Icon = ({ className, d }: { className?: string; d: string }) => (
  <svg className={cx("icon", className)} viewBox="0 0 24 24" aria-hidden="true">
    <path d={d} fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

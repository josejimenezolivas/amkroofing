import type { CSSProperties, ReactNode } from "react";

import { Field } from "../../components/fields";
import { LogoField } from "../../components/LogoField";
import { useDoc } from "../../lib/documentStore";
import { cx } from "../../lib/cx";

import "./modern.css";

/**
 * Margins the server applies when printing a modern document. Chromium's PDF
 * API only understands px/in/cm/mm, so these are inches: 0.75in is 54pt and
 * 0.85in is 61.2pt, matching `.msheet`'s on-screen padding.
 */
export const MODERN_MARGINS = { top: "0.75in", bottom: "0.75in", side: "0.85in" };

export function Letterhead() {
  return (
    <header className="m-head">
      <div className="m-head__brand">
        <LogoField className="m-head__logo" alt="AMK Roofing &amp; Waterproofing" />
        <div>
          <div className="m-head__name">
            <Field name="company_name" />
          </div>
          <div className="m-small">
            License <Field name="company_license" />
          </div>
        </div>
      </div>

      <address className="m-head__contact">
        <Field name="company_street" />
        <br />
        <Field name="company_city" />
        <br />
        <Field name="company_phone" />
        <br />
        <Field name="company_cell" />
        <br />
        <Field name="company_email" />
      </address>
    </header>
  );
}

export function Section({
  title,
  aside,
  className,
  children,
}: {
  title: string;
  aside?: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  return (
    <section className={cx("m-section", className)}>
      <div className="m-section__head">
        <h2 className="m-section__title">{title}</h2>
        {aside && <span className="m-eyebrow">{aside}</span>}
      </div>
      {children}
    </section>
  );
}

/** A labelled value. `field` makes it editable; `children` keeps it static. */
export function Def({
  label,
  field,
  placeholder,
  strong,
  children,
  style,
}: {
  label: string;
  field?: string;
  placeholder?: string;
  strong?: boolean;
  children?: ReactNode;
  style?: CSSProperties;
}) {
  return (
    <div style={style}>
      <div className="m-eyebrow m-def__label">{label}</div>
      <div className={cx("m-def__value", strong && "m-def__value--strong")}>
        {field ? <Field name={field} placeholder={placeholder} variant="block" /> : children}
      </div>
    </div>
  );
}

/** Checkbox rendered as a selectable pill rather than a ruled square. */
export function Pill({ name, label }: { name: string; label: string }) {
  const { data, toggleCheck, readOnly } = useDoc();
  const on = Boolean(data.checks[name]);
  return (
    <button
      type="button"
      className={cx("m-pill", on && "m-pill--on")}
      aria-pressed={on}
      disabled={readOnly}
      onClick={() => toggleCheck(name)}
    >
      {label}
    </button>
  );
}

export function Footer({ label }: { label: string }) {
  return (
    <footer className="m-foot">
      <span>
        <Field name="company_name" variant="flow" /> &middot; License{" "}
        <Field name="company_license" variant="flow" />
      </span>
      <span>{label}</span>
    </footer>
  );
}

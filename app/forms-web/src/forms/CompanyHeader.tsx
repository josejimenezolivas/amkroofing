import { Field } from "../components/fields";
import { LogoField } from "../components/LogoField";

/**
 * The AMK letterhead. Both forms use an identical block; only its vertical
 * offset differs, so every part is placed relative to the "AMK ROOFING" line.
 */
export function CompanyHeader({ top, logoLeft = 35 }: { top: number; logoLeft?: number }) {
  const at = (delta: number) => `${top + delta}pt`;

  return (
    <>
      <LogoField
        className="letterhead__logo"
        alt="AMK Roofing &amp; Waterproofing"
        style={{ left: `${logoLeft}pt`, top: at(-3.8) }}
      />

      <div className="letterhead__name arial" style={{ top: at(0) }}>
        <Field name="company_name" />
      </div>

      <div className="letterhead__line bold" style={{ top: at(18.6) }}>
        License&nbsp;&nbsp;<Field name="company_license" />
      </div>

      <div className="letterhead__line" style={{ top: at(31.1) }}>
        <Field name="company_street" />
      </div>

      <div className="letterhead__line" style={{ top: at(43.6) }}>
        <Field name="company_city" />
      </div>

      <div className="letterhead__line bold" style={{ top: at(56.1) }}>
        <Field name="company_phone" />
        &nbsp;&nbsp;
        <Field name="company_cell" />
      </div>

      <div className="letterhead__email" style={{ top: at(51.0) }}>
        <Field name="company_email" />
      </div>
    </>
  );
}

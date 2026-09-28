import type { ReactNode } from "react";

import { Field } from "../components/fields";

/**
 * The boxed NAME / ADDRESS / ALTERNATE ADDRESS grid. Both forms use the same
 * ruling, so only the y offset and the label in the left gutter change.
 */
export function PartyTable({
  top,
  gutter,
  addressLabel,
  nameField,
  prefix,
}: {
  /** y of the table's top rule, from the source PDF. */
  top: number;
  gutter: ReactNode;
  addressLabel: string;
  nameField: string;
  /** Field-name prefix, e.g. "project" -> project_address, project_city ... */
  prefix: string;
}) {
  const at = (delta: number) => `${top + delta}pt`;
  const rule = (delta: number, left: number, width: number) => (
    <div
      className="rule"
      style={{ top: `${top + delta - 0.5}pt`, left: `${left}pt`, width: `${width}pt` }}
    />
  );

  return (
    <>
      {rule(0, 30.6, 550.8)}
      {rule(24.8, 91.2, 490.2)}
      {rule(49.2, 91.2, 490.2)}
      {rule(73.9, 30.6, 550.8)}
      <div
        className="vrule"
        style={{ left: "90.8pt", top: at(-0.5), height: "73.9pt" }}
      />
      <div
        className="vrule"
        style={{ left: "508.5pt", top: at(24.3), height: "49.1pt" }}
      />

      {gutter}

      <div className="party__label" style={{ left: "96.2pt", top: at(2.2) }}>
        NAME
      </div>
      <div className="party__name" style={{ left: "100.7pt", top: at(13.6) }}>
        <Field name={nameField} placeholder="Client name" />
      </div>

      <div className="party__label" style={{ left: "96.2pt", top: at(26.3) }}>
        {addressLabel}
      </div>
      <div className="party__label" style={{ left: "344.5pt", top: at(26.3) }}>
        CITY
      </div>
      <div className="party__label" style={{ left: "455.4pt", top: at(26.3) }}>
        STATE/ZIP
      </div>
      <div className="party__label" style={{ left: "513.9pt", top: at(26.3) }}>
        PHONE
      </div>

      <div className="party__value" style={{ left: "96.2pt", top: at(37.7) }}>
        <Field name={`${prefix}_address`} placeholder="Street address" />
      </div>
      <div className="party__value" style={{ left: "344.5pt", top: at(37.7) }}>
        <Field name={`${prefix}_city`} placeholder="City" />
      </div>
      <div className="party__value" style={{ left: "455.4pt", top: at(37.7) }}>
        <Field name={`${prefix}_state_zip`} placeholder="State/ZIP" />
      </div>
      <div className="party__value" style={{ left: "513.9pt", top: at(37.7) }}>
        <Field name={`${prefix}_phone`} placeholder="Phone" />
      </div>

      <div className="party__label" style={{ left: "96.2pt", top: at(50.7) }}>
        ALTERNATE ADDRESS<i>&nbsp;(IF ANY)</i>
      </div>
      <div className="party__label" style={{ left: "344.5pt", top: at(50.7) }}>
        CITY
      </div>
      <div className="party__label" style={{ left: "455.4pt", top: at(50.7) }}>
        STATE/ZIP
      </div>
      <div className="party__label" style={{ left: "513.9pt", top: at(50.7) }}>
        PHONE
      </div>

      <div className="party__value" style={{ left: "96.2pt", top: at(62.1) }}>
        <Field name="alt_address" placeholder="Alternate address" />
      </div>
      <div className="party__value" style={{ left: "344.5pt", top: at(62.1) }}>
        <Field name="alt_city" placeholder="City" />
      </div>
      <div className="party__value" style={{ left: "455.4pt", top: at(62.1) }}>
        <Field name="alt_state_zip" placeholder="State/ZIP" />
      </div>
      <div className="party__value" style={{ left: "513.9pt", top: at(62.1) }}>
        <Field name="alt_phone" placeholder="Phone" />
      </div>
    </>
  );
}

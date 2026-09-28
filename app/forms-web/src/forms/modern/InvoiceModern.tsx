import { Cell, Field, RowTools } from "../../components/fields";
import { useDoc } from "../../lib/documentStore";
import { Def, Footer, Letterhead, Pill, Section } from "./parts";

import "./modern.css";

const PAYMENT_OPTIONS: Array<[name: string, label: string]> = [
  ["down_payment", "Down payment"],
  ["progress_payment", "Progress payment"],
  ["final_payment", "Final payment"],
];

const TOTALS: Array<[field: string, label: string]> = [
  ["subtotal", "Subtotal"],
  ["scheduled_payment", "Scheduled payment"],
  ["less_credits", "Less any credits"],
];

/**
 * The invoice, redesigned. Same data as the classic sheet, but it leads with
 * the one number the reader is looking for and lets whitespace do the ruling
 * that the original did with boxes.
 */
export function InvoiceModern() {
  const { rows } = useDoc();

  return (
    <article className="msheet">
      <Letterhead />

      <div style={{ marginTop: "46pt" }}>
        <div className="m-eyebrow">
          <Field name="doc_title" variant="flow" />
        </div>
        <h1 className="m-display" style={{ marginTop: "6pt" }}>
          <Field name="grand_total" placeholder="$0.00" variant="flow" />
        </h1>
        <p className="m-lede" style={{ marginTop: "8pt" }}>
          Total due &middot; Invoice{" "}
          <Field name="invoice_number" placeholder="0000-0000" variant="flow" /> &middot;{" "}
          <Field name="invoice_date" placeholder="Month, Year" variant="flow" />
        </p>
      </div>

      <div className="m-grid m-grid--3" style={{ marginTop: "30pt" }}>
        <Def label="Billed to">
          <Field name="client_name" placeholder="Client name" variant="block" />
          <Field name="project_address" placeholder="Street" variant="block" />
          <span>
            <Field name="project_city" placeholder="City" variant="flow" />{" "}
            <Field name="project_state_zip" placeholder="State ZIP" variant="flow" />
          </span>
          <div className="m-small">
            <Field name="project_phone" placeholder="Phone" variant="flow" />
          </div>
        </Def>

        <Def label="Job">
          <Field name="job_id" placeholder="Job ID" variant="block" />
          <Field name="job_location" placeholder="Location" variant="block" />
        </Def>

        <Def label="Alternate address">
          <Field name="alt_address" placeholder="Street" variant="block" />
          <span>
            <Field name="alt_city" placeholder="City" variant="flow" />{" "}
            <Field name="alt_state_zip" placeholder="State ZIP" variant="flow" />
          </span>
          <div className="m-small">
            <Field name="alt_phone" placeholder="Phone" variant="flow" />
          </div>
        </Def>
      </div>

      <Section title="Scope of work">
        <ol className="m-items">
          {rows("scope").map((_, i) => (
            <li className="m-items__row row" key={i}>
              <RowTools list="scope" index={i} />
              <span className="m-items__num" />
              <span className="m-items__text">
                <Cell
                  list="scope"
                  index={i}
                  field="text"
                  variant="block"
                  multiline
                  placeholder="Describe the work…"
                />
              </span>
            </li>
          ))}
        </ol>
      </Section>

      <Section title="Summary">
        <div className="m-rows">
          {rows("summary").map((_, i) => (
            <div className="m-rows__row row" key={i}>
              <RowTools list="summary" index={i} />
              <span className="m-rows__label">
                <Cell list="summary" index={i} field="label" placeholder="Item" variant="block" />
              </span>
              <span className="m-rows__amount">
                <Cell list="summary" index={i} field="amount" placeholder="$0.00" variant="block" />
              </span>
            </div>
          ))}

          {TOTALS.map(([field, label]) => (
            <div className="m-rows__row m-rows__row--quiet" key={field}>
              <span className="m-rows__label">{label}</span>
              <span className="m-rows__amount">
                <Field name={field} placeholder="$0.00" variant="block" />
              </span>
            </div>
          ))}

          <div className="m-rows__row m-rows__row--total">
            <span className="m-rows__label">Total</span>
            <span className="m-rows__amount">
              <Field name="grand_total" placeholder="$0.00" variant="block" />
            </span>
          </div>
        </div>
      </Section>

      <Section title="Payment">
        <div className="m-pills">
          {PAYMENT_OPTIONS.map(([name, label]) => (
            <Pill key={name} name={name} label={label} />
          ))}
        </div>
        <div className="m-grid m-grid--2" style={{ marginTop: "14pt" }}>
          <Def label="Terms" field="terms" placeholder="e.g. Net 30" />
          <Def label="Warranty">
            <Field name="warranty_prefix" variant="flow" />{" "}
            <Field name="warranty" variant="flow" />
          </Def>
        </div>
      </Section>

      <p className="m-headline" style={{ marginTop: "34pt" }}>
        <Field name="closing" variant="flow" />
      </p>

      <Footer label="Invoice" />
    </article>
  );
}

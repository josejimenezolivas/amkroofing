import { Cell, CheckBox, Field, RowTools } from "../components/fields";
import { useDoc } from "../lib/documentStore";
import { cx } from "../lib/cx";
import { CompanyHeader } from "./CompanyHeader";
import { PartyTable } from "./PartyTable";
import { ScopeList } from "./ScopeList";

import "./letterhead.css";
import "./party.css";
import "./bullets.css";
import "./invoice.css";

const PAYMENT_OPTIONS: Array<[name: string, label: string, box: number, text: number]> = [
  ["down_payment", "Down Payment", 36.9, 60.1],
  ["progress_payment", "Progress Payment", 140.6, 162.8],
  ["final_payment", "Final Payment", 249.5, 271.6],
];

const TOTAL_ROWS: Array<[field: string, label: string, align: "left" | "right"]> = [
  ["subtotal", "SUBTOTAL:", "right"],
  ["scheduled_payment", "SCHEDULED PAYMENT:", "left"],
  ["less_credits", "LESS ANY CREDITS:", "left"],
  ["grand_total", "TOTAL GRAND PRICE", "left"],
];

export function InvoiceForm() {
  const { rows } = useDoc();
  const summary = rows("summary");

  return (
    <section className="sheet inv" data-page="1">
      <div className="sheet__frame" />

      <div className="inv__title">
        <Field name="doc_title" />
      </div>
      <div className="inv__compliance">
        <Field name="compliance" />
      </div>
      <div className="rule" style={{ left: "30.6pt", top: "78.6pt", width: "550.8pt" }} />

      <CompanyHeader top={81.8} />

      <div className="inv__meta">
        <div>
          Invoice #:<Field name="invoice_number" placeholder="0000-0000" />
        </div>
        <div>
          Date <Field name="invoice_date" placeholder="Month, Year" />
        </div>
        <div>
          Job ID:<Field name="job_id" placeholder="Job ID" />
        </div>
        <div>
          Job Location:<Field name="job_location" placeholder="Location" />
        </div>
      </div>

      <PartyTable
        top={198.6}
        prefix="project"
        nameField="client_name"
        addressLabel="PROJECT ADDRESS"
        gutter={
          <div className="party__gutter" style={{ left: "51.8pt", top: "212.2pt" }}>
            TO:
          </div>
        }
      />

      {PAYMENT_OPTIONS.map(([name, label, box, text]) => (
        <span key={name}>
          <CheckBox name={name} className="inv__checkbox" style={{ left: `${box}pt` }} />
          <span className="inv__pay-label" style={{ left: `${text}pt` }}>
            {label}
          </span>
        </span>
      ))}
      <span className="inv__pay-label" style={{ left: "368.6pt" }}>
        Terms:
      </span>
      <div className="inv__terms">
        <Field name="terms" variant="block" placeholder="Payment terms" />
      </div>
      <div className="rule" style={{ left: "402.1pt", top: "293.3pt", width: "179.3pt" }} />
      <div className="rule" style={{ left: "30.6pt", top: "301pt", width: "550.8pt" }} />

      <div className="inv__body">
        <ScopeList />

        <div className="inv__warranty">
          <span className="inv__warranty-prefix">
            <Field name="warranty_prefix" />
          </span>
          <Field name="warranty" placeholder="e.g. 1 yr workmanship warranty" />
        </div>

        <div className="inv-sum">
          <div className="inv-sum__stub" />
          <div className="inv-sum__head">
            <Field name="summary_heading" />
          </div>

          {summary.map((row, i) => (
            <div
              key={i}
              className={cx("inv-sum__row", "row", i === 0 && "inv-sum__row--tall")}
            >
              <RowTools list="summary" index={i} />
              <div
                className={cx(
                  "inv-sum__label",
                  row.align === "right"
                    ? "inv-sum__label--right"
                    : "inv-sum__label--left",
                )}
              >
                <Cell list="summary" index={i} field="label" variant="block" placeholder="Item" />
              </div>
              <div className="inv-sum__divider" />
              <div className="inv-sum__amount">
                <Cell list="summary" index={i} field="amount" variant="block" placeholder="$0.00" />
              </div>
            </div>
          ))}

          {TOTAL_ROWS.map(([field, label, align], i) => (
            <div
              key={field}
              className={cx(
                "inv-sum__row",
                i === TOTAL_ROWS.length - 1 && "inv-sum__row--last",
              )}
            >
              <div
                className={cx(
                  "inv-sum__label",
                  align === "right" ? "inv-sum__label--right" : "inv-sum__label--left",
                )}
              >
                {label}
              </div>
              <div className="inv-sum__divider" />
              <div className="inv-sum__amount">
                <Field name={field} variant="block" />
              </div>
            </div>
          ))}
        </div>

        <div className="inv__footer">
          <div className="inv__thanks">
            <Field name="closing" />
          </div>
          <div className="inv__thanks-rule" />
        </div>
      </div>
    </section>
  );
}

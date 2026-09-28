import { Cell, Field, RowTools } from "../../components/fields";
import { SignatureField } from "../../components/SignatureField";
import { useDoc } from "../../lib/documentStore";
import { LEGAL } from "../legalProse";
import { Def, Footer, Letterhead, Pill, Section } from "./parts";
import { TERMS_BLOCKS } from "./termsProse";

import "./modern.css";

/**
 * The agreement, redesigned. The contract's substance is unchanged -- every
 * clause the original carries is still here, drawn from the same
 * `legalProse` and `termsLines` sources the classic pages use.
 */
export function AgreementModern() {
  return (
    <article className="msheet">
      <Cover />
      <Work />
      <Money />
      <Notices />
      <Signatures />
      <Terms />
      <Footer label="Residential roofing agreement" />
    </article>
  );
}

function Cover() {
  return (
    <>
      <Letterhead />

      <div style={{ marginTop: "54pt" }}>
        <div className="m-eyebrow">
          <Field name="doc_title_line1" variant="flow" />{" "}
          <Field name="doc_title_line2" variant="flow" />
        </div>
        <h1 className="m-display" style={{ marginTop: "6pt" }}>
          <Field name="price_amount" placeholder="$0.00" variant="flow" />
        </h1>
        <p className="m-lede" style={{ marginTop: "8pt" }}>
          Prepared for <Field name="buyer_name" placeholder="Owner" variant="flow" /> &middot;{" "}
          <Field name="agreement_date" placeholder="Month Year" variant="flow" />
        </p>
      </div>

      <div className="m-grid m-grid--3" style={{ marginTop: "30pt" }}>
        <Def label="Owner / buyer">
          <Field name="buyer_name" placeholder="Name" variant="block" />
          <Field name="buyer_address" placeholder="Street" variant="block" />
          <span>
            <Field name="buyer_city" placeholder="City" variant="flow" />{" "}
            <Field name="buyer_state_zip" placeholder="State ZIP" variant="flow" />
          </span>
          <div className="m-small">
            <Field name="buyer_phone" placeholder="Phone" variant="flow" />
          </div>
        </Def>

        <Def label="Project address">
          <Field name="project_address" placeholder="Street" variant="block" />
          <span>
            <Field name="project_city" placeholder="City" variant="flow" />{" "}
            <Field name="project_state" placeholder="State" variant="flow" />{" "}
            <Field name="project_zip" placeholder="ZIP" variant="flow" />
          </span>
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

      <p className="m-p m-dim" style={{ marginTop: "26pt" }}>
        {LEGAL.hereinafter}
      </p>

      <div className="m-panel">
        <div className="m-eyebrow m-panel__title">Legal description</div>
        <p className="m-legal">
          Lot # <Field name="legal_lot" variant="flow" placeholder="—" /> &middot; Tract #{" "}
          <Field name="legal_tract" variant="flow" placeholder="—" /> &middot; Block #{" "}
          <Field name="legal_block" variant="flow" placeholder="—" />
        </p>
        <p className="m-legal">
          Recorded in Book # <Field name="legal_book" variant="flow" placeholder="—" /> &middot;
          Page # <Field name="legal_page" variant="flow" placeholder="—" /> in the office of the
          County Recorder of <Field name="legal_recorder" variant="flow" placeholder="—" />{" "}
          <Field name="legal_state" variant="flow" />
        </p>
      </div>

      <p className="m-small" style={{ marginTop: "20pt" }}>
        <Field name="compliance" variant="flow" /> &middot; {LEGAL.intro}
      </p>
    </>
  );
}

function Work() {
  const { rows } = useDoc();

  return (
    <div className="m-break">
      <Section title="Scope of work" aside="Materials and equipment">
        <ol className="m-items">
          {rows("scope").map((row, i) => (
            <li className="m-items__row row" key={i}>
              <RowTools list="scope" index={i} />
              <span className="m-items__num" />
              <span
                className={
                  row.style === "bullet-bold" ? "m-items__text m-items__text--lead" : "m-items__text"
                }
              >
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

        <div className="m-panel m-panel--accent">
          <div className="m-eyebrow m-panel__title">Warranty</div>
          <div>
            <Field name="warranty_prefix" variant="flow" /> <Field name="warranty" variant="flow" />
          </div>
        </div>

        <div className="m-pills">
          <Pill name="space_insufficient" label={LEGAL.spaceInsufficient} />
          <Pill name="plans_attached" label={LEGAL.plansAttached} />
        </div>
        <p className="m-legal" style={{ marginTop: "8pt" }}>
          {LEGAL.plansIncorporated}
        </p>
      </Section>

      <Section title="Not included">
        <p className="m-p" style={{ marginTop: "10pt" }}>
          {LEGAL.notIncluded} <Field name="not_included" variant="flow" />
        </p>
      </Section>

      <Section title="Allowances">
        <p className="m-legal" style={{ marginTop: "10pt" }}>
          {LEGAL.allowances}
        </p>

        <table className="m-table">
          <thead>
            <tr>
              <th>Item</th>
              <th>Amount</th>
              <th>Item</th>
              <th>Amount</th>
            </tr>
          </thead>
          <tbody>
            {rows("allowances").map((_, i) => (
              <tr className="row" key={i}>
                <td>
                  <RowTools list="allowances" index={i} />
                  <Cell list="allowances" index={i} field="desc1" placeholder="Item" />
                </td>
                <td>
                  $<Cell list="allowances" index={i} field="amt1" placeholder="0.00" />
                </td>
                <td>
                  <Cell list="allowances" index={i} field="desc2" placeholder="Item" />
                </td>
                <td>
                  $<Cell list="allowances" index={i} field="amt2" placeholder="0.00" />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        <div style={{ marginTop: "12pt" }}>
          <div className="m-eyebrow m-def__label">Additional notes</div>
          <Field name="allowance_notes" variant="block" placeholder="Notes" />
        </div>
      </Section>
    </div>
  );
}

function Money() {
  return (
    <div>
      <Section title="Schedule">
        <div className="m-grid m-grid--2">
          <Def label="Work commences within">
            <Field name="start_days" placeholder="—" variant="flow" /> days, approximately{" "}
            <Field name="start_date" placeholder="date" variant="flow" />
          </Def>
          <Def label="Substantially complete within">
            <Field name="complete_days" placeholder="—" variant="flow" /> days, approximately{" "}
            <Field name="complete_date" placeholder="date" variant="flow" />
          </Def>
        </div>
      </Section>

      <Section title="Contract price">
        <div className="m-grid m-grid--2">
          <Def label="Total price" strong field="price_amount" placeholder="$0.00" />
          <Def label="Down payment" strong field="down_payment" placeholder="$0.00" />
        </div>
        <p className="m-p" style={{ marginTop: "14pt" }}>
          Owner agrees to pay Contractor a total price of{" "}
          <Field name="price_words" variant="flow" placeholder="amount in words" /> Dollars.
        </p>
        <p className="m-legal" style={{ marginTop: "8pt" }}>
          <strong>{LEGAL.downPaymentCap}</strong>
        </p>
      </Section>

      <Section title="Progress payments">
        <div className="m-panel">
          <Field name="progress_schedule" variant="block" multiline placeholder="Schedule" />
        </div>
        <p className="m-legal" style={{ marginTop: "12pt" }}>
          <strong>{LEGAL.scheduleMustDescribe}</strong>
        </p>
        <p className="m-legal">{LEGAL.lienRelease}</p>
        <p className="m-legal">{LEGAL.paymentTiming}</p>
        <p className="m-legal">
          <strong>{LEGAL.againstTheLaw.join(" ")}</strong>
        </p>
        <p className="m-legal">{LEGAL.changeOrders}</p>
        <p className="m-legal">{LEGAL.escrow}</p>
      </Section>
    </div>
  );
}

function Notices() {
  return (
    <Section title="Before you sign">
      <p className="m-p" style={{ marginTop: "12pt" }}>
        <strong>{LEGAL.doNotSign.join(" ")}</strong>
      </p>
      <p className="m-legal" style={{ marginTop: "10pt" }}>
        {LEGAL.entireAgreement}
      </p>
      <p className="m-legal">{LEGAL.licenseBoard}</p>
      <p className="m-legal">{LEGAL.performanceBond}</p>
      <p className="m-legal">{LEGAL.incorporatedDocuments}</p>
      <p className="m-legal">
        <strong>{LEGAL.entitledToCopy}</strong>
      </p>
      <p className="m-legal">
        <strong>{LEGAL.rightToCancel.slice(0, 2).join(" ")}</strong>
      </p>
      <div className="m-pills">
        <Pill name="right_to_cancel" label={LEGAL.rightToCancel[2]} />
      </div>
    </Section>
  );
}

function Signatures() {
  return (
    <Section title="Signatures" className="m-section--keep">
      <p className="m-legal" style={{ marginTop: "10pt" }}>
        This agreement consists of <Field name="consists_of_pages" variant="flow" placeholder="—" />{" "}
        pages and <Field name="consists_of_attachments" variant="flow" placeholder="—" />{" "}
        attachments.
      </p>

      <div className="m-signs">
        <SignatureSlot name="owner_1" caption="Owner / buyer" date="owner_sig_date_1" />
        <SignatureSlot name="owner_2" caption="Owner / buyer" date="owner_sig_date_2" />
        <SignatureSlot name="contractor" caption="Contractor" />
      </div>
    </Section>
  );
}

function SignatureSlot({
  name,
  caption,
  date,
}: {
  name: string;
  caption: string;
  date?: string;
}) {
  return (
    <div>
      <div className="m-sign__line">
        <span className="m-sign__x">&times;</span>
        <SignatureField name={name} width={180} height={26} label={`${caption} signature`} />
      </div>
      <div className="m-sign__caption m-eyebrow">
        <span>{caption}</span>
        {date && <Field name={date} variant="flow" placeholder="date" />}
      </div>
    </div>
  );
}

function Terms() {
  return (
    <Section title="Terms and conditions" className="m-break" aside="Incorporated into this agreement">
      <div className="m-terms">
        {TERMS_BLOCKS.map((block, i) =>
          block.heading ? (
            <h3 className="m-terms__heading" key={i}>
              {block.text}
            </h3>
          ) : (
            <p className="m-terms__p" key={i}>
              {block.text}
            </p>
          ),
        )}
      </div>
    </Section>
  );
}

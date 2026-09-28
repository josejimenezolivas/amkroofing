import { Cell, CheckBox, Field, RowTools } from "../components/fields";
import { SignatureField } from "../components/SignatureField";
import { useDoc } from "../lib/documentStore";
import { CompanyHeader } from "./CompanyHeader";
import { PageFooter } from "./PageFooter";
import { PartyTable } from "./PartyTable";
import { ScopeList } from "./ScopeList";
import { LEGAL } from "./legalProse";
import { TermsPages } from "./TermsPages";

import "./letterhead.css";
import "./party.css";
import "./bullets.css";
import "./agreement.css";

/** Renders hand-set lines with the original's line breaks intact. */
function Lines({ of }: { of: readonly string[] }) {
  return (
    <>
      {of.map((line, i) => (
        <span key={i}>
          {i > 0 && <br />}
          {line}
        </span>
      ))}
    </>
  );
}

export function AgreementForm() {
  return (
    <>
      <PageOne />
      <PageTwo />
      <PageThree />
      <TermsPages />
    </>
  );
}

/* ------------------------------------------------------------------ page 1 */

function PageOne() {
  const { rows } = useDoc();

  return (
    <section className="sheet" data-page="1">
      <div className="sheet__frame" />

      <div className="agr__title">
        <Field name="doc_title_line1" />
        <br />
        <Field name="doc_title_line2" />
      </div>
      <div className="agr__compliance">
        <Field name="compliance" />
      </div>

      <p className="agr__intro">{LEGAL.intro}</p>

      <div className="rule" style={{ left: "30.6pt", top: "108pt", width: "550.8pt" }} />
      <div className="agr__banner" style={{ top: "115.8pt" }}>
        THIS AGREEMENT IS BETWEEN
      </div>
      <div className="rule" style={{ left: "30.6pt", top: "130pt", width: "550.8pt" }} />

      <CompanyHeader top={133.2} logoLeft={37.5} />

      <div className="agr__entered">
        <div>THIS AGREEMENT IS ENTERED INTO</div>
        <div>
          THIS DATE:
          <Field name="agreement_date" placeholder="Month Year" />
        </div>
      </div>

      <PartyTable
        top={225}
        prefix="buyer"
        nameField="buyer_name"
        addressLabel="ADDRESS"
        gutter={
          <>
            <div
              className="arial"
              style={{
                position: "absolute",
                left: "38.8pt",
                top: "239.4pt",
                fontSize: "10pt",
              }}
            >
              and
            </div>
            <div className="party__gutter" style={{ left: "36pt", top: "251.4pt", fontSize: "9pt" }}>
              BUYER/
            </div>
            <div className="party__gutter" style={{ left: "36pt", top: "261.7pt", fontSize: "9pt" }}>
              OWNER
            </div>
          </>
        }
      />

      <div className="agr__hereinafter">{LEGAL.hereinafter}</div>

      <div className="rule" style={{ left: "30.6pt", top: "312.3pt", width: "549.9pt" }} />
      <div className="agr__banner" style={{ top: "314.3pt" }}>
        ROOFING PROJECT
      </div>
      <div className="rule" style={{ left: "30.6pt", top: "326.5pt", width: "549.9pt" }} />

      <div className="agr__proj-label" style={{ left: "36pt" }}>
        PROJECT ADDRESS - STREET
      </div>
      <div className="agr__proj-label" style={{ left: "279.9pt" }}>
        CITY
      </div>
      <div className="agr__proj-label" style={{ left: "369.9pt" }}>
        STATE
      </div>
      <div className="agr__proj-label" style={{ left: "491.4pt" }}>
        ZIP CODE
      </div>
      <div className="agr__proj-value" style={{ left: "46pt" }}>
        <Field name="project_address" placeholder="Street" />
      </div>
      <div className="agr__proj-value" style={{ left: "279.9pt" }}>
        <Field name="project_city" placeholder="City" />
      </div>
      <div className="agr__proj-value" style={{ left: "369.9pt" }}>
        <Field name="project_state" placeholder="State" />
      </div>
      <div className="agr__proj-value" style={{ left: "491.4pt" }}>
        <Field name="project_zip" placeholder="ZIP" />
      </div>

      <div className="rule" style={{ left: "30.6pt", top: "352.3pt", width: "549.9pt" }} />

      <div className="agr__legal">
        <div>
          Also Known as Legal Description; Lot #
          <Field name="legal_lot" className="blank" placeholder="—" />
          Tract #
          <Field name="legal_tract" className="blank" style={{ width: "32.5pt" }} placeholder="—" />
          Block #
          <Field name="legal_block" className="blank" placeholder="—" />
        </div>
        <div>
          Recorded in Book #
          <Field name="legal_book" className="blank" placeholder="—" />
          Page #
          <Field name="legal_page" className="blank" placeholder="—" />
          in the office of the County Recorder of
          <Field name="legal_recorder" className="blank" placeholder="County" />
          <Field name="legal_state" />
        </div>
      </div>

      <div className="rule" style={{ left: "30.6pt", top: "388.3pt", width: "550.8pt" }} />

      <div className="agr__body">
        <ScopeList />

        <div className="agr__warranty">
          <span className="agr__warranty-prefix">
            <Field name="warranty_prefix" />
          </span>
          <Field name="warranty" placeholder="e.g. 5 yrs workmanship warranty" />
        </div>

        <div className="agr__checks">
          <CheckBox name="space_insufficient" style={{ top: "2.5pt" }} />
          {LEGAL.spaceInsufficient}
        </div>
        <div className="agr__checks agr__checks-second">
          <CheckBox name="plans_attached" style={{ top: "2.5pt" }} />
          {LEGAL.plansAttached}
          <br />
          {LEGAL.plansIncorporated}
        </div>

        <div className="agr__rule-flow" />

        <div className="agr__notincluded">
          <b>NOT INCLUDED:</b> {LEGAL.notIncluded}{" "}
          <Field name="not_included" variant="flow" placeholder="items the owner provides" />
        </div>

        <div className="agr__allowances-text">
          <b>ALLOWANCES:</b> {LEGAL.allowances}
        </div>

        <div className="agr-allow">
          {rows("allowances").map((_, i) => (
            <div className="agr-allow__row row" key={i}>
              <RowTools list="allowances" index={i} />
              <div className="agr-allow__cell agr-allow__cell--desc">
                <Cell list="allowances" index={i} field="desc1" placeholder="Item" />
              </div>
              <div className="agr-allow__divider" />
              <div className="agr-allow__cell agr-allow__cell--amt">
                $<Cell list="allowances" index={i} field="amt1" placeholder="0.00" />
              </div>
              <div className="agr-allow__divider" />
              <div className="agr-allow__cell agr-allow__cell--desc">
                <Cell list="allowances" index={i} field="desc2" placeholder="Item" />
              </div>
              <div className="agr-allow__divider" />
              <div className="agr-allow__cell agr-allow__cell--amt">
                $<Cell list="allowances" index={i} field="amt2" placeholder="0.00" />
              </div>
              <div className="agr-allow__divider" />
              <div className="agr-allow__cell agr-allow__cell--desc">
                <Cell list="allowances" index={i} field="desc3" placeholder="Item" />
              </div>
              <div className="agr-allow__divider" />
              <div className="agr-allow__cell agr-allow__cell--amt-last">
                $<Cell list="allowances" index={i} field="amt3" placeholder="0.00" />
              </div>
            </div>
          ))}
        </div>

        <div className="agr__notes">
          ADDITIONAL ALLOWANCES NOTES: &lt;
          <Field name="allowance_notes" variant="flow" className="agr__notes-value" placeholder="notes" /> &gt;
        </div>
      </div>

      <PageFooter high />
    </section>
  );
}

/* ------------------------------------------------------------------ page 2 */

function PageTwo() {
  return (
    <section className="sheet" data-page="2">
      <div className="sheet__frame" />
      <div className="rule" style={{ left: "30.6pt", top: "47.5pt", width: "550.8pt" }} />

      <div className="agr-p2__time">
        <b>TIME FOR STARTING AND COMPLETION:</b> The work to be performed by Contractor pursuant to
        this Agreement shall be commenced within{" "}
        <Field name="start_days" className="agr-p2__blank" placeholder="days" /> (
        <Field name="start_days_num" className="agr-p2__blank" placeholder="#" />) days from this date or
        approximately on (Date): <Field name="start_date" className="agr-p2__blank" placeholder="date" /> and shall be
        substantially completed within <Field name="complete_days" className="agr-p2__blank" placeholder="days" /> (
        <Field name="complete_days_num" className="agr-p2__blank" placeholder="#" />) days or approximately on
        (Date): <Field name="complete_date" className="agr-p2__blank" placeholder="date" />
      </div>

      <div className="rule" style={{ left: "30.6pt", top: "148.3pt", width: "550.8pt" }} />
      <div className="agr__banner" style={{ top: "152.2pt" }}>
        CONTRACT PRICE
      </div>
      <div className="rule" style={{ left: "30.6pt", top: "165.3pt", width: "550.8pt" }} />

      <div className="agr-p2__body">
        <p className="para para--flush">
          <b>PAYMENT:</b> Owner agrees to pay Contractor a total price of{" "}
          <Field name="price_words" variant="flow" placeholder="amount in words" /> Dollars (
          <Field name="price_amount" variant="flow" placeholder="$0.00" />
          ).
        </p>

        <p className="para para--loud para--flush" style={{ marginTop: "22.3pt" }}>
          Down Payment: <Field name="down_payment" variant="flow" placeholder="$0.00" />
        </p>

        <p className="para para--loud para--flush">
          {LEGAL.downPaymentCap}
        </p>

        <div className="para para--loud para--flush" style={{ marginTop: "9.2pt" }}>
          <Field
            name="progress_schedule"
            variant="block"
            multiline
            placeholder="Describe each payment and what it covers"
          />
        </div>

        <p className="para para--loud" style={{ marginTop: "19.5pt" }}>
          {LEGAL.scheduleMustDescribe}
        </p>

        <p className="para" style={{ marginTop: "3.4pt" }}>
          {LEGAL.lienRelease}
        </p>

        <p className="para" style={{ marginTop: "11.5pt" }}>
          {LEGAL.paymentTiming}
        </p>

        <p className="para para--loud para--flush" style={{ marginTop: "11.6pt" }}>
          <Lines of={LEGAL.againstTheLaw} />
        </p>

        <p className="para" style={{ marginTop: "4.9pt" }}>
          {LEGAL.changeOrders}
        </p>

        <p className="para" style={{ marginTop: "11.5pt" }}>
          {LEGAL.escrow}
        </p>

        <p className="para" style={{ marginTop: "11.5pt" }}>
          {LEGAL.doNotSign[0]}
        </p>
      </div>

      <PageFooter page={2} wide />
    </section>
  );
}

/* ------------------------------------------------------------------ page 3 */

function PageThree() {
  return (
    <section className="sheet" data-page="3">
      <div className="sheet__frame" />

      <div className="agr-p3__body">
        <p className="para">
          {LEGAL.doNotSign[1]}
        </p>
      </div>

      <div className="rule" style={{ left: "30.6pt", top: "70.5pt", width: "550.8pt" }} />
      <div className="agr__banner" style={{ top: "74.3pt" }}>
        TERMS AND CONDITIONS
      </div>
      <div className="rule" style={{ left: "30.6pt", top: "87.5pt", width: "550.8pt" }} />

      <div className="agr-p3__body" style={{ top: "91.3pt" }}>
        <p className="para">
          {LEGAL.entireAgreement}
        </p>

        <p className="para bold center" style={{ marginTop: "13.5pt" }}>
          NOTICE
        </p>

        <p className="para bold">
          {LEGAL.licenseBoard}
        </p>

        <p className="para" style={{ marginTop: "11.5pt" }}>
          {LEGAL.performanceBond}
        </p>

        <p className="para" style={{ marginTop: "11.5pt" }}>
          {LEGAL.incorporatedDocuments}
        </p>

        <p className="para para--loud para--flush" style={{ marginTop: "11.6pt" }}>
          {LEGAL.entitledToCopy}
        </p>

        <p className="para para--loud para--flush" style={{ marginTop: "11.5pt" }}>
          <Lines of={LEGAL.rightToCancel} />
        </p>
      </div>

      <CheckBox name="right_to_cancel" className="agr__cancel-box" />

      <div className="agr-sign">
        <div className="agr-sign__consists">
          THIS AGREEMENT CONSISTS OF <Field name="consists_of_pages" placeholder="—" /> PAGES AND{" "}
          <Field name="consists_of_attachments" placeholder="—" /> ATTACHMENTS
        </div>

        <span className="agr-sign__slot" style={{ top: "12.4pt" }}>
          <SignatureField name="owner_1" width={230} height={22} label="Owner / Buyer signature" />
        </span>
        <span className="agr-sign__x" style={{ top: "23.3pt" }}>
          X
        </span>
        <span className="agr-sign__suffix" style={{ top: "23.3pt" }}>
          <Field name="owner_sig_date_1" placeholder="date" />
        </span>
        <span className="rule" style={{ left: "284.4pt", top: "34.4pt", width: "266.4pt" }} />
        <span className="agr-sign__caption" style={{ left: "289.8pt", top: "41.4pt" }}>
          OWNER<b>/</b>BUYER SIGNATURE
        </span>

        <span className="agr-sign__slot" style={{ top: "49.6pt" }}>
          <SignatureField name="owner_2" width={230} height={22} label="Owner / Buyer signature" />
        </span>
        <span className="agr-sign__x" style={{ top: "60.4pt" }}>
          X
        </span>
        <span className="agr-sign__suffix" style={{ top: "60.4pt" }}>
          <Field name="owner_sig_date_2" placeholder="date" />
        </span>
        <span className="rule" style={{ left: "284.4pt", top: "71.6pt", width: "266.4pt" }} />
        <span className="agr-sign__caption" style={{ left: "289.8pt", top: "78.6pt" }}>
          OWNER<b>/</b>BUYER SIGNATURE
        </span>

        <span className="agr-sign__slot" style={{ left: "10pt", top: "49.6pt" }}>
          <SignatureField name="contractor" width={230} height={22} label="Contractor signature" />
        </span>
        <span className="rule" style={{ left: "0pt", top: "71.6pt", width: "266.4pt" }} />
        <span className="agr-sign__caption" style={{ left: "5.4pt", top: "78.6pt" }}>
          CONTRACTOR SIGNATURE
        </span>
      </div>

      <PageFooter page={3} wide />
    </section>
  );
}

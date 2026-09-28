import { cx } from "../lib/cx";
import { PageFooter } from "./PageFooter";
import { TERMS_SHEETS, type TermLine } from "./termsLines";

function Line({ line }: { line: TermLine }) {
  return (
    <div
      className={cx("terms__line", line.j && "terms__line--justified")}
      style={{
        left: `${line.x}pt`,
        top: `${line.y}pt`,
        width: `${line.w}pt`,
      }}
    >
      {line.t}
    </div>
  );
}

/**
 * Page 4 is a title page; pages 5-7 carry the static terms, typeset one line
 * per source line so the wording breaks exactly where the original does.
 */
export function TermsPages() {
  return (
    <>
      <section className="sheet" data-page="4">
        <div className="sheet__frame" />
        <div className="terms__title">TERMS AND CONDITIONS</div>
        <PageFooter page={4} label="Terms and Conditions" wide cont />
      </section>

      {TERMS_SHEETS.map(({ page, columns }) => (
        <section className="sheet" key={page} data-page={page}>
          <div className="sheet__frame" />
          {columns.flat().map((line, i) => (
            <Line key={i} line={line} />
          ))}
          <PageFooter page={page} label="Terms and Conditions" />
        </section>
      ))}
    </>
  );
}

import { useEffect, useRef, useState } from "react";

import { AgreementForm } from "../forms/AgreementForm";
import { InvoiceForm } from "../forms/InvoiceForm";
import { api } from "../lib/api";
import { DocumentProvider } from "../lib/documentStore";
import { TEMPLATE_LABELS } from "../lib/templates";
import type { DocumentData, TemplateId } from "../lib/types";

const TEMPLATES: Array<{ id: TemplateId; name: string; Form: () => JSX.Element }> = [
  { id: "invoice", name: "Invoice", Form: InvoiceForm },
  { id: "agreement", name: "Agreement", Form: AgreementForm },
];

/** A US Letter page (612 x 792pt) in CSS pixels. */
const PAGE = { width: 816, height: 1056 };
/** Must match .preview__banner's height and .gallery's gap and padding. */
const BANNER = 60;
const GAP = 40;
/** Smaller than this, two pages side by side are too small to read, so they stack. */
const MIN_SCALE = 0.35;
const MAX_SCALE = 0.85;
/** On a phone, how much of the next page always shows below the current one. */
const PEEK = 72;

const ignore = () => {};

/** The first page of each blank form, sized to fill the stage; picking one starts it. */
export function TemplateGallery({ onStart }: { onStart: (template: TemplateId) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  const [scale, setScale] = useState(0.5);
  const [defaults, setDefaults] = useState<Partial<Record<TemplateId, DocumentData>>>({});

  useEffect(() => {
    for (const { id } of TEMPLATES) {
      api
        .getTemplate(id)
        .then(({ defaults }) => setDefaults((all) => ({ ...all, [id]: defaults })))
        .catch(() => {});
    }
  }, []);

  useEffect(() => {
    const stage = ref.current!;
    const fit = () => {
      // A few pixels of slack so sub-pixel rounding never wraps the row.
      const across = (stage.clientWidth - GAP * (TEMPLATES.length + 1) - 4) / TEMPLATES.length / PAGE.width;
      const down = (stage.clientHeight - BANNER - GAP * 2) / PAGE.height;
      if (across >= MIN_SCALE) {
        setScale(Math.min(MAX_SCALE, Math.max(MIN_SCALE, Math.min(across, down))));
        return;
      }
      // A phone: a vertical carousel, each page short enough that the next one peeks in.
      // The page scrolls there, so the gallery is as tall as its pages; measure the screen below the header.
      const padding = parseFloat(getComputedStyle(stage).paddingLeft);
      const visible = document.documentElement.clientHeight - (stage.getBoundingClientRect().top + window.scrollY);
      const wide = (stage.clientWidth - 2 * padding - 4) / PAGE.width;
      const tall = (visible - BANNER - 2 * padding - PEEK) / PAGE.height;
      setScale(Math.min(MAX_SCALE, wide, tall));
    };
    const observer = new ResizeObserver(fit);
    observer.observe(stage);
    return () => observer.disconnect();
  }, []);

  return (
    <div className="gallery" ref={ref}>
      {TEMPLATES.map(({ id, name, Form }) => (
        <div key={id} className="preview" style={{ width: PAGE.width * scale }} onClick={() => onStart(id)}>
          <button type="button" className="preview__banner">
            <span className="preview__text">
              <span className="preview__name">New {name.toLowerCase()}</span>
              <span className="preview__title">{TEMPLATE_LABELS[id]}</span>
            </span>
            <span className="preview__go">
              Start
              <svg viewBox="0 0 16 16" aria-hidden="true">
                <path d="M3 8h9M8.5 4.5 12 8l-3.5 3.5" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
              </svg>
            </span>
          </button>
          <div className="preview__page" style={{ height: PAGE.height * scale }} aria-hidden="true">
            <div className="preview__scale" style={{ transform: `scale(${scale})` }}>
              {defaults[id] && (
                <DocumentProvider data={defaults[id]} onChange={ignore} readOnly>
                  <Form />
                </DocumentProvider>
              )}
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { api } from "./lib/api";
import { DocumentProvider } from "./lib/documentStore";
import { EXPORT_FORMATS, exportDocument, type ExportFormat } from "./lib/exportDocument";
import type {
  DocStyle,
  DocumentData,
  DocumentSummary,
  FormDocument,
  TemplateId,
} from "./lib/types";
import { cx } from "./lib/cx";
import { AgreementForm } from "./forms/AgreementForm";
import { InvoiceForm } from "./forms/InvoiceForm";
import { AgreementModern } from "./forms/modern/AgreementModern";
import { InvoiceModern } from "./forms/modern/InvoiceModern";
import { MODERN_MARGINS } from "./forms/modern/parts";

const TEMPLATE_LABELS: Record<TemplateId, string> = {
  invoice: "Roofing Job Invoice",
  agreement: "Residential Roofing Agreement",
};

const STYLES: Array<[DocStyle, string]> = [
  ["classic", "Classic"],
  ["modern", "Modern"],
];

/** New documents open in this layout; the toolbar switches between them. */
const DEFAULT_STYLE: DocStyle = "modern";

type SaveState = "idle" | "saving" | "saved" | "error";

/**
 * A document being edited. A draft has no id: it exists only in the browser
 * until it is saved, so starting a form never clutters the document list.
 */
type Editing =
  | { kind: "draft"; template: TemplateId; style: DocStyle }
  | { kind: "saved"; doc: FormDocument };

const templateOf = (e: Editing) => (e.kind === "draft" ? e.template : e.doc.template);
const styleOf = (e: Editing) => (e.kind === "draft" ? e.style : e.doc.style);

export function App() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [current, setCurrent] = useState<Editing | null>(null);
  const [data, setData] = useState<DocumentData | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [zoom, setZoom] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const paperRef = useRef<HTMLDivElement>(null);
  const exportRef = useRef<HTMLDivElement>(null);
  const saveTimer = useRef<number>();

  // Dismiss the export menu on an outside click or Escape.
  useEffect(() => {
    if (!menuOpen) return;

    const onPointerDown = (e: PointerEvent) => {
      if (!exportRef.current?.contains(e.target as Node)) setMenuOpen(false);
    };
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMenuOpen(false);
    };

    document.addEventListener("pointerdown", onPointerDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("pointerdown", onPointerDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [menuOpen]);

  const refreshList = useCallback(async () => setDocs(await api.listDocuments()), []);

  useEffect(() => {
    void refreshList();
  }, [refreshList]);

  // Leaving an untouched draft is silent; a started one asks first.
  const mayDiscardDraft = useCallback(
    () =>
      current?.kind !== "draft" ||
      saveState === "idle" ||
      window.confirm("This document has not been saved yet. Discard it?"),
    [current, saveState],
  );

  const open = useCallback(
    async (id: string) => {
      if (!mayDiscardDraft()) return;
      window.clearTimeout(saveTimer.current);
      const doc = await api.getDocument(id);
      setCurrent({ kind: "saved", doc });
      setData(doc.data);
      setSaveState("idle");
    },
    [mayDiscardDraft],
  );

  // Starting a form only opens a draft; nothing is stored until Save.
  const create = useCallback(
    async (template: TemplateId) => {
      if (!mayDiscardDraft()) return;
      window.clearTimeout(saveTimer.current);
      const { defaults } = await api.getTemplate(template);
      setCurrent({ kind: "draft", template, style: DEFAULT_STYLE });
      setData(defaults);
      setSaveState("idle");
    },
    [mayDiscardDraft],
  );

  const save = useCallback(async () => {
    if (current?.kind !== "draft" || !data) return;
    setSaveState("saving");
    try {
      const doc = await api.createDocument(current.template, current.style, data);
      setCurrent({ kind: "saved", doc });
      setSaveState("saved");
      await refreshList();
    } catch {
      setSaveState("error");
    }
  }, [current, data, refreshList]);

  // Switching style re-renders the same data through the other layout.
  const restyle = useCallback(
    async (style: DocStyle) => {
      if (!current || !data || styleOf(current) === style) return;

      if (current.kind === "draft") {
        setCurrent({ ...current, style });
        return;
      }

      setCurrent({ kind: "saved", doc: { ...current.doc, style } });
      setSaveState("saving");
      try {
        const doc = await api.saveDocument(current.doc.id, data, style);
        setCurrent({ kind: "saved", doc });
        setSaveState("saved");
        void refreshList();
      } catch {
        setSaveState("error");
      }
    },
    [current, data, refreshList],
  );

  const remove = useCallback(
    async (id: string) => {
      await api.deleteDocument(id);
      if (current?.kind === "saved" && current.doc.id === id) {
        setCurrent(null);
        setData(null);
      }
      await refreshList();
    },
    [current, refreshList],
  );

  // Saved documents autosave a moment after typing stops. Drafts just track
  // that they have unsaved work.
  const handleChange = useCallback(
    (next: DocumentData) => {
      setData(next);
      if (!current) return;

      if (current.kind === "draft") {
        setSaveState("saving");
        return;
      }

      setSaveState("saving");
      window.clearTimeout(saveTimer.current);
      saveTimer.current = window.setTimeout(async () => {
        try {
          const doc = await api.saveDocument(current.doc.id, next);
          setCurrent({ kind: "saved", doc });
          setSaveState("saved");
          void refreshList();
        } catch {
          setSaveState("error");
        }
      }, 600);
    },
    [current, refreshList],
  );

  const handleExport = useCallback(
    async (format: ExportFormat) => {
      if (!paperRef.current || !current || !data) return;
      setMenuOpen(false);
      setExporting(true);
      try {
        const style = styleOf(current);
        await exportDocument(
          {
            root: paperRef.current,
            template: templateOf(current),
            style,
            data,
            // Classic sheets paint their own margins; modern layouts flow and
            // need the page box to supply them on every page.
            margins: style === "modern" ? MODERN_MARGINS : undefined,
          },
          current.kind === "saved" ? current.doc.title : "Draft",
          format,
        );
      } catch (err) {
        window.alert(err instanceof Error ? err.message : "Could not create the file.");
      } finally {
        setExporting(false);
      }
    },
    [current, data],
  );

  const body = useMemo(() => {
    if (!current) return null;
    const modern = styleOf(current) === "modern";
    if (templateOf(current) === "invoice") {
      return modern ? <InvoiceModern /> : <InvoiceForm />;
    }
    return modern ? <AgreementModern /> : <AgreementForm />;
  }, [current]);

  return (
    <div className="app">
      <aside className="sidebar">
        <div>
          <h1 className="sidebar__brand">AMK Roofing Forms</h1>
          <a className="sidebar__home" href="/">
            amkroofing.com
          </a>
        </div>

        <h2 className="sidebar__heading">New document</h2>

        <div className="sidebar__new">
          <button type="button" onClick={() => void create("invoice")}>
            Invoice
          </button>
          <button type="button" onClick={() => void create("agreement")}>
            Agreement
          </button>
        </div>

        <h2 className="sidebar__heading">Documents</h2>
        <ul className="doclist">
          {docs.map((doc) => (
            <li
              key={doc.id}
              className={
                current?.kind === "saved" && current.doc.id === doc.id ? "is-active" : undefined
              }
            >
              <button type="button" className="doclist__open" onClick={() => void open(doc.id)}>
                <span className="doclist__title">{doc.title}</span>
                <span className="doclist__meta">
                  <span className={cx("tag", `tag--${doc.style}`)}>
                    {doc.style === "modern" ? "Modern" : "Classic"}
                  </span>
                  {TEMPLATE_LABELS[doc.template]}
                </span>
              </button>
              <button
                type="button"
                className="doclist__delete"
                title="Delete"
                onClick={() => void remove(doc.id)}
              >
                &times;
              </button>
            </li>
          ))}
          {docs.length === 0 && <li className="doclist__empty">No documents yet.</li>}
        </ul>
      </aside>

      <main className="main">
        {current && data ? (
          <>
            <header className="toolbar">
              <div className="toolbar__title">
                <strong>
                  {current.kind === "saved" ? current.doc.title : "Untitled draft"}
                </strong>
                <span className="toolbar__template">
                  {TEMPLATE_LABELS[templateOf(current)]}
                </span>
              </div>

              <div className="segmented" role="radiogroup" aria-label="Design">
                {STYLES.map(([style, label]) => (
                  <button
                    key={style}
                    type="button"
                    role="radio"
                    aria-checked={styleOf(current) === style}
                    className={cx(styleOf(current) === style && "is-on")}
                    onClick={() => void restyle(style)}
                  >
                    {label}
                  </button>
                ))}
              </div>

              {current.kind === "draft" ? (
                <>
                  <span className="toolbar__save">Not saved yet</span>
                  <button type="button" className="ghost" onClick={() => void save()}>
                    Save
                  </button>
                </>
              ) : (
                <span className={`toolbar__save toolbar__save--${saveState}`}>
                  {saveState === "saving" && "Saving…"}
                  {saveState === "saved" && "All changes saved"}
                  {saveState === "error" && "Could not save"}
                </span>
              )}

              <div className="toolbar__zoom">
                <button type="button" onClick={() => setZoom((z) => Math.max(0.4, z - 0.1))}>
                  &minus;
                </button>
                <span>{Math.round(zoom * 100)}%</span>
                <button type="button" onClick={() => setZoom((z) => Math.min(2, z + 0.1))}>
                  +
                </button>
              </div>

              <div className="export" ref={exportRef}>
                <button
                  type="button"
                  className="primary"
                  aria-haspopup="menu"
                  aria-expanded={menuOpen}
                  disabled={exporting}
                  onClick={() => setMenuOpen((open) => !open)}
                >
                  {exporting ? "Preparing…" : "Export"}
                  <span className="export__caret" aria-hidden="true" />
                </button>

                {menuOpen && (
                  <ul className="export__menu" role="menu">
                    {(Object.keys(EXPORT_FORMATS) as ExportFormat[]).map((format) => (
                      <li key={format}>
                        <button
                          type="button"
                          role="menuitem"
                          onClick={() => void handleExport(format)}
                        >
                          <span>{EXPORT_FORMATS[format].label}</span>
                          <span className="export__ext">
                            .{EXPORT_FORMATS[format].extension}
                          </span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            </header>

            <div className="stage">
              <div
                className="stage__scale"
                style={{ transform: `scale(${zoom})`, width: `${612 * zoom}pt` }}
              >
                <div className="document" ref={paperRef}>
                  <DocumentProvider data={data} onChange={handleChange}>
                    {body}
                  </DocumentProvider>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="empty">
            <h2>Pick a document, or start a new one</h2>
            <p>
              Every page is a live copy of the original form. Click any text to edit it, then
              download a print-ready PDF.
            </p>
          </div>
        )}
      </main>
    </div>
  );
}

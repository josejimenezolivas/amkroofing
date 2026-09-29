import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import logo from "./assets/amk-logo-light.png";
import { AccountMenu } from "./components/AccountMenu";
import { ConfirmDialog } from "./components/ConfirmDialog";
import { DocListItem } from "./components/DocListItem";
import { EditableTitle } from "./components/EditableTitle";
import { TemplateGallery } from "./components/TemplateGallery";
import { api } from "./lib/api";
import { useDismiss } from "./lib/dismiss";
import { DocumentProvider } from "./lib/documentStore";
import { EXPORT_FORMATS, exportDocument, type ExportFormat } from "./lib/exportDocument";
import type {
  Account,
  DocStyle,
  DocumentChanges,
  DocumentData,
  DocumentSummary,
  FormDocument,
  TemplateId,
} from "./lib/types";
import { cx } from "./lib/cx";
import { TEMPLATE_LABELS } from "./lib/templates";
import { useTheme } from "./lib/theme";
import { AgreementForm } from "./forms/AgreementForm";
import { InvoiceForm } from "./forms/InvoiceForm";
import { AgreementModern } from "./forms/modern/AgreementModern";
import { InvoiceModern } from "./forms/modern/InvoiceModern";
import { MODERN_MARGINS } from "./forms/modern/parts";

const STYLES: Array<[DocStyle, string]> = [
  ["classic", "Classic"],
  ["modern", "Modern"],
];

/** New documents open in this layout; the toolbar switches between them. */
const DEFAULT_STYLE: DocStyle = "classic";

type SaveState = "idle" | "saving" | "saved" | "error";

/**
 * A document being edited. A draft has no id: it exists only in the browser
 * until it is saved, so starting a form never clutters the document list.
 */
type Editing =
  | { kind: "draft"; template: TemplateId; style: DocStyle; title?: string }
  | { kind: "saved"; doc: FormDocument };

const templateOf = (e: Editing) => (e.kind === "draft" ? e.template : e.doc.template);
const styleOf = (e: Editing) => (e.kind === "draft" ? e.style : e.doc.style);

interface AppProps {
  account: Account;
  onSignOut: () => Promise<void>;
}

export function App({ account, onSignOut }: AppProps) {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [current, setCurrent] = useState<Editing | null>(null);
  const [data, setData] = useState<DocumentData | null>(null);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [zoom, setZoom] = useState(1);
  const [exporting, setExporting] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [recentsOpen, setRecentsOpen] = useState(true);
  const [deleting, setDeleting] = useState<DocumentSummary | null>(null);
  const { choice: themeChoice, setChoice: setThemeChoice, theme } = useTheme();

  const paperRef = useRef<HTMLDivElement>(null);
  const exportRef = useRef<HTMLDivElement>(null);
  const saveTimer = useRef<number>();
  const pendingSave = useRef<(() => Promise<void>) | null>(null);
  /** The saved document the user last asked for; late responses for any other are dropped. */
  const openId = useRef<string | null>(null);
  /**
   * Every document this tab has fetched or saved, by id. Holding the promise
   * lets a hover and the click after it share one request, and makes a document
   * reopened mid-save wait for the save rather than show the copy before it.
   */
  const loaded = useRef(new Map<string, Promise<FormDocument>>());

  const keep = useCallback((id: string, doc: Promise<FormDocument>) => {
    loaded.current.set(id, doc);
    doc.catch(() => {
      if (loaded.current.get(id) === doc) loaded.current.delete(id);
    });
    return doc;
  }, []);

  const load = useCallback(
    (id: string) => loaded.current.get(id) ?? keep(id, api.getDocument(id)),
    [keep],
  );

  /** Send a debounced autosave now instead of dropping it. */
  const flushSave = useCallback(async () => {
    window.clearTimeout(saveTimer.current);
    await pendingSave.current?.();
  }, []);

  useDismiss(exportRef, menuOpen, setMenuOpen);

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
      void flushSave();
      openId.current = id;
      let doc = await load(id);
      // Changed since this tab fetched it, e.g. from another device.
      const listed = docs.find((d) => d.id === id);
      if (listed && listed.updated_at > doc.updated_at) doc = await keep(id, api.getDocument(id));
      if (openId.current !== id) return;
      setCurrent({ kind: "saved", doc });
      setData(doc.data);
      setSaveState("idle");
    },
    [mayDiscardDraft, flushSave, load, keep, docs],
  );

  // Starting a form only opens a draft; nothing is stored until Save.
  const create = useCallback(
    async (template: TemplateId) => {
      if (!mayDiscardDraft()) return;
      void flushSave();
      openId.current = null;
      const { defaults } = await api.getTemplate(template);
      setCurrent({ kind: "draft", template, style: DEFAULT_STYLE });
      setData(defaults);
      setSaveState("idle");
    },
    [mayDiscardDraft, flushSave],
  );

  // Back to the template previews, where a new document is picked.
  const showGallery = useCallback(() => {
    if (!mayDiscardDraft()) return;
    void flushSave();
    openId.current = null;
    setCurrent(null);
    setData(null);
    setSaveState("idle");
  }, [mayDiscardDraft, flushSave]);

  const save = useCallback(async (draft: Editing | null = current) => {
    if (draft?.kind !== "draft" || !data) return;
    setSaveState("saving");
    try {
      const doc = await api.createDocument(draft.template, draft.style, data, draft.title);
      keep(doc.id, Promise.resolve(doc));
      openId.current = doc.id;
      setCurrent({ kind: "saved", doc });
      setSaveState("saved");
      await refreshList();
    } catch {
      setSaveState("error");
    }
  }, [current, data, refreshList, keep]);

  // Restyling or renaming. A draft remembers a new style until Save, but naming
  // it is a decision to keep it, so a rename saves it.
  const change = useCallback(
    async (changes: DocumentChanges) => {
      if (!current || !data) return;

      if (current.kind === "draft") {
        const draft = { ...current, ...changes };
        setCurrent(draft);
        if (changes.title) await save(draft);
        return;
      }

      // This save carries the latest data, so a pending autosave is redundant.
      window.clearTimeout(saveTimer.current);
      pendingSave.current = null;
      const { id } = current.doc;
      setCurrent({ kind: "saved", doc: { ...current.doc, ...changes } });
      setSaveState("saving");
      try {
        const doc = await keep(id, api.saveDocument(id, data, changes));
        if (openId.current !== id) return;
        setCurrent({ kind: "saved", doc });
        setSaveState("saved");
        void refreshList();
      } catch {
        if (openId.current === id) setSaveState("error");
      }
    },
    [current, data, refreshList, keep, save],
  );

  // Renaming from the list. The open document goes through change() so the
  // editor's copy stays current; any other is saved with its stored data.
  const rename = useCallback(
    async (id: string, title: string) => {
      if (current?.kind === "saved" && current.doc.id === id) return change({ title });
      setDocs((all) => all.map((d) => (d.id === id ? { ...d, title } : d)));
      try {
        const doc = await load(id);
        await keep(id, api.saveDocument(id, doc.data, { title }));
      } catch {
        window.alert("Could not rename the document.");
      }
      await refreshList();
    },
    [current, change, load, keep, refreshList],
  );

  const remove = useCallback(
    async (id: string) => {
      await api.deleteDocument(id);
      loaded.current.delete(id);
      if (openId.current === id) {
        window.clearTimeout(saveTimer.current);
        pendingSave.current = null;
        openId.current = null;
        setCurrent(null);
        setData(null);
      }
      await refreshList();
    },
    [refreshList],
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
      const { id, title } = current.doc;
      const persist = async () => {
        pendingSave.current = null;
        try {
          const doc = await keep(id, api.saveDocument(id, next));
          void refreshList();
          if (openId.current !== id) return;
          setCurrent({ kind: "saved", doc });
          setSaveState("saved");
        } catch {
          if (openId.current === id) setSaveState("error");
          else window.alert(`Your last changes to "${title}" could not be saved.`);
        }
      };
      pendingSave.current = persist;
      saveTimer.current = window.setTimeout(persist, 600);
    },
    [current, refreshList, keep],
  );

  const signOut = useCallback(async () => {
    if (!mayDiscardDraft()) return;
    await flushSave();
    await onSignOut();
  }, [mayDiscardDraft, flushSave, onSignOut]);

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
    <div className="app" data-theme={theme}>
      <aside className="sidebar">
        <header className="sidebar__top">
          <a className="sidebar__brand" href="/" aria-label="AMK Roofing home">
            <img src={logo} alt="" />
          </a>
          <span className="sidebar__section">Forms</span>
        </header>

        <button
          type="button"
          className={cx("sidebar__new", !current && "is-active")}
          onClick={showGallery}
        >
          <svg viewBox="0 0 24 24" aria-hidden="true">
            <path
              d="M12 3H5a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7M18.4 2.6a2 2 0 0 1 2.8 2.8L12 14.6l-4 1 1-4Z"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          New document
        </button>

        <h2 className="recents">
          <button
            type="button"
            className="recents__toggle"
            aria-expanded={recentsOpen}
            onClick={() => setRecentsOpen((o) => !o)}
          >
            Recents
            <svg className="recents__chevron" viewBox="0 0 16 16" aria-hidden="true">
              <path d="m4 6 4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </h2>
        {recentsOpen && (
          <ul className="doclist">
            {docs.map((doc) => (
              <DocListItem
                key={doc.id}
                doc={doc}
                active={current?.kind === "saved" && current.doc.id === doc.id}
                onOpen={() => void open(doc.id)}
                onPrefetch={() => void load(doc.id).catch(() => {})}
                onRename={(title) => void rename(doc.id, title)}
                onDelete={() => setDeleting(doc)}
              />
            ))}
            {docs.length === 0 && <li className="doclist__empty">No documents yet.</li>}
          </ul>
        )}

        <AccountMenu
          account={account}
          theme={themeChoice}
          onTheme={setThemeChoice}
          onSignOut={() => void signOut()}
        />
      </aside>

      {deleting && (
        <ConfirmDialog
          title="Delete document?"
          confirmLabel="Delete"
          onCancel={() => setDeleting(null)}
          onConfirm={() => {
            setDeleting(null);
            void remove(deleting.id);
          }}
        >
          <strong>{deleting.title}</strong> will be permanently deleted. This can’t be undone.
        </ConfirmDialog>
      )}

      <main className="main">
        {current && data ? (
          <>
            <header className="toolbar">
              <div className="toolbar__title">
                <EditableTitle
                  value={current.kind === "saved" ? current.doc.title : (current.title ?? "Untitled draft")}
                  onRename={(title) => void change({ title })}
                />
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
                    onClick={() => styleOf(current) !== style && void change({ style })}
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
          <TemplateGallery onStart={(template) => void create(template)} />
        )}
      </main>
    </div>
  );
}

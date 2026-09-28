/**
 * The two export formats are produced in genuinely different ways.
 *
 * PDF ships the live DOM and every stylesheet on the page to the server, so
 * what prints is exactly what is on screen, down to the point.
 *
 * Word instead sends the document's data and lets the server compose a real
 * .docx out of Word's own tables, lists and paragraphs. A converted-HTML
 * document would look close and then fall apart the moment anyone typed in
 * it; this one keeps working as a document.
 */

import type { DocStyle, DocumentData, TemplateId } from "./types";

export type ExportFormat = "pdf" | "word";

interface FormatSpec {
  label: string;
  extension: string;
  path: string;
}

export const EXPORT_FORMATS: Record<ExportFormat, FormatSpec> = {
  pdf: { label: "PDF document", extension: "pdf", path: "/forms/api/render/pdf" },
  word: { label: "Microsoft Word", extension: "docx", path: "/forms/api/render/docx" },
};

/**
 * Fixed-position sheets paint their own margins, so they print edge to edge.
 * The modern layouts flow across pages and need real `@page` margins instead.
 */
export interface PageMargins {
  top: string;
  bottom: string;
  side: string;
}

export const NO_MARGINS: PageMargins = { top: "0", bottom: "0", side: "0" };

export interface ExportSource {
  /** The rendered sheets, for the formats that print what is on screen. */
  root: HTMLElement;
  template: TemplateId;
  style: DocStyle;
  data: DocumentData;
  margins?: PageMargins;
}

function collectCss(): string {
  const chunks: string[] = [];
  for (const sheet of Array.from(document.styleSheets)) {
    try {
      for (const rule of Array.from(sheet.cssRules)) chunks.push(rule.cssText);
    } catch {
      // A cross-origin stylesheet we are not allowed to read; nothing of ours.
    }
  }
  return chunks.join("\n");
}

function payload(source: ExportSource, filename: string, format: ExportFormat) {
  if (format === "word") {
    const { template, style, data } = source;
    return { template, style, data, filename };
  }

  const margins = source.margins ?? NO_MARGINS;
  return {
    html: source.root.outerHTML,
    css: collectCss(),
    filename,
    margin_top: margins.top,
    margin_bottom: margins.bottom,
    margin_side: margins.side,
  };
}

export async function exportDocument(
  source: ExportSource,
  filename: string,
  format: ExportFormat,
): Promise<void> {
  const spec = EXPORT_FORMATS[format];

  const res = await fetch(spec.path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload(source, filename, format)),
  });

  if (!res.ok) throw new Error(`${spec.label} export failed: ${res.status}`);

  const url = URL.createObjectURL(await res.blob());
  const link = document.createElement("a");
  link.href = url;
  link.download = `${filename}.${spec.extension}`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

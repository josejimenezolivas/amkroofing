export type TemplateId = "invoice" | "agreement";

/** "classic" reproduces the reference PDF; "modern" is a redesign of the same data. */
export type DocStyle = "classic" | "modern";

export type ListRow = Record<string, string>;

export interface DocumentData {
  fields: Record<string, string>;
  checks: Record<string, boolean>;
  lists: Record<string, ListRow[]>;
  signatures: Record<string, string>;
  /** Uploaded artwork, keyed by slot. Currently just "logo". */
  images: Record<string, string>;
}

export interface DocumentSummary {
  id: string;
  template: TemplateId;
  style: DocStyle;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface FormDocument extends DocumentSummary {
  data: DocumentData;
}

export interface TemplateInfo {
  id: TemplateId;
  name: string;
  description: string;
  pages: number;
  defaults: DocumentData;
}

export const emptyData = (): DocumentData => ({
  fields: {},
  checks: {},
  lists: {},
  signatures: {},
  images: {},
});

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

/** What a save may change besides the data. */
export type DocumentChanges = Partial<Pick<DocumentSummary, "style" | "title">>;

export interface TemplateInfo {
  id: TemplateId;
  name: string;
  description: string;
  pages: number;
  defaults: DocumentData;
}

/** The signed-in user. */
export interface Account {
  email: string;
  name: string;
  picture: string | null;
}

export const emptyData = (): DocumentData => ({
  fields: {},
  checks: {},
  lists: {},
  signatures: {},
  images: {},
});

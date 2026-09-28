import type {
  DocStyle,
  DocumentData,
  DocumentSummary,
  FormDocument,
  TemplateId,
  TemplateInfo,
} from "./types";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!res.ok) {
    throw new Error(`${init?.method ?? "GET"} ${path} failed: ${res.status}`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const API = "/forms/api";

export const api = {
  listTemplates: () => request<TemplateInfo[]>(`${API}/templates`),

  getTemplate: (id: TemplateId) => request<TemplateInfo>(`${API}/templates/${id}`),

  listDocuments: () => request<DocumentSummary[]>(`${API}/documents`),

  getDocument: (id: string) => request<FormDocument>(`${API}/documents/${id}`),

  createDocument: (template: TemplateId, style: DocStyle = "classic", data?: DocumentData) =>
    request<FormDocument>(`${API}/documents`, {
      method: "POST",
      body: JSON.stringify({ template, style, data }),
    }),

  saveDocument: (id: string, data: DocumentData, style?: DocStyle) =>
    request<FormDocument>(`${API}/documents/${id}`, {
      method: "PUT",
      body: JSON.stringify({ data, style }),
    }),

  deleteDocument: (id: string) =>
    request<void>(`${API}/documents/${id}`, { method: "DELETE" }),
};

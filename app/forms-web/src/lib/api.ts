import type {
  Account,
  DocStyle,
  DocumentData,
  DocumentSummary,
  FormDocument,
  TemplateId,
  TemplateInfo,
} from "./types";

const API = "/forms/api";

/** A failed request, carrying the server's own explanation when it gave one. */
export class ApiError extends Error {
  constructor(
    readonly status: number,
    message: string,
  ) {
    super(message);
  }
}

let onSignedOut: () => void = () => {};

/** Called when the session ends mid-use, so the app can go back to the sign-in page. */
export function whenSignedOut(handler: () => void): void {
  onSignedOut = handler;
}

/** fetch for this API: throws ApiError on failure and reports an ended session. */
export async function send(path: string, init?: RequestInit): Promise<Response> {
  const res = await fetch(path, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (res.ok) return res;

  // The sign-in routes answer 401 for a wrong password; that is not a lost session.
  if (res.status === 401 && !path.startsWith(`${API}/auth/`)) onSignedOut();
  let message = `${init?.method ?? "GET"} ${path} failed: ${res.status}`;
  try {
    const body: unknown = await res.json();
    if (body && typeof body === "object" && "detail" in body && typeof body.detail === "string") {
      message = body.detail;
    }
  } catch {
    // Not JSON; keep the generic message.
  }
  throw new ApiError(res.status, message);
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await send(path, init);
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const post = (body: unknown): RequestInit => ({ method: "POST", body: JSON.stringify(body) });

export const auth = {
  googleStart: `${API}/auth/google/start`,

  config: () => request<{ google: boolean }>(`${API}/auth/config`),

  me: () => request<Account>(`${API}/auth/me`),

  login: (email: string, password: string) =>
    request<Account>(`${API}/auth/email/login`, post({ email, password })),

  acceptInvite: (email: string, token: string, name: string, password: string) =>
    request<Account>(`${API}/auth/email/signup`, post({ email, token, name, password })),

  logout: () => request<{ ok: boolean }>(`${API}/auth/logout`, { method: "POST" }),
};

export const api = {
  listTemplates: () => request<TemplateInfo[]>(`${API}/templates`),

  getTemplate: (id: TemplateId) => request<TemplateInfo>(`${API}/templates/${id}`),

  listDocuments: () => request<DocumentSummary[]>(`${API}/documents`),

  getDocument: (id: string) => request<FormDocument>(`${API}/documents/${id}`),

  createDocument: (template: TemplateId, style: DocStyle = "classic", data?: DocumentData) =>
    request<FormDocument>(`${API}/documents`, post({ template, style, data })),

  saveDocument: (id: string, data: DocumentData, style?: DocStyle) =>
    request<FormDocument>(`${API}/documents/${id}`, {
      method: "PUT",
      body: JSON.stringify({ data, style }),
    }),

  deleteDocument: (id: string) =>
    request<void>(`${API}/documents/${id}`, { method: "DELETE" }),
};

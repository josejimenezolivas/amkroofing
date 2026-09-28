import {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import type { DocumentData, ListRow } from "./types";
import { emptyData } from "./types";

interface Store {
  data: DocumentData;
  readOnly: boolean;
  setField: (name: string, value: string) => void;
  setCheck: (name: string, value: boolean) => void;
  toggleCheck: (name: string) => void;
  setSignature: (name: string, dataUrl: string) => void;
  setImage: (name: string, dataUrl: string | null) => void;
  rows: (name: string) => ListRow[];
  setCell: (list: string, index: number, key: string, value: string) => void;
  addRow: (list: string, index: number, template?: ListRow) => void;
  removeRow: (list: string, index: number) => void;
}

const DocumentContext = createContext<Store | null>(null);

export function useDoc(): Store {
  const store = useContext(DocumentContext);
  if (!store) throw new Error("useDoc must be used inside <DocumentProvider>");
  return store;
}

export function useDocumentState(initial?: DocumentData) {
  const [data, setData] = useState<DocumentData>(initial ?? emptyData());
  return { data, setData };
}

interface ProviderProps {
  data: DocumentData;
  onChange: (next: DocumentData) => void;
  readOnly?: boolean;
  children: ReactNode;
}

export function DocumentProvider({
  data,
  onChange,
  readOnly = false,
  children,
}: ProviderProps) {
  const patch = useCallback(
    (fn: (draft: DocumentData) => DocumentData) => onChange(fn(data)),
    [data, onChange],
  );

  const store = useMemo<Store>(() => {
    const listOf = (name: string) => data.lists[name] ?? [];

    return {
      data,
      readOnly,

      setField: (name, value) =>
        patch((d) => ({ ...d, fields: { ...d.fields, [name]: value } })),

      setCheck: (name, value) =>
        patch((d) => ({ ...d, checks: { ...d.checks, [name]: value } })),

      toggleCheck: (name) =>
        patch((d) => ({
          ...d,
          checks: { ...d.checks, [name]: !d.checks[name] },
        })),

      setSignature: (name, dataUrl) =>
        patch((d) => ({
          ...d,
          signatures: { ...d.signatures, [name]: dataUrl },
        })),

      // A null value drops the slot so the built-in artwork shows again.
      setImage: (name, dataUrl) =>
        patch((d) => {
          const images = { ...d.images };
          if (dataUrl === null) delete images[name];
          else images[name] = dataUrl;
          return { ...d, images };
        }),

      rows: listOf,

      setCell: (list, index, key, value) =>
        patch((d) => {
          const next = [...(d.lists[list] ?? [])];
          next[index] = { ...next[index], [key]: value };
          return { ...d, lists: { ...d.lists, [list]: next } };
        }),

      addRow: (list, index, template) =>
        patch((d) => {
          const current = d.lists[list] ?? [];
          // Default a new row to the same shape as its neighbour, but blank.
          const shape =
            template ??
            Object.fromEntries(
              Object.keys(current[index] ?? { text: "" }).map((k) => [k, ""]),
            );
          const next = [...current];
          next.splice(index + 1, 0, shape);
          return { ...d, lists: { ...d.lists, [list]: next } };
        }),

      removeRow: (list, index) =>
        patch((d) => {
          const next = [...(d.lists[list] ?? [])];
          next.splice(index, 1);
          return { ...d, lists: { ...d.lists, [list]: next } };
        }),
    };
  }, [data, patch, readOnly]);

  return (
    <DocumentContext.Provider value={store}>{children}</DocumentContext.Provider>
  );
}

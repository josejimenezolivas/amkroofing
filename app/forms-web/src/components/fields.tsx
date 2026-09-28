import type { CSSProperties } from "react";

import { useDoc } from "../lib/documentStore";
import { cx } from "../lib/cx";
import { Editable, type EditableProps } from "./Editable";

type Shared = Omit<EditableProps, "value" | "onChange" | "readOnly">;

/** A single named text value on the document. */
export function Field({ name, ...rest }: Shared & { name: string }) {
  const { data, setField, readOnly } = useDoc();
  return (
    <Editable
      value={data.fields[name] ?? ""}
      onChange={(v) => setField(name, v)}
      readOnly={readOnly}
      {...rest}
    />
  );
}

/** One cell of a repeatable row. */
export function Cell({
  list,
  index,
  field,
  ...rest
}: Shared & { list: string; index: number; field: string }) {
  const { rows, setCell, readOnly } = useDoc();
  return (
    <Editable
      value={rows(list)[index]?.[field] ?? ""}
      onChange={(v) => setCell(list, index, field, v)}
      readOnly={readOnly}
      {...rest}
    />
  );
}

/** Square form checkbox; the X is drawn with CSS so it prints cleanly. */
export function CheckBox({
  name,
  className,
  style,
}: {
  name: string;
  className?: string;
  style?: CSSProperties;
}) {
  const { data, toggleCheck, readOnly } = useDoc();
  const checked = Boolean(data.checks[name]);
  return (
    <button
      type="button"
      className={cx("checkbox", checked && "checkbox--on", className)}
      style={style}
      aria-pressed={checked}
      aria-label={name}
      disabled={readOnly}
      onClick={() => toggleCheck(name)}
    />
  );
}

/**
 * Controls for inserting/removing a row. Hidden when printing, so the exported
 * PDF never shows editor chrome.
 */
export function RowTools({ list, index }: { list: string; index: number }) {
  const { addRow, removeRow, readOnly } = useDoc();
  if (readOnly) return null;
  return (
    <span className="row-tools" contentEditable={false}>
      <button type="button" title="Add row below" onClick={() => addRow(list, index)}>
        +
      </button>
      <button type="button" title="Remove row" onClick={() => removeRow(list, index)}>
        &minus;
      </button>
    </span>
  );
}

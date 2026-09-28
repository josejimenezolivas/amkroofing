import { useLayoutEffect, useRef, type CSSProperties } from "react";

import { cx } from "../lib/cx";

/** Browsers leave a trailing newline behind in an emptied contenteditable. */
function readText(el: HTMLElement): string {
  return el.innerText.replace(/\n$/, "");
}

export interface EditableProps {
  value: string;
  onChange: (value: string) => void;
  /**
   * `inline` sits in a fixed slot (table cells, labelled blanks),
   * `flow` runs inside a sentence, `block` is a full paragraph.
   */
  variant?: "inline" | "flow" | "block";
  multiline?: boolean;
  placeholder?: string;
  className?: string;
  style?: CSSProperties;
  readOnly?: boolean;
}

export function Editable({
  value,
  onChange,
  variant = "inline",
  multiline = false,
  placeholder,
  className,
  style,
  readOnly = false,
}: EditableProps) {
  const ref = useRef<HTMLSpanElement>(null);

  // Only touch the DOM when the incoming value and the rendered text actually
  // diverge, otherwise every keystroke would reset the caret to the start.
  useLayoutEffect(() => {
    const el = ref.current;
    if (el && readText(el) !== value) el.innerText = value;
  }, [value]);

  return (
    <span
      ref={ref}
      className={cx("ed", `ed--${variant}`, multiline && "ed--multiline", className)}
      style={style}
      contentEditable={!readOnly}
      suppressContentEditableWarning
      spellCheck={false}
      data-empty={value.length === 0 || undefined}
      data-placeholder={placeholder}
      onInput={(e) => onChange(readText(e.currentTarget))}
      onKeyDown={(e) => {
        if (!multiline && e.key === "Enter") e.preventDefault();
      }}
      onPaste={(e) => {
        // Keep the document's own typography: never inherit pasted styling.
        e.preventDefault();
        const text = e.clipboardData.getData("text/plain");
        document.execCommand("insertText", false, multiline ? text : text.replace(/\s*\n+\s*/g, " "));
      }}
    />
  );
}

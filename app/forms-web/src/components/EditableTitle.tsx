import { useRef, useState } from "react";

import { cx } from "../lib/cx";

interface TitleInputProps {
  value: string;
  className: string;
  /** The new title, or null when it was left empty, unchanged, or cancelled. */
  onDone: (title: string | null) => void;
}

/** A title text box in place of the title: Enter or leaving it saves, Escape cancels. */
export function TitleInput({ value, className, onDone }: TitleInputProps) {
  const [text, setText] = useState(value);
  const cancelled = useRef(false);

  return (
    <span className={cx("rename", className)} data-text={text}>
      <input
        aria-label="Document title"
        value={text}
        size={1}
        maxLength={120}
        autoFocus
        onChange={(e) => setText(e.currentTarget.value)}
        onFocus={(e) => e.currentTarget.select()}
        onBlur={() => {
          const title = cancelled.current ? "" : text.trim();
          onDone(title && title !== value ? title : null);
        }}
        onKeyDown={(e) => {
          cancelled.current = e.key === "Escape";
          if (e.key === "Enter" || e.key === "Escape") e.currentTarget.blur();
        }}
      />
    </span>
  );
}

/** The open document's title, renamed by double-clicking it. */
export function EditableTitle({ value, onRename }: { value: string; onRename: (title: string) => void }) {
  const [editing, setEditing] = useState(false);

  if (editing) {
    return (
      <TitleInput
        className="toolbar__rename"
        value={value}
        onDone={(title) => {
          setEditing(false);
          if (title) onRename(title);
        }}
      />
    );
  }
  return (
    <strong title="Double-click to rename" onDoubleClick={() => setEditing(true)}>
      {value}
    </strong>
  );
}

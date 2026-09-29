import { useState } from "react";

interface TitleInputProps {
  value: string;
  className: string;
  /** The new title, or null when it was left empty, unchanged, or cancelled. */
  onDone: (title: string | null) => void;
}

/** A title text box: Enter or leaving it saves, Escape cancels. */
export function TitleInput({ value, className, onDone }: TitleInputProps) {
  return (
    <input
      className={className}
      aria-label="Document title"
      defaultValue={value}
      maxLength={120}
      autoFocus
      onFocus={(e) => e.currentTarget.select()}
      onBlur={(e) => {
        const title = e.currentTarget.value.trim();
        onDone(title && title !== value ? title : null);
      }}
      onKeyDown={(e) => {
        if (e.key === "Escape") e.currentTarget.value = value;
        if (e.key === "Enter" || e.key === "Escape") e.currentTarget.blur();
      }}
    />
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

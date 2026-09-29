import { useState } from "react";

import { cx } from "../lib/cx";
import { useLongPress } from "../lib/longPress";
import { TEMPLATE_LABELS } from "../lib/templates";
import type { DocumentSummary } from "../lib/types";
import { ContextMenu } from "./ContextMenu";
import { TitleInput } from "./EditableTitle";
import { Icon } from "./Icon";

interface DocListItemProps {
  doc: DocumentSummary;
  active: boolean;
  onOpen: () => void;
  onPrefetch: () => void;
  onRename: (title: string) => void;
  onDelete: () => void;
}

/** A saved document in the sidebar. Right-click, or touch and hold, to rename or delete it. */
export function DocListItem({ doc, active, onOpen, onPrefetch, onRename, onDelete }: DocListItemProps) {
  const [menuAt, setMenuAt] = useState<{ x: number; y: number } | null>(null);
  const [renaming, setRenaming] = useState(false);
  const longPress = useLongPress((x, y) => setMenuAt({ x, y }));

  return (
    <li
      className={cx(active && "is-active", menuAt && "is-menu")}
      onContextMenu={(e) => {
        e.preventDefault();
        setMenuAt({ x: e.clientX, y: e.clientY });
      }}
      {...longPress}
    >
      {renaming ? (
        <TitleInput
          className="doclist__rename"
          value={doc.title}
          onDone={(title) => {
            setRenaming(false);
            if (title) onRename(title);
          }}
        />
      ) : (
        <button type="button" className="doclist__open" onPointerEnter={onPrefetch} onFocus={onPrefetch} onClick={onOpen}>
          <span className="doclist__title">{doc.title}</span>
          <span className="doclist__meta">{TEMPLATE_LABELS[doc.template]}</span>
        </button>
      )}

      {menuAt && (
        <ContextMenu
          at={menuAt}
          onClose={() => setMenuAt(null)}
          items={[
            {
              label: "Rename",
              icon: <Icon d="M12 20h9M16.4 3.6a2 2 0 0 1 2.8 2.8L7 18.6l-4 1 1-4Z" />,
              onSelect: () => setRenaming(true),
            },
            {
              label: "Delete",
              icon: <Icon d="M4 7h16M10 11v6M14 11v6M5 7l1 12a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />,
              danger: true,
              onSelect: onDelete,
            },
          ]}
        />
      )}
    </li>
  );
}

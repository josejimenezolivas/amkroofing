import { useCallback, useLayoutEffect, useRef, useState, type ReactNode } from "react";

import { cx } from "../lib/cx";
import { useDismiss } from "../lib/dismiss";

export interface MenuItem {
  label: string;
  icon: ReactNode;
  danger?: boolean;
  onSelect: () => void;
}

interface ContextMenuProps {
  at: { x: number; y: number };
  items: MenuItem[];
  onClose: () => void;
}

/** A menu opened at a point, kept inside the window. */
export function ContextMenu({ at, items, onClose }: ContextMenuProps) {
  const ref = useRef<HTMLDivElement>(null);
  const [pos, setPos] = useState(at);
  useDismiss(ref, true, useCallback((open: boolean) => !open && onClose(), [onClose]));

  useLayoutEffect(() => {
    const { width, height } = ref.current!.getBoundingClientRect();
    setPos({
      x: Math.max(8, Math.min(at.x, innerWidth - width - 8)),
      y: Math.max(8, Math.min(at.y, innerHeight - height - 8)),
    });
  }, [at]);

  return (
    <div
      ref={ref}
      className="menu menu--context"
      role="menu"
      style={{ left: pos.x, top: pos.y }}
      onContextMenu={(e) => {
        e.preventDefault();
        e.stopPropagation();
      }}
    >
      {items.map((item) => (
        <button
          key={item.label}
          type="button"
          role="menuitem"
          className={cx("menu__item", item.danger && "menu__item--danger")}
          onClick={() => {
            onClose();
            item.onSelect();
          }}
        >
          {item.icon}
          {item.label}
        </button>
      ))}
    </div>
  );
}

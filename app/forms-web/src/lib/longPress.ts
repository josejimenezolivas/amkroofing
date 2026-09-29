import { useRef, type MouseEvent, type PointerEvent } from "react";

/**
 * Touch-and-hold, the phone's right-click. iOS Safari fires no contextmenu
 * event, so this times the press itself. The click that ends a long press is
 * swallowed so it does not also activate what was pressed.
 */
export function useLongPress(onLongPress: (x: number, y: number) => void, ms = 500) {
  const timer = useRef<number>();
  const start = useRef<{ x: number; y: number } | null>(null);
  const fired = useRef(false);

  const cancel = () => {
    window.clearTimeout(timer.current);
    start.current = null;
  };

  return {
    onPointerDown: (e: PointerEvent) => {
      if (e.pointerType !== "touch") return;
      const { clientX: x, clientY: y } = e;
      fired.current = false;
      start.current = { x, y };
      timer.current = window.setTimeout(() => {
        fired.current = true;
        onLongPress(x, y);
      }, ms);
    },
    onPointerMove: (e: PointerEvent) => {
      if (start.current && Math.hypot(e.clientX - start.current.x, e.clientY - start.current.y) > 10) cancel();
    },
    onPointerUp: cancel,
    onPointerCancel: cancel,
    onClickCapture: (e: MouseEvent) => {
      if (!fired.current) return;
      fired.current = false;
      e.preventDefault();
      e.stopPropagation();
    },
  };
}

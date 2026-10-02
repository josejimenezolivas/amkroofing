import { useEffect, useLayoutEffect, useRef } from "react";

/** A point on the unscaled page that should sit under a point on the screen. */
interface Anchor {
  x: number;
  y: number;
  clientX: number;
  clientY: number;
}

/** Safari's trackpad pinch; not in the DOM typings. */
interface GestureEvent extends UIEvent {
  scale: number;
  clientX: number;
  clientY: number;
}

const distance = (a: Touch, b: Touch) => Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
const middle = (a: Touch, b: Touch) => ({ clientX: (a.clientX + b.clientX) / 2, clientY: (a.clientY + b.clientY) / 2 });

/** Scroll the stage so the anchor's page point lands under its screen point. */
function place(stage: HTMLElement, frame: HTMLElement, scale: number, anchor: Anchor) {
  const rect = frame.getBoundingClientRect();
  stage.scrollLeft += rect.left + anchor.x * scale - anchor.clientX;
  stage.scrollTop += rect.top + anchor.y * scale - anchor.clientY;
}

/**
 * Pinching the page, with two fingers or a trackpad, zooms it around the
 * pinched point and leaves it at that zoom. Only the page scales; the browser's
 * own zoom, which would scale the whole editor, is kept out of it.
 */
export function usePinchZoom(
  stage: HTMLElement | null,
  frame: HTMLElement | null,
  scale: number,
  setScale: (scale: number) => void,
  min: number,
  max: number,
) {
  const latest = useRef({ scale, setScale, min, max });
  latest.current = { scale, setScale, min, max };
  const pending = useRef<Anchor | null>(null);

  useLayoutEffect(() => {
    if (!pending.current || !stage || !frame) return;
    place(stage, frame, scale, pending.current);
    pending.current = null;
  });

  useEffect(() => {
    if (!stage || !frame) return;

    const anchorAt = (clientX: number, clientY: number): Anchor => {
      const rect = frame.getBoundingClientRect();
      const { scale } = latest.current;
      return { x: (clientX - rect.left) / scale, y: (clientY - rect.top) / scale, clientX, clientY };
    };

    const zoomTo = (next: number, anchor: Anchor) => {
      const { scale, setScale, min, max } = latest.current;
      const clamped = Math.min(max, Math.max(min, next));
      if (clamped === scale) {
        place(stage, frame, scale, anchor);
      } else {
        pending.current = anchor;
        setScale(clamped);
      }
    };

    // Two fingers. The page point first pinched follows the fingers, so they pan as well as zoom.
    let pinch: { distance: number; scale: number; x: number; y: number } | null = null;
    const onTouchStart = (e: TouchEvent) => {
      if (e.touches.length !== 2) return;
      const [a, b] = [e.touches[0], e.touches[1]];
      const mid = middle(a, b);
      const { x, y } = anchorAt(mid.clientX, mid.clientY);
      pinch = { distance: distance(a, b), scale: latest.current.scale, x, y };
    };
    const onTouchMove = (e: TouchEvent) => {
      if (!pinch || e.touches.length !== 2) return;
      e.preventDefault();
      const [a, b] = [e.touches[0], e.touches[1]];
      zoomTo((pinch.scale * distance(a, b)) / pinch.distance, { x: pinch.x, y: pinch.y, ...middle(a, b) });
    };
    const onTouchEnd = (e: TouchEvent) => {
      if (e.touches.length < 2) pinch = null;
    };

    // Trackpad pinch in Chrome and Firefox, and Ctrl + mouse wheel.
    const onWheel = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      const step = Math.max(-25, Math.min(25, e.deltaY));
      zoomTo(latest.current.scale * Math.exp(-step * 0.01), anchorAt(e.clientX, e.clientY));
    };

    // Trackpad pinch in Safari. On iPhone these come alongside the touches, which already zoom.
    let gesture: { scale: number } | null = null;
    const onGestureStart = (e: Event) => {
      e.preventDefault();
      gesture = pinch ? null : { scale: latest.current.scale };
    };
    const onGestureChange = (e: Event) => {
      e.preventDefault();
      if (!gesture || pinch) return;
      const g = e as GestureEvent;
      zoomTo(gesture.scale * g.scale, anchorAt(g.clientX, g.clientY));
    };
    const onGestureEnd = () => {
      gesture = null;
    };

    const active = { passive: false };
    stage.addEventListener("touchstart", onTouchStart, { passive: true });
    stage.addEventListener("touchmove", onTouchMove, active);
    stage.addEventListener("touchend", onTouchEnd);
    stage.addEventListener("touchcancel", onTouchEnd);
    stage.addEventListener("wheel", onWheel, active);
    stage.addEventListener("gesturestart", onGestureStart, active);
    stage.addEventListener("gesturechange", onGestureChange, active);
    stage.addEventListener("gestureend", onGestureEnd);
    return () => {
      stage.removeEventListener("touchstart", onTouchStart);
      stage.removeEventListener("touchmove", onTouchMove);
      stage.removeEventListener("touchend", onTouchEnd);
      stage.removeEventListener("touchcancel", onTouchEnd);
      stage.removeEventListener("wheel", onWheel);
      stage.removeEventListener("gesturestart", onGestureStart);
      stage.removeEventListener("gesturechange", onGestureChange);
      stage.removeEventListener("gestureend", onGestureEnd);
    };
  }, [stage, frame]);
}

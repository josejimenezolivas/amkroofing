import { useEffect, useState } from "react";

/** An element's content-box size, kept current as it changes. Zero until it mounts. */
export function useSize(el: HTMLElement | null) {
  const [size, setSize] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (!el) return;
    const observer = new ResizeObserver(([entry]) => {
      const { inlineSize: width, blockSize: height } = entry.contentBoxSize[0];
      setSize({ width, height });
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [el]);

  return size;
}

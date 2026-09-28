/**
 * Tighten any `[data-fit]` line whose text is wider than its box.
 *
 * The terms are placed one source line per box, at the width the line had in
 * the original PDF. The local Times can set the same words a few percent
 * wider; a line that wrapped would land on the next absolutely placed line.
 * Measuring against the box is scale-free, so the editor's zoom is irrelevant.
 *
 * `app/forms-api/app/pdf.py` runs the same measurement before printing,
 * because the server's fonts are not the browser's.
 */
export function fitLines(root: ParentNode = document): void {
  const range = document.createRange();
  for (const el of Array.from(root.querySelectorAll<HTMLElement>("[data-fit]"))) {
    el.style.letterSpacing = "";
    const chars = el.textContent?.length ?? 0;
    const box = el.getBoundingClientRect();
    if (!chars || !box.width) continue;

    range.selectNodeContents(el);
    const overflow = range.getBoundingClientRect().width - box.width;
    if (overflow <= 0) continue;

    const scale = box.width / el.offsetWidth;
    el.style.letterSpacing = `${-overflow / scale / chars}px`;
  }
}

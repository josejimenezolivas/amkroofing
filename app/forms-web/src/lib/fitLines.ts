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
 *
 * Reset, measure, then write, in three passes: a measurement after any style
 * write forces a fresh layout of every page, once per line otherwise.
 */
export function fitLines(root: ParentNode = document): void {
  const lines = Array.from(root.querySelectorAll<HTMLElement>("[data-fit]"));
  for (const el of lines) el.style.letterSpacing = "";

  const range = document.createRange();
  const spacing = lines.map((el) => {
    const chars = el.textContent?.length ?? 0;
    const box = el.getBoundingClientRect();
    if (!chars || !box.width) return "";

    range.selectNodeContents(el);
    const overflow = range.getBoundingClientRect().width - box.width;
    if (overflow <= 0) return "";

    const scale = box.width / el.offsetWidth;
    return `${-overflow / scale / chars}px`;
  });

  lines.forEach((el, i) => {
    el.style.letterSpacing = spacing[i];
  });
}

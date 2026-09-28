import { TERMS_SHEETS } from "../termsLines";

export interface TermsBlock {
  heading: boolean;
  text: string;
}

/**
 * Reflow the terms back into prose.
 *
 * `termsLines.ts` stores the original's typeset lines so the classic pages can
 * reproduce them exactly. The modern layout sets its own measure, so it needs
 * paragraphs instead. A justified line is by definition not the last line of
 * its paragraph, which is all the structure we need to stitch them back.
 */
function build(): TermsBlock[] {
  const blocks: TermsBlock[] = [];
  let buffer: string[] = [];

  for (const sheet of TERMS_SHEETS) {
    for (const column of sheet.columns) {
      for (const line of column) {
        buffer.push(line.t.trim());
        if (line.j) continue;

        const text = buffer.join(" ").replace(/\s+/g, " ").trim();
        buffer = [];
        if (!text) continue;
        // Section headings are the short, fully capitalised standalone lines.
        blocks.push({
          text,
          heading: text.length <= 55 && text === text.toUpperCase(),
        });
      }
    }
  }

  return blocks;
}

export const TERMS_BLOCKS: TermsBlock[] = build();

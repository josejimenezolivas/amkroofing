/**
 * The agreement's fixed legal prose, transcribed from the reference contract.
 *
 * The wording lives in `legal.json` because the Word export needs it too, and
 * the server reads that file directly: one copy, so it cannot drift between
 * the two layouts and the two output formats.
 *
 * Entries that are arrays are lines the original sets by hand. The classic
 * layout keeps those breaks; the modern one and Word reflow them.
 */
import legal from "./legal.json";

export const LEGAL = legal as {
  readonly [K in keyof typeof legal]: (typeof legal)[K] extends readonly string[]
    ? readonly string[]
    : string;
};

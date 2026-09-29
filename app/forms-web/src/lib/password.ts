/**
 * The live checklist shown while choosing a password. forms-api/app/password.py
 * enforces the same rules; keep the two in step.
 */

export const MIN_CHARS = 10;
const MAX_CHARS = 256;
const REQUIRED_CLASSES = 3;

const COMMON = new Set([
  "123456", "1234567", "12345678", "123456789", "1234567890", "12345",
  "password", "passwd", "pass", "letmein", "welcome", "admin", "administrator",
  "qwerty", "qwertyuiop", "asdfgh", "asdfghjkl", "zxcvbn", "zxcvbnm", "qazwsx",
  "iloveyou", "princess", "sunshine", "monkey", "dragon", "football",
  "baseball", "superman", "batman", "starwars", "pokemon", "trustno",
  "abc123", "abcd1234", "a1b2c3d4", "test", "testing", "temp", "changeme",
  "secret", "master", "shadow", "michael", "jordan", "hunter", "freedom",
  "whatever", "computer", "internet", "samsung", "google", "facebook",
  "login", "root", "toor", "guest", "user", "default", "system",
  "roofing", "roofer", "amkroofing", "amk",
]);

const LEET: Record<string, string> = {
  "@": "a", "4": "a", "8": "b", "(": "c", "3": "e", "6": "g", "1": "i",
  "!": "i", "|": "i", "0": "o", "5": "s", $: "s", "7": "t", "+": "t",
  "2": "z", "9": "g",
};

function isCommon(password: string): boolean {
  const lowered = password.toLowerCase();
  const folded = [...lowered].map((c) => LEET[c] ?? c).join("");
  const candidates = new Set([
    lowered,
    folded,
    lowered.replace(/[^a-z]/g, ""),
    folded.replace(/[^a-z]/g, ""),
  ]);
  for (const candidate of candidates) {
    if (!candidate) continue;
    if (COMMON.has(candidate)) return true;
    for (const common of COMMON) {
      if (common.length >= 6 && candidate.startsWith(common) && candidate.length - common.length <= 4) {
        return true;
      }
    }
  }
  return false;
}

function identity(email: string, name: string): string[] {
  const [local = "", domain = ""] = email.toLowerCase().split("@");
  return [local, domain.split(".")[0] ?? "", name.toLowerCase()]
    .flatMap((source) => source.split(/[^a-z0-9]+/))
    .filter((chunk) => chunk.length >= 4);
}

function hasRun(password: string): boolean {
  const lowered = password.toLowerCase();
  let repeat = 1;
  let ascending = 1;
  let descending = 1;
  for (let i = 1; i < lowered.length; i += 1) {
    const previous = lowered.charCodeAt(i - 1);
    const current = lowered.charCodeAt(i);
    repeat = current === previous ? repeat + 1 : 1;
    ascending = current === previous + 1 ? ascending + 1 : 1;
    descending = current === previous - 1 ? descending + 1 : 1;
    if (Math.max(repeat, ascending, descending) >= 4) return true;
  }
  return false;
}

export interface Rule {
  label: string;
  met: boolean;
  message: string;
}

export type Strength = "weak" | "fair" | "good" | "strong";

export interface Evaluation {
  rules: Rule[];
  acceptable: boolean;
  strength: Strength;
  /** The first unmet rule, worded as advice. */
  message: string;
}

export function evaluatePassword(password: string, email: string, name: string): Evaluation {
  const classes = [/[a-z]/, /[A-Z]/, /[0-9]/, /[^A-Za-z0-9]/].filter((re) => re.test(password)).length;
  const lowered = password.toLowerCase();
  const typed = password.length > 0;

  const rules: Rule[] = [
    {
      label: `At least ${MIN_CHARS} characters`,
      met: password.length >= MIN_CHARS && password.length <= MAX_CHARS,
      message:
        password.length > MAX_CHARS
          ? `Keep your password under ${MAX_CHARS} characters.`
          : `Use at least ${MIN_CHARS} characters.`,
    },
    {
      label: `${REQUIRED_CLASSES} of these 4: lowercase, uppercase, number, symbol`,
      met: classes >= REQUIRED_CLASSES,
      message: `Mix at least ${REQUIRED_CLASSES} of: lowercase, uppercase, number, symbol.`,
    },
    {
      label: "Not a commonly used password",
      met: typed && !isCommon(password),
      message: "That password shows up in breach lists. Pick something else.",
    },
    {
      label: "No part of your name or email",
      met: typed && !identity(email, name).some((fragment) => lowered.includes(fragment)),
      message: "Leave your name and email out of your password.",
    },
    {
      label: 'No runs like "aaaa" or "1234"',
      met: typed && !hasRun(password),
      message: 'Avoid repeated or sequential runs like "aaaa" or "1234".',
    },
  ];

  const unmet = rules.filter((rule) => !rule.met);
  const acceptable = typed && unmet.length === 0;
  let strength: Strength = "weak";
  if (acceptable) {
    const roomy = password.length >= MIN_CHARS + 4;
    strength = (roomy && classes === 4) || password.length >= MIN_CHARS + 10 ? "strong" : "good";
  } else if (unmet.length === 1 && password.length >= MIN_CHARS - 2) {
    strength = "fair";
  }
  return { rules, acceptable, strength, message: unmet[0]?.message ?? "" };
}

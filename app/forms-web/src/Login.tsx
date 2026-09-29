import { useEffect, useState, type FormEvent, type ReactNode } from "react";

import logo from "./assets/amk-logo-light.png";
import { auth } from "./lib/api";
import { cx } from "./lib/cx";
import { evaluatePassword } from "./lib/password";
import type { Account } from "./lib/types";
import "./styles/login.css";

const LAST_METHOD_KEY = "amk.forms.last-method";
type Method = "email" | "google";

const STRENGTH_LABEL = { weak: "Weak", fair: "Fair", good: "Good", strong: "Strong" } as const;
const STRENGTH_WIDTH = { weak: 25, fair: 50, good: 75, strong: 100 } as const;

function lastMethod(): Method | null {
  try {
    const value = localStorage.getItem(LAST_METHOD_KEY);
    return value === "email" || value === "google" ? value : null;
  } catch {
    return null;
  }
}

function remember(method: Method): void {
  try {
    localStorage.setItem(LAST_METHOD_KEY, method);
  } catch {
    // Private mode; the badge is a nicety.
  }
}

function looksLikeEmail(value: string): boolean {
  return /^[^\s@]+@[^\s@.]+(\.[^\s@.]+)+$/.test(value.trim());
}

/** What the page was opened with: a Google error to show, or an invite to accept. */
function readUrl() {
  const params = new URLSearchParams(window.location.search);
  const token = params.get("invite");
  const email = params.get("email");
  return { error: params.get("auth_error"), invite: token && email ? { token, email } : null };
}

/** Drop the error from the address bar so a reload does not show it again. */
function clearErrorFromUrl(): void {
  const params = new URLSearchParams(window.location.search);
  if (!params.has("auth_error")) return;
  params.delete("auth_error");
  const rest = params.toString();
  window.history.replaceState(null, "", `${window.location.pathname}${rest ? `?${rest}` : ""}`);
}

function clearInviteFromUrl(): void {
  window.history.replaceState(null, "", window.location.pathname);
}

interface LoginProps {
  google: boolean;
  notice?: string;
  onSignedIn: (account: Account) => void;
}

export function Login({ google, notice, onSignedIn }: LoginProps) {
  const [opened] = useState(readUrl);
  const invite = opened.invite;
  useEffect(clearErrorFromUrl, []);
  const [email, setEmail] = useState(invite?.email ?? "");
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState(opened.error ?? "");
  const [busy, setBusy] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [recent] = useState(lastMethod);

  const check = evaluatePassword(password, email, name);
  const emailProblem =
    emailTouched && !invite && email.trim() && !looksLikeEmail(email)
      ? "That does not look like an email address."
      : "";

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    if (!invite) {
      if (!looksLikeEmail(email)) return setError("Enter the email address you were invited with.");
      if (!password) return setError("Enter your password.");
    } else {
      if (!check.acceptable) return setError(check.message);
      if (password !== confirm) return setError("The two passwords do not match.");
    }

    setBusy(true);
    try {
      const account = invite
        ? await auth.acceptInvite(invite.email, invite.token, name, password)
        : await auth.login(email, password);
      remember("email");
      if (invite) clearInviteFromUrl();
      onSignedIn(account);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not sign in.");
      setBusy(false);
    }
  }

  function continueWithGoogle() {
    remember("google");
    setBusy(true);
    window.location.assign(auth.googleStart);
  }

  return (
    <div className="gate">
      <header className="gate__top">
        <a className="gate__brand" href="/" aria-label="AMK Roofing home">
          <img src={logo} alt="" />
        </a>
        <span className="gate__section">Forms</span>
      </header>

      <main className="gate__card">
        <header className="gate__header">
          <h1>{invite ? "Set up your account" : "Sign in"}</h1>
          {invite && (
            <p className="gate__sub">
              You were invited as <strong>{invite.email}</strong>. Choose a password to finish.
            </p>
          )}
        </header>

        {notice && !error && (
          <p className="gate__notice" role="status">
            {notice}
          </p>
        )}

        <form className="gate__form" onSubmit={(e) => void submit(e)} noValidate>
          {invite ? (
            <Field label="Full name" htmlFor="gate-name">
              <input
                id="gate-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="Your full name"
                autoComplete="name"
                autoFocus
              />
            </Field>
          ) : (
            <Field label="Email" htmlFor="gate-email" hint={emailProblem} invalid={!!emailProblem}>
              <input
                id="gate-email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                onBlur={() => setEmailTouched(true)}
                placeholder="you@example.com"
                autoComplete="email"
                autoFocus
              />
            </Field>
          )}

          <Field label="Password" htmlFor="gate-password">
            <SecretInput
              id="gate-password"
              value={password}
              onChange={setPassword}
              autoComplete={invite ? "new-password" : "current-password"}
            />
            {invite && (
              <div className="gate__strength">
                <div className="gate__track">
                  <span
                    className={cx("gate__bar", password && `is-${check.strength}`)}
                    style={{ width: password ? `${STRENGTH_WIDTH[check.strength]}%` : 0 }}
                  />
                </div>
                <p className="gate__strength-label" role="status">
                  {password
                    ? `Password strength: ${STRENGTH_LABEL[check.strength]}`
                    : "Your password needs all of the following."}
                </p>
                <ul className="gate__rules">
                  {check.rules.map((rule) => (
                    <li key={rule.label} className={cx(rule.met && "is-met")}>
                      <span aria-hidden="true">{rule.met ? "✓" : "○"}</span>
                      {rule.label}
                      <span className="gate__sr">{rule.met ? " — met" : " — not met yet"}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </Field>

          {invite && (
            <Field
              label="Confirm password"
              htmlFor="gate-confirm"
              hint={confirm && password !== confirm ? "Does not match yet." : confirm ? "Passwords match." : ""}
              ok={!!confirm && password === confirm}
            >
              <SecretInput
                id="gate-confirm"
                value={confirm}
                onChange={setConfirm}
                autoComplete="new-password"
                placeholder="Re-enter your password"
              />
            </Field>
          )}

          <button type="submit" className="gate__primary" disabled={busy}>
            {busy ? "One moment…" : invite ? "Create account" : "Continue with email"}
            {!busy && <ArrowRight />}
            {!busy && recent === "email" && !invite && <span className="gate__badge">Last used</span>}
          </button>
        </form>

        {google && (
          <>
            <div className="gate__divider">
              <span>or</span>
            </div>
            <button type="button" className="gate__google" onClick={continueWithGoogle} disabled={busy}>
              <GoogleMark />
              Continue with Google
              {recent === "google" && <span className="gate__badge">Last used</span>}
            </button>
          </>
        )}

        {error && (
          <p className="gate__error" role="alert">
            {error}
          </p>
        )}

        <footer className="gate__footer">
          Access is by invitation. <a href="/">amkroofing.com</a>
        </footer>
      </main>
    </div>
  );
}

function Field(props: {
  label: string;
  htmlFor: string;
  hint?: string;
  invalid?: boolean;
  ok?: boolean;
  children: ReactNode;
}) {
  return (
    <div className={cx("gate__field", props.invalid && "is-invalid")}>
      <label htmlFor={props.htmlFor}>{props.label}</label>
      {props.children}
      {props.hint && (
        <p className={cx("gate__hint", props.invalid && "is-error", props.ok && "is-ok")}>{props.hint}</p>
      )}
    </div>
  );
}

function SecretInput(props: {
  id: string;
  value: string;
  onChange: (value: string) => void;
  autoComplete: string;
  placeholder?: string;
}) {
  const [shown, setShown] = useState(false);
  return (
    <div className="gate__secret">
      <input
        id={props.id}
        type={shown ? "text" : "password"}
        value={props.value}
        onChange={(e) => props.onChange(e.target.value)}
        placeholder={props.placeholder ?? "••••••••••"}
        autoComplete={props.autoComplete}
      />
      <button
        type="button"
        className="gate__reveal"
        aria-label={shown ? "Hide password" : "Show password"}
        aria-pressed={shown}
        tabIndex={-1}
        onClick={() => setShown((s) => !s)}
      >
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
          <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7-10-7-10-7Z" />
          <circle cx="12" cy="12" r="3" />
          {shown && <line x1="3" y1="21" x2="21" y2="3" />}
        </svg>
      </button>
    </div>
  );
}

function ArrowRight() {
  return (
    <svg className="gate__arrow" width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M5 12h14M13 6l6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function GoogleMark() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
      <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
      <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.06H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.94l2.85-2.22.81-.63z" />
      <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.06l3.66 2.84c.87-2.6 3.3-4.52 6.16-4.52z" />
    </svg>
  );
}

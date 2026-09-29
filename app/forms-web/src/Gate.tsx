import { useCallback, useEffect, useState } from "react";

import { App } from "./App";
import { Login } from "./Login";
import { auth, whenSignedOut } from "./lib/api";
import type { Account } from "./lib/types";

type Session =
  | { kind: "checking" }
  | { kind: "out"; notice?: string }
  | { kind: "in"; account: Account };

/** Shows the forms to a signed-in user and the sign-in page to everyone else. */
export function Gate() {
  const [session, setSession] = useState<Session>({ kind: "checking" });
  const [google, setGoogle] = useState(false);

  useEffect(() => {
    whenSignedOut(() =>
      setSession({ kind: "out", notice: "Your session ended. Sign in again to keep working." }),
    );
    // Both before the first paint, so the Google button does not pop in late.
    void Promise.allSettled([auth.config(), auth.me()]).then(([config, me]) => {
      if (config.status === "fulfilled") setGoogle(config.value.google);
      setSession(me.status === "fulfilled" ? { kind: "in", account: me.value } : { kind: "out" });
    });
  }, []);

  const signOut = useCallback(async () => {
    await auth.logout().catch(() => {});
    setSession({ kind: "out" });
  }, []);

  // Blank while checking: a signed-in user should not see the gate flash past.
  if (session.kind === "checking") return null;
  if (session.kind === "out") {
    return (
      <Login
        google={google}
        notice={session.notice}
        onSignedIn={(account) => setSession({ kind: "in", account })}
      />
    );
  }
  return <App account={session.account} onSignOut={signOut} />;
}

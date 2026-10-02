import logo from "./assets/amk-logo-light.png";
import { Icon, MENU, NEW_DOCUMENT } from "./components/Icon";
import { storedTheme } from "./lib/theme";
import "./styles/login.css";
import "./styles/skeleton.css";

const SIGNED_IN_KEY = "amk.forms.signed-in";

/** Remember how the last session check came out, so the next visit's placeholder matches. */
export function rememberSignedIn(signedIn: boolean): void {
  try {
    if (signedIn) localStorage.setItem(SIGNED_IN_KEY, "1");
    else localStorage.removeItem(SIGNED_IN_KEY);
  } catch {
    // Private mode: the sign-in placeholder is shown instead.
  }
}

function wasSignedIn(): boolean {
  try {
    return localStorage.getItem(SIGNED_IN_KEY) === "1";
  } catch {
    return false;
  }
}

/**
 * Shown while the session check is in flight, which takes a few seconds when
 * the API has to start up. It is shaped like the page that will replace it:
 * the editor for someone signed in last time, the sign-in card for everyone else.
 */
export function Loading() {
  return wasSignedIn() ? <AppSkeleton /> : <GateSkeleton />;
}

function GateSkeleton() {
  return (
    <div className="gate" aria-busy="true">
      <header className="gate__top">
        <a className="gate__brand" href="/" aria-label="AMK Roofing home">
          <img src={logo} alt="" />
        </a>
        <span className="gate__section">Forms</span>
      </header>

      <main className="gate__card">
        <span className="skel-sr" role="status">
          Loading…
        </span>
        <header className="gate__header">
          <span className="skel skel--title" />
        </header>
        <div className="gate__form">
          {[0, 1].map((field) => (
            <div key={field} className="gate__field">
              <span className="skel skel--label" />
              <span className="skel skel--input" />
            </div>
          ))}
          <span className="skel skel--button skel--primary" />
        </div>
        <div className="gate__divider">
          <span>or</span>
        </div>
        <span className="skel skel--button" />
        <footer className="gate__footer">
          Access is by invitation. <a href="/">amkroofing.com</a>
        </footer>
      </main>
    </div>
  );
}

function AppSkeleton() {
  return (
    <div className="app" data-theme={storedTheme()} aria-busy="true">
      <aside className="sidebar">
        <header className="sidebar__top">
          <a className="sidebar__brand" href="/" aria-label="AMK Roofing home">
            <img src={logo} alt="" />
          </a>
          <span className="sidebar__section">Forms</span>
        </header>
        <div className="sidebar__new is-active skel-static">
          <Icon d={NEW_DOCUMENT} />
          New document
        </div>
        <h2 className="recents">
          <span className="recents__toggle skel-static">Recents</span>
        </h2>
        <ul className="doclist">
          {[0, 1, 2, 3].map((row) => (
            <li key={row} className="skel-doc">
              <span className="skel skel--doc-title" />
              <span className="skel skel--doc-meta" />
            </li>
          ))}
        </ul>
        <div className="account">
          <div className="account__trigger skel-static">
            <span className="skel skel--avatar" />
            <span className="account__who">
              <span className="skel skel--name" />
              <span className="skel skel--email" />
            </span>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="mobilebar">
          <span className="navtoggle">
            <Icon d={MENU} />
          </span>
          <span className="mobilebar__title">New document</span>
        </header>
        <div className="gallery">
          {[0, 1].map((card) => (
            <div key={card} className="preview skel-preview">
              <div className="preview__banner">
                <span className="preview__text">
                  <span className="skel skel--name" />
                  <span className="skel skel--email" />
                </span>
              </div>
              <div className="skel-page">
                <span className="skel skel--letterhead" />
                {[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((line) => (
                  <span key={line} className="skel skel--line" />
                ))}
              </div>
            </div>
          ))}
        </div>
      </main>
      <span className="skel-sr" role="status">
        Loading…
      </span>
    </div>
  );
}

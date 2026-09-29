import { useCallback, useRef, useState } from "react";

import { cx } from "../lib/cx";
import { useDismiss } from "../lib/dismiss";
import type { ThemeChoice } from "../lib/theme";
import type { Account } from "../lib/types";

const THEMES: Array<[ThemeChoice, string]> = [
  ["system", "System"],
  ["light", "Light"],
  ["dark", "Dark"],
];

interface AccountMenuProps {
  account: Account;
  theme: ThemeChoice;
  onTheme: (theme: ThemeChoice) => void;
  onSignOut: () => void;
}

/** The signed-in user; opens their settings and sign-out. */
export function AccountMenu({ account, theme, onTheme, onSignOut }: AccountMenuProps) {
  const [open, setOpen] = useState(false);
  const [themesOpen, setThemesOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  const show = useCallback((next: boolean) => {
    setOpen(next);
    setThemesOpen(false);
  }, []);
  useDismiss(ref, open, show);

  return (
    <div className="account" ref={ref}>
      <button
        type="button"
        className="account__trigger"
        aria-haspopup="menu"
        aria-expanded={open}
        onClick={() => show(!open)}
      >
        {account.picture ? (
          <img className="account__avatar" src={account.picture} alt="" referrerPolicy="no-referrer" />
        ) : (
          <span className="account__avatar" aria-hidden="true">
            {account.name.charAt(0).toUpperCase()}
          </span>
        )}
        <span className="account__who">
          <span className="account__name">{account.name}</span>
          <span className="account__email">{account.email}</span>
        </span>
      </button>

      {open && (
        <div className="menu account__menu" role="menu" aria-label="Account">
          <div className="menu__sub">
            <button
              type="button"
              role="menuitem"
              aria-haspopup="menu"
              aria-expanded={themesOpen}
              className={cx("menu__item", themesOpen && "is-open")}
              onPointerEnter={() => setThemesOpen(true)}
              onClick={() => setThemesOpen((o) => !o)}
              onKeyDown={(e) => e.key === "ArrowRight" && setThemesOpen(true)}
            >
              <ThemeIcon />
              Theme
              <ChevronIcon />
            </button>

            {themesOpen && (
              <div className="menu menu--flyout" role="menu" aria-label="Theme">
                {THEMES.map(([value, label]) => (
                  <button
                    key={value}
                    type="button"
                    role="menuitemradio"
                    aria-checked={theme === value}
                    className="menu__item"
                    onClick={() => onTheme(value)}
                  >
                    {label}
                    {theme === value && <CheckIcon />}
                  </button>
                ))}
              </div>
            )}
          </div>

          <hr className="menu__rule" />

          <button
            type="button"
            role="menuitem"
            className="menu__item"
            onPointerEnter={() => setThemesOpen(false)}
            onClick={onSignOut}
          >
            <SignOutIcon />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}

const Icon = ({ className, d }: { className?: string; d: string }) => (
  <svg className={cx("icon", className)} viewBox="0 0 24 24" aria-hidden="true">
    <path d={d} fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" />
  </svg>
);

const ThemeIcon = () => (
  <Icon d="M12 20a8 8 0 1 0 0-16m0 16a8 8 0 1 1 0-16m0 16V4m0 3.5h5.5M12 12h8M12 16.5h5.5" />
);

const SignOutIcon = () => <Icon d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4M10 16l-4-4 4-4M6 12h10" />;

const ChevronIcon = () => <Icon className="menu__end" d="m10 7 5 5-5 5" />;

const CheckIcon = () => <Icon className="menu__end" d="m5 12.5 4.5 4.5L19 7.5" />;

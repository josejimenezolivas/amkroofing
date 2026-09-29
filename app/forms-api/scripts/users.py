"""Manage who may sign in to the forms.

    .venv/bin/python scripts/users.py invite someone@example.com
    .venv/bin/python scripts/users.py list
    .venv/bin/python scripts/users.py remove someone@example.com

Without DATABASE_URL this edits the local compose.yaml Postgres. With the
production connection string in the environment it edits production:

    DATABASE_URL=postgresql://... .venv/bin/python scripts/users.py \\
        invite someone@example.com --site https://www.amkroofing.com

A non-local --site with the local database is refused, since that link could
never work.

`invite` prints a one-time link, good for 7 days, for choosing a password. An
invited person can also just use "Continue with Google" with that address.
Inviting someone again issues a new link, which is how a password is reset.
"""

import argparse
import sys
import urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import accounts, db  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(dest="command", required=True)
    invite = commands.add_parser("invite", help="let an email in and print its invite link")
    invite.add_argument("email")
    invite.add_argument("--site", default="http://localhost:5173", help="origin the link points at")
    commands.add_parser("list", help="show everyone who may sign in")
    remove = commands.add_parser("remove", help="remove a user and sign them out everywhere")
    remove.add_argument("email")
    args = parser.parse_args()

    target = urllib.parse.urlsplit(db.url())
    print(f"[database] {target.hostname}{target.path}", file=sys.stderr)
    local = ("127.0.0.1", "localhost")
    if args.command == "invite" and target.hostname in local and urllib.parse.urlsplit(args.site).hostname not in local:
        raise SystemExit(
            f"Refusing to put a {args.site} link into the local database: DATABASE_URL is unset or empty. "
            "Set it to the production connection string."
        )
    db.migrate()

    if args.command == "list":
        for user in accounts.list_users():
            ways = [w for w, on in (("password", user.password_hash), ("invite pending", user.invite_hash)) if on]
            last = user.last_login_at.strftime("%Y-%m-%d") if user.last_login_at else "never"
            print(f"{user.email:40} last sign-in {last:10}  {', '.join(ways)}")
        return

    email = accounts.normalize_email(args.email)
    if email is None:
        raise SystemExit(f"Not an email address: {args.email}")

    if args.command == "invite":
        token = accounts.invite(email)
        query = urllib.parse.urlencode({"invite": token, "email": email})
        print(f"{args.site.rstrip('/')}/forms/?{query}")
    elif args.command == "remove":
        if not accounts.remove_user(email):
            raise SystemExit(f"No such user: {email}")
        print(f"Removed {email}")


if __name__ == "__main__":
    main()

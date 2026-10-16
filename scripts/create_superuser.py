"""
Create (or reset) an admin user.

Credentials are never hardcoded. They are read from, in order:
  1. --email / --password arguments
  2. DRONEIMS_ADMIN_EMAIL / DRONEIMS_ADMIN_PASSWORD environment variables
  3. an interactive prompt (password is not echoed)

Usage:
  python scripts/create_superuser.py --email admin@example.com
  docker compose exec backend python scripts/create_superuser.py --email admin@example.com
"""
from __future__ import annotations

import argparse
import asyncio
import getpass
import os
import sys

# Allow running from the repo root without installing the package.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.rbac import Role  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.db.session import AsyncSessionLocal  # noqa: E402
from app.repositories.users import UsersRepository  # noqa: E402

MIN_PASSWORD_LENGTH = 12


def _resolve_credentials(args: argparse.Namespace) -> tuple[str, str]:
    email = (args.email or os.getenv("DRONEIMS_ADMIN_EMAIL") or "").strip().lower()
    if not email:
        email = input("Admin email: ").strip().lower()

    password = args.password or os.getenv("DRONEIMS_ADMIN_PASSWORD") or ""
    if not password:
        password = getpass.getpass("Admin password: ")
        if password != getpass.getpass("Confirm password: "):
            raise SystemExit("Passwords do not match.")

    if "@" not in email:
        raise SystemExit("A valid email is required (it is the login username).")
    if len(password) < MIN_PASSWORD_LENGTH:
        raise SystemExit(f"Password must be at least {MIN_PASSWORD_LENGTH} characters.")
    return email, password


async def create_superuser(email: str, password: str, full_name: str | None) -> None:
    async with AsyncSessionLocal() as session:
        repo = UsersRepository(session)
        user = await repo.get_by_email(email)
        if user:
            user.hashed_password = hash_password(password)
            user.role = Role.admin.value
            user.is_active = True
            action = "updated"
        else:
            await repo.create(
                email=email,
                hashed_password=hash_password(password),
                full_name=full_name,
                role=Role.admin.value,
            )
            action = "created"
        await session.commit()
    print(f"Admin user {action}: {email}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or reset a DroneIMS admin user.")
    parser.add_argument("--email", help="Admin email (used as the login username)")
    parser.add_argument("--password", help="Admin password (prefer the prompt or env var)")
    parser.add_argument("--full-name", default=None, help="Optional display name")
    args = parser.parse_args()

    email, password = _resolve_credentials(args)
    asyncio.run(create_superuser(email, password, args.full_name))


if __name__ == "__main__":
    main()

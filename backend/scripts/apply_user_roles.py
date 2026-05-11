from __future__ import annotations

from pathlib import Path
import sys

from sqlalchemy import text


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.auth import ROLE_ADMIN, ROLE_USER, ensure_users_table  # noqa: E402
from app.database import engine  # noqa: E402


def main() -> None:
    ensure_users_table()

    with engine.begin() as connection:
        connection.execute(text("UPDATE dashboard_users SET role = :role"), {"role": ROLE_USER})
        connection.execute(
            text(
                """
                UPDATE dashboard_users
                SET role = :role, is_active = 1
                WHERE username = :username
                """
            ),
            {"role": ROLE_ADMIN, "username": "admin"},
        )
        rows = connection.execute(
            text(
                """
                SELECT username, role, is_active
                FROM dashboard_users
                ORDER BY role = 'admin' DESC, username ASC
                """
            )
        ).mappings().all()

    for row in rows:
        print(f"{row['username']}:{row['role']}:{int(row['is_active'])}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
import getpass
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.auth import UserCreatePayload, create_user, ensure_users_table  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Creer un utilisateur du dashboard.")
    parser.add_argument("--username", required=True, help="Identifiant de connexion")
    parser.add_argument("--name", required=True, help="Nom affiche dans l'interface")
    parser.add_argument("--password", help="Mot de passe. Si absent, il sera demande.")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Mot de passe: ")
    ensure_users_table()
    user = create_user(
        UserCreatePayload(
            username=args.username,
            displayName=args.name,
            password=password,
        )
    )
    print(f"Utilisateur cree: {user['displayName']} ({user['username']})")


if __name__ == "__main__":
    main()

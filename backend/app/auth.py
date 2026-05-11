from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
from threading import Lock
from datetime import date, datetime, timezone
from typing import Annotated

from fastapi import Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.config import settings
from app.database import engine


SESSION_COOKIE_NAME = "dashboard_session"
PASSWORD_HASH_ALGORITHM = "pbkdf2_sha256"
PASSWORD_HASH_ITERATIONS = 260_000
MIN_PASSWORD_LENGTH = 8
ROLE_ADMIN = "admin"
ROLE_USER = "user"
_users_table_ready = False
_users_table_lock = Lock()


class LoginPayload(BaseModel):
    username: str = Field(min_length=1, max_length=191)
    password: str = Field(min_length=1, max_length=512)


class UserCreatePayload(BaseModel):
    username: str = Field(min_length=1, max_length=191)
    displayName: str = Field(min_length=1, max_length=191)
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=512)


class UserUpdatePayload(BaseModel):
    displayName: str | None = Field(default=None, min_length=1, max_length=191)
    isActive: bool | None = None


class UserPasswordPayload(BaseModel):
    password: str = Field(min_length=MIN_PASSWORD_LENGTH, max_length=512)


def ensure_users_table() -> None:
    global _users_table_ready

    if _users_table_ready:
        return

    with _users_table_lock:
        if _users_table_ready:
            return

        _ensure_users_table()
        _users_table_ready = True


def _ensure_users_table() -> None:
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS dashboard_users (
                    id INT NOT NULL AUTO_INCREMENT,
                    username VARCHAR(191) NOT NULL,
                    display_name VARCHAR(191) NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(32) NOT NULL DEFAULT 'user',
                    is_active TINYINT(1) NOT NULL DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    last_login_at TIMESTAMP NULL DEFAULT NULL,
                    PRIMARY KEY (id),
                    UNIQUE KEY uq_dashboard_users_username (username)
                ) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci
                """
            )
        )
        role_column = connection.execute(
            text(
                """
                SELECT COUNT(*) AS total
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_SCHEMA = DATABASE()
                    AND TABLE_NAME = 'dashboard_users'
                    AND COLUMN_NAME = 'role'
                """
            )
        ).mappings().one()

        if int(role_column["total"]) == 0:
            connection.execute(
                text("ALTER TABLE dashboard_users ADD COLUMN role VARCHAR(32) NOT NULL DEFAULT 'user' AFTER password_hash")
            )

        connection.execute(
            text("UPDATE dashboard_users SET role = :role WHERE role IS NULL OR role = ''"),
            {"role": ROLE_USER},
        )
        admin_count = connection.execute(
            text("SELECT COUNT(*) AS total FROM dashboard_users WHERE role = :role"),
            {"role": ROLE_ADMIN},
        ).mappings().one()

        if int(admin_count["total"]) == 0:
            first_user = connection.execute(
                text(
                    """
                    SELECT id
                    FROM dashboard_users
                    ORDER BY created_at ASC, id ASC
                    LIMIT 1
                    """
                )
            ).mappings().first()

            if first_user:
                connection.execute(
                    text("UPDATE dashboard_users SET role = :role WHERE id = :id"),
                    {"role": ROLE_ADMIN, "id": int(first_user["id"])},
                )


def normalize_username(username: str) -> str:
    return username.strip()


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived_key = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PASSWORD_HASH_ITERATIONS,
    )
    return "$".join(
        [
            PASSWORD_HASH_ALGORITHM,
            str(PASSWORD_HASH_ITERATIONS),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(derived_key).decode("ascii"),
        ]
    )


def verify_password(password: str, password_hash: str) -> bool:
    try:
        algorithm, iterations, salt_value, hash_value = password_hash.split("$", 3)
        if algorithm != PASSWORD_HASH_ALGORITHM:
            return False
        salt = base64.b64decode(salt_value.encode("ascii"), validate=True)
        expected_hash = base64.b64decode(hash_value.encode("ascii"), validate=True)
        candidate_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            int(iterations),
        )
    except (binascii.Error, ValueError, TypeError):
        return False

    return hmac.compare_digest(candidate_hash, expected_hash)


def _to_iso(value: date | datetime | None) -> str | None:
    return value.isoformat() if value else None


def _row_to_user(row: dict[str, object]) -> dict[str, object]:
    role = str(row.get("role") or ROLE_USER)
    return {
        "id": int(row["id"]),
        "username": str(row["username"]),
        "displayName": str(row["display_name"]),
        "role": role,
        "isAdmin": role == ROLE_ADMIN,
        "isActive": bool(row["is_active"]),
        "createdAt": _to_iso(row["created_at"]),
        "lastLoginAt": _to_iso(row["last_login_at"]),
    }


def _get_user_by_id(user_id: int) -> dict[str, object] | None:
    ensure_users_table()
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT id, username, display_name, password_hash, role, is_active, created_at, last_login_at
                FROM dashboard_users
                WHERE id = :id
                """
            ),
            {"id": user_id},
        ).mappings().first()

    return dict(row) if row else None


def _get_user_by_username(username: str) -> dict[str, object] | None:
    ensure_users_table()
    with engine.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT id, username, display_name, password_hash, role, is_active, created_at, last_login_at
                FROM dashboard_users
                WHERE username = :username
                """
            ),
            {"username": normalize_username(username)},
        ).mappings().first()

    return dict(row) if row else None


def authenticate_user(username: str, password: str) -> dict[str, object] | None:
    user = _get_user_by_username(username)
    if not user or not bool(user["is_active"]):
        return None

    if not verify_password(password, str(user["password_hash"])):
        return None

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE dashboard_users SET last_login_at = CURRENT_TIMESTAMP WHERE id = :id"),
            {"id": int(user["id"])},
        )

    refreshed_user = _get_user_by_id(int(user["id"]))
    return _row_to_user(refreshed_user or user)


def list_users() -> list[dict[str, object]]:
    ensure_users_table()
    with engine.connect() as connection:
        rows = connection.execute(
            text(
                """
                SELECT id, username, display_name, role, is_active, created_at, last_login_at
                FROM dashboard_users
                ORDER BY role = 'admin' DESC, is_active DESC, display_name ASC, username ASC
                """
            )
        ).mappings().all()

    return [_row_to_user(dict(row)) for row in rows]


def create_user(payload: UserCreatePayload) -> dict[str, object]:
    ensure_users_table()
    username = normalize_username(payload.username)
    display_name = payload.displayName.strip()

    if not username:
        raise ValueError("L'identifiant est obligatoire.")
    if not display_name:
        raise ValueError("Le nom affiche est obligatoire.")

    try:
        with engine.begin() as connection:
            result = connection.execute(
                text(
                    """
                    INSERT INTO dashboard_users (username, display_name, password_hash)
                    VALUES (:username, :display_name, :password_hash)
                    """
                ),
                {
                    "username": username,
                    "display_name": display_name,
                    "password_hash": hash_password(payload.password),
                },
            )
    except IntegrityError as exc:
        raise ValueError("Cet identifiant existe deja.") from exc

    created_user = _get_user_by_id(int(result.lastrowid))
    if not created_user:
        raise RuntimeError("Utilisateur cree mais introuvable.")

    return _row_to_user(created_user)


def update_user(user_id: int, payload: UserUpdatePayload, current_user_id: int) -> dict[str, object]:
    ensure_users_table()
    existing_user = _get_user_by_id(user_id)
    if not existing_user:
        raise LookupError("Utilisateur introuvable.")

    updates = {}
    if payload.displayName is not None:
        display_name = payload.displayName.strip()
        if not display_name:
            raise ValueError("Le nom affiche est obligatoire.")
        updates["display_name"] = display_name

    if payload.isActive is not None:
        if user_id == current_user_id and payload.isActive is False:
            raise ValueError("Vous ne pouvez pas desactiver votre propre compte.")
        updates["is_active"] = 1 if payload.isActive else 0

    if updates:
        assignments = ", ".join(f"{key} = :{key}" for key in updates)
        with engine.begin() as connection:
            connection.execute(
                text(f"UPDATE dashboard_users SET {assignments} WHERE id = :id"),
                {**updates, "id": user_id},
            )

    updated_user = _get_user_by_id(user_id)
    return _row_to_user(updated_user or existing_user)


def update_user_password(user_id: int, payload: UserPasswordPayload) -> None:
    ensure_users_table()
    existing_user = _get_user_by_id(user_id)
    if not existing_user:
        raise LookupError("Utilisateur introuvable.")

    with engine.begin() as connection:
        connection.execute(
            text("UPDATE dashboard_users SET password_hash = :password_hash WHERE id = :id"),
            {"id": user_id, "password_hash": hash_password(payload.password)},
        )


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _base64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(f"{value}{padding}".encode("ascii"))


def _session_signature(payload: str) -> str:
    signature = hmac.new(
        settings.auth_secret_key.encode("utf-8"),
        payload.encode("ascii"),
        hashlib.sha256,
    ).digest()
    return _base64url_encode(signature)


def create_session_token(user: dict[str, object]) -> str:
    expires_at = int(datetime.now(timezone.utc).timestamp()) + settings.auth_session_seconds
    payload = {
        "sub": int(user["id"]),
        "username": str(user["username"]),
        "exp": expires_at,
        "nonce": secrets.token_urlsafe(12),
    }
    payload_segment = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    return f"{payload_segment}.{_session_signature(payload_segment)}"


def parse_session_token(token: str) -> int | None:
    try:
        payload_segment, signature = token.rsplit(".", 1)
        if not hmac.compare_digest(_session_signature(payload_segment), signature):
            return None
        payload = json.loads(_base64url_decode(payload_segment).decode("utf-8"))
        if int(payload["exp"]) < int(datetime.now(timezone.utc).timestamp()):
            return None
        return int(payload["sub"])
    except (binascii.Error, KeyError, TypeError, ValueError, json.JSONDecodeError):
        return None


def attach_session_cookie(response: Response, user: dict[str, object]) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(user),
        max_age=settings.auth_session_seconds,
        httponly=True,
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        secure=settings.auth_cookie_secure,
        samesite=settings.auth_cookie_samesite,
    )


def get_current_user(
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> dict[str, object]:
    if not session_token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session requise.")

    user_id = parse_session_token(session_token)
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Session invalide.")

    user = _get_user_by_id(user_id)
    if not user or not bool(user["is_active"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur inactif.")

    return _row_to_user(user)


def require_admin_user(current_user: dict[str, object] = Depends(get_current_user)) -> dict[str, object]:
    if current_user.get("role") != ROLE_ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès réservé à l'administrateur.")

    return current_user

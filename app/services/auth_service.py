from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.database import Database


@dataclass
class AuthUser:
    id: int
    name: str
    username: str
    role: str


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


class AuthService:
    def __init__(self, db: Database) -> None:
        self.db = db

    def login(self, username: str, password: str) -> AuthUser | None:
        row = self.db.fetch_one(
            """
            SELECT id, name, username, role
            FROM users
            WHERE username = ? AND password_hash = ? AND active = 1
            """,
            (username.strip(), hash_password(password)),
        )
        if not row:
            return None
        return AuthUser(id=row["id"], name=row["name"], username=row["username"], role=row["role"])

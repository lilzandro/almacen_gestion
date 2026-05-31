import hashlib
import os
from database.connection import get_connection


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 260_000)
    return salt.hex() + ":" + key.hex()


def verify_password(password: str, stored: str) -> bool:
    if ":" not in stored:
        # Hash legacy SHA-256 sin sal — migrar en próximo login
        return hashlib.sha256(password.encode()).hexdigest() == stored
    salt_hex, key_hex = stored.split(":", 1)
    key = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt_hex), 260_000
    )
    return key.hex() == key_hex


def change_password(user_id: int, new_password: str) -> None:
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE users SET password_hash=?, must_change_password=0 WHERE id=?",
            (hash_password(new_password), user_id),
        )
        conn.commit()
    finally:
        conn.close()


def login(username: str, password: str):
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM users WHERE username=?", (username,)
        ).fetchone()
    finally:
        conn.close()
    if not row or not verify_password(password, row["password_hash"]):
        return None
    # Migrar hash legacy SHA-256 → pbkdf2 de forma transparente
    if ":" not in row["password_hash"]:
        change_password(row["id"], password)
        # Recargar fila con el nuevo hash
        conn2 = get_connection()
        try:
            row = conn2.execute(
                "SELECT * FROM users WHERE id=?", (row["id"],)
            ).fetchone()
        finally:
            conn2.close()
    return dict(row)

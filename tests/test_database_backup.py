"""Pruebas de respaldo y restauración de la base de datos."""
import os
import sqlite3

import pytest

from core import database_backup


def _count(db, table: str) -> int:
    conn = db["repo"].get_connection()
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def test_create_backup_genera_una_copia_valida(db, tmp_path):
    dest = tmp_path / "respaldo.db"

    result = database_backup.create_backup(str(dest))

    assert os.path.isfile(dest)
    assert result["path"] == os.path.abspath(str(dest))
    assert result["size"] > 0
    assert not os.path.exists(str(dest) + "-wal")
    assert not os.path.exists(str(dest) + "-shm")
    assert database_backup.validate_database(str(dest))["integrity"] == "ok"

    conn = sqlite3.connect(dest)
    try:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 3
        assert conn.execute("SELECT COUNT(*) FROM users").fetchone()[0] >= 1
    finally:
        conn.close()


def test_restore_database_reemplaza_datos_y_crea_respaldo_de_seguridad(
    db, tmp_path, monkeypatch
):
    monkeypatch.setenv("DIGICABLE_BACKUP_DIR", str(tmp_path / "backups"))
    backup = tmp_path / "respaldo.db"
    database_backup.create_backup(str(backup))

    # Borra los productos de la base activa para comprobar que se restauran.
    conn = db["repo"].get_connection()
    try:
        conn.execute("DELETE FROM movement_items")
        conn.execute("DELETE FROM movements")
        conn.execute("DELETE FROM products")
        conn.commit()
    finally:
        conn.close()
    assert _count(db, "products") == 0

    result = database_backup.restore_database(str(backup))

    assert _count(db, "products") == 3
    assert os.path.isfile(result["safety_backup"])
    assert not os.path.exists(result["safety_backup"] + "-wal")
    assert not os.path.exists(result["safety_backup"] + "-shm")

    # El respaldo de seguridad debe representar el estado previo (sin productos).
    conn = sqlite3.connect(result["safety_backup"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0
    finally:
        conn.close()


def test_restore_database_rechaza_archivo_invalido_sin_tocar_la_base(
    db, tmp_path, monkeypatch
):
    monkeypatch.setenv("DIGICABLE_BACKUP_DIR", str(tmp_path / "backups"))
    bad = tmp_path / "no_es_sqlite.db"
    bad.write_text("esto no es una base de datos", encoding="utf-8")
    before = _count(db, "products")

    with pytest.raises(database_backup.InvalidDatabaseError):
        database_backup.restore_database(str(bad))

    assert _count(db, "products") == before
    backups = tmp_path / "backups"
    assert not backups.exists() or not list(backups.iterdir())


def test_validate_database_exige_las_tablas_de_digicable(tmp_path):
    path = tmp_path / "otra.db"
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE algo (id INTEGER)")
    conn.commit()
    conn.close()

    with pytest.raises(database_backup.InvalidDatabaseError) as exc:
        database_backup.validate_database(str(path))

    assert "Faltan las tablas" in str(exc.value)

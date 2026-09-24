"""Fixtures de prueba: cada test usa una base SQLite temporal y aislada."""
import pytest

import database.connection as connection


@pytest.fixture()
def db(tmp_path, monkeypatch):
    """Apunta el módulo a una BD temporal, crea el esquema y siembra datos."""
    monkeypatch.setattr(connection, "DB_PATH", str(tmp_path / "test.db"))
    connection.initialize_db()

    import database.repository as repo

    wh_id = repo.get_all_warehouses()[0]["id"]
    user_id = repo.get_all_users()[0]["id"]

    # Producto por cantidad (stock 20)
    qty_pid = repo.create_product(
        "Router", "BC-QTY", "TPLink", "", "", 20, None, "und", warehouse_id=wh_id
    )
    # Producto serializado (2 unidades)
    ser_pid_1 = repo.create_product(
        "Switch", "BC-SER-1", "Cisco", "SN-1", "", 0, None, "und", warehouse_id=wh_id
    )
    ser_pid_2 = repo.create_product(
        "Switch", "BC-SER-2", "Cisco", "SN-2", "", 0, None, "und", warehouse_id=wh_id
    )

    return {
        "repo": repo,
        "wh_id": wh_id,
        "user_id": user_id,
        "qty_pid": qty_pid,
        "serials": [ser_pid_1, ser_pid_2],
    }


@pytest.fixture()
def q(db):
    """Helper para consultar la BD de prueba."""
    def _q(sql, args=()):
        conn = db["repo"].get_connection()
        try:
            return conn.execute(sql, args).fetchall()
        finally:
            conn.close()
    return _q

"""Pruebas de movimientos: atomicidad de stock y reversión."""
import pytest


def _stock(q, pid):
    return q("SELECT quantity FROM products WHERE id=?", (pid,))[0]["quantity"]


def _status(q, pid):
    return q("SELECT status FROM products WHERE id=?", (pid,))[0]["status"]


def _last_movement(q):
    return q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]


def test_compound_salida_quantity_es_atomica_y_revierte(db, q):
    repo = db["repo"]
    mid = repo.create_compound_movement(
        "salida", db["user_id"],
        [{"name": "Router", "brand": "TPLink", "qty": 5, "unit": "und",
          "kind": "quantity"}],
        warehouse_id=db["wh_id"],
    )
    assert _stock(q, db["qty_pid"]) == 15
    assert q("SELECT COUNT(*) c FROM movement_items WHERE movement_id=?", (mid,))[0]["c"] == 1

    repo.delete_movement(mid)
    assert _stock(q, db["qty_pid"]) == 20


def test_compound_salida_serial_y_reversion(db, q):
    repo = db["repo"]
    mid = repo.create_compound_movement(
        "salida", db["user_id"],
        [{"name": "Switch", "brand": "Cisco", "qty": 1, "unit": "und",
          "kind": "serial"}],
        warehouse_id=db["wh_id"],
    )
    disponibles = q(
        "SELECT COUNT(*) c FROM products WHERE name='Switch' AND status='disponible'"
    )[0]["c"]
    assert disponibles == 1

    repo.delete_movement(mid)
    disponibles = q(
        "SELECT COUNT(*) c FROM products WHERE name='Switch' AND status='disponible'"
    )[0]["c"]
    assert disponibles == 2


def test_compound_falla_atomico_sin_cambiar_stock(db, q):
    repo = db["repo"]
    movimientos_antes = q("SELECT COUNT(*) c FROM movements")[0]["c"]
    with pytest.raises(ValueError):
        repo.create_compound_movement(
            "salida", db["user_id"],
            [
                {"name": "Router", "brand": "TPLink", "qty": 5, "unit": "und",
                 "kind": "quantity"},
                # El segundo ítem no tiene stock suficiente -> rollback total
                {"name": "Router", "brand": "TPLink", "qty": 9999, "unit": "und",
                 "kind": "quantity"},
            ],
            warehouse_id=db["wh_id"],
        )
    assert _stock(q, db["qty_pid"]) == 20
    assert q("SELECT COUNT(*) c FROM movements")[0]["c"] == movimientos_antes


def test_compound_devolucion_cantidad(db, q):
    repo = db["repo"]
    repo.create_compound_movement(
        "devolucion", db["user_id"],
        [{"name": "Router", "brand": "TPLink", "qty": 3, "unit": "und",
          "kind": "quantity"}],
        warehouse_id=db["wh_id"],
    )
    assert _stock(q, db["qty_pid"]) == 23


def test_simple_movement_edit_y_delete_revierte(db, q):
    repo = db["repo"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 5, "test")
    mid = _last_movement(q)
    assert _stock(q, db["qty_pid"]) == 25

    repo.update_movement(mid, "salida", None, 3, "edit")
    assert _stock(q, db["qty_pid"]) == 17

    repo.delete_movement(mid)
    assert _stock(q, db["qty_pid"]) == 20


def test_no_editar_movimiento_compuesto(db, q):
    repo = db["repo"]
    mid = repo.create_compound_movement(
        "salida", db["user_id"],
        [
            {"name": "Router", "brand": "TPLink", "qty": 1, "unit": "und",
             "kind": "quantity"},
            {"name": "Switch", "brand": "Cisco", "qty": 1, "unit": "und",
             "kind": "serial"},
        ],
        warehouse_id=db["wh_id"],
    )
    with pytest.raises(ValueError):
        repo.update_movement(mid, "salida", None, 2, "x")

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

    item_id = q(
        "SELECT id FROM movement_items WHERE movement_id=?", (mid,)
    )[0]["id"]
    repo.update_movement(
        mid, "salida", None, "edit",
        item_updates=[{"item_id": item_id, "qty": 3}],
    )
    assert _stock(q, db["qty_pid"]) == 17

    repo.delete_movement(mid)
    assert _stock(q, db["qty_pid"]) == 20


def test_get_movement_devuelve_los_items(db, q):
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
    mov = repo.get_movement(mid)
    assert len(mov["items"]) == 2
    assert all("id" in it for it in mov["items"])


def test_editar_compuesto_ajusta_solo_items_sin_seriales(db, q):
    repo = db["repo"]
    mid = repo.create_compound_movement(
        "salida", db["user_id"],
        [
            {"name": "Router", "brand": "TPLink", "qty": 2, "unit": "und",
             "kind": "quantity"},
            {"name": "Switch", "brand": "Cisco", "qty": 1, "unit": "und",
             "kind": "serial"},
        ],
        warehouse_id=db["wh_id"],
    )
    assert _stock(q, db["qty_pid"]) == 18

    items = q(
        "SELECT id, qty, seriales FROM movement_items "
        "WHERE movement_id=? ORDER BY id",
        (mid,),
    )
    qty_item = next(i for i in items if not i["seriales"])
    serial_item = next(i for i in items if i["seriales"])

    repo.update_movement(
        mid, "salida", None, "edit",
        item_updates=[
            {"item_id": qty_item["id"], "qty": 5},
            # El ítem con seriales se ignora aunque venga en la lista.
            {"item_id": serial_item["id"], "qty": 99},
        ],
    )

    assert _stock(q, db["qty_pid"]) == 15
    assert q(
        "SELECT qty FROM movement_items WHERE id=?", (serial_item["id"],)
    )[0]["qty"] == 1
    assert q(
        "SELECT quantity FROM movements WHERE id=?", (mid,)
    )[0]["quantity"] == 6


def test_editar_compuesto_sin_stock_hace_rollback_total(db, q):
    repo = db["repo"]
    cable_pid = repo.create_product(
        "Cable", "BC-CABLE", "Gen", "", "", 50, None, "m",
        warehouse_id=db["wh_id"],
    )
    mid = repo.create_compound_movement(
        "devolucion", db["user_id"],
        [
            {"name": "Router", "brand": "TPLink", "qty": 2, "unit": "und",
             "kind": "quantity"},
            {"name": "Cable", "brand": "Gen", "qty": 5, "unit": "m",
             "kind": "quantity"},
        ],
        warehouse_id=db["wh_id"],
    )
    assert _stock(q, db["qty_pid"]) == 22
    assert _stock(q, cable_pid) == 55

    items = q(
        "SELECT id, name FROM movement_items WHERE movement_id=? ORDER BY id",
        (mid,),
    )
    updates = []
    for it in items:
        qty = 1 if it["name"] == "Router" else 999  # Cable no alcanza
        updates.append({"item_id": it["id"], "qty": qty})

    with pytest.raises(ValueError):
        repo.update_movement(mid, "salida", None, "x", item_updates=updates)

    # Todo o nada: ni stock, ni tipo, ni cantidades cambiaron.
    assert _stock(q, db["qty_pid"]) == 22
    assert _stock(q, cable_pid) == 55
    assert q(
        "SELECT type, quantity FROM movements WHERE id=?", (mid,)
    )[0]["type"] == "devolucion"
    assert {
        r["name"]: r["qty"]
        for r in q(
            "SELECT name, qty FROM movement_items WHERE movement_id=?", (mid,)
        )
    } == {"Router": 2, "Cable": 5}


def test_delete_product_registra_el_producto_en_el_movimiento(db, q):
    repo = db["repo"]
    pid = repo.create_product(
        "Camara", "BC-CAM", "Hik", "CAM-1", "", 0, None, "und",
        warehouse_id=db["wh_id"],
    )
    repo.delete_product(
        pid, user_id=db["user_id"], warehouse_id=db["wh_id"]
    )

    mid = q(
        "SELECT id FROM movements WHERE type='eliminacion' "
        "ORDER BY id DESC LIMIT 1"
    )[0]["id"]
    detail = repo.get_movement_detail(mid)

    assert detail["product"] == "Camara"
    assert len(detail["items"]) == 1
    assert detail["items"][0]["name"] == "Camara"
    assert detail["items"][0]["seriales"] == "CAM-1"


def test_delete_group_registra_los_productos_eliminados(db, q):
    repo = db["repo"]
    for i in (1, 2):
        repo.create_product(
            "AP", f"BC-AP-{i}", "TP-Link", f"AP-{i}", "", 0, None, "und",
            warehouse_id=db["wh_id"],
        )

    eliminados, _ = repo.delete_product_group(
        "AP", "TP-Link", user_id=db["user_id"], warehouse_id=db["wh_id"]
    )
    assert eliminados == 2

    mid = q(
        "SELECT id FROM movements WHERE type='eliminacion_grupo' "
        "ORDER BY id DESC LIMIT 1"
    )[0]["id"]
    detail = repo.get_movement_detail(mid)

    assert len(detail["items"]) == 2
    assert {i["name"] for i in detail["items"]} == {"AP"}
    assert {i["seriales"] for i in detail["items"]} == {"AP-1", "AP-2"}


def test_eliminacion_heredada_sin_items_muestra_la_nota(db, q):
    repo = db["repo"]
    conn = repo.get_connection()
    try:
        cur = conn.execute(
            "INSERT INTO movements "
            "(type, product_id, employee_id, user_id, quantity, notes, warehouse_id) "
            "VALUES ('eliminacion', 0, NULL, ?, 1, ?, ?)",
            (
                db["user_id"],
                "Producto eliminado: Router viejo (Marca)",
                db["wh_id"],
            ),
        )
        mid = cur.lastrowid
        conn.commit()
    finally:
        conn.close()

    detail = repo.get_movement_detail(mid)
    assert "Router viejo" in (detail["product"] or "")


def test_bulk_create_products_genera_un_solo_movimiento(db, q):
    repo = db["repo"]
    items = [
        {"name": "Camara", "brand": "Hik", "serial": "C-1", "mac": "",
         "supplier_id": None, "unit": "und"},
        {"name": "Camara", "brand": "Hik", "serial": "C-2", "mac": "",
         "supplier_id": None, "unit": "und"},
        {"name": "Camara", "brand": "Hik", "serial": "C-3", "mac": "",
         "supplier_id": None, "unit": "und"},
    ]
    ok, duplicados = repo.bulk_create_products(
        items, user_id=db["user_id"], warehouse_id=db["wh_id"]
    )
    assert ok == 3
    assert duplicados == []

    movs = q(
        "SELECT id, type, quantity, product_id FROM movements "
        "WHERE type='entrada' AND notes LIKE 'Alta masiva%'"
    )
    assert len(movs) == 1
    mid = movs[0]["id"]
    assert movs[0]["product_id"] == 0
    assert movs[0]["quantity"] == 3

    n_items = q(
        "SELECT COUNT(*) c FROM movement_items WHERE movement_id=?", (mid,)
    )[0]["c"]
    assert n_items == 3


def test_bulk_create_products_todos_duplicados_no_crea_movimiento(db, q):
    repo = db["repo"]
    item = {
        "name": "Router", "brand": "TPLink", "barcode": "BC-QTY",
        "serial": "", "mac": "", "supplier_id": None, "unit": "und",
    }
    antes = q("SELECT COUNT(*) c FROM movements")[0]["c"]
    ok, duplicados = repo.bulk_create_products(
        [item], user_id=db["user_id"], warehouse_id=db["wh_id"]
    )
    assert ok == 0
    assert duplicados
    assert q("SELECT COUNT(*) c FROM movements")[0]["c"] == antes



def test_get_movements_flat_filtra_por_lista_de_ids(db, q):
    repo = db["repo"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "uno")
    m1 = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "dos")
    m2 = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "tres")

    rows = repo.get_movements_flat(ids=[m1, m2])
    assert {r["id"] for r in rows} == {m1, m2}

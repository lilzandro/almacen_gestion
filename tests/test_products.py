"""Pruebas de persistencia de campos de producto."""
import pytest


def test_create_product_guarda_modelo(db, q):
    repo = db["repo"]
    pid = repo.create_product(
        "Switch", "BC-MOD", "Cisco", "", "", 1, None, "und",
        warehouse_id=db["wh_id"], modelo="SG350",
    )
    row = q("SELECT modelo FROM products WHERE id=?", (pid,))[0]
    assert row["modelo"] == "SG350"


def test_create_product_modelo_por_defecto_vacio(db, q):
    repo = db["repo"]
    pid = repo.create_product(
        "Switch", "BC-MOD2", "Cisco", "", "", 1, None, "und",
        warehouse_id=db["wh_id"],
    )
    row = q("SELECT modelo FROM products WHERE id=?", (pid,))[0]
    assert row["modelo"] in ("", None)


def test_bulk_create_products_guarda_modelo(db, q):
    repo = db["repo"]
    items = [{
        "name": "Camara", "brand": "Hik", "barcode": "BC-CAM9",
        "serial": "C-9", "mac": "", "supplier_id": None, "unit": "und",
        "modelo": "DS-2CD",
    }]
    repo.bulk_create_products(
        items, user_id=db["user_id"], warehouse_id=db["wh_id"]
    )
    row = q("SELECT modelo FROM products WHERE serial='C-9'")[0]
    assert row["modelo"] == "DS-2CD"

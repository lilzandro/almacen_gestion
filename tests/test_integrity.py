"""Pruebas de integridad: duplicados y borrados con dependencias."""
import pytest


def test_cedula_duplicada_lanza_integrityerror(db):
    repo = db["repo"]
    repo.create_employee("Juan Perez", "12345678", "Cargo")
    with pytest.raises(Exception):
        repo.create_employee("Otro", "12345678", "Cargo")


def test_delete_employee_con_movimientos_falla(db, q):
    repo = db["repo"]
    repo.create_employee("Maria", "87654321", "Cargo")
    emp = q("SELECT id FROM employees WHERE cedula='87654321'")[0]["id"]
    repo.create_movement("salida", db["qty_pid"], emp, db["user_id"], 1, "x")
    with pytest.raises(ValueError):
        repo.delete_employee(emp)


def test_delete_employee_sin_movimientos(db, q):
    repo = db["repo"]
    repo.create_employee("Sin Movs", "11112222", "Cargo")
    emp = q("SELECT id FROM employees WHERE cedula='11112222'")[0]["id"]
    repo.delete_employee(emp)
    assert q("SELECT COUNT(*) c FROM employees WHERE id=?", (emp,))[0]["c"] == 0


def test_no_borrar_ultimo_admin(db):
    repo = db["repo"]
    admin = repo.get_all_users()[0]
    with pytest.raises(ValueError):
        repo.delete_user(admin["id"])


def test_password_hash_y_verify():
    from core.auth import hash_password, verify_password

    stored = hash_password("secreta123")
    assert ":" in stored
    assert verify_password("secreta123", stored)
    assert not verify_password("otra", stored)

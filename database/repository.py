import re
import time as _time
from database.connection import get_connection

_cache: dict = {}
_CACHE_TTL = 5  # segundos

_SERIAL_BLOCK = re.compile(r"\[[^\]]*\]")
_SERIAL_MENTION = re.compile(r"[-–—]\s*Serial(?:es)?:\s*[^|\[\]]*", re.IGNORECASE)
_SERIAL_MENTION2 = re.compile(r"Serial(?:es)?:\s*[^|\[\]]*", re.IGNORECASE)


def _clean_product_label(label):
    """Quita seriales de la etiqueta de producto (bloques [serial] y menciones
    "Serial: ...") para no exponerlos en tablas/cards."""
    if not label:
        return label
    s = _SERIAL_BLOCK.sub("", label)
    s = _SERIAL_MENTION.sub("", s)
    s = _SERIAL_MENTION2.sub("", s)
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*[|,;]+\s*$", "", s)
    return s.strip(" |,;")


def _cached(key, fn):
    now = _time.time()
    if key in _cache and (now - _cache[key][0]) < _CACHE_TTL:
        return _cache[key][1]
    data = fn()
    _cache[key] = (now, data)
    return data


def _invalidate(key):
    _cache.pop(key, None)


def _invalidate_prefix(prefix):
    for key in list(_cache.keys()):
        if isinstance(key, tuple) and key[0] == prefix:
            _cache.pop(key, None)


# ── WAREHOUSES ────────────────────────────────────────────────────────────────


def get_all_warehouses():
    def _fetch():
        conn = get_connection()
        try:
            return conn.execute("SELECT * FROM warehouses ORDER BY id").fetchall()
        finally:
            conn.close()
    return _cached("warehouses", _fetch)


def bulk_create_products(items, user_id, warehouse_id=None):
    """
    Inserta N productos + sus movimientos de entrada en UNA sola transacción.

    items: lista de dicts con claves: name, brand, serial, mac, supplier_id, unit[, barcode]
    Retorna: (ok: int, duplicados: list[str])
    """
    conn = get_connection()
    ok = 0
    duplicados = []
    try:
        for item in items:
            try:
                cursor = conn.cursor()
                cursor.execute(
                    """INSERT INTO products
                       (name, barcode, brand, serial, mac, quantity,
                        supplier_id, unit, warehouse_id)
                       VALUES (?,?,?,?,?,0,?,?,?)""",
                    (
                        item["name"],
                        item.get("barcode"),
                        item.get("brand", ""),
                        item.get("serial", ""),
                        item.get("mac", ""),
                        item.get("supplier_id"),
                        item.get("unit", "und"),
                        warehouse_id,
                    ),
                )
                pid = cursor.lastrowid
                conn.execute(
                    """INSERT INTO movements
                       (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
                       VALUES ('entrada', ?, NULL, ?, 1, ?, ?)""",
                    (
                        pid,
                        user_id,
                        f"Alta masiva — Serial: {item.get('serial', '') or 'S/N'}",
                        warehouse_id,
                    ),
                )
                ok += 1
            except Exception:
                label = item.get("serial") or item.get("mac") or f"fila {ok + len(duplicados) + 1}"
                duplicados.append(label)
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
    return ok, duplicados


# ── USERS ─────────────────────────────────────────────────────────────────────


def get_all_users():
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, username, role FROM users ORDER BY id"
        ).fetchall()
        return rows
    finally:
        conn.close()


def create_user(username, password_hash, role):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?,?,?)",
            (username, password_hash, role),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_user(user_id, username, role, password_hash=None):
    conn = get_connection()
    try:
        if password_hash:
            conn.execute(
                "UPDATE users SET username=?, role=?, password_hash=? WHERE id=?",
                (username, role, password_hash, user_id),
            )
        else:
            conn.execute(
                "UPDATE users SET username=?, role=? WHERE id=?",
                (username, role, user_id),
            )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    try:
        user = conn.execute(
            "SELECT username, role FROM users WHERE id=?", (user_id,)
        ).fetchone()
        if not user:
            return
        n = conn.execute(
            "SELECT COUNT(*) FROM movements WHERE user_id=?", (user_id,)
        ).fetchone()[0]
        if n:
            raise ValueError(
                f"No se puede eliminar: el usuario tiene {n} movimiento(s) registrado(s)."
            )
        if user["role"] == "admin":
            admins = conn.execute(
                "SELECT COUNT(*) FROM users WHERE role='admin'"
            ).fetchone()[0]
            if admins <= 1:
                raise ValueError("No se puede eliminar el último usuario administrador.")
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── SUPPLIERS ─────────────────────────────────────────────────────────────────


def get_all_suppliers():
    def _fetch():
        conn = get_connection()
        try:
            return conn.execute("SELECT * FROM suppliers ORDER BY name").fetchall()
        finally:
            conn.close()
    return _cached("suppliers", _fetch)


def create_supplier(name, contact, rif):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO suppliers (name, contact, rif) VALUES (?,?,?)",
            (name, contact, rif),
        )
        conn.commit()
        _invalidate("suppliers")
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_supplier(supplier_id, name, contact, rif):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE suppliers SET name=?, contact=?, rif=? WHERE id=?",
            (name, contact, rif, supplier_id),
        )
        conn.commit()
        _invalidate("suppliers")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_supplier(supplier_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        conn.commit()
        _invalidate("suppliers")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── EMPLOYEES ─────────────────────────────────────────────────────────────────


def get_all_employees():
    def _fetch():
        conn = get_connection()
        try:
            return conn.execute("SELECT * FROM employees ORDER BY name").fetchall()
        finally:
            conn.close()
    return _cached("employees", _fetch)


def create_employee(name, cedula, cargo):
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO employees (name, cedula, cargo) VALUES (?,?,?)",
            (name, cedula, cargo),
        )
        conn.commit()
        _invalidate("employees")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_employee(employee_id, name, cedula, cargo):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE employees SET name=?, cedula=?, cargo=? WHERE id=?",
            (name, cedula, cargo, employee_id),
        )
        conn.commit()
        _invalidate("employees")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_employee(employee_id):
    conn = get_connection()
    try:
        n = conn.execute(
            "SELECT COUNT(*) FROM movements WHERE employee_id=?", (employee_id,)
        ).fetchone()[0]
        if n:
            raise ValueError(
                f"No se puede eliminar: el empleado tiene {n} movimiento(s) asociado(s)."
            )
        conn.execute("DELETE FROM employees WHERE id=?", (employee_id,))
        conn.commit()
        _invalidate("employees")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── VEHICLES ─────────────────────────────────────────────────────────────────


def get_all_vehicles():
    conn = get_connection()
    try:
        rows = conn.execute("SELECT * FROM vehicles ORDER BY id DESC").fetchall()
        return rows
    finally:
        conn.close()


def create_vehicle(brand, model, plate):
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO vehicles (brand, model, plate) VALUES (?,?,?)",
            (brand, model, plate),
        )
        conn.commit()
        return cursor.lastrowid
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_vehicle(vehicle_id, brand, model, plate):
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE vehicles SET brand=?, model=?, plate=? WHERE id=?",
            (brand, model, plate, vehicle_id),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_vehicle(vehicle_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ── PRODUCTS ──────────────────────────────────────────────────────────────────


def get_products_grouped(search="", status_filter="todos", warehouse_id=None):
    """Una fila por (name, brand): total de unidades, proveedor, estado dominante."""
    key = ("products_grouped", search, status_filter, warehouse_id)
    def _fetch():
        conn = get_connection()
        try:
            q = f"%{search}%"
            where = "(p.name LIKE ? OR p.barcode LIKE ?)"
            params = [q, q]
            if status_filter == "disponible":
                where += " AND p.status = 'disponible'"
            elif status_filter == "no disponible":
                where += " AND p.status = 'no disponible'"
            elif status_filter == "inactivo":
                where += " AND p.status = 'inactivo'"
            else:
                where += " AND p.status != 'inactivo'"
            if warehouse_id is not None:
                where += " AND p.warehouse_id = ?"
                params.append(warehouse_id)
            rows = conn.execute(
                f"""
                SELECT p.name, COALESCE(p.brand,'') AS brand,
                       COUNT(*) AS unit_count,
                       SUM(CASE WHEN p.status='disponible' THEN 1 ELSE 0 END) AS disponible_count,
                       MAX(CASE WHEN COALESCE(p.serial,'') != '' THEN 1 ELSE 0 END) AS has_serial,
                       MAX(p.supplier_id) AS supplier_id,
                       COALESCE(MAX(sup.name),'N/A') AS supplier_name,
                       MAX(COALESCE(p.unit,'und')) AS unit,
                        SUM(p.quantity) AS total_quantity
                FROM products p
                LEFT JOIN suppliers sup ON p.supplier_id = sup.id
                WHERE {where}
                GROUP BY p.name, COALESCE(p.brand,'')
                ORDER BY p.name, COALESCE(p.brand,'')
                """,
                params,
            ).fetchall()
            return rows
        finally:
            conn.close()
    return _cached(key, _fetch)


def get_units_by_model(name, brand, warehouse_id=None, inactive_only=False):
    """Devuelve filas individuales para un modelo (name+brand).

    Por defecto excluye inactivos. Con inactive_only=True devuelve solo las
    unidades archivadas (inactivas), p.ej. para la vista de Archivados."""
    key = ("units_by_model", name, brand, warehouse_id, inactive_only)
    def _fetch():
        conn = get_connection()
        try:
            params = [name, brand]
            wh_filter = ""
            if warehouse_id is not None:
                wh_filter = "AND p.warehouse_id = ?"
                params.append(warehouse_id)
            if inactive_only:
                status_filter = "AND p.status = 'inactivo'"
            else:
                status_filter = "AND p.status != 'inactivo'"
            rows = conn.execute(
                f"""
                SELECT p.id, p.serial, p.mac, p.status, p.barcode,
                       COALESCE(p.unit,'und') AS unit,
                       COALESCE(p.quantity, 0) AS quantity,
                       p.created_at
                FROM products p
                WHERE p.name = ? AND COALESCE(p.brand,'') = ?
                  {status_filter}
                  {wh_filter}
                ORDER BY p.id
                """,
                params,
            ).fetchall()
            return rows
        finally:
            conn.close()
    return _cached(key, _fetch)


def get_all_products(search="", include_inactive=False, status_filter="todos",
                     warehouse_id=None):
    """Obtiene todos los productos con filtros opcionales."""
    conn = get_connection()
    try:
        q = f"%{search}%"

        where_clause = "(p.name LIKE ? OR p.barcode LIKE ? OR p.brand LIKE ?)"
        params = [q, q, q]

        if status_filter == "disponible":
            where_clause += " AND p.status = 'disponible'"
        elif status_filter == "no disponible":
            where_clause += " AND p.status = 'no disponible'"
        elif not include_inactive:
            where_clause += " AND p.status != 'inactivo'"

        if warehouse_id is not None:
            where_clause += " AND p.warehouse_id = ?"
            params.append(warehouse_id)

        rows = conn.execute(
            f"""
            SELECT p.id, p.name, p.barcode, p.brand, p.serial, p.mac,
                   p.quantity, COALESCE(p.unit,'und') AS unit, p.status,
                   p.supplier_id, COALESCE(sup.name,'N/A') AS supplier_name,
                   p.created_at, p.updated_at
            FROM products p
            LEFT JOIN suppliers sup ON p.supplier_id = sup.id
            WHERE {where_clause}
            ORDER BY p.id DESC
            """,
            params,
        ).fetchall()
        return rows
    finally:
        conn.close()


def get_product_by_barcode(barcode):
    """Obtiene un producto por su código de barras"""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM products WHERE barcode = ?",
            (barcode,),
        ).fetchone()
        return row
    finally:
        conn.close()


def lookup_product_by_code(code):
    """Busca un producto por código probando variantes EAN-13/UPC-A.

    Un UPC-A de 12 dígitos equivale a un EAN-13 que empieza con '0'; así que
    si el código no coincide exactamente se reintenta con/sin el cero inicial.

    Retorna (row, code_matched) o (None, None)."""
    code = (code or "").strip()
    if not code:
        return None, None
    variants = [code]
    if len(code) == 13 and code.startswith("0"):
        variants.append(code[1:])
    elif len(code) == 12 and code.isdigit():
        variants.append("0" + code)
    for v in variants:
        row = get_product_by_barcode(v)
        if row is not None:
            return row, v
    return None, None


def get_product_by_id(product_id):
    """Obtiene un producto individual por su ID (con nombre de proveedor)."""
    conn = get_connection()
    try:
        return conn.execute(
            """SELECT p.id, p.name, p.barcode, p.brand, p.serial, p.mac,
                      p.quantity, COALESCE(p.unit,'und') AS unit, p.status,
                      p.supplier_id, COALESCE(sup.name,'N/A') AS supplier_name,
                      p.warehouse_id, p.created_at, p.updated_at
               FROM products p
               LEFT JOIN suppliers sup ON p.supplier_id = sup.id
               WHERE p.id=?""",
            (product_id,),
        ).fetchone()
    finally:
        conn.close()


def create_product(
    name,
    barcode,
    brand,
    serial,
    mac,
    quantity,
    supplier_id,
    unit="und",
    warehouse_id=None,
):
    """Crea un nuevo producto"""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO products
               (name, barcode, brand, serial, mac, quantity, supplier_id, unit, warehouse_id)
               VALUES (?,?,?,?,?,?,?,?,?)""",
            (
                name,
                barcode or None,
                brand or "",
                serial or "",
                mac or "",
                quantity or 0,
                supplier_id or None,
                unit or "und",
                warehouse_id,
            ),
        )
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
        return cursor.lastrowid
    finally:
        conn.close()


def update_product(
    product_id,
    name,
    barcode,
    brand,
    supplier_id,
    unit="und",
    status="disponible",
):
    """Actualiza campos editables de un producto. Serial, MAC y cantidad no se modifican aquí."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE products SET name=?, barcode=?, brand=?,
                                 supplier_id=?, unit=?, status=?,
                                 updated_at=datetime('now','localtime')
               WHERE id=?""",
            (
                name,
                barcode or None,
                brand or "",
                supplier_id or None,
                unit or "und",
                status,
                product_id,
            ),
        )
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    finally:
        conn.close()


_UNIT_LABELS = {
    "und": "unidades",
    "m": "metros",
    "caja": "cajas",
    "cm": "cm",
    "kg": "kg",
    "g": "g",
    "L": "L",
    "ml": "ml",
    "rollo": "rollos",
    "par": "pares",
}


def update_product_unit(product_id, serial, mac, barcode, status, user_id=None, warehouse_id=None, quantity=None):
    """Actualiza los identificadores, estado y cantidad de una unidad individual.
    quantity solo se modifica si se proporciona (no None)."""
    conn = get_connection()
    try:
        old = conn.execute(
            "SELECT serial, mac, barcode, status, name, quantity, COALESCE(unit,'und') AS unit FROM products WHERE id=?",
            (product_id,),
        ).fetchone() if user_id else None

        if quantity is None:
            conn.execute(
                """UPDATE products SET serial=?, mac=?, barcode=?, status=?,
                                     updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (serial or None, mac or None, barcode or None, status, product_id),
            )
        else:
            conn.execute(
                """UPDATE products SET serial=?, mac=?, barcode=?, status=?, quantity=?,
                                     updated_at=datetime('now','localtime')
                   WHERE id=?""",
                (serial or None, mac or None, barcode or None, status, quantity, product_id),
            )

        if user_id and old:
            changes = []
            if old["status"] != status:
                changes.append(f"estado: {old['status']}→{status}")
            if quantity is not None and int(old["quantity"] or 0) != quantity:
                lbl = _UNIT_LABELS.get(old["unit"], "cantidad")
                changes.append(f"{lbl}: {int(old['quantity'] or 0)}→{quantity}")
            conn.execute(
                """INSERT INTO movements
                   (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
                   VALUES ('modificacion', ?, NULL, ?, 1, ?, ?)""",
                (product_id, user_id,
                 f"Producto modificado: {old['name']}. {' | '.join(changes)}" if changes else f"Producto modificado: {old['name']}",
                 warehouse_id),
            )

        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_product_group(old_name, old_brand, new_name, new_brand, supplier_id, user_id=None, warehouse_id=None):
    """Actualiza nombre, marca y proveedor de todas las unidades de un grupo."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE products SET name=?, brand=?, supplier_id=?,
                                 updated_at=datetime('now','localtime')
               WHERE name=? AND COALESCE(brand,'')=? AND status!='inactivo'""",
            (new_name, new_brand, supplier_id or None, old_name, old_brand),
        )
        if user_id:
            changes = []
            if old_name != new_name:
                changes.append(f"nombre: {old_name}→{new_name}")
            if old_brand != new_brand:
                changes.append(f"marca: {old_brand}→{new_brand}")
            conn.execute(
                """INSERT INTO movements
                   (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
                   VALUES ('modificacion', COALESCE((SELECT MIN(id) FROM products WHERE name=? AND status!='inactivo'), 0), NULL, ?, 1, ?, ?)""",
                (new_name, user_id, f"Grupo modificado: {' | '.join(changes)}", warehouse_id),
            )
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def deactivate_product(product_id):
    """Da de baja un producto (soft delete)"""
    conn = None
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE products SET status='inactivo', updated_at=datetime('now','localtime') WHERE id=?",
            (product_id,),
        )
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def reactivate_product(product_id):
    """Reactivar un producto dado de baja (vuelve a 'disponible')."""
    conn = None
    try:
        conn = get_connection()
        conn.execute(
            "UPDATE products SET status='disponible', updated_at=datetime('now','localtime') WHERE id=?",
            (product_id,),
        )
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def reactivate_product_group(name, brand):
    """Reactivar todas las unidades archivadas (inactivas) de un grupo.

    Retorna el número de productos reactivados."""
    conn = None
    try:
        conn = get_connection()
        cur = conn.execute(
            "UPDATE products SET status='disponible', updated_at=datetime('now','localtime') "
            "WHERE name = ? AND COALESCE(brand,'') = ? AND status='inactivo'",
            (name, brand or ""),
        )
        count = cur.rowcount
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
        return count
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def _backfill_movement_snapshots(conn, products):
    """Garantiza que cada movimiento de un producto tenga su snapshot en
    movement_items ANTES de eliminar el producto físico.

    products: lista de filas con claves id, name, brand, serial, unit."""
    for p in products:
        pid = p["id"]
        movements = conn.execute(
            "SELECT id, quantity FROM movements WHERE product_id=?", (pid,)
        ).fetchall()
        for m in movements:
            has = conn.execute(
                "SELECT 1 FROM movement_items WHERE movement_id=? AND product_id=? LIMIT 1",
                (m["id"], pid),
            ).fetchone()
            if not has:
                conn.execute(
                    """INSERT INTO movement_items
                       (movement_id, product_id, name, brand, qty, unit, seriales)
                       VALUES (?,?,?,?,?,?,?)""",
                    (
                        m["id"],
                        pid,
                        p["name"],
                        p["brand"],
                        m["quantity"] or 1,
                        p["unit"] or "und",
                        p["serial"] or "",
                    ),
                )


def delete_product(product_id, user_id=None, notes="", warehouse_id=None):
    """Elimina físicamente un producto (con su historial conservado).

    Antes de borrar se respalda el snapshot en movement_items para cada
    movimiento del producto, de modo que Movimientos siga mostrando y
    buscando su historial sin depender de la fila de producto.
    Si se proporciona user_id, registra movimiento de eliminacion.
    Retorna: 'eliminado'."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        prod = conn.execute(
            """SELECT id, name, COALESCE(brand,'') AS brand,
                      COALESCE(serial,'') AS serial, COALESCE(unit,'und') AS unit
               FROM products WHERE id=?""",
            (product_id,),
        ).fetchone()
        if prod is None:
            return "eliminado"
        prod_name = f"{prod['name']} ({prod['brand']})"

        _backfill_movement_snapshots(conn, [prod])

        if user_id:
            conn.execute(
                """INSERT INTO movements
                   (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
                   VALUES ('eliminacion', 0, NULL, ?, 1, ?, ?)""",
                (user_id, notes or f"Producto eliminado: {prod_name}", warehouse_id),
            )

        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))

        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
        return "eliminado"
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def delete_product_group(name, brand, user_id=None, notes="", warehouse_id=None):
    """Elimina físicamente todas las unidades activas de un grupo (name+brand).

    Antes de borrar respalda los snapshots en movement_items por movimiento,
    de modo que el historial quede íntegro en Movimientos.
    Retorna (eliminados: int, 0)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT p.id, p.name, COALESCE(p.brand,'') AS brand,
                      COALESCE(p.serial,'') AS serial, COALESCE(p.unit,'und') AS unit
               FROM products p
               WHERE p.name = ? AND COALESCE(p.brand,'') = ? AND p.status != 'inactivo'""",
            (name, brand or ""),
        ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            _backfill_movement_snapshots(conn, rows)
            conn.executemany("DELETE FROM products WHERE id=?", [(i,) for i in ids])
        if user_id:
            conn.execute(
                """INSERT INTO movements
                   (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
                   VALUES ('eliminacion_grupo', 0, NULL, ?, ?, ?, ?)""",
                (user_id, len(ids),
                 notes or f"Grupo eliminado: {name} ({brand}). {len(ids)} eliminados",
                 warehouse_id),
            )
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
        return len(ids), 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def purge_archived_all():
    """Elimina físicamente todos los productos archivados (inactivos).

    Respalda primero sus snapshots en movement_items. Retorna cuántos se
    purgaron."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT p.id, p.name, COALESCE(p.brand,'') AS brand,
                      COALESCE(p.serial,'') AS serial, COALESCE(p.unit,'und') AS unit
               FROM products p WHERE p.status = 'inactivo'"""
        ).fetchall()
        ids = [r["id"] for r in rows]
        if ids:
            _backfill_movement_snapshots(conn, rows)
            conn.executemany("DELETE FROM products WHERE id=?", [(i,) for i in ids])
        conn.commit()
        if ids:
            _invalidate_prefix("units_by_model")
            _invalidate_prefix("products_grouped")
        return len(ids)
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def product_group_exists(name, brand, exclude_name=None, exclude_brand=None):
    """True si ya existe un grupo (name+brand) con unidades activas.
    Opcionalmente excluye un grupo (exclude_name, exclude_brand)."""
    conn = get_connection()
    try:
        params = [name, brand]
        excl = ""
        if exclude_name is not None and exclude_brand is not None:
            excl = "AND NOT (p.name = ? AND COALESCE(p.brand,'') = ?)"
            params += [exclude_name, exclude_brand]
        row = conn.execute(
            f"""SELECT COUNT(*) AS n
                FROM products p
                WHERE p.name = ? AND COALESCE(p.brand,'') = ?
                  AND p.status != 'inactivo'
                  {excl}""",
            params,
        ).fetchone()
        return row["n"] > 0
    finally:
        conn.close()


# ── MOVEMENTS ─────────────────────────────────────────────────────────────────

_MOVEMENTS_SELECT = """
SELECT m.id, m.type, m.timestamp, m.quantity, m.product_id, m.employee_id,
       COALESCE(p.name,
                (SELECT mi.name FROM movement_items mi
                  WHERE mi.movement_id = m.id ORDER BY mi.id LIMIT 1),
                m.notes) AS product,
       COALESCE(e.name, '-') AS employee,
       u.username AS registered_by, m.notes
FROM movements m
LEFT JOIN products p ON m.product_id = p.id
LEFT JOIN employees e ON m.employee_id = e.id
JOIN users u ON m.user_id = u.id
"""


def _movement_filters(search="", movement_types=None, warehouse_id=None):
    """Construye el WHERE (y params) común: búsqueda sobre producto/empleado/notas,
    lista de tipos reales y almacén."""
    clauses = []
    params = []
    if search:
        q = f"%{search}%"
        clauses.append(
            "(m.type LIKE ? OR COALESCE(p.name,'') LIKE ? OR COALESCE(p.barcode,'') LIKE ? "
            "OR COALESCE(e.name,'') LIKE ? OR COALESCE(m.notes,'') LIKE ? "
            "OR EXISTS (SELECT 1 FROM movement_items mi "
            "WHERE mi.movement_id = m.id AND mi.name LIKE ?))"
        )
        params += [q] * 6
    if movement_types:
        clauses.append(f"m.type IN ({','.join('?' * len(movement_types))})")
        params += list(movement_types)
    if warehouse_id is not None:
        clauses.append("m.warehouse_id = ?")
        params.append(warehouse_id)
    return " AND ".join(clauses) if clauses else "1=1", params


def _attach_item_summaries(conn, rows):
    """Agrega a cada movimiento: item_count, unit_totals, cant_display e item_names.

    Los movimientos compuestos guardan sus productos en `movement_items`; la
    columna `quantity` del movimiento es una suma que mezcla unidades, por lo
    que para mostrarla hay que resumir por unidad (p. ej. "330 m · 100 und").
    """
    for r in rows:
        r["item_count"] = 0
        r["unit_totals"] = {}
        r["cant_display"] = str(r["quantity"] or "")
        r["item_names"] = []

    ids = [r["id"] for r in rows]
    if not ids:
        return rows

    ph = ",".join("?" * len(ids))
    item_rows = conn.execute(
        f"SELECT movement_id, name, unit, qty FROM movement_items "
        f"WHERE movement_id IN ({ph}) ORDER BY movement_id, id",
        ids,
    ).fetchall()

    totals, counts, order, names = {}, {}, {}, {}
    for it in item_rows:
        mid = it["movement_id"]
        unit = it["unit"] or "und"
        d = totals.setdefault(mid, {})
        d[unit] = d.get(unit, 0) + (it["qty"] or 0)
        counts[mid] = counts.get(mid, 0) + 1
        lst = order.setdefault(mid, [])
        if unit not in lst:
            lst.append(unit)
        nlst = names.setdefault(mid, [])
        if it["name"] and it["name"] not in nlst:
            nlst.append(it["name"])

    for r in rows:
        mid = r["id"]
        if mid in totals:
            unit_totals = {u: totals[mid][u] for u in order[mid]}
            r["item_count"] = counts[mid]
            r["unit_totals"] = unit_totals
            r["cant_display"] = _format_quantity_summary(
                counts[mid], unit_totals, r["quantity"])
            r["item_names"] = names[mid]
    return rows


def query_movements_view(warehouse_id=None, search="", movement_types=None,
                         page=1, per_page=25):
    """Datos de una página + total filtrado + conteos por tipo del almacén
    + última actualización. Conteos independientes de búsqueda/filtro."""
    conn = get_connection()
    try:
        where, params = _movement_filters(search, movement_types, warehouse_id)
        total = conn.execute(
            f"SELECT COUNT(*) FROM movements m "
            f"LEFT JOIN products p ON m.product_id = p.id "
            f"LEFT JOIN employees e ON m.employee_id = e.id WHERE {where}",
            params,
        ).fetchone()[0]
        rows = conn.execute(
            _MOVEMENTS_SELECT + f" WHERE {where} ORDER BY m.id DESC LIMIT ? OFFSET ?",
            params + [per_page, (page - 1) * per_page],
        ).fetchall()
        cleaned = [_clean_row_product(r) for r in rows]
        _attach_item_summaries(conn, cleaned)
        if warehouse_id is not None:
            counts_rows = conn.execute(
                "SELECT type, COUNT(*) n FROM movements WHERE warehouse_id=? GROUP BY type",
                (warehouse_id,),
            ).fetchall()
            last_update = conn.execute(
                "SELECT MAX(timestamp) FROM movements WHERE warehouse_id=?",
                (warehouse_id,),
            ).fetchone()[0]
        else:
            counts_rows = conn.execute(
                "SELECT type, COUNT(*) n FROM movements GROUP BY type"
            ).fetchall()
            last_update = conn.execute(
                "SELECT MAX(timestamp) FROM movements"
            ).fetchone()[0]
        return {
            "rows": cleaned,
            "total": total,
            "counts": {c["type"]: c["n"] for c in counts_rows},
            "last_update": last_update or "",
        }
    finally:
        conn.close()


def _format_quantity_summary(item_count, unit_totals, quantity):
    """Formatea cantidades sin perder la unidad.

    - Un solo producto: '100 und' / '100 m'
    - Varios productos con una sola unidad: '101 und'
    - Varios productos con unidades mezcladas: '110 m · 204 und'
    """
    if not unit_totals:
        return str(quantity or "")
    if len(unit_totals) == 1:
        unit = next(iter(unit_totals))
        return f"{unit_totals[unit]} {unit}"
    return " · ".join(f"{tot} {unit}" for unit, tot in unit_totals.items())


def get_movements_flat(warehouse_id=None, search="", movement_types=None, limit=1000000):
    """Todos los movimientos filtrados (sin paginar), p. ej. para exportar."""
    conn = get_connection()
    try:
        where, params = _movement_filters(search, movement_types, warehouse_id)
        rows = conn.execute(
            _MOVEMENTS_SELECT + f" WHERE {where} ORDER BY m.id DESC LIMIT ?",
            params + [limit],
        ).fetchall()
        cleaned = [_clean_row_product(r) for r in rows]
        _attach_item_summaries(conn, cleaned)
        return cleaned
    finally:
        conn.close()


def get_movement(movement_id):
    """Devuelve un solo movimiento (misma forma que get_all_movements) o None."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT m.id, m.type, m.timestamp, m.quantity, m.employee_id,
                   COALESCE(p.name,
                            (SELECT mi.name FROM movement_items mi
                              WHERE mi.movement_id = m.id ORDER BY mi.id LIMIT 1),
                            m.notes) AS product,
                   COALESCE(e.name, '-') AS employee,
                   u.username AS registered_by, m.notes
            FROM movements m
            LEFT JOIN products p ON m.product_id = p.id
            LEFT JOIN employees e ON m.employee_id = e.id
            JOIN users u ON m.user_id = u.id
            WHERE m.id = ?
            """,
            (movement_id,),
        ).fetchone()
        return _clean_row_product(row) if row else None
    finally:
        conn.close()


def _clean_row_product(row):
    d = dict(row)
    d["product"] = _clean_product_label(d.get("product"))
    return d


def get_movement_detail(movement_id):
    """Detalle completo de un movimiento para el dialog del dashboard.
    Devuelve meta + desglose de items (sin seriales) o None si no existe."""
    conn = get_connection()
    try:
        row = conn.execute(
            """
            SELECT m.id, m.type, m.timestamp, m.quantity, m.notes,
                   COALESCE(p.name, '') AS product,
                   COALESCE(p.brand, '') AS brand,
                   COALESCE(p.unit, '') AS unit,
                   COALESCE(e.name, '-') AS employee,
                   COALESCE(e.cargo, '') AS cargo,
                   u.username AS registered_by,
                   COALESCE(w.name, '') AS warehouse
            FROM movements m
            LEFT JOIN products p ON m.product_id = p.id
            LEFT JOIN employees e ON m.employee_id = e.id
            JOIN users u ON m.user_id = u.id
            LEFT JOIN warehouses w ON m.warehouse_id = w.id
            WHERE m.id = ?
            """,
            (movement_id,),
        ).fetchone()
        if row is None:
            return None

        detail = dict(row)
        detail["product"] = _clean_product_label(detail["product"])
        detail["notes"] = _clean_product_label(detail["notes"])

        items = conn.execute(
            """
            SELECT name, brand, qty, unit, seriales
            FROM movement_items
            WHERE movement_id = ?
            ORDER BY id
            """,
            (movement_id,),
        ).fetchall()
        detail["items"] = [dict(i) for i in items]
        return detail
    finally:
        conn.close()


def create_movement(type_, product_id, employee_id, user_id, quantity, notes,
                    warehouse_id=None):
    """Crea un movimiento de inventario.
    Valida stock suficiente para salida/asignacion antes de ejecutar."""
    conn = get_connection()
    try:
        q = quantity or 1

        if type_ in ("salida", "asignacion"):
            current = conn.execute(
                "SELECT quantity FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if not current:
                raise ValueError("El producto no existe.")
            if current["quantity"] < q:
                raise ValueError(
                    f"Stock insuficiente: disponible {current['quantity']}, solicitado {q}"
                )

        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO movements
               (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
               VALUES (?,?,?,?,?,?,?)""",
            (
                type_,
                product_id,
                employee_id or None,
                user_id,
                q,
                notes or "",
                warehouse_id,
            ),
        )
        movement_id = cursor.lastrowid

        p = conn.execute(
            "SELECT name, COALESCE(brand,'') AS brand, unit FROM products WHERE id=?",
            (product_id,),
        ).fetchone()
        if p:
            cursor.execute(
                """INSERT INTO movement_items
                   (movement_id, product_id, name, brand, qty, unit, seriales)
                   VALUES (?, ?, ?, ?, ?, ?, '')""",
                (movement_id, product_id, p["name"], p["brand"], q, p["unit"]),
            )

        if type_ in ("entrada", "devolucion"):
            quantity_change = q
        elif type_ in ("salida", "asignacion"):
            quantity_change = -q
        else:
            quantity_change = 0

        if quantity_change != 0:
            conn.execute(
                "UPDATE products SET quantity = quantity + ?, updated_at=datetime('now','localtime') WHERE id=?",
                (quantity_change, product_id),
            )

        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
        _invalidate_prefix("movements_cache")
    except ValueError:
        conn.rollback()
        raise
    finally:
        conn.close()


def update_movement(movement_id, type_, employee_id, quantity, notes):
    """Edita un movimiento existente y reajusta el stock del producto."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        old = conn.execute(
            "SELECT * FROM movements WHERE id=?", (movement_id,)
        ).fetchone()
        if not old:
            raise ValueError("El movimiento no existe.")

        item_count = conn.execute(
            "SELECT COUNT(*) FROM movement_items WHERE movement_id=?", (movement_id,)
        ).fetchone()[0]
        if item_count > 1 or old["product_id"] in (0, None):
            raise ValueError(
                "Los movimientos con varios productos no se pueden editar. "
                "Elimínalo y regístralo de nuevo."
            )

        old_type = old["type"]
        old_qty = old["quantity"] or 1
        new_qty = quantity or 1
        product_id = old["product_id"]

        # Revertir efecto del movimiento anterior
        if old_type in ("entrada", "devolucion"):
            revert = -old_qty
        elif old_type in ("salida", "asignacion"):
            revert = old_qty
        else:
            revert = 0

        if revert != 0:
            cursor.execute(
                "UPDATE products SET quantity = quantity + ?, updated_at=datetime('now','localtime') WHERE id=?",
                (revert, product_id),
            )

        # Validar stock si el nuevo movimiento es salida/asignacion
        if type_ in ("salida", "asignacion"):
            current = conn.execute(
                "SELECT quantity FROM products WHERE id=?", (product_id,)
            ).fetchone()
            if current and current["quantity"] < new_qty:
                raise ValueError(
                    f"Stock insuficiente: disponible {current['quantity']}, solicitado {new_qty}"
                )

        # Aplicar efecto del nuevo movimiento
        if type_ in ("entrada", "devolucion"):
            apply = new_qty
        elif type_ in ("salida", "asignacion"):
            apply = -new_qty
        else:
            apply = 0

        if apply != 0:
            cursor.execute(
                "UPDATE products SET quantity = quantity + ?, updated_at=datetime('now','localtime') WHERE id=?",
                (apply, product_id),
            )

        cursor.execute(
            """UPDATE movements SET type=?, employee_id=?, quantity=?, notes=?
               WHERE id=?""",
            (type_, employee_id or None, new_qty, notes or "", movement_id),
        )
        # Mantener sincronizado el ítem (los simples tienen uno solo) para que
        # una futura eliminación revierta la cantidad correcta.
        cursor.execute(
            "UPDATE movement_items SET qty=? WHERE movement_id=?",
            (new_qty, movement_id),
        )

        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
        _invalidate_prefix("movements_cache")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def delete_movement(movement_id):
    """Elimina un movimiento y revierte su efecto en el stock (por ítem)."""
    conn = get_connection()
    try:
        old = conn.execute(
            "SELECT * FROM movements WHERE id=?", (movement_id,)
        ).fetchone()
        if not old:
            raise ValueError("El movimiento no existe.")

        items = [
            dict(r)
            for r in conn.execute(
                "SELECT product_id, name, COALESCE(brand,'') AS brand, qty, "
                "COALESCE(seriales,'') AS seriales FROM movement_items "
                "WHERE movement_id=? ORDER BY id",
                (movement_id,),
            ).fetchall()
        ]

        if items:
            revert_movement_stock(conn, old, items)
        else:
            # Movimiento sin ítems (legacy): revertir por la cabecera
            old_type = old["type"]
            old_qty = old["quantity"] or 1
            pid = old["product_id"]
            if old_type in ("entrada", "devolucion"):
                delta = -old_qty
            elif old_type in ("salida", "asignacion"):
                delta = old_qty
            else:
                delta = 0
            if delta and pid:
                conn.execute(
                    "UPDATE products SET quantity = quantity + ?, "
                    "updated_at=datetime('now','localtime') WHERE id=?",
                    (delta, pid),
                )

        conn.execute("DELETE FROM movements WHERE id=?", (movement_id,))
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_movement_available_products(warehouse_id=None):
    """Devuelve productos agrupados por (name,brand) con cantidad real disponible.
    - Serial-tracked (serial != ''): COUNT de filas 'disponible'
    - Quantity-tracked (sin serial): SUM de quantity
    """
    conn = get_connection()
    try:
        wh_filter = ""
        params = []
        if warehouse_id is not None:
            wh_filter = "AND p.warehouse_id = ?"
            params.append(warehouse_id)
        rows = conn.execute(
            f"""
            SELECT p.name, COALESCE(p.brand,'') AS brand,
                   MAX(p.unit) AS unit,
                   MAX(CASE WHEN COALESCE(p.serial,'') != '' THEN 1 ELSE 0 END) AS has_serial,
                   COALESCE(SUM(p.quantity), 0) AS total_quantity,
                   CASE
                       WHEN MAX(p.unit) = 'und'
                            AND MAX(CASE WHEN COALESCE(p.serial,'') != '' THEN 1 ELSE 0 END) = 1
                            AND COALESCE(SUM(p.quantity), 0) = 0
                       THEN SUM(CASE WHEN p.status='disponible' THEN 1 ELSE 0 END)
                       ELSE COALESCE(SUM(CASE WHEN p.status='disponible' THEN p.quantity ELSE 0 END), 0)
                   END AS available
            FROM products p
            WHERE p.status != 'inactivo'
              AND (
                   (p.unit = 'und' AND COALESCE(p.serial,'') != '' AND p.status = 'disponible')
                   OR (COALESCE(p.unit, 'und') != 'und' AND p.quantity > 0)
                   OR (p.unit = 'und' AND COALESCE(p.serial,'') = '' AND p.quantity > 0)
                  )
              {wh_filter}
            GROUP BY p.name, COALESCE(p.brand,'')
            HAVING available > 0
            ORDER BY p.name
            """,
            params,
        ).fetchall()
        return rows
    finally:
        conn.close()


def _parse_compound_notes(notes):
    """Parsea notas de movimiento compuesto:
    '30 m fibra optica | 2 und ROUTER [SN1, SN2]'
    Retorna lista de dicts {name, qty, unit, is_serial}."""
    import re
    items = []
    if not notes:
        return items
    for part in str(notes).split("|"):
        part = part.strip()
        m = re.match(r"^(\d+)\s+(\S+)\s+(.+)$", part)
        if not m:
            continue
        qty = int(m.group(1))
        unit = m.group(2)
        rest = m.group(3).strip()
        is_serial = bool(re.search(r"\[.*\]", rest))
        name = re.sub(r"\s*\[.*\]$", "", rest).strip()
        if name:
            items.append({"name": name, "qty": qty, "unit": unit, "is_serial": is_serial})
    return items


def get_products_pending_return_grouped(warehouse_id=None):
    """Devuelve productos por cantidad con pendiente de devolucion.
    Usa la tabla movement_items (product_id real + brand).
    Excluye items serializados, gestionados en get_serials_pending_return()."""
    conn = get_connection()
    try:
        wh_filter = ""
        params = []
        if warehouse_id is not None:
            wh_filter = "AND m.warehouse_id = ?"
            params.append(warehouse_id)

        rows = conn.execute(
            f"""
            SELECT mi.name, mi.brand, mi.unit, mi.seriales,
                   m.type, mi.qty
            FROM movement_items mi
            JOIN movements m ON mi.movement_id = m.id
            WHERE m.type IN ('salida', 'asignacion', 'devolucion')
              {wh_filter}
            ORDER BY mi.name
            """,
            params,
        ).fetchall()

        # net[(name, brand)] -> {unit, salida, devolucion}
        net = {}
        for r in rows:
            if r["seriales"]:
                continue  # serializados van en get_serials_pending_return
            key = (r["name"], r["brand"])
            d = net.setdefault(key, {"unit": r["unit"], "salida": 0, "devolucion": 0})
            d["unit"] = r["unit"]
            if r["type"] in ("salida", "asignacion"):
                d["salida"] += r["qty"]
            else:
                d["devolucion"] += r["qty"]

        result = []
        for (name, brand), d in net.items():
            pending = d["salida"] - d["devolucion"]
            if pending > 0:
                result.append({"name": name, "brand": brand, "unit": d["unit"], "pending": pending})
        result.sort(key=lambda r: r["name"])
        return result
    finally:
        conn.close()


def _extract_serials(name, notes):
    """Extrae seriales de un item en las notas compuestas para nombre dado."""
    for part in str(notes).split("|"):
        if name in part and "[" in part:
            start = part.find("[")
            end = part.find("]", start)
            if end > start:
                return part[start + 1:end]
    return ""


def create_grouped_movement(type_, name, brand, quantity, employee_id, user_id, notes,
                            warehouse_id=None):
    """Crea movimiento(s) para un grupo de productos (name+brand).
    Serial-tracked (salida): toma N unidades, 1 movimiento con seriales en notas.
    Quantity-tracked: ajusta quantity de un producto del grupo.
    Para devolucion serial usada return_serial() individualmente."""
    if type_ not in ("salida", "asignacion"):
        raise ValueError("create_grouped_movement solo soporta salida/asignacion.")

    conn = get_connection()
    try:
        q = quantity or 1
        sample = conn.execute(
            "SELECT unit, serial FROM products WHERE name=? AND COALESCE(brand,'')=? AND status != 'inactivo' LIMIT 1",
            (name, brand or ""),
        ).fetchone()
        if not sample:
            raise ValueError(f"No hay productos '{name}' disponibles.")

        is_serial = bool(sample["serial"] and sample["unit"] == "und")

        if is_serial:
            units = conn.execute(
                "SELECT id, serial FROM products WHERE name=? AND COALESCE(brand,'')=? AND status='disponible' LIMIT ?",
                (name, brand or "", q),
            ).fetchall()

            if len(units) < q:
                avail = conn.execute(
                    "SELECT COUNT(*) FROM products WHERE name=? AND COALESCE(brand,'')=? AND status='disponible'",
                    (name, brand or ""),
                ).fetchone()[0]
                raise ValueError(
                    f"Stock insuficiente: disponible {avail}, solicitado {q}"
                )

            serials = [u["serial"] for u in units if u["serial"]]
            serial_note = f"Seriales: {', '.join(serials)}" if serials else ""
            combined = (notes + " | " + serial_note) if notes else serial_note

            # Usar el primer unit como producto de referencia
            first_id = units[0]["id"]
            for unit in units:
                conn.execute(
                    "UPDATE products SET status='no disponible', updated_at=datetime('now','localtime') WHERE id=?",
                    (unit["id"],),
                )
            conn.execute(
                """INSERT INTO movements
                   (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
                   VALUES (?,?,?,?,?,?,?)""",
                (type_, first_id, employee_id or None, user_id, q, combined, warehouse_id),
            )
        else:
            if type_ in ("entrada", "devolucion"):
                qty_change = q
                target = conn.execute(
                    "SELECT id FROM products WHERE name=? AND COALESCE(brand,'')=? AND status='disponible' LIMIT 1",
                    (name, brand or ""),
                ).fetchone()
            else:
                qty_change = -q
                target = conn.execute(
                    "SELECT id, quantity FROM products WHERE name=? AND COALESCE(brand,'')=? AND status='disponible' AND quantity > 0 LIMIT 1",
                    (name, brand or ""),
                ).fetchone()

            if not target:
                raise ValueError(f"No hay stock disponible de '{name}'.")

            if qty_change < 0:
                curr = target["quantity"]
                if curr < q:
                    raise ValueError(
                        f"Stock insuficiente: disponible {curr}, solicitado {q}"
                    )

            conn.execute(
                "UPDATE products SET quantity = quantity + ?, updated_at=datetime('now','localtime') WHERE id=?",
                (qty_change, target["id"]),
            )
            conn.execute(
                """INSERT INTO movements
                   (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
                   VALUES (?,?,?,?,?,?,?)""",
                (type_, target["id"], employee_id or None, user_id, q, notes or "", warehouse_id),
            )

        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_serials_pending_return(search="", warehouse_id=None):
    """Devuelve unidades serializadas en estado 'no disponible' (en salida)
    con datos del producto y fecha del ultimo movimiento."""
    conn = get_connection()
    try:
        params = []
        wh_filter = ""
        if warehouse_id is not None:
            wh_filter = "AND p.warehouse_id = ?"
            params.append(warehouse_id)
        search_filter = ""
        if search:
            search_filter = "AND (p.name LIKE ? OR p.serial LIKE ?)"
            params.extend([f"%{search}%", f"%{search}%"])
        rows = conn.execute(
            f"""
            SELECT p.id, p.name, COALESCE(p.brand,'') AS brand,
                   p.serial, p.unit,
                   COALESCE(
                       (SELECT timestamp FROM movements
                        WHERE product_id = p.id AND type IN ('salida','asignacion')
                        ORDER BY id DESC LIMIT 1),
                       p.updated_at
                   ) AS salida_fecha
            FROM products p
            WHERE p.status = 'no disponible'
              AND COALESCE(p.serial,'') != ''
              AND p.unit = 'und'
              {wh_filter}
              {search_filter}
            ORDER BY p.name, p.serial
            """,
            params,
        ).fetchall()
        return rows
    finally:
        conn.close()


def return_serial(product_id, user_id, notes, warehouse_id=None):
    """Marca un producto serializado como 'disponible' y crea movimiento de devolucion."""
    conn = get_connection()
    try:
        prod = conn.execute(
            "SELECT * FROM products WHERE id=?", (product_id,)
        ).fetchone()
        if not prod:
            raise ValueError("Producto no encontrado.")
        if prod["serial"] in (None, ""):
            raise ValueError("El producto no tiene serial.")
        if prod["status"] != "no disponible":
            raise ValueError(f"El producto no esta en estado de salida. Estado actual: {prod['status']}")

        conn.execute(
            "UPDATE products SET status='disponible', updated_at=datetime('now','localtime') WHERE id=?",
            (product_id,),
        )
        conn.execute(
            """INSERT INTO movements
               (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
               VALUES ('devolucion', ?, NULL, ?, 1, ?, ?)""",
            (product_id, user_id, notes or "", warehouse_id),
        )
        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _resolve_quantity_target(conn, name, brand, require_stock):
    """Primer producto de un grupo apto para movimiento por cantidad."""
    cond = " AND quantity > 0" if require_stock else ""
    if brand:
        return conn.execute(
            "SELECT id, quantity, COALESCE(unit,'und') AS unit, COALESCE(brand,'') AS brand "
            "FROM products WHERE name=? AND COALESCE(brand,'')=? AND status='disponible'"
            + cond + " ORDER BY quantity DESC, id LIMIT 1",
            (name, brand),
        ).fetchone()
    return conn.execute(
        "SELECT id, quantity, COALESCE(unit,'und') AS unit, COALESCE(brand,'') AS brand "
        "FROM products WHERE name=? AND status='disponible'"
        + cond + " ORDER BY quantity DESC, id LIMIT 1",
        (name,),
    ).fetchone()


def apply_compound_items(conn, type_, items):
    """Aplica el stock de cada ítem dentro de la transacción de `conn`.

    Modifica los dicts de `items` agregando product_id/serials. Lanza ValueError
    si algo no cuadra; el llamador debe hacer rollback (el stock no se toca)."""
    for item in items:
        name = item["name"]
        brand = item.get("brand", "") or ""
        qty = int(item.get("qty") or 0)
        if qty < 1:
            raise ValueError(f"Cantidad inválida para '{name}'.")
        kind = item.get("kind", "quantity")

        if type_ == "salida":
            if kind == "serial":
                if brand:
                    units = conn.execute(
                        "SELECT id, serial FROM products WHERE name=? AND COALESCE(brand,'')=? "
                        "AND status='disponible' ORDER BY id LIMIT ?",
                        (name, brand, qty),
                    ).fetchall()
                else:
                    units = conn.execute(
                        "SELECT id, serial FROM products WHERE name=? AND status='disponible' "
                        "ORDER BY id LIMIT ?",
                        (name, qty),
                    ).fetchall()
                if len(units) < qty:
                    raise ValueError(
                        f"Stock insuficiente de '{name}': disponible {len(units)}, solicitado {qty}."
                    )
                ids = [u["id"] for u in units]
                conn.execute(
                    "UPDATE products SET status='no disponible', "
                    "updated_at=datetime('now','localtime') WHERE id IN "
                    f"({','.join('?' for _ in ids)})",
                    ids,
                )
                item["product_id"] = ids[0]
                item["serials"] = [u["serial"] for u in units if u["serial"]]
                item["unit"] = item.get("unit") or "und"
            else:
                target = _resolve_quantity_target(conn, name, brand, True)
                avail = target["quantity"] if target else 0
                if not target or target["quantity"] < qty:
                    raise ValueError(
                        f"Stock insuficiente de '{name}': disponible {avail}, solicitado {qty}."
                    )
                conn.execute(
                    "UPDATE products SET quantity = quantity - ?, "
                    "updated_at=datetime('now','localtime') WHERE id=?",
                    (qty, target["id"]),
                )
                item["product_id"] = target["id"]
                item["unit"] = item.get("unit") or target["unit"] or "und"

        else:  # devolucion
            if kind == "serial":
                ids = list(item.get("product_ids") or [])
                if not ids:
                    raise ValueError(f"No se marcaron seriales para '{name}'.")
                ph = ",".join("?" for _ in ids)
                rows = conn.execute(
                    f"SELECT id, serial, status FROM products WHERE id IN ({ph})", ids
                ).fetchall()
                if len(rows) != len(ids):
                    raise ValueError("Algunos productos no fueron encontrados.")
                for r in rows:
                    if r["status"] != "no disponible":
                        raise ValueError(
                            f"El serial {r['serial']} ({name}) no está en estado de salida."
                        )
                conn.execute(
                    "UPDATE products SET status='disponible', "
                    f"updated_at=datetime('now','localtime') WHERE id IN ({ph})",
                    ids,
                )
                item["product_id"] = ids[0]
                item["serials"] = [r["serial"] for r in rows if r["serial"]]
                item["qty"] = len(ids)
                item["unit"] = "und"
            else:
                target = _resolve_quantity_target(conn, name, brand, False)
                if not target:
                    raise ValueError(
                        f"No hay productos del grupo '{name}' disponibles para devolución."
                    )
                conn.execute(
                    "UPDATE products SET quantity = quantity + ?, "
                    "updated_at=datetime('now','localtime') WHERE id=?",
                    (qty, target["id"]),
                )
                item["product_id"] = target["id"]
                item["unit"] = item.get("unit") or target["unit"] or "und"
    return items


def _adjust_product_stock(conn, product_id, name, brand, delta):
    """Suma `delta` a la cantidad de un producto (por id o por nombre/marca)."""
    if product_id:
        conn.execute(
            "UPDATE products SET quantity = quantity + ?, "
            "updated_at=datetime('now','localtime') WHERE id=?",
            (delta, product_id),
        )
        return
    if brand:
        row = conn.execute(
            "SELECT id FROM products WHERE name=? AND COALESCE(brand,'')=? AND status='disponible' "
            "ORDER BY id LIMIT 1",
            (name, brand),
        ).fetchone()
    else:
        row = conn.execute(
            "SELECT id FROM products WHERE name=? AND status='disponible' ORDER BY id LIMIT 1",
            (name,),
        ).fetchone()
    if row:
        conn.execute(
            "UPDATE products SET quantity = quantity + ?, "
            "updated_at=datetime('now','localtime') WHERE id=?",
            (delta, row["id"]),
        )


def revert_movement_stock(conn, movement, items):
    """Revierte el efecto en stock de un movimiento usando sus ítems.

    - salida/asignación: repone cantidad o marca seriales como disponibles.
    - entrada/devolución: descuenta cantidad o marca seriales como no disponibles.
    """
    type_ = movement["type"]
    for it in items:
        pid = it.get("product_id")
        qty = it.get("qty") or 1
        seriales = [
            s.strip() for s in (it.get("seriales") or "").split(",") if s.strip()
        ]
        if type_ in ("salida", "asignacion"):
            if seriales:
                ph = ",".join("?" for _ in seriales)
                conn.execute(
                    "UPDATE products SET status='disponible', "
                    f"updated_at=datetime('now','localtime') WHERE serial IN ({ph})",
                    seriales,
                )
            else:
                _adjust_product_stock(conn, pid, it["name"], it.get("brand") or "", +qty)
        elif type_ in ("entrada", "devolucion"):
            if seriales:
                ph = ",".join("?" for _ in seriales)
                conn.execute(
                    "UPDATE products SET status='no disponible', "
                    f"updated_at=datetime('now','localtime') WHERE serial IN ({ph})",
                    seriales,
                )
            else:
                _adjust_product_stock(conn, pid, it["name"], it.get("brand") or "", -qty)


def get_products_brief(ids):
    """Devuelve id/name/brand/serial/unit para una lista de ids de productos."""
    if not ids:
        return []
    conn = get_connection()
    try:
        ph = ",".join("?" for _ in ids)
        rows = conn.execute(
            f"SELECT id, name, COALESCE(brand,'') AS brand, COALESCE(serial,'') AS serial, "
            f"COALESCE(unit,'und') AS unit FROM products WHERE id IN ({ph})",
            list(ids),
        ).fetchall()
        return rows
    finally:
        conn.close()


def create_compound_movement(type_, user_id, items, notes="", warehouse_id=None, employee_id=None):
    """Crea un movimiento compuesto aplicando el stock en la MISMA transacción.

    items: dicts con name, brand, qty, unit y kind ('quantity'|'serial').
    Para devolución por serial, 'product_ids' con las unidades a reponer.
    Si algo falla no se aplica ningún cambio de stock ni se crea el movimiento.
    """
    conn = get_connection()
    try:
        apply_compound_items(conn, type_, items)

        total_qty = sum(int(i["qty"]) for i in items)
        parts = []
        for item in items:
            line = f"{item['qty']} {item['unit']} {item['name']}"
            serials = item.get("serials") or []
            if serials:
                shown = ", ".join(serials[:3])
                extra = len(serials) - 3
                line += f" [{shown}... +{extra}]" if extra > 0 else f" [{shown}]"
            parts.append(line)
        summary = " | ".join(parts)
        combined = (notes + " | " + summary) if notes else summary

        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO movements
               (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
               VALUES (?, 0, ?, ?, ?, ?, ?)""",
            (type_, employee_id, user_id, total_qty, combined, warehouse_id),
        )
        movement_id = cursor.lastrowid

        for item in items:
            seriales_str = ", ".join(item.get("serials", [])) if item.get("serials") else ""
            cursor.execute(
                """INSERT INTO movement_items
                   (movement_id, product_id, name, brand, qty, unit, seriales)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    movement_id,
                    item.get("product_id"),
                    item["name"],
                    item.get("brand", ""),
                    item["qty"],
                    item.get("unit", "und"),
                    seriales_str,
                ),
            )

        conn.commit()
        _invalidate_prefix("units_by_model")
        _invalidate_prefix("products_grouped")
        return movement_id
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_movement_counts():
    """Obtiene estadísticas de movimientos"""
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT
                COALESCE(SUM(type='entrada'), 0) entrada,
                COALESCE(SUM(type='salida'), 0) salida,
                COALESCE(SUM(type='devolucion'), 0) devolucion,
                COALESCE(SUM(type='asignacion'), 0) asignacion,
                COALESCE(SUM(type='eliminacion'), 0) eliminacion,
                COALESCE(SUM(type='eliminacion_grupo'), 0) eliminacion_grupo,
                COALESCE(SUM(type='modificacion'), 0) modificacion
            FROM movements
        """).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_dashboard_stats(warehouse_id=None):
    """Obtiene conteos de productos, movimientos y movimientos recientes
    en una sola conexión a la base de datos. Opcionalmente filtrar por almacén."""
    conn = get_connection()
    try:
        wh_filter_p = ""
        wh_filter_m = ""
        params_p = []
        params_m = []
        if warehouse_id is not None:
            wh_filter_p = "AND warehouse_id = ?"
            wh_filter_m = "AND m.warehouse_id = ?"
            params_p.append(warehouse_id)
            params_m.append(warehouse_id)

        product_row = conn.execute(
            f"""
            SELECT COUNT(*) total,
                   COALESCE(SUM(CASE WHEN status='disponible' THEN 1 ELSE 0 END), 0) disponible,
                   COALESCE(SUM(CASE WHEN status='disponible' AND quantity <= 0
                                     AND COALESCE(serial,'') = '' THEN 1 ELSE 0 END), 0) sin_stock,
                   COALESCE(SUM(status='inactivo'), 0) inactivo
            FROM products
            WHERE 1=1 {wh_filter_p}
            """,
            params_p,
        ).fetchone()

        movement_row = conn.execute(
            f"""
            SELECT
                COALESCE(SUM(type='entrada'), 0) entrada,
                COALESCE(SUM(type='salida'), 0) salida,
                COALESCE(SUM(type='devolucion'), 0) devolucion,
                COALESCE(SUM(type='asignacion'), 0) asignacion,
                COALESCE(SUM(type='eliminacion'), 0) eliminacion,
                COALESCE(SUM(type='eliminacion_grupo'), 0) eliminacion_grupo,
                COALESCE(SUM(type='modificacion'), 0) modificacion
            FROM movements m
            WHERE 1=1 {wh_filter_m}
            """,
            params_m,
        ).fetchone()

        params_ml = list(params_m)
        params_ml.append(50)
        movements = [
            _clean_row_product(r)
            for r in conn.execute(
                f"""
                SELECT m.id, m.type, m.timestamp, m.quantity,
                       COALESCE(p.name, m.notes) AS product,
                       COALESCE(e.name, '-') AS employee,
                       u.username AS registered_by, m.notes
                FROM movements m
                LEFT JOIN products p ON m.product_id = p.id
                LEFT JOIN employees e ON m.employee_id = e.id
                JOIN users u ON m.user_id = u.id
                WHERE 1=1 {wh_filter_m}
                ORDER BY m.id DESC LIMIT ?
                """,
                params_ml,
            ).fetchall()
        ]

        return {
            "product_counts": dict(product_row),
            "movement_counts": dict(movement_row),
            "recent_movements": movements,
        }
    finally:
        conn.close()

import time as _time
from database.connection import get_connection

_cache: dict = {}
_CACHE_TTL = 5  # segundos


def _cached(key, fn):
    now = _time.time()
    if key in _cache and (now - _cache[key][0]) < _CACHE_TTL:
        return _cache[key][1]
    data = fn()
    _cache[key] = (now, data)
    return data


def _invalidate(key):
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
    finally:
        conn.close()


def delete_user(user_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM users WHERE id=?", (user_id,))
        conn.commit()
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
    finally:
        conn.close()


def delete_supplier(supplier_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM suppliers WHERE id=?", (supplier_id,))
        conn.commit()
        _invalidate("suppliers")
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
    finally:
        conn.close()


def delete_employee(employee_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM employees WHERE id=?", (employee_id,))
        conn.commit()
        _invalidate("employees")
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
    finally:
        conn.close()


def delete_vehicle(vehicle_id):
    conn = get_connection()
    try:
        conn.execute("DELETE FROM vehicles WHERE id=?", (vehicle_id,))
        conn.commit()
    finally:
        conn.close()


# ── PRODUCTS ──────────────────────────────────────────────────────────────────


def get_products_grouped(search="", status_filter="todos", warehouse_id=None):
    """Una fila por (name, brand): total de unidades, proveedor, estado dominante."""
    conn = get_connection()
    try:
        q = f"%{search}%"
        where = "(p.name LIKE ? OR p.brand LIKE ?)"
        params = [q, q]
        if status_filter == "disponible":
            where += " AND p.status = 'disponible'"
        elif status_filter == "no disponible":
            where += " AND p.status = 'no disponible'"
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


def get_units_by_model(name, brand, warehouse_id=None):
    """Devuelve filas individuales para un modelo (name+brand)."""
    conn = get_connection()
    try:
        params = [name, brand]
        wh_filter = ""
        if warehouse_id is not None:
            wh_filter = "AND p.warehouse_id = ?"
            params.append(warehouse_id)
        rows = conn.execute(
            f"""
            SELECT p.id, p.serial, p.mac, p.status, p.barcode,
                   COALESCE(p.unit,'und') AS unit,
                   COALESCE(p.quantity, 0) AS quantity,
                   p.created_at
            FROM products p
            WHERE p.name = ? AND COALESCE(p.brand,'') = ?
              AND p.status != 'inactivo'
              {wh_filter}
            ORDER BY p.id
            """,
            params,
        ).fetchall()
        return rows
    finally:
        conn.close()


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


def get_products_by_status(status):
    """Obtiene productos por estado"""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT id, name || ' - ' || COALESCE(barcode, '') AS label 
               FROM products WHERE status=?""",
            (status,),
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


def get_products_pending_return():
    """Obtiene productos dados salida que aún no han sido devueltos"""
    conn = get_connection()
    try:
        rows = conn.execute(
            """
            SELECT p.id, p.name, p.barcode, p.quantity as stock,
                   COALESCE(salida.qty, 0) - COALESCE(devolucion.qty, 0) as available
            FROM products p
            LEFT JOIN (
                SELECT product_id, SUM(quantity) as qty FROM movements
                WHERE type = 'salida' GROUP BY product_id
            ) salida ON p.id = salida.product_id
            LEFT JOIN (
                SELECT product_id, SUM(quantity) as qty FROM movements
                WHERE type = 'devolucion' GROUP BY product_id
            ) devolucion ON p.id = devolucion.product_id
            WHERE COALESCE(salida.qty, 0) > COALESCE(devolucion.qty, 0)
            ORDER BY available DESC
            """
        ).fetchall()
        return rows
    finally:
        conn.close()


def get_product_counts():
    """Obtiene estadísticas de productos"""
    conn = get_connection()
    try:
        row = conn.execute("""
            SELECT COUNT(*) total,
                    COALESCE(SUM(quantity), 0) disponible,
                    COALESCE(SUM(quantity <= 0), 0) sin_stock,
                    COALESCE(SUM(status='inactivo'), 0)    inactivo
            FROM products
        """).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_low_stock_products():
    """Obtiene productos con stock bajo"""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT p.id, p.name, p.barcode, p.quantity, p.location,
                      COALESCE(sup.name,'N/A') AS supplier_name
               FROM products p
               LEFT JOIN suppliers sup ON p.supplier_id = sup.id
               WHERE p.quantity = 0 AND p.status != 'inactivo'
               ORDER BY p.quantity ASC"""
        ).fetchall()
        return rows
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
    finally:
        conn.close()


def update_product_unit(product_id, serial, mac, barcode, status):
    """Actualiza los identificadores y estado de una unidad individual."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE products SET serial=?, mac=?, barcode=?, status=?,
                                 updated_at=datetime('now','localtime')
               WHERE id=?""",
            (serial or None, mac or None, barcode or None, status, product_id),
        )
        conn.commit()
    finally:
        conn.close()


def update_product_group(old_name, old_brand, new_name, new_brand, supplier_id):
    """Actualiza nombre, marca y proveedor de todas las unidades de un grupo."""
    conn = get_connection()
    try:
        conn.execute(
            """UPDATE products SET name=?, brand=?, supplier_id=?,
                                 updated_at=datetime('now','localtime')
               WHERE name=? AND COALESCE(brand,'')=? AND status!='inactivo'""",
            (new_name, new_brand, supplier_id or None, old_name, old_brand),
        )
        conn.commit()
    finally:
        conn.close()


def update_product_quantity(product_id, quantity_change):
    """Actualiza la cantidad de un producto (puede ser positivo o negativo)"""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE products SET quantity = quantity + ?, updated_at=datetime('now','localtime') WHERE id=?",
            (quantity_change, product_id),
        )
        conn.commit()
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
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def delete_product(product_id):
    """Elimina físicamente un producto solo si no tiene movimientos asociados.
    Para productos con movimientos, usar deactivate_product() en su lugar."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(*) FROM movements WHERE product_id=?", (product_id,)
        )
        movement_count = cursor.fetchone()[0]

        if movement_count > 0:
            raise ValueError(
                f"No se puede eliminar el producto porque tiene {movement_count} movimientos asociados. Use la función de baja en su lugar."
            )

        conn.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def delete_product_group(name, brand):
    """Elimina/desactiva todas las unidades de un grupo (name+brand).
    Sin movimientos → DELETE físico. Con movimientos → status='inactivo'.
    Retorna (eliminados: int, desactivados: int)."""
    conn = get_connection()
    try:
        rows = conn.execute(
            """SELECT p.id,
                      (SELECT COUNT(*) FROM movements WHERE product_id = p.id) AS mov_count
               FROM products p
               WHERE p.name = ? AND COALESCE(p.brand,'') = ? AND p.status != 'inactivo'""",
            (name, brand or ""),
        ).fetchall()
        eliminados = 0
        desactivados = 0
        for row in rows:
            if row["mov_count"] == 0:
                conn.execute("DELETE FROM products WHERE id=?", (row["id"],))
                eliminados += 1
            else:
                conn.execute(
                    "UPDATE products SET status='inactivo', updated_at=datetime('now','localtime') WHERE id=?",
                    (row["id"],),
                )
                desactivados += 1
        conn.commit()
        return eliminados, desactivados
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


# ── MOVEMENTS ─────────────────────────────────────────────────────────────────


def get_all_movements(search="", limit=200, warehouse_id=None):
    conn = get_connection()
    try:
        q = f"%{search}%"
        params = [q, q, q, q]
        wh_filter = ""
        if warehouse_id is not None:
            wh_filter = "AND m.warehouse_id = ?"
            params.append(warehouse_id)
        params.append(limit)
        rows = conn.execute(
            f"""
            SELECT m.id, m.type, m.timestamp, m.quantity,
                   p.name || ' (' || COALESCE(p.barcode, p.serial, '') || ')' AS product,
                   COALESCE(e.name, '-') AS employee,
                   u.username AS registered_by, m.notes
            FROM movements m
            JOIN products p ON m.product_id = p.id
            LEFT JOIN employees e ON m.employee_id = e.id
            JOIN users u ON m.user_id = u.id
            WHERE (m.type LIKE ? OR p.name LIKE ? OR p.barcode LIKE ? OR e.name LIKE ?)
            {wh_filter}
            ORDER BY m.id DESC LIMIT ?
        """,
            params,
        ).fetchall()
        return rows
    finally:
        conn.close()


def create_movement(type_, product_id, employee_id, user_id, quantity, notes,
                    warehouse_id=None):
    """Crea un movimiento de inventario"""
    conn = get_connection()
    try:
        # Insertar el movimiento
        conn.execute(
            """INSERT INTO movements
               (type, product_id, employee_id, user_id, quantity, notes, warehouse_id)
               VALUES (?,?,?,?,?,?,?)""",
            (
                type_,
                product_id,
                employee_id or None,
                user_id,
                quantity or 1,
                notes or "",
                warehouse_id,
            ),
        )

        # Actualizar la cantidad del producto
        if type_ in ("entrada", "devolucion"):
            quantity_change = quantity or 1
        elif type_ in ("salida", "asignacion"):
            quantity_change = -(quantity or 1)
        else:
            quantity_change = 0

        if quantity_change != 0:
            conn.execute(
                "UPDATE products SET quantity = quantity + ?, updated_at=datetime('now','localtime') WHERE id=?",
                (quantity_change, product_id),
            )

        conn.commit()
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
                COALESCE(SUM(type='asignacion'), 0) asignacion
            FROM movements
        """).fetchone()
        return dict(row)
    finally:
        conn.close()


def get_dashboard_stats():
    """Obtiene conteos de productos, movimientos y movimientos recientes
    en una sola conexión a la base de datos."""
    conn = get_connection()
    try:
        product_row = conn.execute("""
            SELECT COUNT(*) total,
                   COALESCE(SUM(quantity), 0) disponible,
                   COALESCE(SUM(quantity <= 0), 0) sin_stock,
                   COALESCE(SUM(status='inactivo'), 0) inactivo
            FROM products
        """).fetchone()

        movement_row = conn.execute("""
            SELECT
                COALESCE(SUM(type='entrada'), 0) entrada,
                COALESCE(SUM(type='salida'), 0) salida,
                COALESCE(SUM(type='devolucion'), 0) devolucion,
                COALESCE(SUM(type='asignacion'), 0) asignacion
            FROM movements
        """).fetchone()

        movements = conn.execute("""
            SELECT m.id, m.type, m.timestamp, m.quantity,
                   p.name || ' (' || COALESCE(p.barcode, p.serial, '') || ')' AS product,
                   COALESCE(e.name, '-') AS employee,
                   u.username AS registered_by, m.notes
            FROM movements m
            JOIN products p ON m.product_id = p.id
            LEFT JOIN employees e ON m.employee_id = e.id
            JOIN users u ON m.user_id = u.id
            ORDER BY m.id DESC LIMIT 50
        """).fetchall()

        return {
            "product_counts": dict(product_row),
            "movement_counts": dict(movement_row),
            "recent_movements": movements,
        }
    finally:
        conn.close()

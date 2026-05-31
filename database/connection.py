import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "inventory.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def initialize_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Primero verificamos si existe la tabla scanners old
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='scanners'"
    )
    old_scanners_exists = cursor.fetchone() is not None

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS warehouses (
            id       INTEGER PRIMARY KEY AUTOINCREMENT,
            name     TEXT UNIQUE NOT NULL,
            location TEXT DEFAULT ''
        );
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'supervisor'
        );
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact TEXT DEFAULT '',
            rif TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            cedula TEXT UNIQUE NOT NULL,
            cargo TEXT DEFAULT '',
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS vehicles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            brand TEXT NOT NULL,
            model TEXT DEFAULT '',
            plate TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            barcode TEXT UNIQUE,
            brand TEXT DEFAULT '',
            serial TEXT,
            mac TEXT,
            quantity INTEGER DEFAULT 0,
            supplier_id INTEGER REFERENCES suppliers(id) ON DELETE SET NULL,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT DEFAULT (datetime('now','localtime'))
        );
        CREATE TABLE IF NOT EXISTS movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            product_id INTEGER NOT NULL,
            employee_id INTEGER REFERENCES employees(id),
            user_id INTEGER NOT NULL REFERENCES users(id),
            quantity INTEGER DEFAULT 1,
            notes TEXT DEFAULT '',
            timestamp TEXT DEFAULT (datetime('now','localtime'))
        );
    """)

    # Agregar columna product_id si no existe (para bases de datos existentes)
    try:
        cursor.execute("ALTER TABLE movements ADD COLUMN product_id INTEGER")
    except sqlite3.OperationalError:
        pass  # La columna ya existe

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN unit TEXT DEFAULT 'und'")
    except sqlite3.OperationalError:
        pass  # La columna ya existe

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN status TEXT DEFAULT 'disponible'")
    except sqlite3.OperationalError:
        pass  # La columna ya existe

    try:
        cursor.execute("ALTER TABLE products ADD COLUMN warehouse_id INTEGER REFERENCES warehouses(id)")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE users ADD COLUMN must_change_password INTEGER DEFAULT 0")
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute("ALTER TABLE movements ADD COLUMN warehouse_id INTEGER REFERENCES warehouses(id)")
    except sqlite3.OperationalError:
        pass

    # Si existe la tabla scanners old, migramos los datos
    if old_scanners_exists:
        # Verificar si movements tiene scanner_id para migrar
        cursor.execute("PRAGMA table_info(movements)")
        columns = [col[1] for col in cursor.fetchall()]

        # Copiamos los datos de scanners a products
        cursor.execute("""
            INSERT INTO products (name, barcode, serial, supplier_id, created_at)
            SELECT model, serial_number, serial_number, supplier_id, created_at
            FROM scanners
        """)

        # Actualizamos movements para referenciar products
        if "scanner_id" in columns:
            cursor.execute("""
                UPDATE movements SET product_id = (
                    SELECT p.id FROM products p 
                    JOIN scanners s ON p.barcode = s.serial_number 
                    WHERE s.id = movements.scanner_id
                )
            """)
        elif "product_id" in columns:
            # product_id ya existe pero puede ser NULL, actualizamos desde products
            cursor.execute("""
                UPDATE movements SET product_id = (
                    SELECT p.id FROM products p 
                    JOIN scanners s ON p.barcode = s.serial_number 
                    WHERE s.id = (
                        SELECT id FROM scanners WHERE serial_number = (
                            SELECT barcode FROM products WHERE id = movements.product_id
                        )
                    )
                )
                WHERE product_id IS NULL OR product_id = 0
            """)

        # Eliminamos la tabla scanners
        cursor.execute("DROP TABLE IF EXISTS scanners")

    # Seed almacenes por defecto
    cursor.execute(
        "INSERT OR IGNORE INTO warehouses (name, location) VALUES (?, ?)",
        ("Almacén Central", "Planta Principal"),
    )
    cursor.execute(
        "INSERT OR IGNORE INTO warehouses (name, location) VALUES (?, ?)",
        ("Almacén Secundario", "Depósito"),
    )

    # Default admin
    from core.auth import hash_password

    admin_hash = hash_password("admin123")
    cursor.execute("SELECT id FROM users WHERE username='admin'")
    if not cursor.fetchone():
        cursor.execute(
            "INSERT INTO users (username, password_hash, role, must_change_password) VALUES (?, ?, ?, 1)",
            ("admin", admin_hash, "admin"),
        )
    conn.commit()
    conn.close()

    # Permisos restrictivos al archivo de BD (solo dueño puede leer/escribir)
    try:
        import os as _os
        _os.chmod(DB_PATH, 0o600)
    except Exception:
        pass

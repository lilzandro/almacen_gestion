"""Respaldos y restauración de la base de datos SQLite de DigiCable.

El respaldo usa la API de backup de SQLite para obtener una copia consistente
aunque la base esté en modo WAL. La restauración valida el archivo de origen,
crea un respaldo automático de la base actual y copia el contenido con la misma
API, evitando reemplazar archivos a mano.
"""
from __future__ import annotations

import os
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

from database import connection

REQUIRED_TABLES = frozenset(
    {
        "warehouses",
        "users",
        "suppliers",
        "employees",
        "vehicles",
        "products",
        "movements",
        "movement_items",
        "app_meta",
    }
)
BACKUP_PREFIX = "DigiCable_respaldo"
SAFETY_PREFIX = "DigiCable_seguridad"


class DatabaseBackupError(Exception):
    """Error controlado al crear o restaurar un respaldo."""


class InvalidDatabaseError(DatabaseBackupError):
    """El archivo seleccionado no es una base de datos válida de DigiCable."""


def database_path() -> str:
    """Ruta absoluta de la base de datos activa."""
    return os.path.abspath(connection.DB_PATH)


def backup_dir() -> str:
    """Carpeta de respaldos automáticos.

    Se puede cambiar con DIGICABLE_BACKUP_DIR (útil en pruebas o despliegues).
    """
    base = os.environ.get("DIGICABLE_BACKUP_DIR")
    if not base:
        base = os.path.join(
            os.environ.get("APPDATA") or os.path.expanduser("~"),
            "DigiCable",
            "backups",
        )
    return base


def default_backup_name(prefix: str = BACKUP_PREFIX, when: datetime | None = None) -> str:
    """Nombre sugerido para un archivo de respaldo."""
    stamp = (when or datetime.now()).strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{stamp}.db"


def _unique_path(directory: str, filename: str) -> str:
    base, ext = os.path.splitext(filename)
    candidate = os.path.join(directory, filename)
    counter = 1
    while os.path.exists(candidate):
        candidate = os.path.join(directory, f"{base}_{counter}{ext}")
        counter += 1
    return candidate


def _remove_sqlite_sidecars(path: str) -> None:
    """Elimina los archivos auxiliares -wal/-shm de una copia ya consolidada."""
    for suffix in ("-wal", "-shm"):
        try:
            os.remove(path + suffix)
        except FileNotFoundError:
            pass
        except OSError:
            pass


def _connect(path: str, *, readonly: bool = False) -> sqlite3.Connection:
    if readonly:
        try:
            uri = Path(path).resolve().as_uri() + "?mode=ro"
            conn = sqlite3.connect(uri, uri=True, timeout=30)
        except sqlite3.Error:
            conn = sqlite3.connect(path, timeout=30)
    else:
        conn = sqlite3.connect(path, timeout=30)
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def validate_database(path: str) -> dict:
    """Comprueba que el archivo sea una base SQLite íntegra de DigiCable.

    Devuelve información básica del archivo. Lanza InvalidDatabaseError con un
    mensaje entendible si no sirve para restaurar.
    """
    path = os.path.abspath(path)
    if not os.path.isfile(path):
        raise InvalidDatabaseError("El archivo seleccionado no existe.")
    if os.path.getsize(path) == 0:
        raise InvalidDatabaseError("El archivo está vacío.")

    conn = None
    try:
        conn = _connect(path, readonly=True)
        integrity = conn.execute("PRAGMA integrity_check").fetchone()
        result = str(integrity[0]).strip().lower() if integrity else ""
        if result != "ok":
            raise InvalidDatabaseError(
                "La verificación de integridad del archivo falló: "
                f"{integrity[0] if integrity else 'sin resultado'}."
            )

        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        missing = sorted(REQUIRED_TABLES - tables)
        if missing:
            raise InvalidDatabaseError(
                "El archivo no parece ser una base de datos de DigiCable. "
                "Faltan las tablas: " + ", ".join(missing) + "."
            )

        return {
            "path": path,
            "size": os.path.getsize(path),
            "tables": sorted(tables),
            "integrity": "ok",
        }
    except sqlite3.DatabaseError as exc:
        raise InvalidDatabaseError(
            "El archivo no es una base de datos SQLite válida o está dañado."
        ) from exc
    finally:
        if conn is not None:
            conn.close()


def create_backup(dest_path: str, source_path: str | None = None) -> dict:
    """Crea una copia consistente de la base activa en dest_path.

    Primero escribe en un archivo temporal, valida la copia y luego la mueve al
    destino definitivo. Así un error no deja un respaldo incompleto.
    """
    source = os.path.abspath(source_path or connection.DB_PATH)
    dest = os.path.abspath(dest_path)
    if not os.path.isfile(source):
        raise DatabaseBackupError("No se encontró la base de datos actual.")
    if os.path.normcase(source) == os.path.normcase(dest):
        raise DatabaseBackupError(
            "El archivo de destino debe ser distinto de la base de datos actual."
        )

    dest_dir = os.path.dirname(dest) or "."
    os.makedirs(dest_dir, exist_ok=True)

    fd, tmp_path = tempfile.mkstemp(
        prefix=".digicable_backup_", suffix=".db", dir=dest_dir
    )
    os.close(fd)
    try:
        src = _connect(source)
        try:
            dst = _connect(tmp_path)
            try:
                src.backup(dst)
                dst.commit()
                try:
                    dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except sqlite3.Error:
                    pass
                try:
                    dst.execute("PRAGMA journal_mode=DELETE")
                except sqlite3.Error:
                    pass
            finally:
                dst.close()
        finally:
            src.close()

        validate_database(tmp_path)
        _remove_sqlite_sidecars(tmp_path)
        os.replace(tmp_path, dest)
        _remove_sqlite_sidecars(dest)
    except Exception:
        try:
            os.remove(tmp_path)
        except OSError:
            pass
        _remove_sqlite_sidecars(tmp_path)
        raise

    return {
        "path": dest,
        "size": os.path.getsize(dest),
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "source": source,
    }


def create_safety_backup(source_path: str | None = None) -> dict:
    """Respaldo automático de la base actual antes de una restauración."""
    directory = backup_dir()
    os.makedirs(directory, exist_ok=True)
    dest = _unique_path(directory, default_backup_name(SAFETY_PREFIX))
    return create_backup(dest, source_path or connection.DB_PATH)


def _clear_repository_cache() -> None:
    from database import repository

    repository.clear_cache()


def restore_database(source_path: str, target_path: str | None = None) -> dict:
    """Reemplaza la base actual con el contenido de un respaldo validado.

    Antes de tocar la base actual crea un respaldo de seguridad en la carpeta de
    respaldos automáticos. Si la restauración falla, ese archivo permite volver
    atrás sin pérdida de datos.
    """
    source = os.path.abspath(source_path)
    target = os.path.abspath(target_path or connection.DB_PATH)

    if not os.path.isfile(source):
        raise DatabaseBackupError("El archivo seleccionado no existe.")
    if os.path.normcase(source) == os.path.normcase(target):
        raise DatabaseBackupError(
            "Selecciona un archivo de respaldo distinto de la base de datos actual."
        )

    validate_database(source)
    safety = create_safety_backup(target)

    try:
        src = _connect(source)
        try:
            dst = _connect(target)
            try:
                src.backup(dst)
                dst.commit()
                check = dst.execute("PRAGMA integrity_check").fetchone()
                if not check or str(check[0]).strip().lower() != "ok":
                    raise sqlite3.DatabaseError(
                        "la verificación de integridad de la copia falló"
                    )
                try:
                    dst.execute("PRAGMA wal_checkpoint(TRUNCATE)")
                except sqlite3.Error:
                    pass
            finally:
                dst.close()
        finally:
            src.close()
    except Exception as exc:
        raise DatabaseBackupError(
            "No se pudo restaurar la base de datos. La base actual no fue "
            f"reemplazada. Respaldo de seguridad: {safety['path']}. Detalle: {exc}"
        ) from exc

    # Aplica migraciones/columnas nuevas y vuelve a validar el resultado.
    try:
        connection.initialize_db()
        _clear_repository_cache()
        validate_database(target)
    except Exception as exc:
        raise DatabaseBackupError(
            "La copia se restauró, pero no se pudo actualizar el esquema de la "
            f"base de datos. Respaldo de seguridad: {safety['path']}. "
            f"Detalle: {exc}"
        ) from exc

    return {
        "path": target,
        "safety_backup": safety["path"],
        "size": os.path.getsize(target),
        "restored_at": datetime.now().isoformat(timespec="seconds"),
    }

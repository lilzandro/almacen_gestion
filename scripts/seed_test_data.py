#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
seed_test_data.py — Limpia la base de datos y la siembra con datos de prueba realistas.

Pasos:
1. Respaldo automático obligatorio de inventory.db (y -wal/-shm).
2. Reset limpio del esquema borrando la BD y llamando a database.connection.initialize_db().
3. Siembra realista usando únicamente funciones de database.repository:
   - Proveedores (de ventanaejemplo/data.py)
   - Empleados y vehículos
   - Usuario supervisor de prueba
   - Productos representativos de las 5 categorías (Equipos de Red, Herramientas, Cableado,
     Conectores/Pasivos, Accesorios de Instalación) distribuidos en los 2 almacenes.
   - Movimientos variados (entradas, salidas compuestas, devoluciones, asignaciones)
     repartidos en los últimos ~60 días con timestamps ajustados.
"""

import os
import shutil
import sys
import time
from datetime import datetime, timedelta

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.auth import hash_password
from database.connection import DB_PATH, get_connection, initialize_db
from database.repository import (
    bulk_create_products,
    create_compound_movement,
    create_employee,
    create_movement,
    create_product,
    create_supplier,
    create_user,
    create_vehicle,
    get_all_users,
    get_all_warehouses,
)


def step_1_backup():
    print("=" * 70)
    print("PASO 1: Creando backup obligatorio antes de modificar nada...")
    ts = time.strftime("%Y%m%d-%H%M%S")
    backed_up = []
    base_target = DB_PATH
    for ext in ("", "-wal", "-shm"):
        src = f"{base_target}{ext}"
        if os.path.exists(src):
            dst = f"{src}.bak-{ts}"
            shutil.copy2(src, dst)
            backed_up.append(dst)

    if backed_up:
        print(f"✓ Backup guardado exitosamente como:")
        for b in backed_up:
            print(f"  -> {b}")
    else:
        print("ℹ No se encontró archivo de BD preexistente para respaldar.")
    print("=" * 70)
    return ts


def step_2_reset_schema():
    print("\nPASO 2: Reseteando esquema de base de datos desde cero...")
    base_target = DB_PATH
    for ext in ("", "-wal", "-shm"):
        p = f"{base_target}{ext}"
        if os.path.exists(p):
            os.remove(p)
            print(f"✓ Eliminado: {p}")

    initialize_db()
    print("✓ Esquema inicializado limpiamente con initialize_db().")


def step_3_seed_data():
    print("\nPASO 3: Sembrando datos realistas...")

    # 1. Obtener almacenes y usuario admin
    warehouses = get_all_warehouses()
    if not warehouses:
        raise RuntimeError("No se encontraron almacenes creados por initialize_db().")
    wh_central = warehouses[0]["id"]
    wh_secundario = warehouses[1]["id"] if len(warehouses) > 1 else wh_central
    print(f"✓ Almacenes disponibles: Central={wh_central}, Secundario={wh_secundario}")

    users = get_all_users()
    admin_user = next((u for u in users if u["username"] == "admin"), None)
    if not admin_user:
        raise RuntimeError("No se encontró usuario admin.")
    admin_id = admin_user["id"]

    # 2. Usuario Supervisor de prueba
    create_user("supervisor", hash_password("super123"), "supervisor")
    users = get_all_users()
    super_user = next(u for u in users if u["username"] == "supervisor")
    super_id = super_user["id"]
    print(f"✓ Creado usuario supervisor de prueba: supervisor / super123 (ID: {super_id})")

    # 3. Proveedores (de ventanaejemplo/data.py)
    suppliers_data = [
        {"name": "Furukawa Electric", "contact": "carlos.mendez@furukawa.com", "rif": "J-30491823-1"},
        {"name": "TP-Link Andina", "contact": "soporte.ventas@tp-link.com", "rif": "J-31298450-4"},
        {"name": "Cisco Systems", "contact": "cuentas@cisco-latam.com", "rif": "J-29847162-8"},
        {"name": "Distribuidora Telecom S.A.", "contact": "ventas@distelecom.com.ve", "rif": "J-40192837-5"},
    ]
    sup_ids = {}
    for s in suppliers_data:
        sid = create_supplier(s["name"], s["contact"], s["rif"])
        sup_ids[s["name"]] = sid
    print(f"✓ Sembrados {len(sup_ids)} proveedores.")

    # 4. Empleados (cargos técnicos/supervisión, cédulas venezolanas)
    employees_data = [
        {"name": "Alejandro Rivas", "cedula": "V-18452109", "cargo": "Técnico Instalador"},
        {"name": "Carlos Mendoza", "cedula": "V-19823411", "cargo": "Técnico de Fibra Óptica"},
        {"name": "Mariana Gómez", "cedula": "V-21345678", "cargo": "Supervisora de Almacén"},
        {"name": "José Luis Rondón", "cedula": "V-16789432", "cargo": "Instalador de Redes"},
    ]
    emp_ids = []
    for e in employees_data:
        eid = create_employee(e["name"], e["cedula"], e["cargo"])
        emp_ids.append(eid)
    print(f"✓ Sembrados {len(emp_ids)} empleados.")

    # 5. Vehículos
    vehicles_data = [
        {"brand": "Toyota", "model": "Hilux 4x4", "plate": "A45BC8D"},
        {"brand": "Empire Keeway", "model": "Horse 150", "plate": "AA1B23C"},
    ]
    for v in vehicles_data:
        create_vehicle(v["brand"], v["model"], v["plate"])
    print(f"✓ Sembrados {len(vehicles_data)} vehículos.")

    # 6. Productos - 5 Categorías repartidas en ambos almacenes
    # Categoría 1: Equipos de Red (modo Serie: serial + mac, unit="und")
    # Huawei HG8245H en Central (5 unidades)
    huawei_items = [
        {"name": "Router ONT Huawei HG8245H", "brand": "Huawei", "modelo": "HG8245H",
         "serial": f"HWTC{8245000+i}", "mac": f"E0-24-7F-AA-BB-{i:02X}",
         "supplier_id": sup_ids["Distribuidora Telecom S.A."], "unit": "und"}
        for i in range(1, 6)
    ]
    bulk_create_products(huawei_items, admin_id, warehouse_id=wh_central)

    # TP-Link EAP225 en Central (4 unidades)
    tplink_items = [
        {"name": "AP TP-Link EAP225", "brand": "TP-Link", "modelo": "EAP225",
         "serial": f"TPL{225000+i}", "mac": f"68-FF-7B-11-22-{i:02X}",
         "supplier_id": sup_ids["TP-Link Andina"], "unit": "und"}
        for i in range(1, 5)
    ]
    bulk_create_products(tplink_items, admin_id, warehouse_id=wh_central)

    # Cisco SG110-08 en Secundario (4 unidades)
    cisco_items = [
        {"name": "Switch Cisco SG110-08", "brand": "Cisco", "modelo": "SG110-08",
         "serial": f"CSCO{11000+i}", "mac": f"00-45-1D-33-44-{i:02X}",
         "supplier_id": sup_ids["Cisco Systems"], "unit": "und"}
        for i in range(1, 5)
    ]
    bulk_create_products(cisco_items, super_id, warehouse_id=wh_secundario)

    # Categoría 2: Herramientas (modo Serie: con serial, sin MAC)
    # Fusionadora de Fibra Fujikura en Central (2 unidades)
    fuji_items = [
        {"name": "Fusionadora de Fibra Fujikura", "brand": "Fujikura", "modelo": "70S+",
         "serial": f"FJK-70S-{100+i}", "mac": "",
         "supplier_id": sup_ids["Distribuidora Telecom S.A."], "unit": "und"}
        for i in range(1, 3)
    ]
    bulk_create_products(fuji_items, admin_id, warehouse_id=wh_central)

    # Pelacables de precisión en Secundario (3 unidades)
    pela_items = [
        {"name": "Pelacables de precisión", "brand": "Miller", "modelo": "FO 103-S",
         "serial": f"MLR-FO-{200+i}", "mac": "",
         "supplier_id": sup_ids["Distribuidora Telecom S.A."], "unit": "und"}
        for i in range(1, 4)
    ]
    bulk_create_products(pela_items, super_id, warehouse_id=wh_secundario)

    # Categoría 3: Cableado (modo Cantidad, unit="m")
    # Fibra Óptica Monomodo en Central (1500 m)
    p_fibra_c = create_product(
        name="Fibra Óptica Monomodo", barcode="BOB-FO-SM-01", brand="Furukawa",
        serial="", mac="", quantity=0, supplier_id=sup_ids["Furukawa Electric"],
        unit="m", warehouse_id=wh_central, modelo="12 Hilos"
    )
    create_movement("entrada", p_fibra_c, None, admin_id, 1500, "Ingreso de bobinas de fibra óptica monomodo", wh_central)

    # Cable UTP Cat6 en Central (2000 m)
    p_utp_c = create_product(
        name="Cable UTP Cat6", barcode="BOB-UTP-C6-01", brand="Furukawa",
        serial="", mac="", quantity=0, supplier_id=sup_ids["Furukawa Electric"],
        unit="m", warehouse_id=wh_central, modelo="Cat6 Azul Exterior"
    )
    create_movement("entrada", p_utp_c, None, admin_id, 2000, "Lote inicial bobinas UTP Cat6", wh_central)

    # Cable UTP Cat6 en Secundario (1000 m)
    p_utp_s = create_product(
        name="Cable UTP Cat6", barcode="BOB-UTP-C6-02", brand="Furukawa",
        serial="", mac="", quantity=0, supplier_id=sup_ids["Furukawa Electric"],
        unit="m", warehouse_id=wh_secundario, modelo="Cat6 Azul Exterior"
    )
    create_movement("entrada", p_utp_s, None, super_id, 1000, "Transferencia de stock a secundario", wh_secundario)

    # Categoría 4: Conectores / Pasivos (modo Cantidad, unit="caja")
    # Conector SC/APC en Central (80 cajas)
    p_sc_c = create_product(
        name="Conector SC/APC", barcode="CON-SC-APC-01", brand="Furukawa",
        serial="", mac="", quantity=0, supplier_id=sup_ids["Furukawa Electric"],
        unit="caja", warehouse_id=wh_central, modelo="Caja x 50u"
    )
    create_movement("entrada", p_sc_c, None, admin_id, 80, "Cajas de conectores mecánicos SC/APC", wh_central)

    # Conector RJ45 en Central (50 cajas)
    p_rj45_c = create_product(
        name="Conector RJ45", barcode="CON-RJ45-C6-01", brand="TP-Link",
        serial="", mac="", quantity=0, supplier_id=sup_ids["TP-Link Andina"],
        unit="caja", warehouse_id=wh_central, modelo="Cat6 Caja x 100u"
    )
    create_movement("entrada", p_rj45_c, None, admin_id, 50, "Cajas de conectores RJ45 Cat6", wh_central)

    # Conector RJ45 en Secundario (25 cajas)
    p_rj45_s = create_product(
        name="Conector RJ45", barcode="CON-RJ45-C6-02", brand="TP-Link",
        serial="", mac="", quantity=0, supplier_id=sup_ids["TP-Link Andina"],
        unit="caja", warehouse_id=wh_secundario, modelo="Cat6 Caja x 100u"
    )
    create_movement("entrada", p_rj45_s, None, super_id, 25, "Stock conectores RJ45 secundario", wh_secundario)

    # Categoría 5: Accesorios de Instalación (modo Cantidad, unit="caja")
    # Grapas para cable en Central (60 cajas)
    p_grapas = create_product(
        name="Grapas para cable", barcode="ACC-GRP-01", brand="Genérico",
        serial="", mac="", quantity=0, supplier_id=sup_ids["Distribuidora Telecom S.A."],
        unit="caja", warehouse_id=wh_central, modelo="Caja x 200u"
    )
    create_movement("entrada", p_grapas, None, admin_id, 60, "Grapas para tendido de fibra/cable", wh_central)

    # Bridas plásticas en Central (70 cajas)
    p_bridas = create_product(
        name="Bridas plásticas", barcode="ACC-BRD-01", brand="Genérico",
        serial="", mac="", quantity=0, supplier_id=sup_ids["Distribuidora Telecom S.A."],
        unit="caja", warehouse_id=wh_central, modelo="Negras 200mm Bolsa x 100u"
    )
    create_movement("entrada", p_bridas, None, admin_id, 70, "Bridas para sujeción exterior", wh_central)

    print("✓ Productos creados en las 5 categorías.")

    # 7. Salidas, Devoluciones y Asignaciones
    # Salida 1: Material e instalación a Alejandro Rivas (Central)
    mov_salida_1 = create_compound_movement(
        type_="salida",
        user_id=admin_id,
        items=[
            {"name": "Router ONT Huawei HG8245H", "brand": "Huawei", "qty": 2, "unit": "und", "kind": "serial"},
            {"name": "Cable UTP Cat6", "brand": "Furukawa", "qty": 150, "unit": "m", "kind": "quantity"},
            {"name": "Conector RJ45", "brand": "TP-Link", "qty": 4, "unit": "caja", "kind": "quantity"},
            {"name": "Grapas para cable", "brand": "Genérico", "qty": 3, "unit": "caja", "kind": "quantity"},
        ],
        notes="Despacho para instalación de 2 clientes residenciales Sector Norte",
        warehouse_id=wh_central,
        employee_id=emp_ids[0],
    )

    # Salida 2: Trabajo de fibra a Carlos Mendoza (Central)
    mov_salida_2 = create_compound_movement(
        type_="salida",
        user_id=admin_id,
        items=[
            {"name": "Fibra Óptica Monomodo", "brand": "Furukawa", "qty": 300, "unit": "m", "kind": "quantity"},
            {"name": "Conector SC/APC", "brand": "Furukawa", "qty": 8, "unit": "caja", "kind": "quantity"},
            {"name": "AP TP-Link EAP225", "brand": "TP-Link", "qty": 1, "unit": "und", "kind": "serial"},
        ],
        notes="Despacho para empalme troncal y punto corporativo",
        warehouse_id=wh_central,
        employee_id=emp_ids[1],
    )

    # Salida 3: En Almacén Secundario a José Luis Rondón
    mov_salida_3 = create_compound_movement(
        type_="salida",
        user_id=super_id,
        items=[
            {"name": "Switch Cisco SG110-08", "brand": "Cisco", "qty": 1, "unit": "und", "kind": "serial"},
            {"name": "Cable UTP Cat6", "brand": "Furukawa", "qty": 80, "unit": "m", "kind": "quantity"},
            {"name": "Conector RJ45", "brand": "TP-Link", "qty": 2, "unit": "caja", "kind": "quantity"},
        ],
        notes="Instalación en agencia sucursal",
        warehouse_id=wh_secundario,
        employee_id=emp_ids[3],
    )

    # Salida 4: Asignación de herramienta a técnico
    mov_asig_1 = create_compound_movement(
        type_="salida",
        user_id=admin_id,
        items=[
            {"name": "Pelacables de precisión", "brand": "Miller", "qty": 1, "unit": "und", "kind": "serial"},
        ],
        notes="Dotación de herramienta de campo para técnico",
        warehouse_id=wh_secundario,
        employee_id=emp_ids[1],
    )

    # Devolución 1: Alejandro Rivas devuelve cable y sobrante de grapas (por cantidad)
    mov_dev_1 = create_compound_movement(
        type_="devolucion",
        user_id=admin_id,
        items=[
            {"name": "Cable UTP Cat6", "brand": "Furukawa", "qty": 30, "unit": "m", "kind": "quantity"},
            {"name": "Grapas para cable", "brand": "Genérico", "qty": 1, "unit": "caja", "kind": "quantity"},
        ],
        notes="Sobrante de instalación devuelto a almacén",
        warehouse_id=wh_central,
        employee_id=emp_ids[0],
    )

    # Devolución 2: Devolución de un equipo serial que estuvo en salida
    # Buscar una ONT Huawei que esté en 'no disponible'
    conn = get_connection()
    try:
        row_nodisp = conn.execute(
            "SELECT id, serial FROM products WHERE name='Router ONT Huawei HG8245H' AND status='no disponible' LIMIT 1"
        ).fetchone()
    finally:
        conn.close()

    if row_nodisp:
        mov_dev_serial = create_compound_movement(
            type_="devolucion",
            user_id=admin_id,
            items=[
                {
                    "name": "Router ONT Huawei HG8245H",
                    "brand": "Huawei",
                    "kind": "serial",
                    "product_ids": [row_nodisp["id"]],
                    "qty": 1,
                    "unit": "und",
                }
            ],
            notes=f"Equipo devuelto por cliente cancelado (Serial: {row_nodisp['serial']})",
            warehouse_id=wh_central,
            employee_id=emp_ids[0],
        )
    else:
        mov_dev_serial = None

    # Asignación simple individual a Mariana Gómez
    mov_asig_simple = create_movement(
        type_="asignacion",
        product_id=p_bridas,
        employee_id=emp_ids[2],
        user_id=admin_id,
        quantity=5,
        notes="Uso interno en adecuación de racks de almacén",
        warehouse_id=wh_central,
    )

    print("✓ Movimientos compuestos de salida, asignación y devolución registrados.")

    # 8. Repartir fechas de movimientos en los últimos ~60 días
    # Obtener todos los movimientos ordenados por id ascendente
    conn = get_connection()
    try:
        movements = conn.execute("SELECT id, type FROM movements ORDER BY id ASC").fetchall()
        total_movs = len(movements)
        now = datetime.now()
        # Repartimos de hace 58 días hasta hoy
        for idx, m in enumerate(movements):
            # Progresión temporal con variaciones para simular días reales
            days_ago = max(1, int(58 - (idx * (55 / max(1, total_movs - 1)))))
            hour = 8 + (idx * 3) % 9
            minute = (idx * 17) % 60
            second = (idx * 23) % 60
            ts_date = now - timedelta(days=days_ago)
            ts_str = ts_date.strftime(f"%Y-%m-%d {hour:02d}:{minute:02d}:{second:02d}")
            conn.execute("UPDATE movements SET timestamp=? WHERE id=?", (ts_str, m["id"]))
        conn.commit()
        print(f"✓ Fechas de los {total_movs} movimientos distribuidas en el rango de ~60 días.")
    finally:
        conn.close()


def step_4_verify():
    print("\n" + "=" * 70)
    print("PASO 4: Verificación final de registros sembrados...")
    conn = get_connection()
    try:
        tables = [
            "warehouses", "users", "suppliers", "employees",
            "vehicles", "products", "movements", "movement_items"
        ]
        counts = {}
        for t in tables:
            cnt = conn.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
            counts[t] = cnt
            print(f"  - Tabla {t:<15}: {cnt:>4} registros")

        # Verificaciones clave
        assert counts["warehouses"] >= 2, "Faltan almacenes"
        assert counts["users"] >= 2, "Faltan usuarios"
        assert counts["suppliers"] >= 4, "Faltan proveedores"
        assert counts["employees"] >= 4, "Faltan empleados"
        assert counts["vehicles"] >= 2, "Faltan vehículos"
        assert counts["products"] >= 15, "Faltan productos"
        assert counts["movements"] >= 10, "Faltan movimientos"
        assert counts["movement_items"] >= 10, "Faltan movement_items"

        # Rango de fechas de movimientos
        min_ts = conn.execute("SELECT MIN(timestamp) FROM movements").fetchone()[0]
        max_ts = conn.execute("SELECT MAX(timestamp) FROM movements").fetchone()[0]
        print(f"\n  * Rango de fechas de movimientos: {min_ts}  ->  {max_ts}")

        # Resumen de productos por categoría y stock
        disp = conn.execute("SELECT COUNT(*) FROM products WHERE status='disponible'").fetchone()[0]
        no_disp = conn.execute("SELECT COUNT(*) FROM products WHERE status='no disponible'").fetchone()[0]
        print(f"  * Unidades disponibles: {disp} | No disponibles (salida): {no_disp}")

        print("\n✓ Todas las validaciones de base de datos pasaron con éxito.")
    finally:
        conn.close()
    print("=" * 70)


def main():
    step_1_backup()
    step_2_reset_schema()
    step_3_seed_data()
    step_4_verify()
    print("\n✓ ¡Proceso de limpieza y sembrado de datos de prueba finalizado con éxito!")


if __name__ == "__main__":
    main()

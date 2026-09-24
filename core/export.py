"""Generación de reportes PDF.

La dependencia `reportlab` se importa de forma perezosa (dentro de `_build_pdf`)
para que el resto de la app funcione aunque no esté instalada; en ese caso el
export muestra un error claro en vez de romper la interfaz.
"""
from datetime import datetime

from database.repository import get_movements_flat, get_products_grouped

_TIPO_LABEL = {
    "entrada": "Entrada",
    "salida": "Salida",
    "devolucion": "Devolución",
    "asignacion": "Asignación",
    "eliminacion": "Eliminación",
    "eliminacion_grupo": "Eliminación grupo",
    "modificacion": "Modificación",
}


def _build_pdf(**kwargs):
    """Importa el motor de PDF solo cuando se usa (reportlab es opcional)."""
    try:
        from core.pdf_export import build_pdf
    except ImportError as e:
        raise RuntimeError(
            "Falta la dependencia 'reportlab'. "
            "Instálala con:  pip install -r requirements.txt"
        ) from e
    return build_pdf(**kwargs)


def _fmt_ts(ts):
    if not ts:
        return "—"
    try:
        return datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S").strftime(
            "%d/%m/%Y %H:%M"
        )
    except ValueError:
        return str(ts)[:16]


def _movement_product_label(r):
    """Etiqueta de producto: lista los ítems si el movimiento es compuesto."""
    names = r.get("item_names") or []
    if len(names) > 1:
        return ", ".join(names)
    if names:
        return names[0]
    return r.get("product") or "—"


def export_movements(
    filepath,
    movements=None,
    *,
    warehouse_name="",
    filters_text="",
    generated_by="",
):
    """Genera el reporte PDF de movimientos (respeta los filtros ya aplicados).

    Un movimiento agrupado (varios productos en `movement_items`) se muestra en
    una sola fila: la cantidad como resumen por unidad (p. ej. "330 m · 100 und")
    y la columna Producto listando los productos involucrados.
    """
    if movements is None:
        movements = get_movements_flat(limit=10000)
    movements = [r if isinstance(r, dict) else dict(r) for r in movements]

    headers = [
        "ID", "Tipo", "Fecha/Hora", "Cant.", "Producto",
        "Empleado", "Registrado por", "Notas",
    ]
    widths = [26, 50, 74, 56, 163, 115, 80, 182]
    rows = [
        [
            r["id"],
            _TIPO_LABEL.get(str(r["type"]).lower(), r["type"]),
            _fmt_ts(r["timestamp"]),
            r.get("cant_display") or r["quantity"],
            _movement_product_label(r),
            r["employee"] or "—",
            r["registered_by"] or "—",
            r["notes"] or "",
        ]
        for r in movements
    ]

    subtitle = [f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"]
    if generated_by:
        subtitle[0] += f"   ·   Usuario: {generated_by}"
    if warehouse_name:
        subtitle.append(f"Almacén: {warehouse_name}")
    subtitle.append(f"Filtros: {filters_text}" if filters_text else "Filtros: ninguno")

    _build_pdf(
        filepath=filepath,
        title="Reporte de Movimientos",
        subtitle=subtitle,
        headers=headers,
        col_widths=widths,
        rows=rows,
        total_label=f"Total: {len(rows)} movimiento(s).",
        landscape_mode=True,
    )


def export_inventory(filepath, products=None, *, warehouse_name=""):
    """Genera el reporte PDF del inventario agrupado por modelo/marca.

    Una fila por (nombre, marca): cantidad de unidades y stock (disponible si el
    modelo se controla por serial, total en caso contrario), igual que la vista.
    """
    if products is None:
        products = get_products_grouped()

    headers = ["Modelo / Equipo", "Marca", "Unidades", "Stock", "Proveedor"]
    widths = [150, 90, 65, 90, 132]
    rows = []
    for raw in products:
        g = raw if isinstance(raw, dict) else dict(raw)
        unit = g.get("unit") or "und"
        has_serial = bool(g.get("has_serial", 0))
        stock = (
            g.get("disponible_count", 0)
            if unit == "und" and has_serial
            else (g.get("total_quantity") or 0)
        )
        rows.append([
            g["name"],
            g.get("brand") or "—",
            f"{g.get('unit_count', 0)} {unit}",
            f"{stock} {unit}",
            g.get("supplier_name") or "—",
        ])

    subtitle = [f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}"]
    if warehouse_name:
        subtitle.append(f"Almacén: {warehouse_name}")
    subtitle.append(f"Modelos: {len(rows)}")

    _build_pdf(
        filepath=filepath,
        title="Reporte de Inventario",
        subtitle=subtitle,
        headers=headers,
        col_widths=widths,
        rows=rows,
        total_label=f"Total: {len(rows)} modelo(s).",
    )

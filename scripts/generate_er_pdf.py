"""Genera el modelo entidad-relación de la base de datos en PDF.

Introspecciona el esquema real de SQLite (tablas, columnas, PK/FK/UNIQUE) y
dibuja un diagrama ER en A3 horizontal más una página de diccionario de datos.

Uso:
    python scripts/generate_er_pdf.py [salida.pdf]

Por defecto escribe docs/modelo_entidad_relacion.pdf
"""
import os
import sqlite3
import sys
from datetime import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from reportlab.lib.colors import HexColor, white  # noqa: E402
from reportlab.lib.pagesizes import A3, landscape  # noqa: E402
from reportlab.pdfgen import canvas  # noqa: E402

from database.connection import DB_PATH  # noqa: E402

NAVY = HexColor("#1F3A5F")
INK = HexColor("#1B2433")
MUTED = HexColor("#5B6B82")
LINE = HexColor("#B9C5D6")
SOFT = HexColor("#F3F6FA")
PK_C = HexColor("#A67C00")
FK_C = HexColor("#2E6DB4")
UQ_C = HexColor("#7A4FA0")
DANGER = HexColor("#B23A2E")

HEADER_H = 20
ROW_H = 13
BOX_PAD = 4
FONT = "Helvetica"
FONT_B = "Helvetica-Bold"
FONT_M = "Courier"

# Posiciones del diagrama (A3 horizontal: 1191 x 842)
LAYOUT = {
    "warehouses": (36, 700, 250),
    "suppliers": (36, 560, 250),
    "employees": (36, 430, 250),
    "users": (36, 300, 250),
    "vehicles": (36, 170, 250),
    "products": (380, 480, 300),
    "movements": (380, 150, 300),
    "movement_items": (780, 340, 300),
    "app_meta": (780, 190, 300),
}


def read_schema(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        names = [
            r["name"]
            for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        schema = {}
        for name in names:
            cols = conn.execute(f'PRAGMA table_info("{name}")').fetchall()
            fks = conn.execute(f'PRAGMA foreign_key_list("{name}")').fetchall()
            fk_by_col = {fk["from"]: fk for fk in fks}
            uniques = set()
            for idx in conn.execute(f'PRAGMA index_list("{name}")').fetchall():
                if not idx["unique"]:
                    continue
                info = conn.execute(
                    f'PRAGMA index_info("{idx["name"]}")'
                ).fetchall()
                if len(info) == 1:
                    uniques.add(info[0]["name"])
            columns = []
            for col in cols:
                columns.append(
                    {
                        "name": col["name"],
                        "type": (col["type"] or "").upper(),
                        "pk": bool(col["pk"]),
                        "notnull": bool(col["notnull"]),
                        "default": col["dflt_value"],
                        "unique": col["name"] in uniques,
                        "fk": fk_by_col.get(col["name"]),
                    }
                )
            schema[name] = columns
        return names, schema
    finally:
        conn.close()


def col_index(columns, name):
    for i, col in enumerate(columns):
        if col["name"] == name:
            return i
    return 0


def constraint_text(col):
    if col["fk"]:
        return f"FK → {col['fk']['table']}", FK_C
    if col["unique"]:
        return "UNIQUE", UQ_C
    if col["pk"]:
        return "PK", PK_C
    if col["notnull"]:
        return "NOT NULL", MUTED
    return "", MUTED


class Box:
    def __init__(self, name, columns, x, y, w):
        self.name = name
        self.columns = columns
        self.x = x
        self.y = y
        self.w = w
        self.h = HEADER_H + len(columns) * ROW_H + BOX_PAD

    def row_y(self, column_name):
        idx = col_index(self.columns, column_name)
        return self.y + self.h - HEADER_H - idx * ROW_H - ROW_H / 2

    @property
    def top(self):
        return self.y + self.h

    @property
    def right(self):
        return self.x + self.w

    @property
    def cx(self):
        return self.x + self.w / 2


def draw_box(c, box):
    c.setFillColor(white)
    c.setStrokeColor(HexColor("#9DAEC4"))
    c.setLineWidth(1)
    c.roundRect(box.x, box.y, box.w, box.h, 6, stroke=1, fill=1)

    c.setFillColor(NAVY)
    c.roundRect(box.x, box.top - HEADER_H, box.w, HEADER_H, 6, stroke=0, fill=1)
    c.rect(box.x, box.top - HEADER_H - 6, box.w, 6, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(FONT_B, 9.5)
    c.drawString(box.x + 9, box.top - HEADER_H + 6.5, box.name.upper())
    c.setFont(FONT, 7)
    c.drawRightString(box.right - 9, box.top - HEADER_H + 6.5,
                      f"{len(box.columns)} campos")

    for i, col in enumerate(box.columns):
        y = box.top - HEADER_H - i * ROW_H
        if i % 2 == 0:
            c.setFillColor(SOFT)
            c.rect(box.x + 1, y - ROW_H, box.w - 2, ROW_H, stroke=0, fill=1)
        base = y - ROW_H + 4

        marker = ""
        marker_color = INK
        if col["pk"]:
            marker, marker_color = "PK", PK_C
        elif col["fk"]:
            marker, marker_color = "FK", FK_C
        elif col["unique"]:
            marker, marker_color = "UQ", UQ_C

        c.setFillColor(marker_color if marker else MUTED)
        c.setFont(FONT_B if marker else FONT, 6.6)
        c.drawString(box.x + 8, base, marker or "·")

        c.setFillColor(INK)
        c.setFont(FONT_B if (col["pk"] or col["fk"]) else FONT, 7.6)
        c.drawString(box.x + 26, base, col["name"])

        c.setFillColor(MUTED)
        c.setFont(FONT_M, 6.6)
        c.drawString(box.x + 128, base, col["type"][:14])

        if col["fk"]:
            extra = f"→{col['fk']['table']}"
            c.setFillColor(FK_C)
            c.setFont(FONT, 6.4)
            c.drawRightString(box.right - 8, base, extra)
        elif col["unique"]:
            c.setFillColor(UQ_C)
            c.setFont(FONT, 6.4)
            c.drawRightString(box.right - 8, base, "único")

    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.line(box.x + 1, box.top - HEADER_H, box.right - 1, box.top - HEADER_H)


def line_path(c, points, dashed=False, color=MUTED, width=1.1):
    c.setStrokeColor(color)
    c.setLineWidth(width)
    c.setDash(4, 3) if dashed else c.setDash([], 0)
    p = c.beginPath()
    p.moveTo(*points[0])
    for pt in points[1:]:
        p.lineTo(*pt)
    c.drawPath(p)
    c.setDash([], 0)
    for x, y in (points[0], points[-1]):
        c.setFillColor(color)
        c.circle(x, y, 1.8, stroke=0, fill=1)


def connect(c, src, src_col, dst, dst_col, dashed=False, midx=None,
            label="1:N", vertical=False):
    if vertical:
        x = (src.cx + dst.cx) / 2
        y1, y2 = (src.top, dst.y) if src.y < dst.y else (src.y, dst.top)
        line_path(c, [(x, y1), (x, y2)], dashed)
        lx, ly = x + 6, (y1 + y2) / 2
    else:
        y1 = src.row_y(src_col)
        y2 = dst.row_y(dst_col)
        if src.right <= dst.x:
            x1, x2 = src.right, dst.x
        elif dst.right <= src.x:
            x1, x2 = src.x, dst.right
        else:
            x1, x2 = src.right, dst.x
        mx = midx if midx is not None else (x1 + x2) / 2
        line_path(c, [(x1, y1), (mx, y1), (mx, y2), (x2, y2)], dashed)
        lx, ly = mx + 5, (y1 + y2) / 2
    c.setFillColor(DANGER if dashed else MUTED)
    c.setFont(FONT_B, 6.8)
    c.drawString(lx, ly + 3, label)


def draw_legend(c, x, y):
    c.setFillColor(INK)
    c.setFont(FONT_B, 8.5)
    c.drawString(x, y, "LEYENDA")
    entries = [
        ("PK", "Clave primaria", PK_C),
        ("FK", "Clave foránea declarada", FK_C),
        ("UQ", "Valor único", UQ_C),
        ("—", "Relación con FK declarada", MUTED),
        ("--", "Relación lógica sin FK en SQLite", DANGER),
    ]
    yy = y - 14
    for tag, text, color in entries:
        c.setFillColor(color)
        c.setFont(FONT_B, 7)
        c.drawString(x, yy, tag)
        c.setFillColor(INK)
        c.setFont(FONT, 7)
        c.drawString(x + 34, yy, text)
        yy -= 11


def page_diagram(c, names, schema):
    c.setFillColor(NAVY)
    c.rect(0, 802, 1191, 40, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(FONT_B, 18)
    c.drawString(36, 815, "DigiCable — Modelo Entidad-Relación")
    c.setFont(FONT, 8.5)
    c.drawRightString(1155, 817,
                      "SQLite · inventory.db · " +
                      datetime.now().strftime("%d/%m/%Y %H:%M"))

    boxes = {}
    for name in names:
        x, y, w = LAYOUT.get(name, (36, 36, 250))
        boxes[name] = Box(name, schema[name], x, y, w)
    for name in names:
        draw_box(c, boxes[name])

    get = lambda n: boxes[n]
    connect(c, get("suppliers"), "id", get("products"), "supplier_id",
            midx=333, label="1:N")
    connect(c, get("warehouses"), "id", get("products"), "warehouse_id",
            midx=318, label="1:N")
    connect(c, get("warehouses"), "id", get("movements"), "warehouse_id",
            midx=300, label="1:N")
    connect(c, get("employees"), "id", get("movements"), "employee_id",
            midx=349, label="1:N")
    connect(c, get("users"), "id", get("movements"), "user_id",
            midx=364, label="1:N")
    connect(c, get("products"), "id", get("movements"), "product_id",
            dashed=True, vertical=True, label="1:N lógica")
    connect(c, get("movements"), "id", get("movement_items"), "movement_id",
            midx=730, label="1:N")
    connect(c, get("products"), "id", get("movement_items"), "product_id",
            dashed=True, midx=745, label="1:N lógica")

    c.setFillColor(MUTED)
    c.setFont(FONT, 7.2)
    c.drawString(36, 120,
                 "Nota: movements.product_id y movement_items.product_id no tienen "
                 "FK declarada en el esquema; se representan con línea discontinua.")
    c.drawString(36, 108,
                 "Borrado en cascada declarado: movement_items → movements "
                 "(ON DELETE CASCADE). products.supplier_id → suppliers "
                 "(ON DELETE SET NULL).")
    draw_legend(c, 980, 150)
    c.setFillColor(MUTED)
    c.setFont(FONT, 6.8)
    c.drawCentredString(595, 18, "Página 1 de 2 · Diagrama entidad-relación")


def constraint_label(col):
    parts = []
    if col["pk"]:
        parts.append("PK")
    if col["unique"]:
        parts.append("UNIQUE")
    if col["notnull"]:
        parts.append("NOT NULL")
    if col["default"] is not None:
        parts.append(f"DEFAULT {col['default']}")
    if col["fk"]:
        fk = col["fk"]
        extra = f"FK → {fk['table']}.{fk['to']}"
        if fk["on_delete"] and fk["on_delete"] != "NO ACTION":
            extra += f" ON DELETE {fk['on_delete']}"
        parts.append(extra)
    return " · ".join(parts)


def page_dictionary(c, names, schema):
    c.setFillColor(NAVY)
    c.rect(0, 802, 1191, 40, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont(FONT_B, 18)
    c.drawString(36, 815, "DigiCable — Diccionario de datos")
    c.setFont(FONT, 8.5)
    c.drawRightString(1155, 817, f"{len(names)} tablas · SQLite")

    left = ["warehouses", "users", "suppliers", "employees", "vehicles"]
    right = ["products", "movements", "movement_items", "app_meta"]
    left = [n for n in left if n in schema]
    right = [n for n in right if n in schema]

    def draw_block(name, x, y, w):
        cols = schema[name]
        h = 20 + len(cols) * 12.5 + 6
        c.setFillColor(white)
        c.setStrokeColor(HexColor("#9DAEC4"))
        c.setLineWidth(0.8)
        c.roundRect(x, y - h, w, h, 5, stroke=1, fill=1)
        c.setFillColor(NAVY)
        c.roundRect(x, y - 18, w, 18, 5, stroke=0, fill=1)
        c.rect(x, y - 24, w, 6, stroke=0, fill=1)
        c.setFillColor(white)
        c.setFont(FONT_B, 8.8)
        c.drawString(x + 8, y - 13, name.upper())
        yy = y - 30
        for col in cols:
            c.setFillColor(INK)
            c.setFont(FONT_B, 7.4)
            c.drawString(x + 8, yy, col["name"])
            c.setFillColor(MUTED)
            c.setFont(FONT_M, 6.8)
            c.drawString(x + 130, yy, col["type"][:18])
            c.setFillColor(FK_C if col["fk"] else MUTED)
            c.setFont(FONT, 6.4)
            c.drawString(x + 230, yy, constraint_label(col)[:70])
            yy -= 12.5
        return h

    y = 780
    for name in left:
        y -= draw_block(name, 36, y, 550) + 10
    y = 780
    for name in right:
        y -= draw_block(name, 605, y, 550) + 10

    c.setFillColor(MUTED)
    c.setFont(FONT, 6.8)
    c.drawCentredString(595, 18, "Página 2 de 2 · Diccionario de datos")


def build(db_path, out_path):
    names, schema = read_schema(db_path)
    c = canvas.Canvas(out_path, pagesize=landscape(A3))
    c.setTitle("DigiCable — Modelo Entidad-Relación")
    c.setAuthor("DigiCable")
    page_diagram(c, names, schema)
    c.showPage()
    page_dictionary(c, names, schema)
    c.showPage()
    c.save()
    return names


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        ROOT, "docs", "modelo_entidad_relacion.pdf"
    )
    os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
    tables = build(DB_PATH, out)
    print(f"PDF generado: {out}")
    print(f"Tablas: {', '.join(tables)}")

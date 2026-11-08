"""Genera el PDF de Historias de Usuario a partir del Markdown del proyecto.

Uso:
    python scripts/generate_user_stories_pdf.py [salida.pdf]

Por defecto escribe docs/HISTORIAS_DE_USUARIO.pdf y deja una copia en el
Escritorio con el nombre "Historias de Usuario - DigiCable.pdf".
"""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sys
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    HRFlowable,
    LongTable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(ROOT, "docs", "HISTORIAS_DE_USUARIO.md")
DEFAULT_OUT = os.path.join(ROOT, "docs", "HISTORIAS_DE_USUARIO.pdf")
DESKTOP = os.path.join(
    os.path.expanduser("~"), "Desktop", "Historias de Usuario - DigiCable.pdf"
)

# ── Paleta ──────────────────────────────────────────────────────────────────
NAVY = HexColor("#123B5D")
NAVY_DARK = HexColor("#0B2A4A")
ORANGE = HexColor("#E67E22")
INK = HexColor("#1F2937")
MUTED = HexColor("#5B6B82")
LIGHT = HexColor("#E8EEF5")
SOFT = HexColor("#F6F8FB")
GRID = HexColor("#D5DEE8")
GREEN = HexColor("#1A7F37")
RED = HexColor("#B42318")

PAGE_W, PAGE_H = A4
MARGIN_X = 56.7
CONTENT_W = PAGE_W - 2 * MARGIN_X  # ≈ 481.9 pt

# ── Fuentes ─────────────────────────────────────────────────────────────────
FONT = "SegoeUI"
FONT_B = "SegoeUI-Bold"
FONT_I = "SegoeUI-Italic"
FONT_BI = "SegoeUI-BoldItalic"


def register_fonts() -> None:
    """Registra Segoe UI; si no existe, cae a Helvetica."""
    global FONT, FONT_B, FONT_I, FONT_BI
    base = os.path.join(os.environ.get("WINDIR", r"C:\Windows"), "Fonts")
    files = {
        "SegoeUI": "segoeui.ttf",
        "SegoeUI-Bold": "segoeuib.ttf",
        "SegoeUI-Italic": "segoeuii.ttf",
        "SegoeUI-BoldItalic": "segoeuiz.ttf",
    }
    if all(os.path.exists(os.path.join(base, fn)) for fn in files.values()):
        for name, fn in files.items():
            pdfmetrics.registerFont(TTFont(name, os.path.join(base, fn)))
        pdfmetrics.registerFontFamily(
            "SegoeUI",
            normal="SegoeUI",
            bold="SegoeUI-Bold",
            italic="SegoeUI-Italic",
            boldItalic="SegoeUI-BoldItalic",
        )
    else:
        FONT, FONT_B, FONT_I, FONT_BI = (
            "Helvetica",
            "Helvetica-Bold",
            "Helvetica-Oblique",
            "Helvetica-BoldOblique",
        )


register_fonts()

# ── Estilos ─────────────────────────────────────────────────────────────────
BODY = ParagraphStyle(
    "Body",
    fontName=FONT,
    fontSize=9.4,
    leading=13.4,
    textColor=INK,
    alignment=TA_JUSTIFY,
    spaceAfter=3,
)
BODY_LEFT = ParagraphStyle("BodyLeft", parent=BODY, alignment=TA_LEFT)
BULLET = ParagraphStyle(
    "Bullet",
    parent=BODY,
    leftIndent=14,
    bulletIndent=2,
    spaceAfter=2.4,
    alignment=TA_LEFT,
)
BULLET_SUB = ParagraphStyle(
    "BulletSub",
    parent=BULLET,
    leftIndent=28,
    bulletIndent=16,
)
META = ParagraphStyle(
    "Meta",
    parent=BODY,
    fontSize=8.3,
    leading=10.8,
    textColor=MUTED,
    spaceBefore=1,
    spaceAfter=9,
    alignment=TA_LEFT,
)
NOTE = ParagraphStyle(
    "Note",
    fontName=FONT_I,
    fontSize=8.2,
    leading=11,
    textColor=MUTED,
    alignment=TA_LEFT,
    spaceBefore=5,
    spaceAfter=4,
)
H1 = ParagraphStyle(
    "H1",
    fontName=FONT_B,
    fontSize=18,
    leading=22,
    textColor=NAVY_DARK,
    spaceBefore=14,
    spaceAfter=7,
    keepWithNext=1,
)
H2 = ParagraphStyle(
    "H2",
    fontName=FONT_B,
    fontSize=13,
    leading=16.5,
    textColor=NAVY,
    spaceBefore=14,
    spaceAfter=4,
    keepWithNext=1,
)
H3 = ParagraphStyle(
    "H3Story",
    fontName=FONT_B,
    fontSize=11,
    leading=14,
    textColor=NAVY_DARK,
    spaceBefore=12,
    spaceAfter=3,
    keepWithNext=1,
)
TABLE_HEAD = ParagraphStyle(
    "TableHead",
    fontName=FONT_B,
    fontSize=8.4,
    leading=10.8,
    textColor=white,
    alignment=TA_LEFT,
)
TABLE_CELL = ParagraphStyle(
    "TableCell",
    fontName=FONT,
    fontSize=8.3,
    leading=10.8,
    textColor=INK,
    alignment=TA_LEFT,
)
TOCTitle = ParagraphStyle(
    "TOCTitle",
    fontName=FONT_B,
    fontSize=18,
    leading=22,
    textColor=NAVY_DARK,
    spaceAfter=8,
)
TOC0 = ParagraphStyle(
    "TOC0",
    fontName=FONT_B,
    fontSize=10.5,
    leading=15,
    textColor=NAVY_DARK,
    leftIndent=0,
    firstLineIndent=0,
    spaceBefore=7,
)
TOC1 = ParagraphStyle(
    "TOC1",
    fontName=FONT_B,
    fontSize=9.4,
    leading=13,
    textColor=NAVY,
    leftIndent=14,
    firstLineIndent=0,
    spaceBefore=2,
)
TOC2 = ParagraphStyle(
    "TOC2",
    fontName=FONT,
    fontSize=8.7,
    leading=11.5,
    textColor=INK,
    leftIndent=30,
    firstLineIndent=0,
    spaceBefore=1,
)

# Portada
COVER_KICKER = ParagraphStyle(
    "CoverKicker",
    fontName=FONT_B,
    fontSize=8.5,
    leading=11,
    textColor=ORANGE,
    spaceAfter=4,
)
COVER_TITLE = ParagraphStyle(
    "CoverTitle",
    fontName=FONT_B,
    fontSize=17,
    leading=21,
    textColor=NAVY_DARK,
    spaceAfter=8,
)
COVER_BODY = ParagraphStyle(
    "CoverBody",
    fontName=FONT,
    fontSize=9.8,
    leading=14.5,
    textColor=INK,
    alignment=TA_JUSTIFY,
    spaceAfter=6,
)
STAT_NUM = ParagraphStyle(
    "StatNum",
    fontName=FONT_B,
    fontSize=22,
    leading=26,
    textColor=NAVY_DARK,
    alignment=TA_CENTER,
)
STAT_LBL = ParagraphStyle(
    "StatLbl",
    fontName=FONT,
    fontSize=8.2,
    leading=10.5,
    textColor=MUTED,
    alignment=TA_CENTER,
)
COVER_LABEL = ParagraphStyle(
    "CoverLabel",
    fontName=FONT_B,
    fontSize=8.5,
    leading=11.5,
    textColor=NAVY,
)
COVER_VALUE = ParagraphStyle(
    "CoverValue",
    fontName=FONT,
    fontSize=8.5,
    leading=11.5,
    textColor=INK,
)


# ── Markdown inline ─────────────────────────────────────────────────────────
def inline_md(text: str) -> str:
    """Convierte **negrita**, *cursiva*, `código` y símbolos a markup PDF."""
    parts = re.split(r"(`[^`]+`)", text)
    out: list[str] = []
    for part in parts:
        if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
            code = part[1:-1]
            out.append(
                '<font name="Courier" size="8.1" color="#1F2937">'
                + escape(code)
                + "</font>"
            )
            continue
        s = escape(part)
        s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
        s = re.sub(r"\*([^*]+)\*", r"<i>\1</i>", s)
        s = s.replace("✅", '<font color="#1A7F37"><b>Sí</b></font>')
        s = s.replace("❌", '<font color="#B42318"><b>No</b></font>')
        out.append(s)
    return "".join(out)


def col_widths_for(header: list[str]) -> list[float]:
    h = [c.strip().lower() for c in header]
    if h and h[0] == "funcionalidad":
        return [250.0, 116.0, CONTENT_W - 366.0]
    if h and h[0] == "versión":
        return [70.0, 100.0, CONTENT_W - 170.0]
    if h and h[0] == "id":
        return [45.0, 245.0, 120.0, CONTENT_W - 410.0]
    if h and h[0] == "épica" and len(header) == 2:
        return [165.0, CONTENT_W - 165.0]
    if h and h[0] == "épica" and len(header) == 3:
        return [160.0, 100.0, CONTENT_W - 260.0]
    n = max(1, len(header))
    return [CONTENT_W / n] * n


def build_table(table_lines: list[str]):
    raw_rows: list[list[str]] = []
    for line in table_lines:
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        raw_rows.append(cells)
    if len(raw_rows) < 2:
        return Spacer(1, 1)
    header = raw_rows[0]
    sep = raw_rows[1]
    body = raw_rows[2:]
    ncols = len(header)

    def norm(row: list[str]) -> list[str]:
        return (row + [""] * ncols)[:ncols]

    header = norm(header)
    body = [norm(r) for r in body]
    aligns: list[str] = []
    for cell in norm(sep):
        c = cell.strip()
        if c.startswith(":") and c.endswith(":"):
            aligns.append("CENTER")
        elif c.endswith(":"):
            aligns.append("RIGHT")
        else:
            aligns.append("LEFT")

    widths = col_widths_for(header)
    data = []
    for r_i, row in enumerate([header] + body):
        cells = []
        for c_i, cell in enumerate(row):
            style = TABLE_HEAD if r_i == 0 else TABLE_CELL
            cells.append(Paragraph(inline_md(cell), style))
        data.append(cells)

    table = LongTable(data, colWidths=widths, repeatRows=1)
    cmds = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("FONTNAME", (0, 0), (-1, 0), FONT_B),
        ("GRID", (0, 0), (-1, -1), 0.35, GRID),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
    ]
    for j, align in enumerate(aligns):
        cmds.append(("ALIGN", (j, 0), (j, -1), align))
    table.setStyle(TableStyle(cmds))
    return table


# ── Documento ───────────────────────────────────────────────────────────────
class UserStoriesDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        BaseDocTemplate.__init__(self, filename, **kwargs)
        self.toc = TableOfContents()
        self.toc.levelStyles = [TOC0, TOC1, TOC2]
        self.toc.dotsMinLevel = 0

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        level = {"H1": 0, "H2": 1, "H3Story": 2}.get(style_name)
        if level is None:
            return
        text = flowable.getPlainText()
        # Clave determinista: multiBuild repite la construcción y las claves
        # incrementales harían que el TOC nunca se estabilice.
        digest = hashlib.md5(text.encode("utf-8")).hexdigest()[:12]
        key = f"h{level}_{digest}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


def on_page(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        band_h = 185
        canvas.setFillColor(NAVY_DARK)
        canvas.rect(0, PAGE_H - band_h, PAGE_W, band_h, fill=1, stroke=0)
        canvas.setFillColor(ORANGE)
        canvas.rect(0, PAGE_H - band_h - 5, PAGE_W, 5, fill=1, stroke=0)

        canvas.setFillColor(white)
        canvas.setFont(FONT_B, 15)
        canvas.drawString(MARGIN_X, PAGE_H - 48, "DIGICABLE")
        canvas.setFont(FONT_B, 30)
        canvas.drawString(MARGIN_X, PAGE_H - 85, "Historias de Usuario")
        canvas.setFillColor(HexColor("#D7E3F0"))
        canvas.setFont(FONT, 12)
        canvas.drawString(
            MARGIN_X, PAGE_H - 108, "Sistema de Control de Inventarios"
        )
        canvas.setFont(FONT, 9)
        canvas.drawString(
            MARGIN_X,
            PAGE_H - 128,
            "Documento de requisitos · Versión 1.0 · 07/11/2026",
        )
        canvas.setStrokeColor(HexColor("#3E6285"))
        canvas.setLineWidth(0.6)
        canvas.line(MARGIN_X, PAGE_H - 143, PAGE_W - MARGIN_X, PAGE_H - 143)
    else:
        canvas.setFillColor(MUTED)
        canvas.setFont(FONT, 8)
        canvas.drawString(MARGIN_X, PAGE_H - 34, "DigiCable · Historias de Usuario")
        canvas.drawRightString(
            PAGE_W - MARGIN_X, PAGE_H - 34, "v1.0 · 07/11/2026"
        )
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_X, PAGE_H - 40, PAGE_W - MARGIN_X, PAGE_H - 40)

        canvas.setFillColor(MUTED)
        canvas.setFont(FONT, 8)
        canvas.drawString(MARGIN_X, 30, "Documento interno · DigiCable")
        canvas.drawRightString(
            PAGE_W - MARGIN_X, 30, f"Página {doc.page}"
        )
        canvas.setStrokeColor(GRID)
        canvas.setLineWidth(0.5)
        canvas.line(MARGIN_X, 42, PAGE_W - MARGIN_X, 42)
    canvas.restoreState()


def make_cover() -> list:
    stats = Table(
        [
            [
                Paragraph("51", STAT_NUM),
                Paragraph("9", STAT_NUM),
                Paragraph("9", STAT_NUM),
            ],
            [
                Paragraph("historias implementadas", STAT_LBL),
                Paragraph("épicas", STAT_LBL),
                Paragraph("propuestas de backlog", STAT_LBL),
            ],
        ],
        colWidths=[CONTENT_W / 3.0] * 3,
    )
    stats.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("BOX", (0, 0), (-1, -1), 0.5, GRID),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, white),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    meta = Table(
        [
            [
                Paragraph("Sistema", COVER_LABEL),
                Paragraph("DigiCable — Control de Inventarios", COVER_VALUE),
            ],
            [
                Paragraph("Alcance", COVER_LABEL),
                Paragraph(
                    "Aplicación de escritorio para Windows con base de datos "
                    "local SQLite",
                    COVER_VALUE,
                ),
            ],
            [
                Paragraph("Audiencia", COVER_LABEL),
                Paragraph(
                    "Administradores, supervisores y equipo de desarrollo",
                    COVER_VALUE,
                ),
            ],
            [
                Paragraph("Versión", COVER_LABEL),
                Paragraph("1.0 · 07/11/2026", COVER_VALUE),
            ],
        ],
        colWidths=[75, CONTENT_W - 75],
    )
    meta.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.35, GRID),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )

    note = Table(
        [
            [
                Paragraph(
                    "Las historias marcadas como <b>Implementado</b> reflejan "
                    "funcionalidad existente en el sistema. Las marcadas como "
                    "<b>Propuesto</b> forman parte del backlog y no deben "
                    "considerarse entregadas.",
                    NOTE,
                )
            ]
        ],
        colWidths=[CONTENT_W],
    )
    note.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    return [
        Spacer(1, 125),
        Paragraph("RESUMEN DEL DOCUMENTO", COVER_KICKER),
        Paragraph("Requisitos funcionales y criterios de aceptación", COVER_TITLE),
        Paragraph(
            "Este documento recopila las historias de usuario del sistema "
            "DigiCable, una aplicación de escritorio para el control de "
            "inventarios. Cada historia describe el rol, el objetivo, los "
            "criterios de aceptación y su estado actual.",
            COVER_BODY,
        ),
        Spacer(1, 8),
        stats,
        Spacer(1, 14),
        meta,
        Spacer(1, 14),
        note,
        PageBreak(),
    ]


def parse_markdown(text: str) -> list:
    lines = text.splitlines()
    start = next(
        (i for i, line in enumerate(lines) if line.startswith("## ")), 0
    )
    lines = lines[start:]
    flowables: list = []
    para: list[str] = []

    def flush_para() -> None:
        if not para:
            return
        txt = " ".join(x.strip() for x in para).strip()
        para.clear()
        if not txt:
            return
        if txt.startswith("**Prioridad:**"):
            flowables.append(Paragraph(inline_md(txt), META))
        elif txt.startswith("*Documento generado"):
            flowables.append(Spacer(1, 6))
            flowables.append(Paragraph(inline_md(txt), NOTE))
        else:
            flowables.append(Paragraph(inline_md(txt), BODY))

    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped:
            flush_para()
            i += 1
            continue

        if stripped.startswith("|"):
            flush_para()
            table_lines = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                table_lines.append(lines[i].strip())
                i += 1
            flowables.append(build_table(table_lines))
            flowables.append(Spacer(1, 8))
            continue

        if stripped == "---":
            flush_para()
            i += 1
            continue

        if stripped.startswith("#### "):
            flush_para()
            flowables.append(CondPageBreak(70))
            flowables.append(Paragraph(inline_md(stripped[5:].strip()), H3))
            i += 1
            continue

        if stripped.startswith("### "):
            flush_para()
            flowables.append(CondPageBreak(160))
            flowables.append(Paragraph(inline_md(stripped[4:].strip()), H2))
            flowables.append(
                HRFlowable(
                    width="100%",
                    thickness=0.7,
                    color=ORANGE,
                    spaceBefore=2,
                    spaceAfter=7,
                )
            )
            i += 1
            continue

        if stripped.startswith("## "):
            flush_para()
            flowables.append(CondPageBreak(120))
            flowables.append(Paragraph(inline_md(stripped[3:].strip()), H1))
            flowables.append(
                HRFlowable(
                    width="100%",
                    thickness=1.2,
                    color=NAVY,
                    spaceBefore=2,
                    spaceAfter=8,
                )
            )
            i += 1
            continue

        if stripped.startswith("# "):
            flush_para()
            flowables.append(CondPageBreak(120))
            flowables.append(Paragraph(inline_md(stripped[2:].strip()), H1))
            i += 1
            continue

        if stripped.startswith("- "):
            flush_para()
            indent = len(line) - len(line.lstrip())
            style = BULLET if indent < 2 else BULLET_SUB
            flowables.append(
                Paragraph(
                    inline_md(stripped[2:].strip()), style, bulletText="•"
                )
            )
            i += 1
            continue

        numbered = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if numbered:
            flush_para()
            flowables.append(
                Paragraph(
                    inline_md(numbered.group(2)),
                    BULLET,
                    bulletText=f"{numbered.group(1)}.",
                )
            )
            i += 1
            continue

        para.append(line)
        i += 1

    flush_para()
    return flowables


def build(src: str = SRC, out: str = DEFAULT_OUT) -> str:
    if not os.path.exists(src):
        raise FileNotFoundError(f"No existe el Markdown: {src}")
    with open(src, encoding="utf-8") as fh:
        text = fh.read()

    doc = UserStoriesDoc(
        out,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=70,
        bottomMargin=60,
        title="Historias de Usuario — DigiCable",
        author="DigiCable",
        subject="Documento de requisitos del sistema de inventario",
        creator="DigiCable",
    )
    frame = Frame(
        MARGIN_X,
        60,
        CONTENT_W,
        PAGE_H - 70 - 60,
        id="content",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame], onPage=on_page)])

    story: list = []
    story.extend(make_cover())
    story.append(Paragraph("Contenido", TOCTitle))
    story.append(Spacer(1, 4))
    story.append(doc.toc)
    story.append(PageBreak())
    story.extend(parse_markdown(text))

    doc.multiBuild(story)
    return out


def main() -> int:
    out = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_OUT
    out = os.path.abspath(out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    build(SRC, out)

    size = os.path.getsize(out)
    print(f"PDF generado: {out} ({size / 1024:.1f} KB)")
    if os.path.isdir(os.path.dirname(DESKTOP)):
        try:
            shutil.copy2(out, DESKTOP)
            print(f"Copia en Escritorio: {DESKTOP}")
        except OSError as exc:
            print(f"No se pudo copiar al Escritorio: {exc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

"""Genera el PDF del manual de usuario de DigiCable desde Markdown.

Uso:
    python scripts/generate_user_manual_pdf.py
    python scripts/generate_user_manual_pdf.py --source docs/GUIA_WINDOWS.md \
        --output docs/GUIA_WINDOWS.pdf --title "Guía de instalación y uso" \
        --subtitle "DigiCable Inventario" --skip-first-h1 --no-desktop

El renderizador admite un subconjunto de Markdown: encabezados (#, ##, ###),
párrafos, listas con viñetas y numeradas, tablas, bloques de código, citas y
reglas horizontales.
"""

from __future__ import annotations

import argparse
import os
import re
import shutil
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    HRFlowable,
    KeepTogether,
    LongTable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Preformatted,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SOURCE = os.path.join(ROOT, "docs", "MANUAL_DE_USUARIO.md")
DEFAULT_OUTPUT = os.path.join(ROOT, "docs", "MANUAL_DE_USUARIO.pdf")
DEFAULT_DESKTOP = os.path.join(
    os.path.expanduser("~"), "Desktop", "Manual de usuario - DigiCable.pdf"
)

# ── Paleta ──────────────────────────────────────────────────────────────────
NAVY = HexColor("#123B5D")
NAVY_DARK = HexColor("#0B2A4A")
ORANGE = HexColor("#E67E22")
ORANGE_SOFT = HexColor("#FFF4E8")
INK = HexColor("#1F2937")
MUTED = HexColor("#5B6B82")
LIGHT = HexColor("#E8EEF5")
SOFT = HexColor("#F6F8FB")
GRID = HexColor("#D5DEE8")
GREEN = HexColor("#1A7F37")
RED = HexColor("#B42318")

PAGE_W, PAGE_H = A4
MARGIN_X = 56.7
CONTENT_W = PAGE_W - 2 * MARGIN_X
TOP_MARGIN = 66
BOTTOM_MARGIN = 50

# ── Tipografía ──────────────────────────────────────────────────────────────
FONT = "SegoeUI"
FONT_B = "SegoeUI-Bold"
FONT_I = "SegoeUI-Italic"
MONO = "Courier"


def _register_fonts() -> None:
    """Registra Segoe UI si está disponible; si no, usa Helvetica."""
    global FONT, FONT_B, FONT_I
    candidates = {
        FONT: r"C:\Windows\Fonts\segoeui.ttf",
        FONT_B: r"C:\Windows\Fonts\segoeuib.ttf",
        FONT_I: r"C:\Windows\Fonts\segoeuii.ttf",
    }
    for name, path in candidates.items():
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:  # noqa: BLE001 - fallback controlado
                continue
    available = set(pdfmetrics.getRegisteredFontNames())
    if FONT not in available:
        FONT, FONT_B, FONT_I = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"
    pdfmetrics.registerFontFamily(
        FONT,
        normal=FONT,
        bold=FONT_B,
        italic=FONT_I,
        boldItalic=FONT_B,
    )


_register_fonts()

# ── Estilos ─────────────────────────────────────────────────────────────────
BODY = ParagraphStyle(
    "Body",
    fontName=FONT,
    fontSize=9.6,
    leading=13.8,
    textColor=INK,
    alignment=TA_LEFT,
    spaceAfter=7,
)
BODY_LEFT = ParagraphStyle(
    "BodyLeft",
    parent=BODY,
    alignment=TA_LEFT,
)
BULLET = ParagraphStyle(
    "Bullet",
    fontName=FONT,
    fontSize=9.4,
    leading=13.2,
    textColor=INK,
    leftIndent=14,
    bulletIndent=2,
    spaceAfter=3,
)
NUMBER = ParagraphStyle(
    "Number",
    parent=BULLET,
    leftIndent=18,
    bulletIndent=2,
)
H1 = ParagraphStyle(
    "H1",
    fontName=FONT_B,
    fontSize=19,
    leading=24,
    textColor=NAVY_DARK,
    spaceBefore=2,
    spaceAfter=4,
)
H2 = ParagraphStyle(
    "H2",
    fontName=FONT_B,
    fontSize=12.8,
    leading=16.5,
    textColor=NAVY,
    spaceBefore=13,
    spaceAfter=4,
)
H3 = ParagraphStyle(
    "H3",
    fontName=FONT_B,
    fontSize=10.6,
    leading=14,
    textColor=NAVY,
    spaceBefore=9,
    spaceAfter=3,
)
TABLE_HEADER = ParagraphStyle(
    "TableHeader",
    fontName=FONT_B,
    fontSize=8.2,
    leading=10.7,
    textColor=white,
    alignment=TA_LEFT,
)
TABLE_CELL = ParagraphStyle(
    "TableCell",
    fontName=FONT,
    fontSize=8.2,
    leading=10.7,
    textColor=INK,
    alignment=TA_LEFT,
)
TABLE_CELL_B = ParagraphStyle(
    "TableCellB",
    parent=TABLE_CELL,
    fontName=FONT_B,
)
CODE = ParagraphStyle(
    "Code",
    fontName=MONO,
    fontSize=8.2,
    leading=10.8,
    textColor=NAVY_DARK,
)
CALLOUT = ParagraphStyle(
    "Callout",
    fontName=FONT,
    fontSize=9.2,
    leading=12.8,
    textColor=INK,
    alignment=TA_LEFT,
)
CAPTION = ParagraphStyle(
    "Caption",
    fontName=FONT_I,
    fontSize=8,
    leading=10.5,
    textColor=MUTED,
    alignment=TA_LEFT,
)
TOCTitle = ParagraphStyle(
    "TOCTitle",
    fontName=FONT_B,
    fontSize=20,
    leading=24,
    textColor=NAVY_DARK,
    spaceAfter=10,
)
TOC0 = ParagraphStyle(
    "TOC0",
    fontName=FONT_B,
    fontSize=10.4,
    leading=15,
    textColor=NAVY_DARK,
    leftIndent=0,
    firstLineIndent=0,
    spaceBefore=4,
)
TOC1 = ParagraphStyle(
    "TOC1",
    fontName=FONT,
    fontSize=9.4,
    leading=12.8,
    textColor=INK,
    leftIndent=14,
    firstLineIndent=0,
)
TOC2 = ParagraphStyle(
    "TOC2",
    fontName=FONT,
    fontSize=8.8,
    leading=12,
    textColor=MUTED,
    leftIndent=28,
    firstLineIndent=0,
)


# ── Markdown en línea ───────────────────────────────────────────────────────
def md_inline(text: str) -> str:
    """Convierte **negrita**, *cursiva*, `código` y enlaces a markup de ReportLab."""
    text = escape(str(text or ""))
    parts = re.split(r"(`[^`]+`)", text)
    result = []
    for part in parts:
        if part.startswith("`") and part.endswith("`") and len(part) >= 2:
            code = part[1:-1]
            result.append(f'<font name="{MONO}">{code}</font>')
            continue
        part = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", part)
        part = re.sub(
            r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)",
            r"<i>\1</i>",
            part,
        )
        part = re.sub(
            r"\[([^\]]+)\]\(([^)]+)\)",
            r'<link href="\2">\1</link>',
            part,
        )
        result.append(part)
    return "".join(result)


# ── Parser Markdown ─────────────────────────────────────────────────────────
def _is_table_start(lines: list[str], i: int) -> bool:
    if i + 1 >= len(lines):
        return False
    if not lines[i].lstrip().startswith("|"):
        return False
    sep = lines[i + 1].strip()
    return bool(re.match(r"^\|?[\s:|-]+\|[\s:|-]*$", sep))


def _split_table_row(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [cell.strip() for cell in line.split("|")]


def _parse_blocks(text: str) -> list[tuple[str, object]]:
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    blocks: list[tuple[str, object]] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            i += 1
            continue

        if stripped.startswith("```"):
            code_lines: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            if i < len(lines):
                i += 1
            blocks.append(("code", "\n".join(code_lines)))
            continue

        heading = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if heading:
            level = min(len(heading.group(1)), 3)
            blocks.append(("heading", (level, heading.group(2).strip())))
            i += 1
            continue

        if re.match(r"^-{3,}$", stripped):
            blocks.append(("rule", None))
            i += 1
            continue

        if stripped.startswith(">"):
            quote_lines: list[str] = []
            while i < len(lines) and lines[i].strip().startswith(">"):
                quote_lines.append(lines[i].strip()[1:].strip())
                i += 1
            blocks.append(("callout", quote_lines))
            continue

        if _is_table_start(lines, i):
            header = _split_table_row(lines[i])
            i += 2
            rows: list[list[str]] = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                rows.append(_split_table_row(lines[i]))
                i += 1
            width = len(header)
            rows = [row + [""] * (width - len(row)) for row in rows]
            blocks.append(("table", [header] + rows))
            continue

        bullet = re.match(r"^\s*[-*]\s+(.*)$", line)
        if bullet:
            items: list[str] = []
            while i < len(lines):
                match = re.match(r"^\s*[-*]\s+(.*)$", lines[i])
                if match:
                    items.append(match.group(1).strip())
                    i += 1
                    continue
                if (
                    items
                    and lines[i].strip()
                    and lines[i].startswith((" ", "\t"))
                    and not lines[i].strip().startswith("```")
                    and not re.match(r"^\s*#{1,4}\s+", lines[i])
                    and not _is_table_start(lines, i)
                ):
                    items[-1] = f"{items[-1]} {lines[i].strip()}"
                    i += 1
                    continue
                break
            blocks.append(("bullets", items))
            continue

        number = re.match(r"^\s*(\d+)\.\s+(.*)$", line)
        if number:
            items: list[tuple[int, str]] = []
            while i < len(lines):
                match = re.match(r"^\s*(\d+)\.\s+(.*)$", lines[i])
                if match:
                    items.append((int(match.group(1)), match.group(2).strip()))
                    i += 1
                    continue
                if (
                    items
                    and lines[i].strip()
                    and lines[i].startswith((" ", "\t"))
                    and not lines[i].strip().startswith("```")
                    and not re.match(r"^\s*#{1,4}\s+", lines[i])
                    and not _is_table_start(lines, i)
                ):
                    number_value, text = items[-1]
                    items[-1] = (number_value, f"{text} {lines[i].strip()}")
                    i += 1
                    continue
                break
            blocks.append(("numbers", items))
            continue

        paragraph: list[str] = []
        while i < len(lines):
            current = lines[i]
            current_stripped = current.strip()
            if not current_stripped:
                break
            if current_stripped.startswith("<!--"):
                break
            if current_stripped.startswith("```"):
                break
            if re.match(r"^(#{1,4})\s+", current_stripped):
                break
            if re.match(r"^-{3,}$", current_stripped):
                break
            if current_stripped.startswith(">"):
                break
            if _is_table_start(lines, i):
                break
            if re.match(r"^\s*[-*]\s+", current):
                break
            if re.match(r"^\s*\d+\.\s+", current):
                break
            paragraph.append(current_stripped)
            i += 1
        if paragraph:
            blocks.append(("paragraph", " ".join(paragraph)))
        else:
            i += 1
    return blocks


# ── Generación de flowables ─────────────────────────────────────────────────
def _table_widths(ncols: int) -> list[float]:
    if ncols == 2:
        fractions = [0.33, 0.67]
    elif ncols == 3:
        fractions = [0.22, 0.39, 0.39]
    elif ncols == 4:
        fractions = [0.16, 0.28, 0.28, 0.28]
    else:
        fractions = [1 / ncols] * ncols
    return [CONTENT_W * f for f in fractions]


def _make_table(rows: list[list[str]]) -> LongTable:
    ncols = max(len(row) for row in rows)
    normalized = [row + [""] * (ncols - len(row)) for row in rows]
    data = []
    for r, row in enumerate(normalized):
        style = TABLE_HEADER if r == 0 else TABLE_CELL
        data.append([Paragraph(md_inline(cell), style) for cell in row])
    table = LongTable(
        data,
        colWidths=_table_widths(ncols),
        repeatRows=1,
        hAlign="LEFT",
    )
    style_commands = [
        ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ("TEXTCOLOR", (0, 0), (-1, 0), white),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.45, GRID),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
    ]
    table.setStyle(TableStyle(style_commands))
    return table


def _make_code_block(code: str) -> KeepTogether:
    paragraph = Preformatted(code, CODE)
    box = Table([[paragraph]], colWidths=[CONTENT_W])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("BOX", (0, 0), (-1, -1), 0.5, GRID),
                ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ("RIGHTPADDING", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )
    return KeepTogether([box, Spacer(1, 6)])


def _make_callout(lines: list[str]) -> Table:
    text = "<br/>".join(md_inline(line) for line in lines if line)
    paragraph = Paragraph(text, CALLOUT)
    box = Table([[paragraph]], colWidths=[CONTENT_W])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), ORANGE_SOFT),
                ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
                ("BOX", (0, 0), (-1, -1), 0.4, HexColor("#F5C99B")),
                ("LEFTPADDING", (0, 0), (-1, -1), 11),
                ("RIGHTPADDING", (0, 0), (-1, -1), 11),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return box


# ── Documento ───────────────────────────────────────────────────────────────
class ManualDoc(BaseDocTemplate):
    def __init__(self, filename: str, **kwargs):
        super().__init__(filename, **kwargs)
        self.toc = TableOfContents()
        self.toc.levelStyles = [TOC0, TOC1]
        self.toc.dotsMinLevel = 0
        self._heading_count = 0
        self._outline_started = False

    def afterFlowable(self, flowable) -> None:
        if not isinstance(flowable, Paragraph):
            return
        style_name = flowable.style.name
        if style_name not in ("H1", "H2"):
            return
        level = int(style_name[1]) - 1
        if not self._outline_started and level > 0:
            level = 0
        self._outline_started = True
        text = flowable.getPlainText()
        self._heading_count += 1
        key = f"heading-{self._heading_count}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page))


def _cover_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(NAVY)
    canvas.rect(0, PAGE_H * 0.42, PAGE_W, PAGE_H * 0.58, fill=1, stroke=0)
    canvas.setFillColor(ORANGE)
    canvas.rect(0, PAGE_H * 0.42 - 5, PAGE_W, 5, fill=1, stroke=0)

    canvas.setFillColor(white)
    canvas.setFont(FONT_B, 12)
    canvas.drawString(MARGIN_X, PAGE_H - 78, "DIGICABLE")
    canvas.setFont(FONT_B, 34)
    canvas.drawString(MARGIN_X, PAGE_H - 150, doc.cover_title)
    canvas.setFont(FONT, 16)
    canvas.drawString(MARGIN_X, PAGE_H - 184, doc.cover_subtitle)
    canvas.setFillColor(HexColor("#BBD4EA"))
    canvas.setFont(FONT, 10)
    canvas.drawString(MARGIN_X, PAGE_H - 214, doc.cover_version)

    canvas.setFillColor(NAVY_DARK)
    canvas.setFont(FONT_B, 19)
    canvas.drawString(MARGIN_X, PAGE_H * 0.31, "Contenido")
    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 11)
    canvas.drawString(
        MARGIN_X,
        PAGE_H * 0.31 - 24,
        "Guía práctica para administradores y supervisores",
    )

    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.6)
    canvas.line(MARGIN_X, PAGE_H * 0.24, PAGE_W - MARGIN_X, PAGE_H * 0.24)

    canvas.setFillColor(INK)
    canvas.setFont(FONT_B, 10)
    canvas.drawString(MARGIN_X, PAGE_H * 0.21, "En este manual")
    canvas.setFont(FONT, 9.5)
    bullets = [
        "Instalación y puesta en marcha.",
        "Uso diario: productos, movimientos y comprobantes.",
        "Reportes por período, ranking y cierre crítico.",
        "Envío por correo con Outlook y por WhatsApp.",
        "Respaldos, seguridad y solución de problemas.",
    ]
    y = PAGE_H * 0.18
    for bullet in bullets:
        canvas.setFillColor(ORANGE)
        canvas.circle(MARGIN_X + 2, y + 3, 2, fill=1, stroke=0)
        canvas.setFillColor(INK)
        canvas.drawString(MARGIN_X + 12, y, bullet)
        y -= 15

    canvas.setFillColor(MUTED)
    canvas.setFont(FONT, 8)
    canvas.drawString(MARGIN_X, 32, "DigiCable · Documento de usuario")
    canvas.drawRightString(PAGE_W - MARGIN_X, 32, "Noviembre de 2026")
    canvas.restoreState()


def _normal_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont(FONT, 8)
    canvas.setFillColor(MUTED)
    title = getattr(doc, "cover_title", "Manual de usuario")
    canvas.drawString(MARGIN_X, PAGE_H - 36, f"DigiCable · {title}")
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 36, "Noviembre de 2026")
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_X, PAGE_H - 42, PAGE_W - MARGIN_X, PAGE_H - 42)
    canvas.drawString(MARGIN_X, 28, "Documento de usuario")
    canvas.drawRightString(PAGE_W - MARGIN_X, 28, f"Página {doc.page}")
    canvas.restoreState()


def _story_from_blocks(
    blocks: list[tuple[str, object]],
    *,
    skip_first_h1: bool = False,
) -> list:
    story: list = []
    first_h1_seen = False
    for kind, payload in blocks:
        if kind == "heading":
            level, text = payload  # type: ignore[misc]
            if level == 1:
                if skip_first_h1 and not first_h1_seen:
                    first_h1_seen = True
                    continue
                first_h1_seen = True
                if story:
                    story.append(CondPageBreak(150))
                story.append(Paragraph(md_inline(text), H1))
                story.append(
                    HRFlowable(
                        width="100%",
                        thickness=1.2,
                        color=ORANGE,
                        spaceBefore=2,
                        spaceAfter=8,
                    )
                )
            elif level == 2:
                story.append(Paragraph(md_inline(text), H2))
            else:
                story.append(Paragraph(md_inline(text), H3))
            continue
        if kind == "paragraph":
            story.append(Paragraph(md_inline(payload), BODY))  # type: ignore[arg-type]
            continue
        if kind == "bullets":
            for item in payload:  # type: ignore[union-attr]
                story.append(Paragraph(md_inline(item), BULLET, bulletText="•"))
            story.append(Spacer(1, 3))
            continue
        if kind == "numbers":
            for n, item in payload:  # type: ignore[union-attr]
                story.append(Paragraph(md_inline(item), NUMBER, bulletText=f"{n}."))
            story.append(Spacer(1, 3))
            continue
        if kind == "table":
            story.append(_make_table(payload))  # type: ignore[arg-type]
            story.append(Spacer(1, 8))
            continue
        if kind == "code":
            story.append(_make_code_block(payload))  # type: ignore[arg-type]
            continue
        if kind == "callout":
            story.append(_make_callout(payload))  # type: ignore[arg-type]
            story.append(Spacer(1, 7))
            continue
        if kind == "rule":
            story.append(
                HRFlowable(
                    width="100%",
                    thickness=0.6,
                    color=GRID,
                    spaceBefore=6,
                    spaceAfter=6,
                )
            )
    return story


def build(
    source: str,
    output: str,
    *,
    title: str = "Manual de usuario",
    subtitle: str = "Sistema de Control de Inventarios",
    version: str = "Versión 2.0 · Noviembre de 2026",
    skip_first_h1: bool = False,
) -> None:
    with open(source, encoding="utf-8") as fh:
        markdown = fh.read()
    blocks = _parse_blocks(markdown)
    story = _story_from_blocks(blocks, skip_first_h1=skip_first_h1)

    doc = ManualDoc(
        output,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=TOP_MARGIN,
        bottomMargin=BOTTOM_MARGIN,
        title=title,
        author="DigiCable",
        subject="Manual de usuario del sistema de control de inventarios",
    )
    doc.cover_title = title
    doc.cover_subtitle = subtitle
    doc.cover_version = version

    frame = Frame(
        MARGIN_X,
        BOTTOM_MARGIN,
        CONTENT_W,
        PAGE_H - TOP_MARGIN - BOTTOM_MARGIN,
        id="content",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[frame], onPage=_cover_page),
            PageTemplate(id="normal", frames=[frame], onPage=_normal_page),
        ]
    )

    full_story = [
        Spacer(1, 1),
        NextPageTemplate("normal"),
        PageBreak(),
        Paragraph("Contenido", TOCTitle),
        doc.toc,
        PageBreak(),
    ]
    full_story.extend(story)
    doc.multiBuild(full_story)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", default=DEFAULT_SOURCE)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--title", default="Manual de usuario")
    parser.add_argument("--subtitle", default="Sistema de Control de Inventarios")
    parser.add_argument("--version", default="Versión 2.0 · Noviembre de 2026")
    parser.add_argument("--skip-first-h1", action="store_true")
    parser.add_argument("--no-desktop", action="store_true")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(os.path.abspath(args.output)), exist_ok=True)
    build(
        args.source,
        args.output,
        title=args.title,
        subtitle=args.subtitle,
        version=args.version,
        skip_first_h1=args.skip_first_h1,
    )
    print(f"PDF generado: {args.output}")

    if not args.no_desktop:
        desktop = DEFAULT_DESKTOP
        try:
            shutil.copy2(args.output, desktop)
            print(f"Copia en Escritorio: {desktop}")
        except OSError as exc:
            print(f"No se pudo copiar al Escritorio: {exc}")


if __name__ == "__main__":
    main()

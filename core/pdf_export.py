"""Render de PDF con reportlab (dependencia opcional en tiempo de import).

Se importa de forma perezosa desde `core.export` para que el resto de la app
funcione aunque `reportlab` no esté instalado.
"""
import os
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdf_canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    LongTable,
    PageTemplate,
    Paragraph,
    Spacer,
    TableStyle,
)

# ── Paleta (misma que ui/colors.py, duplicada para no acoplar core -> ui) ─────
AZUL_NOCHE = colors.HexColor("#031D44")
AZUL_CERULEO = colors.HexColor("#219EBC")
NARANJA = colors.HexColor("#F58A07")
GRIS_TEXTO = colors.HexColor("#3A4A5A")
GRIS_CLARO = colors.HexColor("#EEF2F7")
GRIS_BORDE = colors.HexColor("#D8DCE3")
GRIS_SUBTITULO = colors.HexColor("#B9C7DA")

_LOGO_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "img", "logo.png"
)


class _NumberedCanvas(pdf_canvas.Canvas):
    """Canvas que numera las páginas al final, cuando ya se conoce el total."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_states = []

    def showPage(self):  # noqa: N802 (API de reportlab)
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_states)
        for index, state in enumerate(self._saved_states, start=1):
            self.__dict__.update(state)
            self._draw_footer(index, total)
            super().showPage()
        super().save()

    def _draw_footer(self, page_no, total):
        width = self._pagesize[0]
        self.saveState()
        self.setStrokeColor(GRIS_BORDE)
        self.setLineWidth(0.5)
        self.line(12 * mm, 12 * mm, width - 12 * mm, 12 * mm)
        self.setFont("Helvetica", 8)
        self.setFillColor(GRIS_TEXTO)
        self.drawString(12 * mm, 8 * mm, "DigiCable · Sistema de Control de Inventarios")
        self.drawRightString(width - 12 * mm, 8 * mm, f"Página {page_no} de {total}")
        self.restoreState()


def _draw_header(canvas, doc, title, subtitle):
    width, height = doc.pagesize
    band_h = 18 * mm
    canvas.saveState()
    canvas.setFillColor(AZUL_NOCHE)
    canvas.rect(0, height - band_h, width, band_h, stroke=0, fill=1)

    logo_w = 0
    if os.path.exists(_LOGO_PATH):
        try:
            from PIL import Image

            iw, ih = Image.open(_LOGO_PATH).size
            logo_h = 11 * mm
            logo_w = logo_h * iw / ih
            canvas.drawImage(
                _LOGO_PATH,
                12 * mm,
                height - band_h + (band_h - logo_h) / 2,
                width=logo_w,
                height=logo_h,
                mask="auto",
            )
        except Exception:
            logo_w = 0

    text_x = 12 * mm + (logo_w + 4 * mm if logo_w else 0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 13)
    canvas.drawString(text_x, height - 11.5 * mm, title)
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(GRIS_SUBTITULO)
    canvas.drawRightString(width - 12 * mm, height - 11.5 * mm, "DigiCable")

    canvas.setFont("Helvetica", 8.5)
    canvas.setFillColor(GRIS_TEXTO)
    y = height - band_h - 5 * mm
    for line in subtitle:
        canvas.drawString(12 * mm, y, line)
        y -= 4.3 * mm
    canvas.restoreState()


def build_pdf(
    filepath,
    *,
    title,
    subtitle,
    headers,
    col_widths,
    rows,
    total_label=None,
    landscape_mode=False,
):
    page_size = landscape(A4) if landscape_mode else A4
    doc = BaseDocTemplate(
        filepath,
        pagesize=page_size,
        leftMargin=12 * mm,
        rightMargin=12 * mm,
        topMargin=32 * mm,
        bottomMargin=16 * mm,
        title=title,
        author="DigiCable",
        subject=title,
    )
    frame = Frame(
        doc.leftMargin,
        doc.bottomMargin,
        doc.width,
        doc.height,
        id="main",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates([
        PageTemplate(
            id="report",
            frames=[frame],
            onPage=lambda c, d: _draw_header(c, d, title, subtitle),
        )
    ])

    head_style = ParagraphStyle(
        "head",
        fontName="Helvetica-Bold",
        fontSize=7.5,
        leading=9,
        textColor=colors.white,
        alignment=TA_CENTER,
    )
    cell_style = ParagraphStyle(
        "cell",
        fontName="Helvetica",
        fontSize=7.5,
        leading=9,
        textColor=GRIS_TEXTO,
    )

    data = [[Paragraph(escape(str(h)), head_style) for h in headers]]
    for row in rows:
        data.append([
            Paragraph(escape(str(v)), cell_style) if isinstance(v, str) else v
            for v in row
        ])

    table = LongTable(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("BACKGROUND", (0, 0), (-1, 0), AZUL_NOCHE),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 0.4, GRIS_BORDE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GRIS_CLARO]),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]
    table.setStyle(TableStyle(style))

    story = [table]
    if total_label:
        story.append(Spacer(1, 4 * mm))
        story.append(Paragraph(total_label, cell_style))

    doc.build(story, canvasmaker=_NumberedCanvas)

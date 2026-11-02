"""Escala tipográfica global: una sola constante para CTk y tkinter puro.

`ctk.set_widget_scaling` solo agranda widgets de CustomTkinter; las tablas
`ttk.Treeview` y los `tk.Label` con tamaños literales no escalan solos.
Estos tests fijan la constante y los pocos lugares que la consumen a mano.
"""
import os
import tkinter as tk

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)


def _size_from_font(spec):
    """Extrae el tamaño numérico de una especificación de fuente de ttk."""
    for token in str(spec).replace("{", "").replace("}", "").split():
        if token.isdigit():
            return int(token)
    raise AssertionError(f"sin tamaño numérico en {spec!r}")


def test_ui_scale_es_1_2():
    from ui.colors import UI_SCALE

    assert UI_SCALE == 1.2


def test_treeview_escala_alto_y_fuente():
    from tkinter import ttk

    from ui.colors import UI_SCALE
    from ui.widgets import setup_treeview_style

    root = tk.Tk()
    root.withdraw()
    try:
        setup_treeview_style()
        style = ttk.Style()
        assert int(style.lookup("Inv.Treeview", "rowheight")) == round(32 * UI_SCALE)
        assert _size_from_font(style.lookup("Inv.Treeview", "font")) == round(
            12 * UI_SCALE
        )
        assert _size_from_font(style.lookup("Inv.Treeview.Heading", "font")) == round(
            12 * UI_SCALE
        )
    finally:
        root.destroy()


def test_products_usa_la_misma_escala_para_los_labels_tkinter():
    from ui.colors import UI_SCALE
    from ui.views import products

    assert products._LABEL_SIZE == round(15 * UI_SCALE)

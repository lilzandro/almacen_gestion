"""Contrato de geometría de ventanas emergentes del módulo Productos."""
import os
import tkinter as tk

import pytest


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_editar_producto_la_ventana_entra_el_contenido_real(monkeypatch):
    import ui.views.products as products_mod

    monkeypatch.setattr(products_mod, "get_all_suppliers", lambda: [])

    root = tk.Tk()
    root.geometry("1400x900+3000+3000")
    root.update_idletasks()
    root.update()
    try:
        dlg = products_mod._ProductDialog(
            root,
            title="Editar Unidad",
            on_save=lambda: None,
            initial={
                "name": "Router ONT Huawei HG8245H modelo largo",
                "brand": "Huawei Technologies Co. Ltd.",
                "serial": "HWTC824500123456789",
            },
        )
        # Bombear el loop para que los callbacks after() de construcción del
        # contenido (ej. _build_edit_mode en after(20)) se ejecuten antes de
        # medir las dimensiones reales.
        root.after(600, root.quit)
        root.mainloop()
        root.update_idletasks()
        root.update()
        declared = dlg.geometry()
        declared_w = int(declared.split("x")[0])
        declared_h = int(declared.split("x")[1].split("+")[0])
        assert dlg.winfo_reqwidth() <= declared_w, (
            f"el contenido pide {dlg.winfo_reqwidth()}px de ancho pero la "
            f"ventana declara solo {declared_w}px"
        )
        assert dlg.winfo_reqheight() <= declared_h, (
            f"el contenido pide {dlg.winfo_reqheight()}px de alto pero la "
            f"ventana declara solo {declared_h}px"
        )
    finally:
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_group_edit_add_more_acepta_fila_sqlite(monkeypatch):
    """'Agregar más' recibía un sqlite3.Row y llamaba .get(), inexistente."""
    import sqlite3

    import ui.views.products as products_mod

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT 'AP' AS name, 'TP-Link' AS brand, 'EAP225' AS modelo, "
        "2 AS unit_count, 2 AS disponible_count, 0 AS has_serial, "
        "1 AS supplier_id, 'TP-Link Andina' AS supplier_name, "
        "'und' AS unit, 2 AS total_quantity"
    ).fetchone()

    capturado = {}

    class _FakeRegistrar:
        def __init__(self, parent, on_save=None, products_view=None,
                     prefill=None):
            capturado["prefill"] = prefill

    monkeypatch.setattr(products_mod, "_RegistrarProductoDialog", _FakeRegistrar)
    monkeypatch.setattr(products_mod, "get_all_suppliers", lambda: [])

    root = tk.Tk()
    root.withdraw()
    dlg = products_mod._GroupEditDialog(
        root, row, on_save=lambda *a: None, on_add_more=lambda *a: None
    )
    try:
        dlg._open_add_more()
        assert capturado["prefill"]["name"] == "AP"
        assert capturado["prefill"]["modelo"] == "EAP225"
    finally:
        dlg.destroy()
        root.destroy()

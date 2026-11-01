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

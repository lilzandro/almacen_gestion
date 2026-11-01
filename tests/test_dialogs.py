"""Regresión de los diálogos compartidos de notificación (`ui/widgets.py`).

Bug reportado: en algunas confirmaciones los botones "Sí, continuar"/
"Cancelar" no se veían completos. La causa era el frame de botones de
`ConfirmDialog`, creado con `pack_propagate(False)` y el alto por defecto de
`CTkFrame` (200 px): pedía más alto del que la ventana —fija, con
`resizable(False, False)`— puede mostrar, así que Tk recortaba el frame.
"""
import os
import tkinter as tk

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)


@pytest.fixture()
def root():
    r = tk.Tk()
    r.withdraw()
    yield r
    r.destroy()


def _confirm(root, message):
    from ui.widgets import ConfirmDialog

    dlg = ConfirmDialog(root, "Eliminar", message)
    dlg.update_idletasks()
    dlg.update()
    return dlg


@pytest.mark.parametrize(
    "message",
    [
        "¿Eliminar el proveedor X?",
        "¿Eliminar definitivamente la unidad 'Router ONT Huawei HG8245H con "
        "un nombre bastante largo' (ID 123)? Esta acción no se puede deshacer.",
    ],
)
def test_confirm_dialog_no_recorta_su_contenido(root, message):
    dlg = _confirm(root, message)
    try:
        # Si el alto pedido por el contenido supera el alto fijo de la
        # ventana, algo queda recortado (antes: el frame de botones).
        assert dlg.winfo_reqheight() <= dlg.winfo_height()
    finally:
        dlg.destroy()


def test_movement_info_error_usa_padre_persistente(root, db, monkeypatch):
    """Si el detalle no carga, el aviso no puede morir con el diálogo.

    `_MovementInfoDialog` se autodestruye tras avisar el error; si la
    notificación lo usa como padre, Tk la destruye junto con él y el usuario
    nunca alcanza a verla (misma clase de bug que los botones invisibles).
    """
    from ui.views import movements as movements_view

    llamadas = []

    class _FakeMessageDialog:
        def __init__(self, master, *args, **kwargs):
            llamadas.append(master)

    monkeypatch.setattr(movements_view, "MessageDialog", _FakeMessageDialog)

    dlg = movements_view._MovementInfoDialog(root, movement_id=999999)
    try:
        assert len(llamadas) == 1
        assert llamadas[0] is root, "el aviso debe colgar de la vista persistente"
        assert not dlg.winfo_exists(), "el diálogo de detalle debe cerrarse"
    finally:
        if dlg.winfo_exists():
            dlg.destroy()


def test_confirm_dialog_muestra_sus_dos_botones_completos(root):
    import customtkinter as ctk

    dlg = _confirm(root, "¿Eliminar el proveedor X?")
    try:
        botones = [
            boton
            for frame in dlg.winfo_children()
            for boton in frame.winfo_children()
            if isinstance(boton, ctk.CTkButton)
        ]
        assert len(botones) == 2

        alto_ventana = dlg.winfo_height()
        for boton in botones:
            # Posición absoluta del borde inferior del botón dentro del diálogo.
            borde_inferior = (
                boton.winfo_rooty() - dlg.winfo_rooty() + boton.winfo_height()
            )
            assert borde_inferior <= alto_ventana, (
                f"El botón {boton.cget('text')!r} queda fuera de la ventana"
            )
    finally:
        dlg.destroy()

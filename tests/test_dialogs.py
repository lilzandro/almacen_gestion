"""Regresión y contrato visual de los diálogos compartidos (`ui/widgets.py`).

Cubre dos cosas:
- El bug de botones recortados en `ConfirmDialog` (frame de botones con
  `pack_propagate(False)` y alto por defecto de 200 px en una ventana fija).
- El rediseño de notificaciones: franja de color, pill de estado, texto
  alineado a la izquierda, botones a la derecha y estados Aviso/Error
  distinguibles por color.
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


def _walk(widget):
    for child in widget.winfo_children():
        yield child
        yield from _walk(child)


def _confirm(root, message, **kwargs):
    from ui.widgets import ConfirmDialog

    dlg = ConfirmDialog(root, "Eliminar", message, **kwargs)
    dlg.update_idletasks()
    dlg.update()
    return dlg


def _message(root, title, message, **kwargs):
    from ui.widgets import MessageDialog

    dlg = MessageDialog(root, title, message, **kwargs)
    dlg.update_idletasks()
    dlg.update()
    return dlg


def _franja(dlg):
    """Franja de color: CTkFrame de 8 px empaquetado al borde izquierdo."""
    import customtkinter as ctk

    for child in dlg.winfo_children():
        if isinstance(child, ctk.CTkFrame) and child.cget("width") == 8:
            return child
    return None


def _botones(dlg):
    import customtkinter as ctk

    return [w for w in _walk(dlg) if isinstance(w, ctk.CTkButton)]


def _textos(dlg):
    import customtkinter as ctk

    return [w.cget("text") for w in _walk(dlg) if isinstance(w, ctk.CTkLabel)]


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
        # ventana, algo queda recortado.
        assert dlg.winfo_reqheight() <= dlg.winfo_height()
    finally:
        dlg.destroy()


def test_confirm_dialog_muestra_sus_dos_botones_completos(root):
    dlg = _confirm(root, "¿Eliminar el proveedor X?")
    try:
        botones = _botones(dlg)
        assert len(botones) == 2

        alto_ventana = dlg.winfo_height()
        for boton in botones:
            borde_inferior = (
                boton.winfo_rooty() - dlg.winfo_rooty() + boton.winfo_height()
            )
            assert borde_inferior <= alto_ventana, (
                f"El botón {boton.cget('text')!r} queda fuera de la ventana"
            )
    finally:
        dlg.destroy()


def test_confirm_dialog_usa_franja_y_textos_personalizados(root):
    from ui.colors import NARANJA_INTENSO

    dlg = _confirm(
        root,
        "¿Eliminar el proveedor X?",
        is_danger=True,
        confirm_text="Eliminar",
        cancel_text="Volver",
    )
    try:
        franja = _franja(dlg)
        assert franja is not None
        assert franja.cget("fg_color") == NARANJA_INTENSO
        assert {b.cget("text") for b in _botones(dlg)} == {"Eliminar", "Volver"}
    finally:
        dlg.destroy()


def test_message_dialog_exito_usa_azul_y_pill(root):
    from ui.colors import AZUL_CERULEO

    dlg = _message(root, "Registro guardado", "El producto se guardó.")
    try:
        assert _franja(dlg).cget("fg_color") == AZUL_CERULEO
        textos = _textos(dlg)
        assert "Éxito" in textos
        assert "Registro guardado" in textos
    finally:
        dlg.destroy()


def test_message_dialog_aviso_es_amarillo_sin_tocar_la_llamada(root):
    from ui.colors import AMARILLO_AMBAR

    dlg = _message(root, "Aviso", "Selecciona un empleado.")
    try:
        assert _franja(dlg).cget("fg_color") == AMARILLO_AMBAR
        assert "Aviso" in _textos(dlg)
    finally:
        dlg.destroy()


def test_message_dialog_error_es_naranja(root):
    from ui.colors import NARANJA_INTENSO

    # Título "Error" sin is_error: el estado se deduce del título para no
    # tener que corregir las decenas de llamadas existentes.
    dlg = _message(root, "Error", "No se pudo generar el PDF.")
    try:
        assert _franja(dlg).cget("fg_color") == NARANJA_INTENSO
        assert "Error" in _textos(dlg)
    finally:
        dlg.destroy()


def test_message_dialog_is_warning_explicito(root):
    from ui.colors import AMARILLO_AMBAR

    dlg = _message(root, "Fecha inválida", "Formato incorrecto.", is_warning=True)
    try:
        assert _franja(dlg).cget("fg_color") == AMARILLO_AMBAR
        assert "Aviso" in _textos(dlg)
    finally:
        dlg.destroy()


def test_message_dialog_texto_de_boton_personalizado(root):
    dlg = _message(root, "Éxito", "Listo.", button_text="Cerrar")
    try:
        assert [b.cget("text") for b in _botones(dlg)] == ["Cerrar"]
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


def test_message_dialog_mensaje_alineado_a_la_izquierda(root):
    import customtkinter as ctk

    dlg = _message(root, "Éxito", "Texto de prueba")
    try:
        msg = [
            w
            for w in _walk(dlg)
            if isinstance(w, ctk.CTkLabel) and w.cget("text") == "Texto de prueba"
        ][0]
        assert msg.cget("anchor") == "w"
        assert msg.cget("justify") == "left"
    finally:
        dlg.destroy()

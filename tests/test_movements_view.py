"""Contrato del clic en la columna de acciones y del header de Editar Movimiento."""
import os
import tkinter as tk
from types import SimpleNamespace

import pytest


def _event(x):
    return SimpleNamespace(x=x, y=5)


def _stub_view(calls, col="#8", box=(100, 0, 80, 46), row="7"):
    """Objeto mínimo con la interfaz que usa MovementsView._on_single_click."""
    from ui.views.movements import MovementsView

    class _Tree:
        def identify_row(self, y):
            return row

        def identify_column(self, x):
            return col

        def bbox(self, iid, column):
            return box

    class _View:
        COLS = MovementsView.COLS
        _tree = _Tree()
        _acc_column = MovementsView._acc_column

        def _edit_movement(self, mid):
            calls.append(("edit", mid))

        def _delete_movement(self, mid):
            calls.append(("delete", mid))

    return _View()


def test_click_en_mitad_izquierda_de_acc_edita():
    from ui.views.movements import MovementsView

    calls = []
    view = _stub_view(calls)
    # bbox: x=100, ancho=80 -> mitad izquierda hasta 140.
    assert MovementsView._on_single_click(view, _event(110)) == "break"
    assert calls == [("edit", 7)]


def test_click_en_mitad_derecha_de_acc_elimina():
    from ui.views.movements import MovementsView

    calls = []
    view = _stub_view(calls)
    assert MovementsView._on_single_click(view, _event(170)) == "break"
    assert calls == [("delete", 7)]


def test_click_fuera_de_acc_no_dispara_nada():
    from ui.views.movements import MovementsView

    calls = []
    view = _stub_view(calls, col="#5")
    assert MovementsView._on_single_click(view, _event(110)) is None
    assert calls == []


def test_click_sin_fila_no_dispara_nada():
    from ui.views.movements import MovementsView

    calls = []
    view = _stub_view(calls, row="")
    assert MovementsView._on_single_click(view, _event(110)) is None
    assert calls == []


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_acciones_de_fila_son_botones_reales_con_texto():
    import customtkinter as ctk

    from ui.views.movements import MovementsView

    root = tk.Tk()
    root.withdraw()

    class _View:
        _body = root

    _View._make_row_buttons = MovementsView._make_row_buttons
    view = _View()
    botones = MovementsView._make_row_buttons(view, "7")
    try:
        assert all(isinstance(b, ctk.CTkButton) for b in botones)
        assert [b.cget("text") for b in botones] == ["Editar", "Eliminar"]
    finally:
        for b in botones:
            b.destroy()
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_edit_dialog_tine_el_header_segun_el_tipo(monkeypatch):
    import ui.views.movements as mv

    monkeypatch.setattr(mv, "get_all_employees", lambda: [])
    root = tk.Tk()
    root.withdraw()
    movement = {
        "id": 83,
        "type": "salida",
        "timestamp": "2026-10-21 14:30:00",
        "quantity": 3,
        "employee_id": None,
        "notes": "",
        "product": "Router ONT",
        "items": [
            {"id": 1, "name": "Router ONT", "brand": "", "qty": 3,
             "unit": "und", "seriales": ""},
        ],
    }
    dlg = mv._MovementEditDialog(root, movement, {"role": "admin"}, lambda: None)
    try:
        dlg.update_idletasks()
        header = dlg.winfo_children()[0]
        assert header.cget("fg_color") == mv._MovementInfoDialog.TYPE_META[
            "salida"
        ][4]

        textos = []
        stack = [dlg]
        while stack:
            w = stack.pop()
            if type(w).__name__ == "CTkLabel":
                textos.append(str(w.cget("text")))
            stack.extend(w.winfo_children())
        assert any("#83" in t for t in textos)
        assert any("2026-10-21" in t for t in textos)
        assert any("Router ONT" in t for t in textos)
    finally:
        dlg.destroy()
        root.destroy()

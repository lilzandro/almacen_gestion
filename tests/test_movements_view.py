"""Contrato del detalle de Movimientos y del header de Editar Movimiento."""
import os
import tkinter as tk

import pytest


def _textos(dlg):
    textos = []
    stack = [dlg]
    while stack:
        w = stack.pop()
        if hasattr(w, "cget") and "text" in w.keys():
            textos.append(str(w.cget("text")))
        stack.extend(w.winfo_children())
    return textos


def _detalle_eliminacion_grupo():
    return {
        "id": 42,
        "type": "eliminacion_grupo",
        "timestamp": "2026-11-01 10:00:00",
        "quantity": 2,
        "notes": "Grupo eliminado: AP (TP-Link). 2 eliminados",
        "product": "",
        "brand": "",
        "unit": "",
        "employee": "-",
        "cargo": "",
        "registered_by": "admin",
        "warehouse": "",
        "items": [
            {"name": "AP", "brand": "TP-Link", "qty": 1, "unit": "und",
             "seriales": "AP-1"},
            {"name": "AP", "brand": "TP-Link", "qty": 1, "unit": "und",
             "seriales": "AP-2"},
        ],
    }


def test_lista_de_movimientos_ya_no_tiene_columna_de_acciones():
    from ui.views.movements import MovementsView

    assert "acc" not in MovementsView.COLS
    assert "acc" not in MovementsView.COL_ANCHOR
    assert len(MovementsView.COL_MINS) == len(MovementsView.COLS)
    assert len(MovementsView.COL_WEIGHTS) == len(MovementsView.COLS)
    assert all(text != "Acciones" for _col, text, _anchor in MovementsView.HEADERS)


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


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_detalle_de_eliminacion_de_grupo_muestra_cada_producto(monkeypatch):
    import ui.views.movements as movements_mod

    detail = {
        "id": 42,
        "type": "eliminacion_grupo",
        "timestamp": "2026-11-01 10:00:00",
        "quantity": 2,
        "notes": "Grupo eliminado: AP (TP-Link). 2 eliminados",
        "product": "",
        "brand": "",
        "unit": "",
        "employee": "-",
        "cargo": "",
        "registered_by": "admin",
        "warehouse": "",
        "items": [
            {"name": "AP", "brand": "TP-Link", "qty": 1, "unit": "und",
             "seriales": "AP-1"},
            {"name": "AP", "brand": "TP-Link", "qty": 1, "unit": "und",
             "seriales": "AP-2"},
        ],
    }
    monkeypatch.setattr(movements_mod, "get_movement_detail", lambda mid: detail)

    root = tk.Tk()
    root.withdraw()
    try:
        dlg = movements_mod._MovementInfoDialog(root, movement_id=42)
        texts = []
        stack = [dlg]
        while stack:
            w = stack.pop()
            if hasattr(w, "cget") and "text" in w.keys():
                texts.append(str(w.cget("text")))
            stack.extend(w.winfo_children())
        assert sum("AP-1" in t for t in texts) == 1
        assert sum("AP-2" in t for t in texts) == 1
    finally:
        dlg.destroy()
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_detalle_muestra_eliminar_y_ejecuta_el_callback(monkeypatch):
    import ui.views.movements as mv

    monkeypatch.setattr(
        mv, "get_movement_detail", lambda mid: _detalle_eliminacion_grupo()
    )
    root = tk.Tk()
    root.withdraw()
    llamado = []
    dlg = mv._MovementInfoDialog(
        root, 42, on_delete=lambda: llamado.append(True)
    )
    try:
        textos = _textos(dlg)
        assert sum("Eliminar" in t for t in textos) == 1
        dlg._delete()
        assert llamado == [True]
        assert not dlg.winfo_exists()
    finally:
        if dlg.winfo_exists():
            dlg.destroy()
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_detalle_sin_callback_no_muestra_eliminar(monkeypatch):
    import ui.views.movements as mv

    monkeypatch.setattr(
        mv, "get_movement_detail", lambda mid: _detalle_eliminacion_grupo()
    )
    root = tk.Tk()
    root.withdraw()
    dlg = mv._MovementInfoDialog(root, 42)
    try:
        assert not any("Eliminar" in t for t in _textos(dlg))
    finally:
        dlg.destroy()
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_editar_movimiento_la_ventana_entra_el_contenido_real(monkeypatch):
    import ui.views.movements as movements_mod

    movement = {
        "id": 99, "type": "salida", "timestamp": "2026-11-01 10:00:00",
        "product": "", "employee_id": None, "notes": "",
        "items": [
            {"id": 1, "name": "Router", "brand": "TPLink", "qty": 1,
             "unit": "und", "seriales": ""},
        ],
    }
    monkeypatch.setattr(movements_mod, "get_all_employees", lambda: [])

    root = tk.Tk()
    root.geometry("1400x900+3000+3000")
    root.update_idletasks()
    root.update()
    try:
        dlg = movements_mod._MovementEditDialog(
            root, movement=movement,
            current_user={"id": 1, "role": "admin"}, on_save=lambda: None,
        )
        root.update_idletasks()
        root.update()
        declared_h = int(dlg.geometry().split("x")[1].split("+")[0])
        assert dlg.winfo_reqheight() <= declared_h, (
            f"el contenido pide {dlg.winfo_reqheight()}px pero la ventana "
            f"declara solo {declared_h}px de alto"
        )
    finally:
        root.destroy()


def test_on_tree_select_resalta_todas_las_filas_seleccionadas():
    from ui.views.movements import MovementsView

    tagged = {}

    class _Tree:
        def get_children(self):
            return ["1", "2", "3"]

        def exists(self, iid):
            return True

        def selection(self):
            return ("1", "3")  # selección múltiple

        def item(self, iid, tags=None):
            tagged[iid] = tags[0]

    class _View:
        _tree = _Tree()
        _row_tag_for_index = MovementsView._row_tag_for_index

    MovementsView._on_tree_select(_View())
    assert tagged["1"] == "sel"
    assert tagged["3"] == "sel"
    assert tagged["2"] != "sel"

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


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_reportes_arranca_con_el_filtro_de_tipo_activo_en_la_lista():
    from ui.views.movements import _ReportsDialog

    class _View:
        _tipo = "salida"
        current_user = {"username": "admin"}

        def _warehouse_id(self):
            return None

        def _warehouse_name(self):
            return ""

    root = tk.Tk()
    try:
        dlg = _ReportsDialog(root, _View())
        assert dlg._tipo_filtro.get() == "salida"
    finally:
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_reporte_por_periodo_pasa_el_tipo_filtrado(monkeypatch):
    from datetime import date

    import ui.views.movements as mv

    capturado = {}
    monkeypatch.setattr(
        mv, "get_movements_flat",
        lambda **kw: capturado.update(consulta=kw) or [],
    )
    monkeypatch.setattr(
        mv, "export_movements",
        lambda *a, **k: capturado.update(export=k),
    )

    class _View:
        _tipo = None
        current_user = {"username": "admin"}

        def _warehouse_id(self):
            return None

        def _warehouse_name(self):
            return ""

    root = tk.Tk()
    try:
        dlg = mv._ReportsDialog(root, _View())
        dlg._tipo_filtro.set("salida")
        dlg._build_pdf(
            "Diario", "/tmp/x.pdf", date(2026, 11, 1), date(2026, 11, 1),
            "2026-11-01", "2026-11-01", None, "", "admin",
        )
        assert capturado["consulta"]["movement_types"] == ["salida"]
        assert "Tipo: Salida" in capturado["export"]["filters_text"]

        dlg._tipo_filtro.set("todos")
        dlg._build_pdf(
            "Diario", "/tmp/x.pdf", date(2026, 11, 1), date(2026, 11, 1),
            "2026-11-01", "2026-11-01", None, "", "admin",
        )
        assert capturado["consulta"]["movement_types"] is None
        assert "Tipo:" not in capturado["export"]["filters_text"]
    finally:
        dlg.destroy()
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_reporte_de_seleccion_sin_filas_seleccionadas_avisa_y_no_genera(monkeypatch):
    import ui.views.movements as mv

    class _Tree:
        def selection(self):
            return ()

    class _View:
        _tree = _Tree()
        current_user = {"username": "admin"}

        def _warehouse_id(self):
            return None

        def _warehouse_name(self):
            return ""

    root = tk.Tk()
    root.withdraw()
    avisos = []
    monkeypatch.setattr(
        "ui.views.movements.MessageDialog",
        lambda *a, **k: avisos.append(a),
    )
    # Evita que se abra un diálogo de archivo real si el flujo no corta antes.
    monkeypatch.setattr(mv.filedialog, "asksaveasfilename", lambda **k: "")
    try:
        dlg = mv._ReportsDialog(root, _View())
        dlg._kind.set("Selección actual")
        dlg._on_type_changed("Selección actual")
        dlg._generate()
        assert avisos
    finally:
        dlg.destroy()
        root.destroy()


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_reporte_de_seleccion_genera_pdf_con_los_ids(monkeypatch):
    import ui.views.movements as mv

    captured = {}

    class _Tree:
        def selection(self):
            return ("25", "24")

    class _View:
        _tree = _Tree()
        current_user = {"username": "admin"}

        def _warehouse_id(self):
            return None

        def _warehouse_name(self):
            return "Principal"

    root = tk.Tk()
    root.withdraw()
    monkeypatch.setattr(
        mv, "get_movements_flat",
        lambda **kw: captured.update(consulta=kw) or [],
    )
    monkeypatch.setattr(
        mv, "export_movements",
        lambda *a, **k: captured.update(export=k),
    )
    monkeypatch.setattr(
        mv.filedialog, "asksaveasfilename", lambda **k: "/tmp/sel.pdf"
    )
    monkeypatch.setattr(mv, "MessageDialog", lambda *a, **k: None)
    try:
        dlg = mv._ReportsDialog(root, _View())
        dlg._kind.set("Selección actual")
        dlg._on_type_changed("Selección actual")
        assert dlg._dates_frame.winfo_manager() == ""
        assert dlg._tipo_frame.winfo_manager() == ""
        assert "2 movimiento(s)" in dlg._status.cget("text")
        dlg._generate()
        assert captured["consulta"]["ids"] == [25, 24]
        assert "Selección manual: 2" in captured["export"]["filters_text"]
    finally:
        dlg.destroy()
        root.destroy()


def test_clic_derecho_ya_no_dispara_menu_contextual():
    """Tras quitar _ctx_menu, la clase no debe tener rastros del mecanismo viejo."""
    from ui.views.movements import MovementsView

    assert not hasattr(MovementsView, "_on_right_click")
    assert not hasattr(MovementsView, "_edit_ctx")
    assert not hasattr(MovementsView, "_delete_ctx")


def test_on_tree_select_resalta_sin_importar_el_orden_de_clic():
    """Ctrl+clic en la fila 5 y luego en la 2 (orden 'hacia atrás') debe
    resaltar ambas igual que si se hubiera hecho en orden ascendente —
    _on_tree_select no debe depender del orden de selection()."""
    from ui.views.movements import MovementsView

    tagged = {}

    class _Tree:
        def get_children(self):
            return ["1", "2", "3", "4", "5"]

        def exists(self, iid):
            return True

        def selection(self):
            # Tkinter puede devolver la selección en cualquier orden interno;
            # aquí se simula deliberadamente "5 antes que 2" para probar que
            # el método no asume orden ascendente.
            return ("5", "2")

        def item(self, iid, tags=None):
            tagged[iid] = tags[0]

    class _View:
        _tree = _Tree()
        _row_tag_for_index = MovementsView._row_tag_for_index

    MovementsView._on_tree_select(_View())
    assert tagged["2"] == "sel"
    assert tagged["5"] == "sel"
    assert tagged["1"] != "sel"
    assert tagged["3"] != "sel"
    assert tagged["4"] != "sel"


def test_on_tree_select_deselecciona_fila_que_sale_de_selection():
    """Si una fila deja de estar en selection() (el usuario la deselecciona
    con otro Ctrl+clic), debe volver a su tag zebra normal, no quedar
    marcada 'sel' para siempre."""
    from ui.views.movements import MovementsView

    tagged = {}

    class _Tree:
        def get_children(self):
            return ["1", "2", "3"]

        def exists(self, iid):
            return True

        def selection(self):
            return ("1",)  # "2" ya no está seleccionada

        def item(self, iid, tags=None):
            tagged[iid] = tags[0]

    class _View:
        _tree = _Tree()
        _row_tag_for_index = MovementsView._row_tag_for_index

    MovementsView._on_tree_select(_View())
    assert tagged["1"] == "sel"
    assert tagged["2"] != "sel"
    assert tagged["3"] != "sel"


def test_send_incluye_whatsapp_si_el_checkbox_esta_tildado(monkeypatch):
    import core.whatsapp_report as whatsapp_report
    from ui.views import movements as movements_mod

    captured = {}
    monkeypatch.setattr(
        whatsapp_report, "send_report_whatsapp",
        lambda path, caption="": captured.setdefault("called", (path, caption)),
    )

    class _Dialog:
        _email_var = type("V", (), {"get": lambda self: False})()
        _telegram_var = type("V", (), {"get": lambda self: False})()
        _whatsapp_var = type("V", (), {"get": lambda self: True})()

    import datetime
    errors = movements_mod._ReportsDialog._send(
        _Dialog(), "x.pdf", "Reporte", datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 31),
    )
    assert errors == []
    assert captured["called"][0] == "x.pdf"


def test_send_whatsapp_error_no_bloquea_correo_ni_telegram(monkeypatch):
    import core.email_report as email_report
    import core.telegram_report as telegram_report
    import core.whatsapp_report as whatsapp_report
    from ui.views import movements as movements_mod

    calls = []
    monkeypatch.setattr(
        email_report, "send_report_email", lambda *a, **k: calls.append("email")
    )
    monkeypatch.setattr(
        telegram_report, "send_report_telegram",
        lambda *a, **k: calls.append("telegram"),
    )

    def boom(*a, **k):
        calls.append("whatsapp")
        raise RuntimeError("ventana 24h")

    monkeypatch.setattr(whatsapp_report, "send_report_whatsapp", boom)

    class _Dialog:
        _email_var = type("V", (), {"get": lambda self: True})()
        _telegram_var = type("V", (), {"get": lambda self: True})()
        _whatsapp_var = type("V", (), {"get": lambda self: True})()

    import datetime
    errors = movements_mod._ReportsDialog._send(
        _Dialog(), "x.pdf", "Reporte", datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 31),
    )
    assert calls == ["email", "telegram", "whatsapp"]
    assert errors == ["WhatsApp: ventana 24h"]


@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_checkbox_whatsapp_gateado_por_variables_de_entorno(monkeypatch):
    import ui.views.movements as mv

    class _View:
        _tipo = None
        current_user = {"username": "admin"}

        def _warehouse_id(self):
            return None

        def _warehouse_name(self):
            return ""

    def _checkbox(dlg):
        stack = [dlg]
        while stack:
            w = stack.pop()
            if (
                type(w).__name__ == "CTkCheckBox"
                and "WhatsApp" in str(w.cget("text"))
            ):
                return w
            stack.extend(w.winfo_children())
        raise AssertionError("no se encontró el checkbox de WhatsApp")

    root = tk.Tk()
    root.withdraw()
    try:
        for key in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID", "WHATSAPP_TO"):
            monkeypatch.delenv(key, raising=False)
        dlg = mv._ReportsDialog(root, _View())
        assert _checkbox(dlg).cget("state") == "disabled"
        dlg.destroy()

        monkeypatch.setenv("WHATSAPP_TOKEN", "TOKEN")
        monkeypatch.setenv("WHATSAPP_PHONE_ID", "111222333")
        monkeypatch.setenv("WHATSAPP_TO", "584121234567")
        dlg = mv._ReportsDialog(root, _View())
        assert _checkbox(dlg).cget("state") == "normal"
        dlg.destroy()
    finally:
        root.destroy()

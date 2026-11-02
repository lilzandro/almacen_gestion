"""Regresión: el diálogo de usuarios valida la contraseña sin crashear."""
import os
import tkinter as tk

import pytest

pytestmark = pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)


def test_user_dialog_valida_password_corta_sin_crashear(monkeypatch):
    import ui.views.users as users_view
    from ui.views.users import _UserDialog

    avisos = []
    monkeypatch.setattr(
        users_view, "MessageDialog", lambda *a, **k: avisos.append(a)
    )
    guardados = []
    root = tk.Tk()
    root.withdraw()
    dlg = _UserDialog(
        root, "Nuevo usuario", on_save=lambda data: guardados.append(data)
    )
    try:
        dlg.user_e.insert(0, "operador")
        dlg.pass_e.insert(0, "123")
        dlg._save()
        assert guardados == []
        assert any("al menos 8" in str(a) for a in avisos)
    finally:
        dlg.destroy()
        root.destroy()

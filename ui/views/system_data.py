import os
import textwrap
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

from core.database_backup import (
    backup_dir,
    create_backup,
    default_backup_name,
    restore_database,
)
from database import connection
from ui.colors import *
from ui.widgets import ConfirmDialog, MessageDialog


def _format_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{size} B"


def _wrap_text(text: str, width: int = 42) -> str:
    """Rompe texto largo para que los diálogos no recorten el mensaje."""
    lines = []
    for paragraph in str(text).splitlines():
        if not paragraph.strip():
            lines.append("")
            continue
        lines.extend(
            textwrap.wrap(
                paragraph,
                width=width,
                break_long_words=True,
                break_on_hyphens=False,
            )
        )
    return "\n".join(lines)


def _break_path(path: str, width: int = 44) -> str:
    """Divide una ruta larga en líneas sin partir los nombres de carpeta."""
    parts = str(path).split(os.sep)
    if len(parts) == 1:
        return _wrap_text(path, width)
    lines = []
    current = parts[0]
    for part in parts[1:]:
        candidate = current + os.sep + part
        if len(candidate) > width and current:
            lines.append(current + os.sep)
            current = part
        else:
            current = candidate
    if current:
        lines.append(current)
    return "\n".join(lines)


class SystemDataView(ctk.CTkFrame):
    """Respaldo y restauración de la base de datos (solo administrador)."""

    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)
        self.current_user = current_user
        self.app = app
        self._is_admin = str(current_user.get("role", "")).lower() == "admin"
        self._busy = False
        self._backup_btn = None
        self._restore_btn = None
        self._status_lbl = None
        self._db_path_lbl = None
        self._db_size_lbl = None
        self._backup_dir_lbl = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(4, weight=1)
        self._build()
        self.refresh()

    # ── Construcción ────────────────────────────────────────────────────────
    def _build(self):
        header = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            header,
            text="Datos del sistema",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(side="left")
        ctk.CTkLabel(
            header,
            text="🛡️ Solo Admin",
            text_color=HOVER_EXPORT,
            font=ctk.CTkFont(size=14),
        ).pack(side="left", padx=10)

        ctk.CTkLabel(
            self,
            text=(
                "Administra una copia de seguridad de la base de datos o "
                "restaura la información desde un respaldo anterior."
            ),
            font=ctk.CTkFont(size=14),
            text_color=GRIS_AZULADO,
            anchor="w",
            justify="left",
            wraplength=1000,
        ).grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        if not self._is_admin:
            self._build_access_denied()
            return

        cards = ctk.CTkFrame(self, fg_color="transparent")
        cards.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        cards.grid_rowconfigure(0, weight=1)
        cards.grid_columnconfigure(0, weight=1, uniform="system_cards")
        cards.grid_columnconfigure(1, weight=1, uniform="system_cards")

        self._build_backup_card(cards)
        self._build_restore_card(cards)
        self._build_info_panel()

    def _build_backup_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=BLANCO,
            corner_radius=14,
            border_width=2,
            border_color=AZUL_CIELO,
        )
        card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="💾",
            font=ctk.CTkFont(size=44),
            text_color=AZUL_CERULEO,
        ).pack(pady=(26, 6))
        ctk.CTkLabel(
            card,
            text="Respaldo de base de datos",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(padx=20)
        ctk.CTkLabel(
            card,
            text=(
                "Guarda una copia completa de la base de datos actual en el "
                "equipo. Podrás restaurarla más adelante si lo necesitas."
            ),
            font=ctk.CTkFont(size=13),
            text_color=GRIS_AZULADO,
            wraplength=360,
            justify="center",
        ).pack(padx=24, pady=(8, 18))

        self._backup_btn = ctk.CTkButton(
            card,
            text="💾  Guardar respaldo…",
            height=42,
            width=220,
            corner_radius=8,
            fg_color=AZUL_MARINO,
            hover_color=AZUL_NOCHE,
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._backup,
        )
        self._backup_btn.pack(pady=(0, 28))

    def _build_restore_card(self, parent):
        card = ctk.CTkFrame(
            parent,
            fg_color=BLANCO,
            corner_radius=14,
            border_width=2,
            border_color=AMARILLO_AMBAR,
        )
        card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=5)
        card.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            card,
            text="📥",
            font=ctk.CTkFont(size=44),
            text_color=NARANJA_INTENSO,
        ).pack(pady=(26, 6))
        ctk.CTkLabel(
            card,
            text="Carga de base de datos",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(padx=20)
        ctk.CTkLabel(
            card,
            text=(
                "Restaura la información desde un archivo de respaldo. La base "
                "actual se reemplaza por completo."
            ),
            font=ctk.CTkFont(size=13),
            text_color=GRIS_AZULADO,
            wraplength=360,
            justify="center",
        ).pack(padx=24, pady=(8, 8))
        ctk.CTkLabel(
            card,
            text="⚠ Antes de restaurar se crea un respaldo automático.",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=HOVER_NARANJA_INT,
            wraplength=360,
            justify="center",
        ).pack(padx=24, pady=(0, 14))

        self._restore_btn = ctk.CTkButton(
            card,
            text="📂  Seleccionar respaldo…",
            height=42,
            width=220,
            corner_radius=8,
            fg_color=NARANJA_INTENSO,
            hover_color=HOVER_NARANJA_SEL,
            text_color="white",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._restore,
        )
        self._restore_btn.pack(pady=(0, 28))

    def _build_info_panel(self):
        info = ctk.CTkFrame(
            self,
            fg_color=BLANCO,
            corner_radius=12,
            border_width=2,
            border_color=AZUL_CIELO,
        )
        info.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 20))
        info.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            info,
            text="Información actual",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=AZUL_NOCHE,
        ).grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 6))

        self._db_path_lbl = self._info_row(
            info, 1, "Base de datos", "—"
        )
        self._db_size_lbl = self._info_row(
            info, 2, "Tamaño y actualización", "—"
        )
        self._backup_dir_lbl = self._info_row(
            info, 3, "Respaldos automáticos", backup_dir()
        )

        self._status_lbl = ctk.CTkLabel(
            info,
            text="Listo para respaldar o restaurar.",
            font=ctk.CTkFont(size=12),
            text_color=TEXTO_SECUNDARIO,
            anchor="w",
        )
        self._status_lbl.grid(
            row=4, column=0, columnspan=2, sticky="w", padx=16, pady=(4, 12)
        )

    def _info_row(self, parent, row: int, label: str, value: str):
        ctk.CTkLabel(
            parent,
            text=label,
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=AZUL_MARINO,
            width=170,
            anchor="w",
        ).grid(row=row, column=0, sticky="nw", padx=(16, 10), pady=2)
        value_lbl = ctk.CTkLabel(
            parent,
            text=value,
            font=ctk.CTkFont(size=13),
            text_color=GRIS_AZULADO,
            anchor="w",
            justify="left",
            wraplength=900,
        )
        value_lbl.grid(row=row, column=1, sticky="ew", padx=(0, 16), pady=2)
        return value_lbl

    def _build_access_denied(self):
        box = ctk.CTkFrame(
            self,
            fg_color=BLANCO,
            corner_radius=14,
            border_width=2,
            border_color=NARANJA_INTENSO,
        )
        box.grid(row=2, column=0, sticky="nsew", padx=20, pady=20)
        ctk.CTkLabel(
            box, text="🔒", font=ctk.CTkFont(size=48)
        ).pack(pady=(50, 8))
        ctk.CTkLabel(
            box,
            text="Acceso restringido",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack()
        ctk.CTkLabel(
            box,
            text=(
                "Esta sección solo está disponible para el usuario "
                "administrador."
            ),
            font=ctk.CTkFont(size=14),
            text_color=GRIS_AZULADO,
        ).pack(pady=(6, 50))

    # ── Estado y datos ──────────────────────────────────────────────────────
    def refresh(self):
        if not self._is_admin or self._db_path_lbl is None:
            return
        path = os.path.abspath(connection.DB_PATH)
        self._db_path_lbl.configure(text=path)
        try:
            size = os.path.getsize(path)
            updated = datetime.fromtimestamp(os.path.getmtime(path)).strftime(
                "%d/%m/%Y %H:%M"
            )
            self._db_size_lbl.configure(
                text=f"{_format_size(size)}  ·  Última actualización: {updated}"
            )
        except OSError:
            self._db_size_lbl.configure(text="No disponible")
        self._backup_dir_lbl.configure(text=backup_dir())

    def _set_busy(self, busy: bool, status: str | None = None):
        self._busy = busy
        state = "disabled" if busy else "normal"
        if self._backup_btn is not None:
            self._backup_btn.configure(state=state)
        if self._restore_btn is not None:
            self._restore_btn.configure(state=state)
        if status is not None and self._status_lbl is not None:
            self._status_lbl.configure(text=status)
        self.update_idletasks()

    def _initial_dir(self) -> str:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        return desktop if os.path.isdir(desktop) else os.path.expanduser("~")

    def _show_message(
        self,
        title: str,
        message: str,
        *,
        is_error: bool = False,
        is_warning: bool = False,
        badge_text: str | None = None,
    ):
        dialog = MessageDialog(
            self,
            title,
            message,
            is_error=is_error,
            is_warning=is_warning,
            badge_text=badge_text,
        )
        self.wait_window(dialog)

    def _ensure_admin(self) -> bool:
        if self._is_admin:
            return True
        self._show_message(
            "Acceso restringido",
            "Solo el usuario administrador puede gestionar los datos del sistema.",
            is_warning=True,
        )
        return False

    # ── Acciones ────────────────────────────────────────────────────────────
    def _backup(self):
        if self._busy or not self._ensure_admin():
            return
        path = filedialog.asksaveasfilename(
            parent=self,
            title="Guardar respaldo de la base de datos",
            defaultextension=".db",
            initialfile=default_backup_name(),
            initialdir=self._initial_dir(),
            filetypes=[
                ("Base de datos SQLite", "*.db"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path:
            return

        self._set_busy(True, "Creando respaldo…")
        try:
            result = create_backup(path)
        except Exception as exc:  # noqa: BLE001 - se muestra al usuario
            self._set_busy(False, "No se pudo crear el respaldo.")
            self._show_message(
                "No se pudo crear el respaldo",
                _wrap_text(str(exc)),
                is_error=True,
            )
            return

        self._set_busy(False, "Respaldo creado correctamente.")
        self._show_message(
            "Respaldo creado",
            "Se guardó una copia completa de la base de datos.\n\n"
            "Archivo:\n"
            f"{_break_path(result['path'])}\n\n"
            f"Tamaño: {_format_size(result['size'])}",
            badge_text="Respaldo",
        )

    def _restore(self):
        if self._busy or not self._ensure_admin():
            return
        path = filedialog.askopenfilename(
            parent=self,
            title="Seleccionar respaldo de la base de datos",
            initialdir=self._initial_dir(),
            filetypes=[
                ("Base de datos SQLite", "*.db"),
                ("Todos los archivos", "*.*"),
            ],
        )
        if not path:
            return

        confirm = ConfirmDialog(
            self,
            "Restaurar base de datos",
            "Se reemplazarán TODOS los datos actuales\n"
            "por el contenido de:\n\n"
            f"{_wrap_text(os.path.basename(path), 40)}\n\n"
            "Antes de continuar se creará un respaldo\n"
            "automático de la base actual.\n"
            "Al finalizar se cerrará la sesión.",
            is_danger=True,
            confirm_text="Sí, restaurar",
        )
        self.wait_window(confirm)
        if not confirm.result:
            return

        self._set_busy(True, "Restaurando base de datos…")
        try:
            result = restore_database(path)
        except Exception as exc:  # noqa: BLE001 - se muestra al usuario
            self._set_busy(False, "No se pudo restaurar la base de datos.")
            self._show_message(
                "No se pudo restaurar",
                _wrap_text(str(exc)),
                is_error=True,
            )
            return

        self._set_busy(False, "Base de datos restaurada correctamente.")
        self._show_message(
            "Base de datos restaurada",
            "La información se restauró correctamente.\n\n"
            "Respaldo de seguridad creado antes de restaurar:\n"
            f"{_break_path(result['safety_backup'])}\n\n"
            "Por seguridad, se cerrará la sesión para\n"
            "que ingreses con los usuarios de la base restaurada.",
            badge_text="Restauración",
        )
        if self.app is not None:
            self.after(100, self.app._logout)

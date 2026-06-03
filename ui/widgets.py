import customtkinter as ctk
import tkinter as tk
from tkinter import ttk
from ui.colors import *


def setup_treeview_style():
    style = ttk.Style()
    style.theme_use("clam")

    # Eliminamos el layout del borde gris nativo para que no choque con el azul
    style.layout("Inv.Treeview", [("Inv.Treeview.treearea", {"sticky": "nswe"})])

    style.configure(
        "Inv.Treeview",
        background="white",
        foreground=AZUL_NOCHE,
        fieldbackground="white",
        rowheight=32,
        font=("Segoe UI", 12),
        borderwidth=0,
        relief="flat",
        indent=15,
    )
    style.configure("Inv.Treeview", padding=(10, 0))
    style.configure(
        "Inv.Treeview.Heading",
        background=AZUL_MARINO,
        foreground="white",
        font=("Segoe UI", 12, "bold"),
        relief="flat",
    )
    style.map(
        "Inv.Treeview",
        background=[("selected", NARANJA_SELECCION)],
        foreground=[("selected", "white")],
    )
    style.map("Inv.Treeview.Heading", background=[("active", AZUL_NOCHE)])


def make_table(parent, columns: list, bg_color="white") -> ttk.Treeview:
    """
    Crea la tabla con bordes definidos en color #031d44.
    """
    # Restauramos el borde del Frame con el nuevo color solicitado
    frame = ctk.CTkFrame(
        parent,
        fg_color=bg_color,
        border_color=AZUL_MARINO,  # Color azul oscuro solicitado
        border_width=3,  # Grosor del borde exterior
        corner_radius=2,
    )
    frame.grid(row=0, column=0, sticky="nsew")

    tree = ttk.Treeview(
        frame,
        columns=[c[0] for c in columns],
        show="headings",
        style="Inv.Treeview",
        selectmode="browse",
    )

    for col_id, label, width in columns:
        tree.heading(col_id, text=label)
        tree.column(col_id, width=width, anchor="center", minwidth=40)

    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    # Empujamos el tree ligeramente (1-2px) para que respete el redondeado del frame azul
    tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
    vsb.grid(row=0, column=1, sticky="ns", pady=1, padx=(0, 1))

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    _add_separators(tree, frame, columns)

    return tree


def _add_separators(tree, frame, columns):
    tree._separators = []
    tree._frame = frame
    tree._columns = columns
    frame.bind("<Configure>", lambda e: _update_separators(tree))
    tree.after_idle(lambda: _update_separators(tree))


def _update_separators(tree):
    # Limpiar separadores previos
    for sep in tree._separators:
        sep.destroy()
    tree._separators = []

    frame = tree._frame
    tree.update_idletasks()

    # Calcular el ancho total de todas las columnas configuradas
    total_width = 0
    for col_id in tree["columns"]:
        total_width += tree.column(col_id, "width")

    # Líneas verticales internas (color azul original #084887 y grosor 3)
    prev_col = None
    for x in range(1, total_width):
        col = tree.identify_column(x)
        if col != prev_col and prev_col is not None:
            # Colocar la línea en x-1 para coincidir con el borde derecho de la columna anterior
            sep = tk.Frame(frame, bg=AZUL_MARINO, width=3)
            sep.place(x=x - 4, y=0, relheight=1.0)
            tree._separators.append(sep)
        prev_col = col


def clear_tree(tree: ttk.Treeview):
    tree.delete(*tree.get_children())


def center_dialog(dialog):
    """Centra un diálogo Toplevel sobre su ventana padre."""
    dialog.update_idletasks()
    parent_x = dialog.master.winfo_x()
    parent_y = dialog.master.winfo_y()
    parent_w = dialog.master.winfo_width()
    parent_h = dialog.master.winfo_height()
    dialog_w = dialog.winfo_width()
    dialog_h = dialog.winfo_height()
    x = parent_x + (parent_w - dialog_w) // 2
    y = parent_y + (parent_h - dialog_h) // 2
    dialog.geometry(f"+{x}+{y}")


class ConfirmDialog(ctk.CTkToplevel):
    """Diálogo de confirmación con botones Sí/No."""

    def __init__(self, parent, title, message, is_danger=False):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=BLANCO_CALIDO)
        self.result = False
        self.after_idle(lambda: center_dialog(self))

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(pady=(20, 10))

        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=16),
            text_color=GRIS_AZULADO,
            wraplength=360,
            justify="center",
        )
        msg_label.pack(pady=10, padx=20)

        self.update_idletasks()
        min_height = max(280, msg_label.winfo_reqheight() + 160)
        self.geometry(f"450x{min_height}")

        btn_frame = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        btn_frame.pack(pady=20)
        btn_frame.pack_propagate(False)
        btn_frame.configure(width=360)

        btn_color = NARANJA_INTENSO if is_danger else AZUL_CERULEO

        ctk.CTkButton(
            btn_frame,
            text="Sí, continuar",
            command=self._on_yes,
            fg_color=btn_color,
            hover_color=HOVER_MARINO if is_danger else HOVER_FILTRO_DISP,
            text_color="white",
            width=150,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=10)

        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=self._on_no,
            fg_color=CANCELAR_BG,
            hover_color=CANCELAR_HOVER,
            text_color="white",
            width=150,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(side="left", padx=10)

        self.update_idletasks()
        self.grab_set()

    def _on_yes(self):
        self.result = True
        self.destroy()

    def _on_no(self):
        self.result = False
        self.destroy()


class MessageDialog(ctk.CTkToplevel):
    """Diálogo de mensaje informativo o de error."""

    def __init__(self, parent, title, message, is_error=False):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.configure(fg_color=BLANCO_CALIDO)
        self.after_idle(lambda: center_dialog(self))

        icon_color = NARANJA_INTENSO if is_error else AZUL_CERULEO
        icon_text = "✕" if is_error else "✓"

        ctk.CTkLabel(
            self,
            text=icon_text,
            font=ctk.CTkFont(size=42, weight="bold"),
            text_color=icon_color,
        ).pack(pady=(15, 5))

        ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(pady=(5, 10))

        msg_label = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=16),
            text_color=GRIS_AZULADO,
            wraplength=360,
            justify="center",
        )
        msg_label.pack(pady=5, padx=20)

        self.update_idletasks()
        min_height = max(240, msg_label.winfo_reqheight() + 140)
        self.geometry(f"420x{min_height}")

        ctk.CTkButton(
            self,
            text="Aceptar",
            command=self.destroy,
            fg_color=AZUL_CERULEO,
            hover_color=HOVER_FILTRO_DISP,
            text_color="white",
            width=120,
            height=38,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=15)

        self.update_idletasks()
        self.grab_set()

import customtkinter as ctk
from tkinter import messagebox
from ui.colors import *
from ui.widgets import make_table, clear_tree, setup_treeview_style
from database.repository import (
    get_all_employees,
    create_employee,
    update_employee,
    delete_employee,
)


class EmployeesView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)  # Fondo Base
        self.current_user = current_user
        setup_treeview_style()
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            hdr,
            text="Empleados",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(side="left")
        ctk.CTkButton(
            hdr,
            text="+ Agregar Empleado",
            height=36,
            command=self._add_dialog,
            fg_color=NARANJA_SELECCION,
            hover_color=HOVER_NARANJA_SEL,
            text_color="white",
        ).pack(side="right")

        sf = ctk.CTkFrame(
            self, fg_color=BLANCO, border_width=1, border_color=AZUL_MARINO
        )
        sf.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        sf.pack_propagate(False)
        sf.configure(height=50)
        ctk.CTkLabel(
            sf, text="Buscar:", font=ctk.CTkFont(size=17), text_color=AZUL_MARINO
        ).pack(side="left", padx=(12, 4))
        self._search = ctk.StringVar()
        self._search.trace_add("write", lambda *_: self.refresh())
        self._search_entry = ctk.CTkEntry(
            sf,
            textvariable=self._search,
            placeholder_text="Buscar por nombre o cédula...",
            border_width=0,
            fg_color="transparent",
            text_color=AZUL_NOCHE,
            placeholder_text_color=TEXTO_PLACEHOLDER,
            font=ctk.CTkFont(size=15),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        tf = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        tf.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        cols = [
            ("id", "ID", 50),
            ("name", "Nombre", 200),
            ("cedula", "Cédula", 120),
            ("cargo", "Cargo", 180),
            ("created_at", "Fecha Reg.", 140),
        ]
        self.tree = make_table(tf, cols, bg_color="white")

        af = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        af.grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 10))
        ctk.CTkButton(
            af,
            text="✏️ Editar",
            width=120,
            height=34,
            command=self._edit_dialog,
            fg_color=AZUL_MARINO,
            hover_color=SIDEBAR_HOVER,
            text_color="white",
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            af,
            text="🗑️ Eliminar",
            width=120,
            height=34,
            fg_color=AZUL_MARINO,  # Secundario
            hover_color=SIDEBAR_HOVER,
            text_color="white",
            command=self._delete,
        ).pack(side="left", padx=4)

    def refresh(self):
        q = self._search.get().lower() if hasattr(self, "_search") else ""
        clear_tree(self.tree)
        for r in get_all_employees():
            if q in r["name"].lower() or q in (r["cedula"] or "").lower():
                self.tree.insert(
                    "",
                    "end",
                    iid=r["id"],
                    values=(
                        r["id"],
                        r["name"],
                        r["cedula"],
                        r["cargo"],
                        r["created_at"],
                    ),
                )

    def _selected(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un empleado.")
        return sel or None

    def _add_dialog(self):
        _EmpDialog(
            self,
            "Agregar Empleado",
            on_save=lambda d: (
                create_employee(d["name"], d["cedula"], d["cargo"]),
                self.refresh(),
            ),
        )

    def _edit_dialog(self):
        iid = self._selected()
        if not iid:
            return
        vals = self.tree.item(iid, "values")
        _EmpDialog(
            self,
            "Editar Empleado",
            initial={"name": vals[1], "cedula": vals[2], "cargo": vals[3]},
            on_save=lambda d: (
                update_employee(int(iid), d["name"], d["cedula"], d["cargo"]),
                self.refresh(),
            ),
        )

    def _delete(self):
        iid = self._selected()
        if not iid:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este empleado?"):
            delete_employee(int(iid))
            self.refresh()


class _EmpDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, on_save, initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("550x420")
        self.minsize(450, 350)
        self.resizable(True, True)
        self.configure(fg_color=BLANCO_CALIDO)
        self.transient(parent)
        self.on_save = on_save
        d = initial or {}

        main = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        main.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main, fg_color=AZUL_NOCHE, height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=title.upper(),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white",
        ).pack(pady=15)

        content = ctk.CTkFrame(main, fg_color=BLANCO_CALIDO)
        content.pack(fill="both", expand=True, padx=20)

        left = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(
            left,
            text="DATOS PERSONALES",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            left,
            text="Nombre *",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.name_e = ctk.CTkEntry(
            left,
            height=38,
            text_color=AZUL_NOCHE,
            fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=TEXTO_PLACEHOLDER,
            border_width=1,
            border_color=AZUL_MARINO,
        )
        if d.get("name"):
            self.name_e.insert(0, d["name"])
        self.name_e.pack(fill="x", padx=15)

        ctk.CTkLabel(
            left,
            text="Cédula *",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(10, 0))
        self.cedula_e = ctk.CTkEntry(
            left,
            height=38,
            text_color=AZUL_NOCHE,
            fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=TEXTO_PLACEHOLDER,
            border_width=1,
            border_color=AZUL_MARINO,
        )
        if d.get("cedula"):
            self.cedula_e.insert(0, d["cedula"])
        self.cedula_e.pack(fill="x", padx=15)

        ctk.CTkLabel(
            right,
            text="DATOS LABORALES",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            right,
            text="Cargo",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.cargo_e = ctk.CTkEntry(
            right,
            height=38,
            text_color=AZUL_NOCHE,
            fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=TEXTO_PLACEHOLDER,
            border_width=1,
            border_color=AZUL_MARINO,
        )
        if d.get("cargo"):
            self.cargo_e.insert(0, d["cargo"])
        self.cargo_e.pack(fill="x", padx=15)

        btns = ctk.CTkFrame(main, fg_color=BLANCO_CALIDO)
        btns.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(
            btns,
            text="✓ GUARDAR",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save,
            fg_color=AZUL_MARINO,
            hover_color=AZUL_NOCHE,
            text_color="white",
            height=45,
        ).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(
            btns,
            text="✕ CANCELAR",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color=NARANJA_INTENSO,
            hover_color=HOVER_NARANJA_SEL,
            text_color="white",
            height=45,
            command=self.destroy,
        ).pack(side="left", expand=True, padx=5)

    def _save(self):
        import re

        name = self.name_e.get().strip()
        if not name:
            messagebox.showwarning("Aviso", "El nombre es obligatorio.", parent=self)
            return
        if not re.match(r"^[a-zA-Z\sáéíóúÁÉÍÓÚÑñ]+$", name):
            messagebox.showwarning(
                "Aviso", "El nombre solo puede tener letras.", parent=self
            )
            return

        cedula = self.cedula_e.get().strip()
        if not cedula:
            messagebox.showwarning("Aviso", "La cédula es obligatoria.", parent=self)
            return
        if not re.match(r"^[0-9]{6,10}$", cedula):
            messagebox.showwarning(
                "Aviso", "Cédula inválida (6-10 dígitos).", parent=self
            )
            return

        cargo = self.cargo_e.get().strip()
        if cargo and not re.match(r"^[a-zA-Z0-9\s\-_.,áéíóúÁÉÍÓÚÑñ]+$", cargo):
            messagebox.showwarning(
                "Aviso", "Cargo con caracteres inválidos.", parent=self
            )
            return

        self.on_save(
            {
                "name": name.upper(),
                "cedula": cedula,
                "cargo": cargo.upper(),
            }
        )
        self.destroy()

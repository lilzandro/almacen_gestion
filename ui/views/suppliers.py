import customtkinter as ctk
from tkinter import messagebox
from ui.widgets import make_table, clear_tree, setup_treeview_style
from database.repository import (
    get_all_suppliers,
    create_supplier,
    update_supplier,
    delete_supplier,
)


class SuppliersView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color="#F7F5FB")  # Fondo Base
        self.current_user = current_user
        setup_treeview_style()
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        # Header row
        hdr = ctk.CTkFrame(self, fg_color="#F7F5FB")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            hdr,
            text="Proveedores",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="#031D44",
        ).pack(side="left")
        ctk.CTkButton(
            hdr,
            text="+ Agregar Proveedor",
            height=36,
            command=self._add_dialog,
            fg_color="#F58A07",
            hover_color="#D67A00",
            text_color="white",
        ).pack(side="right")

        # Search
        sf = ctk.CTkFrame(
            self, fg_color="#FFFFFF", border_width=1, border_color="#084887"
        )
        sf.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        sf.pack_propagate(False)
        sf.configure(height=50)
        ctk.CTkLabel(
            sf, text="Buscar:", font=ctk.CTkFont(size=17), text_color="#084887"
        ).pack(side="left", padx=(12, 4))
        self._search = ctk.StringVar()
        self._search.trace_add("write", lambda *_: self.refresh())
        self._search_entry = ctk.CTkEntry(
            sf,
            textvariable=self._search,
            placeholder_text="Buscar por nombre o rif...",
            border_width=0,
            fg_color="transparent",
            text_color="#031D44",
            placeholder_text_color="#9CA3AF",
            font=ctk.CTkFont(size=15),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Table
        tf = ctk.CTkFrame(self, fg_color="#F7F5FB")
        tf.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        cols = [
            ("id", "ID", 50),
            ("name", "Nombre", 200),
            ("contact", "Contacto", 180),
            ("rif", "Rif", 150),
            ("created_at", "Fecha Reg.", 140),
        ]
        self.tree = make_table(tf, cols, bg_color="white")

        # Actions
        af = ctk.CTkFrame(self, fg_color="#F7F5FB")
        af.grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 10))
        ctk.CTkButton(
            af,
            text="✏️ Editar",
            width=120,
            height=34,
            command=self._edit_dialog,
            fg_color="#084887",
            hover_color="#063A69",
            text_color="white",
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            af,
            text="🗑️ Eliminar",
            width=120,
            height=34,
            fg_color="#084887",  # Secundario
            hover_color="#063A69",
            text_color="white",
            command=self._delete,
        ).pack(side="left", padx=4)

    def refresh(self):
        q = self._search.get().lower() if hasattr(self, "_search") else ""
        clear_tree(self.tree)
        for r in get_all_suppliers():
            if q in r["name"].lower() or q in (r["contact"] or "").lower():
                self.tree.insert(
                    "",
                    "end",
                    iid=r["id"],
                    values=(
                        r["id"],
                        r["name"],
                        r["contact"],
                        r["rif"] or "",
                        r["created_at"],
                    ),
                )

    def _selected(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un proveedor.")
        return sel or None

    def _add_dialog(self):
        _SupplierDialog(self, title="Agregar Proveedor", on_save=self._save_new)

    def _edit_dialog(self):
        iid = self._selected()
        if not iid:
            return
        vals = self.tree.item(iid, "values")
        _SupplierDialog(
            self,
            title="Editar Proveedor",
            initial={"name": vals[1], "contact": vals[2], "rif": vals[3]},
            on_save=lambda d: self._save_edit(int(iid), d),
        )

    def _save_new(self, data):
        create_supplier(data["name"], data["contact"], data["rif"])
        self.refresh()

    def _save_edit(self, sid, data):
        update_supplier(sid, data["name"], data["contact"], data["rif"])
        self.refresh()

    def _delete(self):
        iid = self._selected()
        if not iid:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este proveedor?"):
            delete_supplier(int(iid))
            self.refresh()


class _SupplierDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, on_save, initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("550x400")
        self.minsize(450, 350)
        self.resizable(True, True)
        self.configure(fg_color="#F7F5FB")
        self.transient(parent)
        self.on_save = on_save
        d = initial or {}

        main = ctk.CTkFrame(self, fg_color="#F7F5FB")
        main.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main, fg_color="#031D44", height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=title.upper(),
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white",
        ).pack(pady=15)

        content = ctk.CTkFrame(main, fg_color="#F7F5FB")
        content.pack(fill="both", expand=True, padx=20)

        left = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        ctk.CTkLabel(
            left,
            text="DATOS DEL PROVEEDOR",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#031D44",
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            left,
            text="Nombre *",
            anchor="w",
            text_color="#031D44",
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.name_e = ctk.CTkEntry(
            left,
            height=38,
            text_color="#031D44",
            fg_color="#F7F5FB",
            font=ctk.CTkFont(size=14),
            placeholder_text_color="#9CA3AF",
            border_width=1,
            border_color="#084887",
        )
        if d.get("name"):
            self.name_e.insert(0, d["name"])
        self.name_e.pack(fill="x", padx=15)

        ctk.CTkLabel(
            left,
            text="Contacto",
            anchor="w",
            text_color="#031D44",
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(10, 0))
        self.contact_e = ctk.CTkEntry(
            left,
            height=38,
            text_color="#031D44",
            fg_color="#F7F5FB",
            font=ctk.CTkFont(size=14),
            placeholder_text_color="#9CA3AF",
            border_width=1,
            border_color="#084887",
        )
        if d.get("contact"):
            self.contact_e.insert(0, d["contact"])
        self.contact_e.pack(fill="x", padx=15)

        ctk.CTkLabel(
            right,
            text="IDENTIFICACIÓN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#031D44",
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            right,
            text="Rif",
            anchor="w",
            text_color="#031D44",
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.rif_e = ctk.CTkEntry(
            right,
            height=38,
            text_color="#031D44",
            fg_color="#F7F5FB",
            font=ctk.CTkFont(size=14),
            placeholder_text_color="#9CA3AF",
            border_width=1,
            border_color="#084887",
        )
        if d.get("rif"):
            self.rif_e.insert(0, d["rif"])
        self.rif_e.pack(fill="x", padx=15)

        btns = ctk.CTkFrame(main, fg_color="#F7F5FB")
        btns.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(
            btns,
            text="✓ GUARDAR",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save,
            fg_color="#084887",
            hover_color="#031D44",
            text_color="white",
            height=45,
        ).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(
            btns,
            text="✕ CANCELAR",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#FB8500",
            hover_color="#D67A00",
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
        if not re.match(r"^[a-zA-Z0-9\s\-_.,áéíóúÁÉÍÓÚÑñ]+$", name):
            messagebox.showwarning(
                "Aviso", "El nombre contiene caracteres inválidos.", parent=self
            )
            return

        contact = self.contact_e.get().strip()
        if contact and not re.match(r"^[a-zA-Z0-9\s\-_.,áéíóúÁÉÍÓÚÑñ]+$", contact):
            messagebox.showwarning(
                "Aviso", "Contacto con caracteres inválidos.", parent=self
            )
            return

        rif = self.rif_e.get().strip().upper()
        if rif and not re.match(r"^[A-Z0-9\-]{6,15}$", rif):
            messagebox.showwarning("Aviso", "Rif inválido.", parent=self)
            return

        self.on_save(
            {
                "name": name.upper(),
                "contact": contact.upper() if contact else "",
                "rif": rif if rif else "",
            }
        )
        self.destroy()

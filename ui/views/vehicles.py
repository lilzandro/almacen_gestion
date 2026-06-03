import customtkinter as ctk
from tkinter import messagebox
from ui.colors import *
from ui.widgets import make_table, clear_tree, setup_treeview_style
from database.repository import (
    get_all_vehicles,
    create_vehicle,
    update_vehicle,
    delete_vehicle,
)


class VehiclesView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)
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
            text="Vehículos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(side="left")
        if self.current_user["role"] == "admin":
            ctk.CTkButton(
                hdr,
                text="+ Agregar Vehículo",
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
            placeholder_text="Buscar por marca o placa...",
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
            ("brand", "Marca", 150),
            ("model", "Modelo", 150),
            ("plate", "Placa", 120),
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
        if self.current_user["role"] == "admin":
            ctk.CTkButton(
                af,
                text="🗑️ Eliminar",
                width=120,
                height=34,
                fg_color=AZUL_MARINO,
                hover_color=SIDEBAR_HOVER,
                text_color="white",
                command=self._delete,
            ).pack(side="left", padx=4)

    def refresh(self):
        q = self._search.get().lower() if hasattr(self, "_search") else ""
        clear_tree(self.tree)
        for r in get_all_vehicles():
            if q in r["brand"].lower() or q in r["plate"].lower():
                self.tree.insert(
                    "",
                    "end",
                    iid=r["id"],
                    values=(
                        r["id"],
                        r["brand"],
                        r["model"],
                        r["plate"],
                        r["created_at"],
                    ),
                )

    def _selected(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un vehículo.")
        return sel or None

    def _add_dialog(self):
        _VehicleDialog(self, title="Agregar Vehículo", on_save=self._save_new)

    def _edit_dialog(self):
        iid = self._selected()
        if not iid:
            return
        vals = self.tree.item(iid, "values")
        _VehicleDialog(
            self,
            title="Editar Vehículo",
            initial={"brand": vals[1], "model": vals[2], "plate": vals[3]},
            on_save=lambda d: self._save_edit(int(iid), d),
        )

    def _save_new(self, data):
        create_vehicle(data["brand"], data["model"], data["plate"])
        self.refresh()

    def _save_edit(self, vid, data):
        update_vehicle(vid, data["brand"], data["model"], data["plate"])
        self.refresh()

    def _delete(self):
        iid = self._selected()
        if not iid:
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este vehículo?"):
            delete_vehicle(int(iid))
            self.refresh()


class _VehicleDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, on_save, initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("550x400")
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
            text="DATOS DEL VEHÍCULO",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            left,
            text="Marca *",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.brand_e = ctk.CTkEntry(
            left,
            height=38,
            text_color=AZUL_NOCHE,
            fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=TEXTO_PLACEHOLDER,
            border_width=1,
            border_color=AZUL_MARINO,
        )
        if d.get("brand"):
            self.brand_e.insert(0, d["brand"])
        self.brand_e.pack(fill="x", padx=15)

        ctk.CTkLabel(
            left,
            text="Modelo",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(10, 0))
        self.model_e = ctk.CTkEntry(
            left,
            height=38,
            text_color=AZUL_NOCHE,
            fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=TEXTO_PLACEHOLDER,
            border_width=1,
            border_color=AZUL_MARINO,
        )
        if d.get("model"):
            self.model_e.insert(0, d["model"])
        self.model_e.pack(fill="x", padx=15)

        ctk.CTkLabel(
            right,
            text="IDENTIFICACIÓN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            right,
            text="Placa *",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.plate_e = ctk.CTkEntry(
            right,
            height=38,
            text_color=AZUL_NOCHE,
            fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=TEXTO_PLACEHOLDER,
            border_width=1,
            border_color=AZUL_MARINO,
        )
        if d.get("plate"):
            self.plate_e.insert(0, d["plate"])
        self.plate_e.pack(fill="x", padx=15)

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

        brand = self.brand_e.get().strip()
        if not brand:
            messagebox.showwarning("Aviso", "La marca es obligatoria.", parent=self)
            return
        if not re.match(r"^[a-zA-Z0-9\s\-]+$", brand):
            messagebox.showwarning("Aviso", "Marca inválida.", parent=self)
            return

        model = self.model_e.get().strip()
        if model and not re.match(r"^[a-zA-Z0-9\s\-]+$", model):
            messagebox.showwarning("Aviso", "Modelo inválido.", parent=self)
            return

        plate = self.plate_e.get().strip().upper()
        if not plate:
            messagebox.showwarning("Aviso", "La placa es obligatoria.", parent=self)
            return
        if not re.match(r"^[A-Z0-9]{5,8}$", plate):
            messagebox.showwarning(
                "Aviso", "Placa inválida (5-8 caracteres alfanuméricos).", parent=self
            )
            return

        self.on_save(
            {
                "brand": brand.upper(),
                "model": model.upper() if model else "",
                "plate": plate,
            }
        )
        self.destroy()

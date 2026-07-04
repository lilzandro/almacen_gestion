import customtkinter as ctk
from tkinter import messagebox, filedialog

from ui.colors import *
from ui.widgets import make_table, clear_tree, setup_treeview_style
from database.repository import (
    get_all_movements,
    get_all_employees,
    get_all_vehicles,
    get_all_products,
    get_products_pending_return,
    create_movement,
)
from core.export import export_movements


class MovementsView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)  # Fondo Base
        self.current_user = current_user
        self.app = app
        setup_treeview_style()
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        # Header
        hdr = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            hdr,
            text="Movimientos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(side="left")
        btn_frame = ctk.CTkFrame(hdr, fg_color=BLANCO_CALIDO)
        btn_frame.pack(side="right")
        ctk.CTkButton(
            btn_frame,
            text="+ Registrar Movimiento",
            height=36,
            command=self._register_dialog,
            fg_color=NARANJA_SELECCION,
            hover_color=HOVER_NARANJA_SEL,
            text_color="white",
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            btn_frame,
            text="📥 Exportar Excel",
            height=36,
            fg_color=HOVER_EXPORT,
            hover_color=HOVER_EXPORT,
            text_color="white",
            command=self._export,
        ).pack(side="left", padx=4)

        # Search
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
            placeholder_text="Buscar producto, empleado...",
            border_width=0,
            fg_color="transparent",
            text_color=AZUL_NOCHE,
            placeholder_text_color=TEXTO_PLACEHOLDER,
            font=ctk.CTkFont(size=15),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Filtros por tipo
        self._type_filter = ctk.StringVar(value="todos")
        self._type_btns = {}
        type_defs = [
            ("todos", "Todos", AZUL_MARINO, AZUL_NOCHE),
            ("entrada", "Entrada", AZUL_CERULEO, HOVER_FILTRO_DISP),
            ("salida", "Salida", NARANJA_SELECCION, HOVER_NARANJA_SEL),
            ("devolucion", "Devolución", AMARILLO_AMBAR, HOVER_AMBAR),
            ("asignacion", "Asignación", AZUL_CIELO, HOVER_MOV_ASIG),
        ]
        for val, label, fg, hover in type_defs:
            btn = ctk.CTkButton(
                sf,
                text=label,
                width=90,
                height=28,
                fg_color=fg,
                hover_color=hover,
                text_color="white",
                font=ctk.CTkFont(size=11),
                command=lambda v=val: self.set_type_filter(v),
            )
            btn.pack(side="right", padx=(0, 4))
            self._type_btns[val] = btn
        self._update_type_buttons()

        # Table
        tf = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        tf.grid(row=2, column=0, sticky="nsew", padx=20, pady=(0, 10))
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        cols = [
            ("id", "ID", 50),
            ("type", "Tipo", 100),
            ("timestamp", "Fecha/Hora", 160),
            ("quantity", "Cant.", 60),
            ("product", "Producto", 220),
            ("employee", "Empleado", 170),
            ("registered_by", "Registrado por", 120),
            ("notes", "Notas", 180),
        ]
        self.tree = make_table(tf, cols, bg_color="white")

    def set_type_filter(self, type_: str):
        self._type_filter.set(type_)
        self._update_type_buttons()
        self.refresh()

    def _update_type_buttons(self):
        active = self._type_filter.get()
        styles = {
            "todos": (AZUL_MARINO, AZUL_NOCHE),
            "entrada": (AZUL_CERULEO, HOVER_FILTRO_DISP),
            "salida": (NARANJA_SELECCION, HOVER_NARANJA_SEL),
            "devolucion": (AMARILLO_AMBAR, HOVER_AMBAR),
            "asignacion": (AZUL_CIELO, HOVER_MOV_ASIG),
        }
        for val, btn in self._type_btns.items():
            fg, _ = styles[val]
            if val == active:
                btn.configure(
                    fg_color=fg,
                    border_width=2,
                    border_color="white",
                    font=ctk.CTkFont(size=11, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color=fg,
                    border_width=0,
                    font=ctk.CTkFont(size=11, weight="normal"),
                )

    def refresh(self):
        q = self._search.get() if hasattr(self, "_search") else ""
        type_ = self._type_filter.get() if hasattr(self, "_type_filter") else "todos"
        wh_id = self.app.current_warehouse_id if self.app else None
        clear_tree(self.tree)
        rows = get_all_movements(search=q, warehouse_id=wh_id)
        if type_ != "todos":
            rows = [r for r in rows if r["type"] == type_]
        for r in rows:
            self.tree.insert(
                "",
                "end",
                iid=r["id"],
                values=(
                    r["id"],
                    r["type"],
                    r["timestamp"],
                    r["quantity"],
                    r["product"],
                    r["employee"],
                    r["registered_by"],
                    r["notes"],
                ),
            )

    def _register_dialog(self):
        _MovementDialog(
            self,
            current_user=self.current_user,
            on_save=lambda: self.refresh(),
            warehouse_id=self.app.current_warehouse_id if self.app else None,
        )

    def _export(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel", "*.xlsx")],
            initialfile="movimientos.xlsx",
        )
        if path:
            export_movements(path)
            messagebox.showinfo("Éxito", f"Exportado en:\n{path}")


class _SearchableMultiSelect(ctk.CTkFrame):
    """Reusable searchable multi-select widget for large lists"""

    def __init__(
        self,
        parent,
        items,
        item_key,
        item_label,
        placeholder="Buscar...",
        show_quantity=False,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._items = [dict(item) for item in items]
        self._item_key = item_key
        self._item_label = item_label
        self._selected = set()
        self._quantities = {}
        self._show_quantity = show_quantity
        self._item_qty_entries = {}

        search_frame = ctk.CTkFrame(self, fg_color="white")
        search_frame.pack(fill="x", pady=(0, 5))
        ctk.CTkLabel(search_frame, text="🔍", text_color=TEXTO_SECUNDARIO).pack(
            side="left", padx=(10, 2)
        )
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._filter_items())
        self._search_entry = ctk.CTkEntry(
            search_frame,
            textvariable=self.search_var,
            placeholder_text=placeholder,
            border_width=0,
            fg_color="white",
            text_color=TEXTO_MOV_FIELD,
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self._count_label = ctk.CTkLabel(
            self,
            text="0 seleccionados",
            text_color=AZUL_MARINO,
            font=ctk.CTkFont(size=14, weight="bold"),
        )
        self._count_label.pack(anchor="w", pady=(0, 5))

        self._list_frame = ctk.CTkScrollableFrame(self, fg_color="white", height=180)
        self._list_frame.pack(fill="both", expand=True)

        self._checkboxes = {}
        self._qty_entries = {}
        self._display_items = []
        self._filter_items()

    def _filter_items(self):
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._checkboxes = {}
        self._qty_entries = {}

        search = self.search_var.get().lower()
        self._display_items = [
            item for item in self._items if search in self._item_label(item).lower()
        ][:50]

        for item in self._display_items:
            item_id = item[self._item_key]
            row = ctk.CTkFrame(self._list_frame, fg_color="white")
            row.pack(fill="x", pady=2)

            var = ctk.CTkCheckBox(
                row,
                text=self._item_label(item)[:40],
                font=ctk.CTkFont(size=14),
                command=lambda i=item_id: self._toggle(i),
            )
            var.pack(side="left", padx=5)
            if item_id in self._selected:
                var.select()

            if self._show_quantity:
                qty_entry = ctk.CTkEntry(
                    row,
                    width=60,
                    height=30,
                    text_color=TEXTO_MOV_FIELD,
                    fg_color=FONDO_MULTI_QTY,
                    font=ctk.CTkFont(size=14),
                    placeholder_text="und",
                    placeholder_text_color=TEXTO_PLACEHOLDER_LOGIN,
                    border_width=1,
                )
                qty_entry.insert(0, str(self._quantities.get(item_id, 1)))
                qty_entry.pack(side="right", padx=5)
                self._qty_entries[item_id] = qty_entry
                ctk.CTkLabel(
                    row,
                    text="uds:",
                    text_color=TEXTO_SECUNDARIO,
                    font=ctk.CTkFont(size=12),
                ).pack(side="right", padx=(0, 2))

            self._checkboxes[item_id] = var

    def _toggle(self, item_id):
        if item_id in self._selected:
            self._selected.discard(item_id)
        else:
            self._selected.add(item_id)
            if item_id not in self._quantities:
                self._quantities[item_id] = 1
        self._count_label.configure(text=f"{len(self._selected)} seleccionados")
        self._filter_items()

    def get_selected(self):
        if self._show_quantity:
            result = []
            for item_id in self._selected:
                entry = self._qty_entries.get(item_id)
                if entry:
                    try:
                        qty = int(entry.get().strip() or 1)
                    except ValueError:
                        qty = 1
                    result.append((item_id, qty))
            return result
        return list(self._selected)


class _MovementDialog(ctk.CTkToplevel):
    TYPES = ["salida", "devolucion"]

    def __init__(self, parent, current_user, on_save, warehouse_id=None):
        super().__init__(parent)
        self.warehouse_id = warehouse_id
        self.title("Registrar Movimiento")
        self.geometry("900x750")
        self.minsize(700, 600)
        self.resizable(True, True)
        self.configure(fg_color=BLANCO_CALIDO)
        self.transient(parent)
        self.current_user = current_user
        self.on_save = on_save

        self._all_products = get_all_products(search="", include_inactive=False)
        self._employees = get_all_employees()
        self._vehicles = get_all_vehicles()

        main = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        main.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main, fg_color=AZUL_NOCHE, height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="📦 REGISTRAR MOVIMIENTO",
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
            text="DATOS DEL MOVIMIENTO",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        type_frame = ctk.CTkFrame(left, fg_color="transparent")
        type_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(
            type_frame,
            text="Tipo:",
            font=ctk.CTkFont(size=14),
            text_color=TEXTO_MOV_FIELD,
        ).pack(side="left")
        self.type_opt = ctk.CTkOptionMenu(
            type_frame,
            values=self.TYPES,
            font=ctk.CTkFont(size=14),
            command=self._on_type_change,
            text_color="white",
            button_color=AZUL_MARINO,
            button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO,
            dropdown_font=ctk.CTkFont(size=14),
            width=130,
        )
        self.type_opt.pack(side="left", padx=(10, 0))
        self.type_opt.set("salida")

        ctk.CTkLabel(
            left,
            text="PRODUCTOS *",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(
            left,
            text="Selecciona y escribe la cantidad por cada producto",
            font=ctk.CTkFont(size=11),
            text_color=TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=15, pady=(0, 5))

        products = [dict(p) for p in self._all_products if p["quantity"] > 0]
        self._prod_select = _SearchableMultiSelect(
            left,
            products,
            "id",
            lambda p: f"{p['name']} (disp: {p['quantity']})",
            placeholder="Buscar producto...",
            fg_color=FONDO_MULTISELECT,
            show_quantity=True,
        )
        self._prod_select.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        ctk.CTkLabel(
            right,
            text="ASIGNACIÓN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        self._emp_frame = ctk.CTkFrame(right, fg_color="transparent")
        self._emp_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(
            self._emp_frame,
            text="👤 Empleados",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", pady=(5, 5))
        self._emp_select = _SearchableMultiSelect(
            self._emp_frame,
            [dict(e) for e in self._employees],
            "id",
            lambda e: f"{e['name']} ({e['cedula']})",
            placeholder="Buscar empleado...",
            fg_color=FONDO_MULTISELECT,
        )
        self._emp_select.pack(fill="x")

        self._veh_frame = ctk.CTkFrame(right, fg_color="transparent")
        self._veh_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(
            self._veh_frame,
            text="🚚 Vehículo",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", pady=(5, 5))
        vehicle_names = [
            f"{dict(v)['brand']} - {dict(v)['plate']}" for v in self._vehicles
        ] or ["Sin vehículo"]
        self.vehicle_opt = ctk.CTkOptionMenu(
            self._veh_frame,
            values=vehicle_names,
            font=ctk.CTkFont(size=14),
            text_color="white",
            button_color=AZUL_MARINO,
            button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO,
            dropdown_font=ctk.CTkFont(size=14),
        )
        self.vehicle_opt.pack(fill="x")

        ctk.CTkLabel(
            right,
            text="📝 NOTAS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", padx=15, pady=(15, 5))
        self.notes_e = ctk.CTkEntry(
            right,
            height=80,
            text_color=TEXTO_MOV_FIELD,
            fg_color=FONDO_MULTISELECT,
            font=ctk.CTkFont(size=14),
            placeholder_text_color=TEXTO_PLACEHOLDER,
            border_width=1,
        )
        self.notes_e.pack(fill="x", padx=15, pady=(0, 15))

        btns = ctk.CTkFrame(main, fg_color=FONDO_BTN_PIE)
        btns.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(
            btns,
            text="✓ REGISTRAR MOVIMIENTO",
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
            hover_color=HOVER_MOV_CANCEL,
            text_color="white",
            height=45,
            command=self.destroy,
        ).pack(side="left", expand=True, padx=5)

        self.grab_set()

    def _on_type_change(self, type_):
        if type_ == "salida":
            self._emp_frame.pack(fill="x", pady=(0, 10))
            self._veh_frame.pack(fill="x", pady=(0, 10))
            products = [dict(p) for p in self._all_products if p["quantity"] > 0]
            label_fn = lambda p: (
                f"{p['name']} (disp: {p['quantity']}) - {(p['barcode'] or '')}"
            )
        else:
            self._emp_frame.pack_forget()
            self._veh_frame.pack_forget()
            products = [dict(p) for p in get_products_pending_return()]
            label_fn = lambda p: (
                f"{p['name']} (pend: {p['available']}) - {(p['barcode'] or '')}"
            )

        self._prod_select._items = products
        self._prod_select._item_label = label_fn
        self._prod_select._selected = set()
        self._prod_select._quantities = {}
        self._prod_select._filter_items()

    def _save(self):
        type_ = self.type_opt.get()
        selected_products = self._prod_select.get_selected()
        if not selected_products:
            messagebox.showwarning(
                "Aviso", "Selecciona al menos un producto.", parent=self
            )
            return

        selected_employees = self._emp_select.get_selected()
        if type_ == "salida" and not selected_employees:
            messagebox.showwarning(
                "Aviso", "Selecciona al menos un empleado para salida.", parent=self
            )
            return

        notes = self.notes_e.get().strip()

        employees_to_assign = selected_employees if selected_employees else [None]
        for product_id, quantity in selected_products:
            if quantity < 1:
                continue
            for employee_id in employees_to_assign:
                create_movement(
                    type_,
                    product_id,
                    employee_id,
                    self.current_user["id"],
                    quantity,
                    notes,
                    warehouse_id=self.warehouse_id,
                )

        self.on_save()
        self.destroy()

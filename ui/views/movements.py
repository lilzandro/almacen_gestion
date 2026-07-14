import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog

from ui.colors import *
from ui.widgets import make_table, clear_tree, setup_treeview_style, center_dialog
from database.repository import (
    get_all_movements,
    get_all_employees,
    get_all_vehicles,
    get_movement_available_products,
    get_products_pending_return_grouped,
    get_serials_pending_return,
    create_grouped_movement,
    create_quantity_return,
    return_serial,
    update_movement,
    delete_movement,
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
            ("actions", "Acciones", 120),
        ]
        self.tree = make_table(tf, cols, bg_color="white")
        self.tree.bind("<Double-1>", self._on_double_click)
        self._context_menu = tk.Menu(self, tearoff=0, font=ctk.CTkFont(size=13))
        self._context_menu.add_command(label="✎ Editar", command=self._edit_selected)
        self._context_menu.add_separator()
        self._context_menu.add_command(
            label="✕ Eliminar", foreground="#E04F16", command=self._delete_selected
        )
        self.tree.bind("<Button-3>", self._on_right_click)

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
                    "✎ ✕",
                ),
            )

    def _selected_movement(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un movimiento.")
            return None
        return int(sel[0])

    def _on_double_click(self, event):
        self._edit_selected()

    def _on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self._context_menu.post(event.x_root, event.y_root)

    def _edit_selected(self):
        mid = self._selected_movement()
        if mid is None:
            return
        rows = get_all_movements()
        mov = next((r for r in rows if r["id"] == mid), None)
        if not mov:
            return
        _MovementEditDialog(
            self,
            movement=dict(mov),
            current_user=self.current_user,
            on_save=lambda: self.refresh(),
        )

    def _delete_selected(self):
        mid = self._selected_movement()
        if mid is None:
            return
        from ui.widgets import ConfirmDialog

        d = ConfirmDialog(
            self,
            "Eliminar movimiento",
            "¿Eliminar este movimiento?\nEl stock del producto se reajustará automáticamente.",
            is_danger=True,
        )
        self.wait_window(d)
        if d.result:
            try:
                delete_movement(mid)
                self.refresh()
                messagebox.showinfo("Éxito", "Movimiento eliminado y stock reajustado.")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _register_dialog(self):
        def _on_save():
            self.refresh()
            if self.app:
                pv = self.app._views.get("products")
                if pv:
                    pv.refresh(force=True)
        _MovementDialog(
            self,
            current_user=self.current_user,
            on_save=_on_save,
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

        self._employees = get_all_employees()
        self._vehicles = get_all_vehicles()
        self._group_items = {}

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
            text="Selecciona el grupo y escribe la cantidad deseada",
            font=ctk.CTkFont(size=11),
            text_color=TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=15, pady=(0, 5))

        # Build grouped product list
        grouped = get_movement_available_products(warehouse_id=warehouse_id)
        products = []
        for g in grouped:
            d = dict(g)
            d["key"] = f"{g['name']}||{g['brand']}"
            self._group_items[d["key"]] = d
            products.append(d)
        self._prod_select = _SearchableMultiSelect(
            left,
            products,
            "key",
            lambda g: f"{g['name']} ({g.get('brand', '') or '—'}) — disp: {g['available']} {g['unit']}",
            placeholder="Buscar producto...",
            fg_color=FONDO_MULTISELECT,
            show_quantity=True,
        )
        self._prod_select.pack(fill="both", expand=True, padx=15, pady=(0, 15))

        # Seriales pendientes de devolución (oculto por defecto)
        self._serial_frame = ctk.CTkFrame(left, fg_color="transparent")
        ctk.CTkLabel(
            self._serial_frame,
            text="SERIALES EN SALIDA",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", pady=(10, 5))
        ctk.CTkLabel(
            self._serial_frame,
            text="Marca los seriales a devolver",
            font=ctk.CTkFont(size=11),
            text_color=TEXTO_SECUNDARIO,
        ).pack(anchor="w")
        self._serial_inner = ctk.CTkScrollableFrame(
            self._serial_frame, fg_color="white", height=200
        )
        self._serial_inner.pack(fill="both", expand=True, pady=(5, 0))
        self._serial_checkvars = {}
        self._serial_ids = {}
        self._serial_frame.pack_forget()  # oculto hasta seleccionar devolucion

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
            self._serial_frame.pack_forget()
            grouped = get_movement_available_products(warehouse_id=self.warehouse_id)
        else:
            self._emp_frame.pack_forget()
            self._veh_frame.pack_forget()
            self._serial_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
            self._load_serials_pending()
            grouped = get_products_pending_return_grouped(warehouse_id=self.warehouse_id)

        products = []
        self._group_items = {}
        for g in grouped:
            d = dict(g)
            d["key"] = f"{g['name']}||{g['brand']}"
            self._group_items[d["key"]] = d
            products.append(d)

        metric = "available" if type_ == "salida" else "pending"
        label_fn = lambda g, m=metric: (
            f"{g['name']} ({g.get('brand', '') or '—'}) — {m}: {g.get(m, 0)} {g['unit']}"
        )
        self._prod_select._items = products
        self._prod_select._item_label = label_fn
        self._prod_select._item_key = "key"
        self._prod_select._selected = set()
        self._prod_select._quantities = {}
        self._prod_select._filter_items()

    def _load_serials_pending(self):
        """Carga la lista de seriales en estado 'no disponible' (pendientes de devolucion)."""
        for w in self._serial_inner.winfo_children():
            w.destroy()
        self._serial_checkvars = {}
        self._serial_ids = {}

        serials = [dict(s) for s in get_serials_pending_return(warehouse_id=self.warehouse_id)]
        if not serials:
            ctk.CTkLabel(
                self._serial_inner,
                text="No hay seriales pendientes de devolución.",
                font=ctk.CTkFont(size=13),
                text_color=TEXTO_SECUNDARIO,
            ).pack(pady=20)
            return

        for s in serials:
            row = ctk.CTkFrame(self._serial_inner, fg_color="white")
            row.pack(fill="x", pady=1)

            var = ctk.BooleanVar()
            chk = ctk.CTkCheckBox(
                row,
                text=f"{s['name']} ({s.get('brand', '') or '—'}) — S/N: {s['serial']}",
                variable=var,
                font=ctk.CTkFont(size=12),
                checkbox_height=20, checkbox_width=20,
            )
            chk.pack(side="left", padx=6, pady=4)
            if s.get("salida_fecha"):
                ctk.CTkLabel(
                    row,
                    text=f"Salida: {s['salida_fecha'][:10]}",
                    font=ctk.CTkFont(size=11),
                    text_color=TEXTO_SECUNDARIO,
                ).pack(side="right", padx=8)

            self._serial_checkvars[s["id"]] = var
            self._serial_ids[s["id"]] = s

    def _save(self):
        type_ = self.type_opt.get()
        notes = self.notes_e.get().strip()
        selected_employees = self._emp_select.get_selected()

        if type_ == "salida":
            if not selected_employees:
                messagebox.showwarning(
                    "Aviso", "Selecciona al menos un empleado para salida.", parent=self
                )
                return
            selected_raw = self._prod_select.get_selected()
            if not selected_raw:
                messagebox.showwarning(
                    "Aviso", "Selecciona al menos un producto.", parent=self
                )
                return
            for key, quantity in selected_raw:
                if quantity < 1:
                    continue
                g = self._group_items.get(key)
                if not g:
                    continue
                name = g["name"]
                brand = g.get("brand", "")
                for employee_id in selected_employees:
                    try:
                        create_grouped_movement(
                            type_, name, brand, quantity,
                            employee_id, self.current_user["id"], notes,
                            warehouse_id=self.warehouse_id,
                        )
                    except ValueError as e:
                        messagebox.showerror("Error", str(e), parent=self)
                        return
        else:
            # Devolucion: procesar cantidad + seriales
            selected_raw = self._prod_select.get_selected()
            has_qty = bool(selected_raw)
            has_serials = any(
                v.get() for v in self._serial_checkvars.values()
            ) if hasattr(self, "_serial_checkvars") else False

            if not has_qty and not has_serials:
                messagebox.showwarning(
                    "Aviso",
                    "Selecciona productos por cantidad o marca seriales a devolver.",
                    parent=self,
                )
                return

            if has_qty:
                for key, quantity in selected_raw:
                    if quantity < 1:
                        continue
                    g = self._group_items.get(key)
                    if not g:
                        continue
                    try:
                        create_quantity_return(
                            g["name"], g.get("brand", ""), quantity,
                            self.current_user["id"], notes,
                            warehouse_id=self.warehouse_id,
                        )
                    except ValueError as e:
                        messagebox.showerror("Error", str(e), parent=self)
                        return

            if has_serials:
                for pid, var in self._serial_checkvars.items():
                    if var.get():
                        try:
                            return_serial(
                                pid, self.current_user["id"], notes,
                                warehouse_id=self.warehouse_id,
                            )
                        except ValueError as e:
                            messagebox.showerror("Error", str(e), parent=self)
                            return

        self.on_save()
        self.destroy()


class _MovementEditDialog(ctk.CTkToplevel):
    def __init__(self, parent, movement, current_user, on_save):
        super().__init__(parent)
        self.title("Editar Movimiento")
        self.geometry("500x480")
        self.resizable(False, False)
        self.configure(fg_color=BLANCO_CALIDO)
        self.transient(parent)
        self._movement = movement
        self._current_user = current_user
        self.on_save = on_save
        self._employees = get_all_employees()

        header = ctk.CTkFrame(self, fg_color=AZUL_NOCHE, height=60)
        header.pack(fill="x")
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="✎ EDITAR MOVIMIENTO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(pady=15)

        body = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        def _lbl(text):
            ctk.CTkLabel(
                body, text=text, anchor="w", text_color=AZUL_NOCHE,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(fill="x", padx=14, pady=(10, 2))

        _lbl("Producto")
        info = ctk.CTkFrame(body, fg_color=FONDO_SUBHEADER, corner_radius=6)
        info.pack(fill="x", padx=14)
        ctk.CTkLabel(
            info, text=movement["product"],
            font=ctk.CTkFont(size=13), text_color=GRIS_AZULADO,
        ).pack(side="left", padx=12, pady=8)

        _lbl("Tipo")
        self.type_opt = ctk.CTkOptionMenu(
            body, height=36,
            font=ctk.CTkFont(size=13), text_color="white",
            button_color=AZUL_MARINO, button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO, dropdown_font=ctk.CTkFont(size=13),
            values=["entrada", "salida", "devolucion", "asignacion"],
        )
        self.type_opt.set(movement["type"])
        self.type_opt.pack(fill="x", padx=14)

        _lbl("Empleado")
        emp_names = ["Ninguno"] + [
            f"{e['name']} ({e['cedula']})" for e in self._employees
        ]
        self.emp_opt = ctk.CTkOptionMenu(
            body, height=36,
            font=ctk.CTkFont(size=13), text_color="white",
            button_color=AZUL_MARINO, button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO, dropdown_font=ctk.CTkFont(size=13),
            values=emp_names,
        )
        current_emp = next(
            (f"{e['name']} ({e['cedula']})" for e in self._employees
             if e["id"] == movement.get("employee_id")),
            "Ninguno",
        )
        self.emp_opt.set(current_emp)
        self.emp_opt.pack(fill="x", padx=14)

        _lbl("Cantidad")
        self.qty_e = ctk.CTkEntry(
            body, height=36,
            text_color=AZUL_NOCHE, fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=13), border_width=1, border_color=AZUL_MARINO,
        )
        self.qty_e.insert(0, str(movement["quantity"] or 1))
        self.qty_e.pack(fill="x", padx=14)

        _lbl("Notas")
        self.notes_e = ctk.CTkEntry(
            body, height=80,
            text_color=AZUL_NOCHE, fg_color=BLANCO_CALIDO,
            font=ctk.CTkFont(size=13), border_width=1, border_color=AZUL_MARINO,
            placeholder_text_color=TEXTO_PLACEHOLDER,
        )
        self.notes_e.insert(0, movement.get("notes") or "")
        self.notes_e.pack(fill="x", padx=14, pady=(0, 10))

        btns = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        btns.pack(fill="x", padx=16, pady=(0, 12))
        ctk.CTkButton(
            btns, text="✓ GUARDAR", height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=AZUL_MARINO, hover_color=AZUL_NOCHE, text_color="white",
            command=self._save,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            btns, text="✕ CANCELAR", height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=NARANJA_INTENSO, hover_color=HOVER_NARANJA_INT,
            text_color="white",
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True)

        center_dialog(self)
        self.after(50, self.grab_set)

    def _save(self):
        try:
            qty = int(self.qty_e.get().strip() or 1)
        except ValueError:
            messagebox.showwarning("Aviso", "Cantidad inválida.", parent=self)
            return
        emp_text = self.emp_opt.get()
        emp_id = None
        if emp_text != "Ninguno":
            emp_id = next(
                (e["id"] for e in self._employees
                 if f"{e['name']} ({e['cedula']})" == emp_text),
                None,
            )
        try:
            update_movement(
                self._movement["id"],
                self.type_opt.get(),
                emp_id,
                qty,
                self.notes_e.get().strip(),
            )
        except ValueError as e:
            messagebox.showerror("Error", str(e), parent=self)
            return
        self.on_save()
        self.destroy()

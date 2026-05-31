import customtkinter as ctk
from ui.animations import dialog_open
from ui.widgets import (
    clear_tree,
    setup_treeview_style,
    center_dialog,
    MessageDialog,
    ConfirmDialog,
)
from database.repository import (
    get_all_products,
    get_products_grouped,
    get_units_by_model,
    get_all_suppliers,
    create_product,
    update_product,
    delete_product,
    get_product_by_barcode,
    create_movement,
    bulk_create_products,
)


class ProductsView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color="#F7F5FB")
        self.current_user = current_user
        self.app = app
        setup_treeview_style()
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        # Corporate header - Deep blue background
        hdr = ctk.CTkFrame(self, fg_color="#031D44")
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        # Title section
        title_section = ctk.CTkFrame(hdr, fg_color="transparent")
        title_section.pack(side="left", fill="both", padx=15, pady=12)

        ctk.CTkLabel(
            title_section,
            text="Gestión de Productos",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#F7F5FB",
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_section,
            text="Administra el inventario del almacén",
            font=ctk.CTkFont(size=14),
            text_color="#8ECAE6",
        ).pack(anchor="w", pady=(2, 5))

        # Action buttons section
        action_section = ctk.CTkFrame(hdr, fg_color="transparent")
        action_section.pack(side="right", fill="both", padx=15, pady=12)

        ctk.CTkButton(
            action_section,
            text="+ Nuevo Producto",
            height=32,
            command=self._add_dialog,
            fg_color="#F58A07",
            hover_color="#D67A00",
            text_color="white",
            font=ctk.CTkFont(size=14, weight="normal"),
            border_width=0,
        ).pack(side="right")

        # Search and filters bar
        sf = ctk.CTkFrame(
            self, fg_color="#FFFFFF", border_width=1, border_color="#084887"
        )
        sf.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        sf.pack_propagate(False)
        sf.configure(height=55)

        ctk.CTkLabel(
            sf, text="🔍 Buscar:", font=ctk.CTkFont(size=14), text_color="#084887"
        ).pack(side="left", padx=(12, 4))

        self._search = ctk.StringVar()
        self._search.trace_add("write", lambda *_: self.refresh())
        self._search_entry = ctk.CTkEntry(
            sf,
            textvariable=self._search,
            placeholder_text="nombre, código, serie o marca...",
            border_width=0,
            fg_color="transparent",
            text_color="#031D44",
            placeholder_text_color="#9CA3AF",
            font=ctk.CTkFont(size=15),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        # Filtros de estado
        self._status_filter = ctk.StringVar(value="todos")
        self._filter_btns = {}
        filter_defs = [
            ("todos",         "Todos",          "#084887", "#031D44"),
            ("disponible",    "Disponible",     "#219EBC", "#126782"),
            ("no disponible", "No Disponible",  "#FFB703", "#E6A500"),
        ]
        for val, label, fg, hover in filter_defs:
            btn = ctk.CTkButton(
                sf, text=label, width=105, height=28,
                fg_color=fg, hover_color=hover, text_color="white",
                font=ctk.CTkFont(size=12),
                command=lambda v=val: self.set_status_filter(v),
            )
            btn.pack(side="right", padx=(0, 6))
            self._filter_btns[val] = btn
        self._update_filter_buttons()

        # Table container
        tf = ctk.CTkFrame(
            self,
            fg_color="#FFFFFF",
            border_width=2,
            border_color="#084887",
        )
        tf.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        self.tree = self._make_grouped_table(tf)
        self.tree.bind("<Double-Button-1>", lambda e: self._on_row_double_click())

        # Action buttons bar
        af = ctk.CTkFrame(self, fg_color="transparent")
        af.grid(row=3, column=0, sticky="ew", padx=20, pady=(10, 15))

        ctk.CTkButton(
            af,
            text="Escanear",
            width=120,
            height=32,
            command=self._scan_barcode,
            fg_color="#219EBC",
            hover_color="#126782",
            text_color="white",
            font=ctk.CTkFont(size=14),
            border_width=0,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            af,
            text="Editar",
            width=100,
            height=32,
            command=self._edit_dialog,
            fg_color="#084887",
            hover_color="#031D44",
            text_color="white",
            font=ctk.CTkFont(size=14),
            border_width=0,
        ).pack(side="left", padx=4)

        if self.current_user["role"] == "admin":
            ctk.CTkButton(
                af,
                text="Eliminar",
                width=100,
                height=32,
                fg_color="#F58A07",
                hover_color="#D67A00",
                text_color="white",
                font=ctk.CTkFont(size=14),
                border_width=0,
                command=self._delete,
            ).pack(side="left", padx=4)

    def set_status_filter(self, status: str):
        self._status_filter.set(status)
        self._update_filter_buttons()
        self.refresh()

    def _update_filter_buttons(self):
        active = self._status_filter.get()
        styles = {
            "todos":         ("#084887", "#031D44"),
            "disponible":    ("#219EBC", "#126782"),
            "no disponible": ("#FFB703", "#E6A500"),
        }
        for val, btn in self._filter_btns.items():
            fg, hover = styles[val]
            if val == active:
                btn.configure(fg_color=fg, border_width=2, border_color="white",
                              font=ctk.CTkFont(size=12, weight="bold"))
            else:
                btn.configure(fg_color=fg, border_width=0,
                              font=ctk.CTkFont(size=12, weight="normal"))

    def _make_grouped_table(self, parent):
        from tkinter import ttk
        frame = ctk.CTkFrame(parent, fg_color="white", border_color="#084887",
                             border_width=3, corner_radius=2)
        frame.grid(row=0, column=0, sticky="nsew")

        cols = ("brand", "units", "serial", "mac", "status", "supplier")
        tree = ttk.Treeview(frame, columns=cols, show="tree headings",
                            style="Inv.Treeview", selectmode="browse")

        tree.heading("#0",      text="Modelo / Equipo")
        tree.heading("brand",   text="Marca")
        tree.heading("units",   text="Unidades")
        tree.heading("serial",  text="Serial")
        tree.heading("mac",     text="MAC")
        tree.heading("status",  text="Estado")
        tree.heading("supplier",text="Proveedor")

        tree.column("#0",       width=200, minwidth=140, anchor="w")
        tree.column("brand",    width=100, anchor="center")
        tree.column("units",    width=80,  anchor="center")
        tree.column("serial",   width=130, anchor="center")
        tree.column("mac",      width=150, anchor="center")
        tree.column("status",   width=100, anchor="center")
        tree.column("supplier", width=140, anchor="center")

        # Colores de fila para distinguir modelos alternados
        tree.tag_configure("model_even", background="#EAF4FB", font=("Segoe UI", 12, "bold"))
        tree.tag_configure("model_odd",  background="#D6EAF8", font=("Segoe UI", 12, "bold"))
        tree.tag_configure("unit",       background="white",   font=("Segoe UI", 11))

        vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        vsb.grid(row=0, column=1, sticky="ns", pady=1, padx=(0, 1))
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        return tree

    def refresh(self):
        q = self._search.get() if hasattr(self, "_search") else ""
        status = self._status_filter.get() if hasattr(self, "_status_filter") else "todos"
        wh_id = self.app.current_warehouse_id if self.app else None

        # Guardar qué grupos están expandidos para restaurar tras refresh
        expanded = {iid for iid in self.tree.get_children("")
                    if self.tree.item(iid, "open")}

        clear_tree(self.tree)

        groups = get_products_grouped(search=q, status_filter=status, warehouse_id=wh_id)
        for i, g in enumerate(groups):
            model_iid = f"model__{g['name']}__{g['brand']}"
            tag = "model_even" if i % 2 == 0 else "model_odd"
            self.tree.insert(
                "", "end",
                iid=model_iid,
                text=f"  {g['name']}",
                values=(
                    g["brand"],
                    f"{g['unit_count']} uds.",
                    "",
                    "",
                    g["status"],
                    g["supplier_name"],
                ),
                tags=(tag,),
                open=model_iid in expanded,
            )
            units = get_units_by_model(g["name"], g["brand"], wh_id)
            for u in units:
                self.tree.insert(
                    model_iid, "end",
                    iid=str(u["id"]),
                    text="",
                    values=(
                        "",
                        "",
                        u["serial"] or "—",
                        u["mac"] or "—",
                        u["status"],
                        "",
                    ),
                    tags=("unit",),
                )

    def _scan_barcode(self):
        """Abre un diálogo para escanear código de barras"""
        _BarcodeScanDialog(
            self,
            on_scan=self._handle_barcode_scan,
        )

    def _handle_barcode_scan(self, barcode):
        """Maneja el código de barras escaneado"""
        product = get_product_by_barcode(barcode)
        if product:
            # El producto existe, mostrar diálogo de edición rápida
            self.tree.selection_set(product["id"])
            self.tree.focus(product["id"])
            MessageDialog(
                self,
                "Producto encontrado",
                f"Producto: {product['name']}\nCantidad actual: {product['quantity']}\nCódigo: {barcode}",
            )
        else:
            # El producto no existe, abrir diálogo de edición con barcode prellenado
            _ProductDialog(
                self,
                "Registrar Producto",
                initial={"barcode": barcode},
                on_save=lambda d: (self._do_edit_save(d),),
            )

    def _do_edit_save(self, d):
        wh_id = self.app.current_warehouse_id if self.app else None
        pid = create_product(
            d["name"], d["barcode"], d["brand"], d["serial"], d["mac"],
            0, d["supplier_id"], d["unit"], warehouse_id=wh_id,
        )
        if d.get("quantity", 0) > 0:
            create_movement("entrada", pid, None, self.current_user["id"],
                            d["quantity"], "Registro inicial", warehouse_id=wh_id)
        self.refresh()

    def _on_row_double_click(self):
        iid = self.tree.focus()
        if not iid:
            return
        if iid.startswith("model__"):
            # Toggle expand/collapse
            self.tree.item(iid, open=not self.tree.item(iid, "open"))
        else:
            self._edit_dialog()

    def _selected_unit(self):
        """Retorna iid si es una unidad individual, None si es grupo o nada."""
        iid = self.tree.focus()
        if not iid or iid.startswith("model__"):
            MessageDialog(self, "Aviso", "Selecciona una unidad individual (fila hijo).")
            return None
        return iid

    def _selected(self):
        sel = self.tree.focus()
        if not sel:
            MessageDialog(self, "Aviso", "Selecciona un producto.")
        return sel or None

    def _do_add(self, d):
        qty = d["quantity"]
        wh_id = self.app.current_warehouse_id if self.app else None
        product_id = create_product(
            d["name"],
            d["barcode"],
            d["brand"],
            d["serial"],
            d["mac"],
            0,
            d["supplier_id"],
            d["unit"],
            warehouse_id=wh_id,
        )
        if qty > 0:
            create_movement(
                "entrada",
                product_id,
                None,
                self.current_user["id"],
                qty,
                "Registro inicial de producto",
                warehouse_id=wh_id,
            )
        self.refresh()

    def _add_dialog(self):
        _ProductDialog(self, "Registrar Producto", on_save=self._do_bulk_add)

    def _do_bulk_add(self, common, items):
        """common: name/brand/supplier_id/unit. items: lista de {serial, mac}."""
        wh_id = self.app.current_warehouse_id if self.app else None
        payload = [
            {
                "name": common["name"],
                "brand": common.get("brand", ""),
                "serial": item["serial"],
                "mac": item["mac"],
                "supplier_id": common.get("supplier_id"),
                "unit": common.get("unit", "und"),
            }
            for item in items
        ]
        ok, duplicados = bulk_create_products(
            payload,
            user_id=self.current_user["id"],
            warehouse_id=wh_id,
        )
        self.refresh()
        msg = f"{ok} equipo(s) registrado(s)."
        if duplicados:
            msg += f"\nOmitidos: {', '.join(duplicados)}"
        MessageDialog(self, "Alta Masiva", msg)

    def _edit_dialog(self):
        iid = self._selected_unit()
        if not iid:
            return
        # Cargar datos frescos desde BD
        rows = get_all_products()
        prod = next((r for r in rows if str(r["id"]) == str(iid)), None)
        if not prod:
            return
        _ProductDialog(
            self,
            "Editar Producto",
            initial={
                "name":     prod["name"],
                "barcode":  prod["barcode"] or "",
                "brand":    prod["brand"] or "",
                "serial":   prod["serial"] or "",
                "mac":      prod["mac"] or "",
                "quantity": prod["quantity"],
                "unit":     prod["unit"] or "und",
            },
            on_save=lambda d: (
                update_product(
                    int(iid),
                    d["name"], d["barcode"], d["brand"],
                    d["serial"], d["mac"], d["quantity"],
                    d["supplier_id"], d["unit"],
                ),
                self.refresh(),
            ),
        )

    def _delete(self):
        iid = self._selected_unit()
        if not iid:
            return

        product_id = int(iid)
        rows = get_all_products()
        prod = next((r for r in rows if str(r["id"]) == str(iid)), None)
        product_name = prod["name"] if prod else str(iid)

        dialog = ConfirmDialog(
            self,
            "Confirmar Eliminación",
            f"¿Eliminar la unidad '{product_name}' (ID {product_id})?\n"
            "Esta acción NO se puede deshacer.",
            is_danger=True,
        )
        self.wait_window(dialog)

        if dialog.result:
            try:
                delete_product(product_id)
                self.refresh()
                MessageDialog(
                    self,
                    "Éxito",
                    f"El producto '{product_name}' ha sido eliminado.",
                )
            except Exception:
                MessageDialog(
                    self,
                    "Error",
                    "No se pudo eliminar. El producto tiene movimientos registrados.",
                    is_error=True,
                )


class _BarcodeScanDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_scan):
        super().__init__(parent)
        self.title("Escanear Código de Barras")
        self.geometry("400x200")
        self.resizable(False, False)
        self.configure(fg_color="#F7F5FB")
        self.transient(parent)
        self.on_scan = on_scan

        ctk.CTkLabel(
            self,
            text="Escanee o ingrese el código de barras",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#031D44",
        ).pack(pady=(20, 10))

        self.barcode_entry = ctk.CTkEntry(
            self,
            height=50,
            font=ctk.CTkFont(size=20),
            placeholder_text="Código de barras...",
            text_color="#031D44",
        )
        self.barcode_entry.pack(pady=10, padx=20, fill="x")
        self.barcode_entry.focus()

        ctk.CTkButton(
            self,
            text="Aceptar",
            command=self._on_accept,
            fg_color="#219EBC",
            hover_color="#126782",
            text_color="white",
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=10)

        self.barcode_entry.bind("<Return>", lambda e: self._on_accept())
        self.grab_set()
        self.after(1, lambda: dialog_open(self))

    def _center_and_grab(self):
        center_dialog(self)
        self.grab_set()

    def _on_accept(self):
        barcode = self.barcode_entry.get().strip()
        if barcode:
            self.destroy()
            self.on_scan(barcode)


class _ProductDialog(ctk.CTkToplevel):

    def __init__(self, parent, title, on_save, initial=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(True, True)
        self.configure(fg_color="#F7F5FB")
        self.transient(parent)
        self.on_save = on_save
        self._is_add = initial is None
        self._rows = []
        d = initial or {}

        suppliers = get_all_suppliers()
        self._supplier_map = {"Sin proveedor": None}
        self._supplier_map.update({f"{s['name']} (ID:{s['id']})": s["id"] for s in suppliers})
        sup_names = ["Sin proveedor"] + [f"{s['name']} (ID:{s['id']})" for s in suppliers]

        if self._is_add:
            self.geometry("900x660")
            self.minsize(800, 560)
            self._build_add_mode(sup_names)
        else:
            self.geometry("850x600")
            self.minsize(700, 500)
            self._build_edit_mode(sup_names, d)

        self.grab_set()
        self.after(1, lambda: dialog_open(self))

    # ── ADD MODE ──────────────────────────────────────────────────────────────

    def _build_add_mode(self, sup_names):
        def _e(parent, placeholder="", width=0, **kw):
            return ctk.CTkEntry(
                parent, height=34, font=ctk.CTkFont(size=13),
                fg_color="#F7F5FB", border_width=1, border_color="#084887",
                text_color="#031D44", placeholder_text=placeholder,
                **({"width": width} if width else {}), **kw,
            )

        def _lbl(parent, text):
            ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=12, weight="bold"),
                         text_color="#2D3748").grid(sticky="w")

        # Header
        hdr = ctk.CTkFrame(self, fg_color="#031D44", height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="REGISTRAR PRODUCTO",
                     font=ctk.CTkFont(size=20, weight="bold"),
                     text_color="white").pack(side="left", padx=20, pady=14)
        self._counter_lbl = ctk.CTkLabel(hdr, text="1 equipo",
                                         font=ctk.CTkFont(size=13), text_color="#8ECAE6")
        self._counter_lbl.pack(side="right", padx=20)

        # Campos comunes
        cf = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        cf.pack(fill="x", padx=14, pady=(10, 6))
        ctk.CTkLabel(cf, text="DATOS COMUNES",
                     font=ctk.CTkFont(size=11, weight="bold"),
                     text_color="#084887").grid(row=0, column=0, columnspan=6,
                                               sticky="w", padx=14, pady=(8, 4))

        labels = ["Nombre *", "Marca", "Proveedor", "Unidad"]
        for col, lbl in enumerate(labels):
            ctk.CTkLabel(cf, text=lbl, font=ctk.CTkFont(size=12),
                         text_color="#2D3748").grid(row=1, column=col,
                                                    sticky="w", padx=(14 if col == 0 else 4, 4))

        self.name_e = _e(cf, "Router TP-Link...", 210)
        self.name_e.grid(row=2, column=0, padx=(14, 6), pady=(0, 10))

        self.brand_e = _e(cf, "TP-Link...", 140)
        self.brand_e.grid(row=2, column=1, padx=(0, 6), pady=(0, 10))

        self.sup_opt = ctk.CTkOptionMenu(
            cf, height=34, width=180, values=sup_names,
            font=ctk.CTkFont(size=12), text_color="white",
            fg_color="#084887", button_color="#084887", button_hover_color="#031D44",
        )
        self.sup_opt.grid(row=2, column=2, padx=(0, 6), pady=(0, 10))

        self.unit_opt = ctk.CTkOptionMenu(
            cf, height=34, width=90,
            values=["und", "m", "cm", "kg", "g", "L", "ml", "rollo", "caja", "par"],
            font=ctk.CTkFont(size=12), text_color="white",
            fg_color="#084887", button_color="#084887", button_hover_color="#031D44",
        )
        self.unit_opt.grid(row=2, column=3, padx=(0, 14), pady=(0, 10))

        # Fila: cantidad + botón generar
        ctk.CTkLabel(cf, text="Cantidad de equipos",
                     font=ctk.CTkFont(size=12), text_color="#2D3748",
                     ).grid(row=3, column=0, sticky="w", padx=(14, 4), pady=(4, 0))
        ctk.CTkLabel(cf, text="(genera filas automáticamente)",
                     font=ctk.CTkFont(size=11), text_color="#8ECAE6",
                     ).grid(row=3, column=1, columnspan=2, sticky="w", padx=(0, 4), pady=(4, 0))

        gen_row = ctk.CTkFrame(cf, fg_color="transparent")
        gen_row.grid(row=4, column=0, columnspan=4, sticky="w", padx=(14, 14), pady=(4, 10))

        self._qty_gen_e = ctk.CTkEntry(
            gen_row, width=70, height=34, font=ctk.CTkFont(size=13),
            fg_color="#F7F5FB", border_width=1, border_color="#084887",
            text_color="#031D44", placeholder_text="ej: 5",
        )
        self._qty_gen_e.pack(side="left", padx=(0, 8))
        self._qty_gen_e.bind("<Return>", lambda e: self._generate_rows())

        ctk.CTkButton(
            gen_row, text="▶ Generar filas", height=34, width=140,
            fg_color="#219EBC", hover_color="#1976A1", text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._generate_rows,
        ).pack(side="left")

        # Cabecera tabla
        th = ctk.CTkFrame(self, fg_color="#084887", height=32, corner_radius=0)
        th.pack(fill="x", padx=14)
        th.pack_propagate(False)
        for col_txt, w in [("#", 36), ("Serial", 260), ("MAC  (AA-BB-CC-DD-EE-FF)", 280), ("", 44)]:
            ctk.CTkLabel(th, text=col_txt, width=w, anchor="w",
                         font=ctk.CTkFont(size=11, weight="bold"),
                         text_color="white").pack(side="left", padx=6)

        # Filas scrollables
        self._scroll = ctk.CTkScrollableFrame(self, fg_color="#EFEFEF", corner_radius=0)
        self._scroll.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        # Footer
        footer = ctk.CTkFrame(self, fg_color="#F7F5FB")
        footer.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkButton(footer, text="+ Agregar equipo", width=150, height=34,
                      fg_color="#219EBC", hover_color="#1976A1", text_color="white",
                      font=ctk.CTkFont(size=13), command=self._add_row,
                      ).pack(side="left")
        ctk.CTkButton(footer, text="✕ Cancelar", width=120, height=34,
                      fg_color="#FB8500", hover_color="#E67600", text_color="white",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self.destroy).pack(side="right", padx=(8, 0))
        ctk.CTkButton(footer, text="✓ Guardar", width=140, height=34,
                      fg_color="#084887", hover_color="#031D44", text_color="white",
                      font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._save_add).pack(side="right")

        self._add_row()

    def _generate_rows(self):
        try:
            n = int(self._qty_gen_e.get().strip())
        except ValueError:
            return
        if n < 1 or n > 200:
            MessageDialog(self, "Aviso", "Cantidad debe ser entre 1 y 200.")
            return
        # Limpiar filas existentes
        for r in list(self._rows):
            r["frame"].destroy()
        self._rows.clear()
        # Crear N filas nuevas
        for _ in range(n):
            self._add_row()

    def _add_row(self):
        idx = len(self._rows) + 1
        rf = ctk.CTkFrame(self._scroll, fg_color="white", corner_radius=6, height=42)
        rf.pack(fill="x", pady=2)
        rf.pack_propagate(False)

        ctk.CTkLabel(rf, text=str(idx), width=36,
                     font=ctk.CTkFont(size=13), text_color="#084887").pack(side="left", padx=4)

        serial_e = ctk.CTkEntry(rf, width=260, height=30, font=ctk.CTkFont(size=13),
                                fg_color="#F7F5FB", border_width=1, border_color="#084887",
                                text_color="#031D44", placeholder_text="SN-XXXXXXXXXX")
        serial_e.pack(side="left", padx=(0, 6))

        mac_var = ctk.StringVar()
        _upd = [False]

        def _fmt(*_):
            if _upd[0]:
                return
            raw = mac_var.get()
            clean = "".join(c for c in raw if c.isalnum())[:12].upper()
            _upd[0] = True
            mac_var.set("-".join(clean[i:i+2] for i in range(0, len(clean), 2)))
            _upd[0] = False

        mac_var.trace_add("write", _fmt)
        mac_e = ctk.CTkEntry(rf, width=260, height=30, font=ctk.CTkFont(size=13),
                             fg_color="#F7F5FB", border_width=1, border_color="#084887",
                             text_color="#031D44", textvariable=mac_var,
                             placeholder_text="AA-BB-CC-DD-EE-FF")
        mac_e.pack(side="left", padx=(0, 6))

        row = {"frame": rf, "serial": serial_e, "mac_var": mac_var}
        self._rows.append(row)

        ctk.CTkButton(rf, text="✕", width=30, height=28,
                      fg_color="#FB8500", hover_color="#E67600", text_color="white",
                      font=ctk.CTkFont(size=11),
                      command=lambda r=row: self._remove_row(r)).pack(side="left")
        self._update_counter()

    def _remove_row(self, row):
        if len(self._rows) <= 1:
            return
        row["frame"].destroy()
        self._rows.remove(row)
        for i, r in enumerate(self._rows, 1):
            r["frame"].winfo_children()[0].configure(text=str(i))
        self._update_counter()

    def _update_counter(self):
        n = len(self._rows)
        self._counter_lbl.configure(text=f"{n} equipo{'s' if n != 1 else ''}")

    def _save_add(self):
        import re
        name = self.name_e.get().strip()
        if not name:
            MessageDialog(self, "Aviso", "El nombre es obligatorio.")
            return
        if not re.match(r"^[a-zA-Z0-9\s\-_.,áéíóúÁÉÍÓÚÑñ]+$", name):
            MessageDialog(self, "Aviso", "Nombre con caracteres inválidos.")
            return
        brand = self.brand_e.get().strip()

        items = []
        seen_serials = set()
        for i, r in enumerate(self._rows, 1):
            serial = r["serial"].get().strip()
            mac = r["mac_var"].get().strip()
            if not serial and not mac:
                continue
            if mac and not re.match(r"^([A-Za-z0-9]{2}[:\-]){5}[A-Za-z0-9]{2}$", mac):
                MessageDialog(self, "Aviso",
                              f"Fila {i}: MAC inválida.\nUsa formato AA-BB-CC-DD-EE-FF")
                return
            if serial and serial in seen_serials:
                MessageDialog(self, "Aviso", f"Fila {i}: Serial '{serial}' duplicado.")
                return
            if serial:
                seen_serials.add(serial)
            items.append({"serial": serial, "mac": mac.upper() if mac else ""})

        if not items:
            MessageDialog(self, "Aviso", "Completa al menos una fila con serial o MAC.")
            return

        common = {
            "name": name,
            "brand": brand,
            "supplier_id": self._supplier_map.get(self.sup_opt.get()),
            "unit": self.unit_opt.get(),
        }
        self.destroy()
        self.on_save(common, items)

    # ── EDIT MODE ─────────────────────────────────────────────────────────────

    def _build_edit_mode(self, sup_names, d):
        main = ctk.CTkFrame(self, fg_color="#F7F5FB")
        main.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main, fg_color="#031D44", height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        ctk.CTkLabel(header, text="EDITAR PRODUCTO",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color="white").pack(pady=15)

        content = ctk.CTkFrame(main, fg_color="#F7F5FB")
        content.pack(fill="both", expand=True, padx=20)

        left = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))
        right = ctk.CTkFrame(content, fg_color="white", corner_radius=10)
        right.pack(side="right", fill="both", expand=True, padx=(10, 0))

        def _lbl(parent, text, pady=(10, 0)):
            ctk.CTkLabel(parent, text=text, anchor="w", text_color="#031D44",
                         font=ctk.CTkFont(size=14)).pack(fill="x", padx=15, pady=(pady[0], 0))

        def _entry(parent, val=""):
            e = ctk.CTkEntry(parent, height=38, text_color="#031D44", fg_color="#F7F5FB",
                             font=ctk.CTkFont(size=14), border_width=1, border_color="#084887")
            if val:
                e.insert(0, val)
            e.pack(fill="x", padx=15)
            return e

        ctk.CTkLabel(left, text="DATOS BÁSICOS",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#031D44").pack(anchor="w", padx=15, pady=(15, 10))
        _lbl(left, "Nombre *", (5, 0))
        self.name_e = _entry(left, d.get("name", ""))
        _lbl(left, "Código de Barras")
        self.barcode_e = _entry(left, d.get("barcode", ""))
        _lbl(left, "Marca")
        self.brand_e = _entry(left, d.get("brand", ""))
        _lbl(left, "Serial")
        self.serial_e = _entry(left, d.get("serial", ""))

        ctk.CTkLabel(right, text="IDENTIFICADORES",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#031D44").pack(anchor="w", padx=15, pady=(15, 10))
        _lbl(right, "MAC", (5, 0))

        self._mac_var = ctk.StringVar()
        self._mac_upd = False

        def _fmt_mac(*_):
            if self._mac_upd:
                return
            raw = self._mac_var.get()
            clean = "".join(c for c in raw if c.isalnum())[:12].upper()
            self._mac_upd = True
            self._mac_var.set("-".join(clean[i:i+2] for i in range(0, len(clean), 2)))
            self._mac_upd = False
            self.mac_e.after(1, lambda: self.mac_e._entry.icursor("end"))

        self._mac_var.trace_add("write", _fmt_mac)
        self.mac_e = ctk.CTkEntry(right, height=38, text_color="#031D44", fg_color="#F7F5FB",
                                  font=ctk.CTkFont(size=14), border_width=1,
                                  border_color="#084887", textvariable=self._mac_var)
        if d.get("mac"):
            self._mac_var.set(d["mac"])
        self.mac_e.pack(fill="x", padx=15)

        qr = ctk.CTkFrame(right, fg_color="transparent")
        qr.pack(fill="x", padx=15, pady=(15, 0))
        qr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(qr, text="CANTIDAD", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#031D44").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(qr, text="UNIDAD", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#031D44").grid(row=0, column=1, sticky="w", padx=(10, 0))
        self.quantity_e = ctk.CTkEntry(qr, height=38, text_color="#031D44", fg_color="#F7F5FB",
                                       font=ctk.CTkFont(size=14), border_width=1,
                                       border_color="#084887", width=100)
        self.quantity_e.insert(0, d.get("quantity", "0"))
        self.quantity_e.grid(row=1, column=0, sticky="w")
        self.unit_opt = ctk.CTkOptionMenu(
            qr, height=38, width=110, font=ctk.CTkFont(size=14),
            values=["und", "m", "cm", "kg", "g", "L", "ml", "rollo", "caja", "par"],
            text_color="white", button_color="#084887", button_hover_color="#031D44",
            fg_color="#084887", dropdown_font=ctk.CTkFont(size=14),
        )
        self.unit_opt.set(d.get("unit", "und"))
        self.unit_opt.grid(row=1, column=1, sticky="w", padx=(10, 0))

        ctk.CTkLabel(right, text="PROVEEDOR",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color="#031D44").pack(anchor="w", padx=15, pady=(15, 0))
        self.sup_opt = ctk.CTkOptionMenu(
            right, height=38, font=ctk.CTkFont(size=14), values=sup_names,
            text_color="white", button_color="#084887", button_hover_color="#031D44",
            fg_color="#084887", dropdown_font=ctk.CTkFont(size=14),
        )
        self.sup_opt.pack(fill="x", padx=15)

        btns = ctk.CTkFrame(main, fg_color="#F7F5FB")
        btns.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(btns, text="✓ GUARDAR PRODUCTO",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save_edit, fg_color="#084887", hover_color="#031D44",
                      text_color="white", height=45).pack(side="left", expand=True, padx=5)
        ctk.CTkButton(btns, text="✕ CANCELAR",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      fg_color="#FB8500", hover_color="#D67A00", text_color="white",
                      height=45, command=self.destroy).pack(side="left", expand=True, padx=5)

    def _save_edit(self):
        import re
        name = self.name_e.get().strip()
        if not name:
            MessageDialog(self, "Aviso", "El nombre es obligatorio.")
            return
        if not re.match(r"^[a-zA-Z0-9\s\-_.,áéíóúÁÉÍÓÚÑñ]+$", name):
            MessageDialog(self, "Aviso", "Nombre con caracteres inválidos.")
            return
        barcode = self.barcode_e.get().strip()
        if barcode and not re.match(r"^[a-zA-Z0-9\-]+$", barcode):
            MessageDialog(self, "Aviso", "Código de barras inválido.")
            return
        brand = self.brand_e.get().strip()
        if brand and not re.match(r"^[a-zA-Z0-9\s\-]+$", brand):
            MessageDialog(self, "Aviso", "Marca inválida.")
            return
        serial = self.serial_e.get().strip()
        if serial and not re.match(r"^[a-zA-Z0-9\-]+$", serial):
            MessageDialog(self, "Aviso", "Serial inválido.")
            return
        mac = self.mac_e.get().strip()
        if mac and not re.match(r"^([A-Za-z0-9]{2}[:-]){5}([A-Za-z0-9]{2})$", mac):
            MessageDialog(self, "Aviso",
                          "MAC inválida (formato: XX:XX:XX:XX:XX:XX o XX-XX-XX-XX-XX-XX).")
            return
        try:
            quantity = int(self.quantity_e.get() or 0)
        except ValueError:
            MessageDialog(self, "Error", "Cantidad debe ser numérica.")
            return
        if quantity < 0:
            MessageDialog(self, "Aviso", "La cantidad no puede ser negativa.")
            return
        self.on_save({
            "name": name, "barcode": barcode, "brand": brand,
            "serial": serial, "mac": mac.upper() if mac else "",
            "quantity": quantity, "unit": self.unit_opt.get(),
            "supplier_id": self._supplier_map.get(self.sup_opt.get()),
        })
        self.destroy()

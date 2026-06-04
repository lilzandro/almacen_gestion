import tkinter as tk
import customtkinter as ctk
from ui.animations import dialog_open
from ui.colors import (
    AZUL_NOCHE,
    AZUL_MARINO,
    AZUL_CERULEO,
    AZUL_CIELO,
    BLANCO_CALIDO,
    AMARILLO_AMBAR,
    NARANJA_INTENSO,
    GRIS_AZULADO,
    NARANJA_SELECCION,
    HOVER_CERULEO,
    HOVER_MARINO,
    HOVER_AMBAR,
    HOVER_FILTRO_DISP,
    HOVER_NARANJA_SEL,
    HOVER_NARANJA_INT,
    DISPONIBLE_BG,
    DISPONIBLE_FG,
    NO_DISPONIBLE_BG,
    NO_DISPONIBLE_FG,
    INACTIVO_BG,
    INACTIVO_FG,
    STOCK_DISP_BG,
    STOCK_DISP_FG,
    STOCK_BAJO_BG,
    STOCK_BAJO_FG,
    STOCK_AGOTADO_BG,
    STOCK_AGOTADO_FG,
    BLANCO,
    FONDO_SCROLL,
    FONDO_ROW_PAR,
    FONDO_ROW_IMPAR,
    FONDO_EXPANDIDO,
    FONDO_SUBHEADER,
    FONDO_BADGE,
    TEXTO_SECUNDARIO,
    TEXTO_PLACEHOLDER,
    TEXTO_MODELO,
    SELECCION_BG,
    HOVER_FILA_BG,
    CHEVRON_HOVER,
    FILTRO_TODOS_FG,
    FILTRO_TODOS_HOVER,
    FILTRO_DISP_FG,
    FILTRO_DISP_HOVER,
    FILTRO_NO_DISP_FG,
    FILTRO_NO_DISP_HOVER,
)
from ui.widgets import (
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
    update_product_unit,
    update_product_group,
    delete_product,
    delete_product_group,
    get_product_by_barcode,
    create_movement,
    bulk_create_products,
)

_PILL_COLORS = {
    "disponible": (DISPONIBLE_BG, DISPONIBLE_FG),
    "no disponible": (NO_DISPONIBLE_BG, NO_DISPONIBLE_FG),
    "inactivo": (INACTIVO_BG, INACTIVO_FG),
}
_STATUS_LABELS = {
    "disponible": "Disponible",
    "no disponible": "No Disponible",
    "inactivo": "Inactivo",
}

_STOCK_PILL_COLORS = {
    "disponible": (STOCK_DISP_BG, STOCK_DISP_FG, "Disponible"),
    "bajo": (STOCK_BAJO_BG, STOCK_BAJO_FG, "Stock Bajo"),
    "agotado": (STOCK_AGOTADO_BG, STOCK_AGOTADO_FG, "Agotado"),
}

# Columnas del panel de detalle: (encabezado, ancho_px, padx)
_DETAIL_COLS = [
    ("Serial", 180, (16, 8)),
    ("MAC", 200, (8, 8)),
    ("Código", 160, (8, 8)),
    ("Registro", 140, (8, 8)),
    ("Estado", 0, (8, 8)),
]


def _trunc(text, maxchars):
    """Trunca texto con … si excede maxchars."""
    text = text or "—"
    return text if len(text) <= maxchars else text[: maxchars - 1] + "…"


def _setup_table_cols(frame):
    """Config de columnas compartida entre header y _GroupRow."""
    frame.grid_columnconfigure(0, weight=0, minsize=50)  # chevron
    frame.grid_columnconfigure(1, weight=2, minsize=160)  # modelo
    frame.grid_columnconfigure(2, weight=1, minsize=120)  # marca
    frame.grid_columnconfigure(3, weight=0, minsize=120)  # unidades
    frame.grid_columnconfigure(4, weight=0, minsize=160)  # stock
    frame.grid_columnconfigure(5, weight=1, minsize=100)  # proveedor
    frame.grid_columnconfigure(6, weight=0, minsize=80)  # acciones grupo
    frame.grid_rowconfigure(0, weight=1)


def _truncating_label(parent, full_text, **kw):
    """tk.Label que trunca con … cuando el texto excede el ancho disponible."""
    import tkinter.font as tkfont

    var = tk.StringVar(value=full_text)
    lbl = tk.Label(parent, textvariable=var, **kw)

    def _resize(e):
        try:
            fo = tkfont.Font(font=lbl.cget("font"))
            avail = max(e.width - 6, 20)
            if fo.measure(full_text) <= avail:
                var.set(full_text)
                return
            t = full_text
            while t and fo.measure(t + "…") > avail:
                t = t[:-1]
            var.set((t.rstrip() + "…") if t else "…")
        except Exception:
            pass

    lbl.bind("<Configure>", _resize)
    return lbl


class ProductsView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)
        self.current_user = current_user
        self.app = app
        self._selected_id = None
        self._selected_widget = None
        self._expanded = {}
        self._last_refresh = 0.0
        self._group_edit_fn = lambda g: self._edit_group(g)
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.refresh(force=True)

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=AZUL_NOCHE)
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))

        title_section = ctk.CTkFrame(hdr, fg_color="transparent")
        title_section.pack(side="left", fill="both", padx=15, pady=12)

        ctk.CTkLabel(
            title_section,
            text="Gestión de Productos",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=BLANCO_CALIDO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_section,
            text="Administra el inventario del almacén",
            font=ctk.CTkFont(size=16),
            text_color=AZUL_CIELO,
        ).pack(anchor="w", pady=(2, 5))

        action_section = ctk.CTkFrame(hdr, fg_color="transparent")
        action_section.pack(side="right", fill="both", padx=15, pady=12)

        ctk.CTkButton(
            action_section,
            text="⊕  Nuevo Producto",
            height=38,
            width=165,
            corner_radius=8,
            command=self._add_dialog,
            fg_color=AZUL_CERULEO,
            hover_color=HOVER_CERULEO,
            text_color="white",
            font=ctk.CTkFont(size=15, weight="bold"),
            border_width=0,
        ).pack(side="right", padx=(8, 0))

        ctk.CTkButton(
            action_section,
            text="⌕  Escanear",
            height=38,
            width=130,
            corner_radius=8,
            command=self._scan_barcode,
            fg_color="transparent",
            hover_color=HOVER_MARINO,
            text_color=AZUL_CIELO,
            font=ctk.CTkFont(size=15, weight="bold"),
            border_width=1,
            border_color=AZUL_CIELO,
        ).pack(side="right")

        sf = ctk.CTkFrame(
            self, fg_color="#FFFFFF", border_width=1, border_color=AZUL_MARINO
        )
        sf.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))
        sf.pack_propagate(False)
        sf.configure(height=55)

        ctk.CTkLabel(
            sf, text="🔍 Buscar:", font=ctk.CTkFont(size=16), text_color=AZUL_MARINO
        ).pack(side="left", padx=(12, 4))

        self._search = ctk.StringVar()
        self._search.trace_add("write", lambda *_: self.refresh())
        self._search_entry = ctk.CTkEntry(
            sf,
            textvariable=self._search,
            placeholder_text="nombre, código, serie o marca...",
            border_width=0,
            fg_color="transparent",
            text_color=AZUL_NOCHE,
            placeholder_text_color=TEXTO_PLACEHOLDER,
            font=ctk.CTkFont(size=17),
        )
        self._search_entry.pack(side="left", fill="x", expand=True, padx=(0, 12))

        self._status_filter = ctk.StringVar(value="todos")
        self._filter_btns = {}
        filter_defs = [
            ("todos", "Todos", AZUL_MARINO, AZUL_NOCHE),
            ("disponible", "Disponible", AZUL_CERULEO, HOVER_FILTRO_DISP),
            ("no disponible", "No Disponible", AMARILLO_AMBAR, HOVER_AMBAR),
        ]
        for val, label, fg, hover in filter_defs:
            btn = ctk.CTkButton(
                sf,
                text=label,
                width=115,
                height=32,
                corner_radius=16,
                fg_color=fg,
                hover_color=hover,
                text_color="white",
                font=ctk.CTkFont(size=14, weight="bold"),
                command=lambda v=val: self.set_status_filter(v),
                border_width=0,
            )
            btn.pack(side="right", padx=(0, 6))
            self._filter_btns[val] = btn
        self._update_filter_buttons()

        tf = ctk.CTkFrame(
            self, fg_color="#FFFFFF", border_width=2, border_color=AZUL_MARINO
        )
        tf.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        tf.grid_rowconfigure(1, weight=1)
        tf.grid_columnconfigure(0, weight=1)

        self._build_table_header(tf)

        self._scroll = ctk.CTkScrollableFrame(tf, fg_color="#FFFFFF", corner_radius=0)
        self._scroll.grid(row=1, column=0, sticky="nsew")
        self._scroll.grid_columnconfigure(0, weight=1)


    def _build_table_header(self, parent):
        outer = ctk.CTkFrame(parent, fg_color=AZUL_MARINO, height=36, corner_radius=0)
        outer.grid(row=0, column=0, sticky="ew")
        outer.pack_propagate(False)

        inner = tk.Frame(outer, bg=AZUL_MARINO)
        # padx derecho compensa el ancho del scrollbar de CTkScrollableFrame (~16px)
        inner.pack(fill="both", expand=True, padx=(0, 16))
        _setup_table_cols(inner)

        headers = ["", "Modelo / Equipo", "Marca", "Unidades", "Stock", "Proveedor", ""]
        for col, text in enumerate(headers):
            px = (12, 4) if col == 0 else (8, 4)
            tk.Label(
                inner,
                text=text,
                bg=AZUL_MARINO,
                fg="white",
                font=("Segoe UI", 11, "bold"),
                anchor="w",
            ).grid(row=0, column=col, sticky="ew", padx=px, pady=4)

    def set_status_filter(self, status: str):
        self._status_filter.set(status)
        self._update_filter_buttons()
        self.refresh(force=True)

    def _update_filter_buttons(self):
        active = self._status_filter.get()
        styles = {
            "todos": (AZUL_MARINO, AZUL_NOCHE),
            "disponible": (AZUL_CERULEO, HOVER_FILTRO_DISP),
            "no disponible": (AMARILLO_AMBAR, HOVER_AMBAR),
        }
        for val, btn in self._filter_btns.items():
            fg, hover = styles[val]
            if val == active:
                btn.configure(
                    fg_color=fg,
                    border_width=2,
                    border_color="white",
                    font=ctk.CTkFont(size=14, weight="bold"),
                )
            else:
                btn.configure(
                    fg_color=fg,
                    border_width=0,
                    font=ctk.CTkFont(size=14, weight="normal"),
                )

    def refresh(self, force=False):
        import time
        if not hasattr(self, "_scroll"):
            return
        now = time.time()
        if not force and (now - self._last_refresh) < 1.5:
            return
        self._last_refresh = now
        q = self._search.get() if hasattr(self, "_search") else ""
        status = (
            self._status_filter.get() if hasattr(self, "_status_filter") else "todos"
        )
        wh_id = self.app.current_warehouse_id if self.app else None

        expanded_keys = set(self._expanded.keys())

        for w in self._scroll.winfo_children():
            w.destroy()
        self._expanded.clear()
        self._selected_id = None
        self._selected_widget = None

        groups = get_products_grouped(
            search=q, status_filter=status, warehouse_id=wh_id
        )
        for i, g in enumerate(groups):
            group_key = f"{g['name']}__{g['brand']}"
            bg = FONDO_ROW_PAR if i % 2 == 0 else FONDO_ROW_IMPAR

            row = _GroupRow(
                self._scroll,
                g,
                on_toggle=self._toggle_row,
                bg_color=bg,
                on_edit_group=self._group_edit_fn,
            )
            row.pack(fill="x", pady=(0, 1))

            if group_key in expanded_keys:
                row.is_open = True
                row.chevron.configure(text="▾")
                self._open_group(row, g, wh_id)

    def _toggle_row(self, group_row):
        g = group_row.data
        group_key = f"{g['name']}__{g['brand']}"
        wh_id = self.app.current_warehouse_id if self.app else None

        if group_row.is_open:
            self._open_group(group_row, g, wh_id)
        else:
            if group_key in self._expanded:
                self._expanded.pop(group_key).destroy()

    def _open_group(self, group_row, g, wh_id):
        group_key = f"{g['name']}__{g['brand']}"
        container = ctk.CTkFrame(
            self._scroll, fg_color=FONDO_EXPANDIDO, corner_radius=4
        )
        container.pack(fill="x", pady=(0, 2), after=group_row)

        # Sub-header alineado con columnas de _ChildRow
        sub_hdr = ctk.CTkFrame(
            container, fg_color=FONDO_SUBHEADER, height=26, corner_radius=0
        )
        sub_hdr.pack(fill="x", padx=(64, 8), pady=(2, 0))
        sub_hdr.pack_propagate(False)
        for txt, w, px in _DETAIL_COLS:
            kw = {"width": w} if w else {}
            ctk.CTkLabel(
                sub_hdr,
                text=txt,
                fg_color="transparent",
                text_color=AZUL_MARINO,
                font=ctk.CTkFont(size=12, weight="bold"),
                anchor="w",
                **kw,
            ).pack(side="left", padx=px)
        ctk.CTkLabel(
            sub_hdr,
            text="Acciones",
            fg_color="transparent",
            text_color=AZUL_MARINO,
            font=ctk.CTkFont(size=12, weight="bold"),
            anchor="e",
        ).pack(side="right", padx=(4, 8))

        is_admin = self.current_user["role"] == "admin"
        units = get_units_by_model(g["name"], g["brand"], wh_id)
        for u in units:
            child = _ChildRow(
                container,
                u,
                on_select=self._select_unit,
                on_edit=self._edit_dialog,
                on_delete=self._delete if is_admin else None,
            )
            child.pack(fill="x", padx=(64, 8), pady=1)

        self._expanded[group_key] = container

    def _select_unit(self, unit_id, widget):
        if self._selected_widget and self._selected_widget.winfo_exists():
            self._selected_widget.deselect()
        self._selected_id = unit_id
        self._selected_widget = widget
        widget.select()

    def _edit_group(self, group_data):
        def _on_save(d):
            update_product_group(
                group_data["name"],
                group_data["brand"],
                d["name"],
                d["brand"],
                d["supplier_id"],
            )
            self.refresh(force=True)

        def _on_delete():
            try:
                elim, desact = delete_product_group(group_data["name"], group_data["brand"])
                self.refresh(force=True)
                partes = []
                if elim:
                    partes.append(f"{elim} unidad(es) eliminada(s)")
                if desact:
                    partes.append(f"{desact} unidad(es) desactivada(s) (tenían movimientos)")
                MessageDialog(self, "Grupo eliminado", "\n".join(partes) or "Sin cambios.")
            except Exception as e:
                MessageDialog(self, "Error", str(e), is_error=True)

        _GroupEditDialog(self, group_data, on_save=_on_save, on_add_more=self._do_bulk_add, on_delete=_on_delete)

    def _scan_barcode(self):
        _BarcodeScanDialog(self, on_scan=self._handle_barcode_scan)

    def _handle_barcode_scan(self, barcode):
        product = get_product_by_barcode(barcode)
        if product:
            MessageDialog(
                self,
                "Producto encontrado",
                f"Producto: {product['name']}\nCantidad actual: {product['quantity']}\nCódigo: {barcode}",
            )
        else:
            _ProductDialog(
                self,
                "Registrar Producto",
                initial={"barcode": barcode},
                on_save=lambda d: (self._do_edit_save(d),),
            )

    def _do_edit_save(self, d):
        wh_id = self.app.current_warehouse_id if self.app else None
        pid = create_product(
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
        if d.get("quantity", 0) > 0:
            create_movement(
                "entrada",
                pid,
                None,
                self.current_user["id"],
                d["quantity"],
                "Registro inicial",
                warehouse_id=wh_id,
            )
        self.refresh(force=True)

    def _selected_unit(self):
        if not self._selected_id:
            MessageDialog(
                self, "Aviso", "Selecciona una unidad individual (fila hijo)."
            )
            return None
        return str(self._selected_id)

    def _selected(self):
        if not self._selected_id:
            MessageDialog(self, "Aviso", "Selecciona un producto.")
        return str(self._selected_id) if self._selected_id else None

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
        self.refresh(force=True)

    def _add_dialog(self):
        _ProductDialog(self, "Registrar Producto", on_save=self._do_bulk_add)

    def _do_bulk_add(self, common, items):
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
        self.refresh(force=True)
        msg = f"{ok} equipo(s) registrado(s)."
        if duplicados:
            msg += f"\nOmitidos: {', '.join(duplicados)}"
        MessageDialog(self, "Alta Masiva", msg)

    def _edit_dialog(self):
        iid = self._selected_unit()
        if not iid:
            return
        rows = get_all_products()
        prod = next((r for r in rows if str(r["id"]) == str(iid)), None)
        if not prod:
            return

        def _on_save(d):
            import sqlite3

            try:
                update_product_unit(
                    int(iid),
                    d["serial"],
                    d["mac"],
                    d["barcode"] or None,
                    d["status"],
                )
                self.refresh(force=True)
            except sqlite3.IntegrityError:
                MessageDialog(
                    self,
                    "Error",
                    "El código de barras ya existe en otro producto.",
                    is_error=True,
                )

        _ProductDialog(
            self,
            "Editar Producto",
            initial={
                "name": prod["name"],
                "barcode": prod["barcode"] or "",
                "brand": prod["brand"] or "",
                "serial": prod["serial"] or "",
                "mac": prod["mac"] or "",
                "status": prod["status"] or "disponible",
                "unit": prod["unit"] or "und",
                "supplier_id": prod["supplier_id"],
            },
            on_save=_on_save,
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
                self.refresh(force=True)
                MessageDialog(
                    self, "Éxito", f"El producto '{product_name}' ha sido eliminado."
                )
            except Exception:
                MessageDialog(
                    self,
                    "Error",
                    "No se pudo eliminar. El producto tiene movimientos registrados.",
                    is_error=True,
                )


# ── Widgets de tabla ──────────────────────────────────────────────────────────


class _StatusPill(ctk.CTkFrame):
    def __init__(self, parent, status):
        bg, fg = _PILL_COLORS.get(status, (FONDO_BADGE, TEXTO_SECUNDARIO))
        super().__init__(parent, fg_color=bg, corner_radius=12)
        ctk.CTkLabel(
            self,
            text="●",
            text_color=fg,
            font=ctk.CTkFont(size=8),
        ).pack(side="left", padx=(8, 4))
        ctk.CTkLabel(
            self,
            text=_STATUS_LABELS.get(status, status),
            text_color=fg,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left", padx=(0, 10), pady=3)


class _ChildRow(ctk.CTkFrame):
    _NORMAL_BG = "white"
    _HOVER_BG = HOVER_FILA_BG
    _SELECT_BG = SELECCION_BG

    def __init__(self, parent, unit, on_select, on_edit, on_delete=None):
        super().__init__(parent, fg_color=self._NORMAL_BG, height=50, corner_radius=4)
        self.unit = unit
        self._on_select = on_select
        self._on_edit = on_edit
        self._on_delete = on_delete
        self._is_selected = False
        self.pack_propagate(False)
        self._build()
        self._bind_events()

    def _build(self):
        raw_date = self.unit["created_at"] or ""
        try:
            from datetime import datetime

            fecha = datetime.fromisoformat(raw_date).strftime("%d/%m/%Y")
        except Exception:
            fecha = raw_date[:10] if raw_date else "—"

        ctk.CTkLabel(
            self,
            text=_trunc(self.unit["serial"], 18),
            width=180,
            font=ctk.CTkFont(size=13),
            text_color=GRIS_AZULADO,
            anchor="w",
        ).pack(side="left", padx=(16, 8))
        ctk.CTkLabel(
            self,
            text=_trunc(self.unit["mac"], 19),
            width=200,
            font=ctk.CTkFont(size=13),
            text_color=GRIS_AZULADO,
            anchor="w",
        ).pack(side="left", padx=(8, 8))
        ctk.CTkLabel(
            self,
            text=_trunc(self.unit["barcode"], 16),
            width=160,
            font=ctk.CTkFont(size=13),
            text_color=GRIS_AZULADO,
            anchor="w",
        ).pack(side="left", padx=(8, 8))
        ctk.CTkLabel(
            self,
            text=fecha,
            width=140,
            font=ctk.CTkFont(size=13),
            text_color=TEXTO_SECUNDARIO,
            anchor="w",
        ).pack(side="left", padx=(8, 8))
        _StatusPill(self, self.unit["status"]).pack(side="left", padx=8)

        def _do_edit():
            self._on_select(self.unit["id"], self)
            self._on_edit()

        btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        btn_frame.pack(side="right", padx=(4, 8))
        ctk.CTkButton(
            btn_frame,
            text="✎ Editar",
            width=85,
            height=28,
            command=_do_edit,
            fg_color=BLANCO,
            hover_color=HOVER_FILA_BG,
            text_color=AZUL_MARINO,
            font=ctk.CTkFont(size=12, weight="bold"),
            border_width=1,
            border_color=AZUL_MARINO,
        ).pack(side="left", padx=(0, 4))
        if self._on_delete:

            def _do_delete():
                self._on_select(self.unit["id"], self)
                self._on_delete()

            ctk.CTkButton(
                btn_frame,
                text="✕ Eliminar",
                width=85,
                height=28,
                command=_do_delete,
                fg_color=BLANCO,
                hover_color=HOVER_FILA_BG,
                text_color=NARANJA_INTENSO,
                font=ctk.CTkFont(size=12, weight="bold"),
                border_width=1,
                border_color=NARANJA_INTENSO,
            ).pack(side="left")

    def _bind_events(self):
        def click(e):
            self._on_select(self.unit["id"], self)

        def enter(e):
            if not self._is_selected:
                self.configure(fg_color=self._HOVER_BG)

        def leave(e):
            if not self._is_selected:
                self.configure(fg_color=self._NORMAL_BG)

        for w in [self] + self._descendants():
            w.bind("<Button-1>", click, add="+")
            w.bind("<Enter>", enter, add="+")
            w.bind("<Leave>", leave, add="+")

    def _descendants(self):
        result = []

        def collect(w):
            for c in w.winfo_children():
                result.append(c)
                collect(c)

        collect(self)
        return result

    def select(self):
        self._is_selected = True
        self.configure(fg_color=self._SELECT_BG)

    def deselect(self):
        self._is_selected = False
        self.configure(fg_color=self._NORMAL_BG)


class _GroupRow(ctk.CTkFrame):
    def __init__(
        self, parent, data, on_toggle, bg_color=FONDO_ROW_PAR, on_edit_group=None
    ):
        super().__init__(parent, fg_color=bg_color, height=52)
        self.data = data
        self.is_open = False
        self._on_toggle = on_toggle
        self._on_edit_group = on_edit_group
        self._bg = bg_color
        self._tk_labels = []  # tk.Label refs para actualizar en hover
        self.pack_propagate(False)
        self._build()
        self._bind_hover()

    def _build(self):
        inner = tk.Frame(self, bg=self._bg)
        inner.pack(fill="both", expand=True)
        inner.pack_propagate(False)
        self._inner = inner
        _setup_table_cols(inner)

        # Col 0: chevron
        self.chevron = ctk.CTkButton(
            inner,
            text="▸",
            width=26,
            height=26,
            fg_color="transparent",
            hover_color=CHEVRON_HOVER,
            text_color=TEXTO_SECUNDARIO,
            font=ctk.CTkFont(size=13),
            command=self._toggle,
        )
        self.chevron.grid(row=0, column=0, padx=(10, 2))

        # Col 1: modelo (trunca con … si excede el ancho)
        lbl = _truncating_label(
            inner,
            self.data["name"],
            font=("Segoe UI", 12, "bold"),
            fg=TEXTO_MODELO,
            bg=self._bg,
            anchor="w",
        )
        lbl.grid(row=0, column=1, sticky="ew", padx=(8, 4))
        self._tk_labels.append(lbl)

        # Col 2: marca
        lbl = tk.Label(
            inner,
            text=self.data["brand"] or "—",
            font=("Segoe UI", 12),
            fg=TEXTO_MODELO,
            bg=self._bg,
            anchor="w",
        )
        lbl.grid(row=0, column=2, sticky="ew", padx=(4, 4))
        self._tk_labels.append(lbl)

        # Col 3: unidades badge
        count = self.data["unit_count"]
        ctk.CTkLabel(
            inner,
            text=f"{count}  {'unidad' if count == 1 else 'uds.'}",
            fg_color=FONDO_BADGE,
            corner_radius=12,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=GRIS_AZULADO,
        ).grid(row=0, column=3, padx=8, sticky="w")

        # Col 4: stock pill
        dc = self.data["disponible_count"]
        if dc == 0:
            stock_bg, stock_fg, stock_txt = (
                STOCK_AGOTADO_BG,
                STOCK_AGOTADO_FG,
                "Agotado",
            )
        elif dc <= 10:
            stock_bg, stock_fg, stock_txt = (
                STOCK_BAJO_BG,
                STOCK_BAJO_FG,
                f"Stock Bajo ({dc})",
            )
        else:
            stock_bg, stock_fg, stock_txt = (
                STOCK_DISP_BG,
                STOCK_DISP_FG,
                f"Disponible ({dc})",
            )
        pill = ctk.CTkFrame(inner, fg_color=stock_bg, corner_radius=12)
        pill.grid(row=0, column=4, padx=8, sticky="w")
        ctk.CTkLabel(
            pill, text="●", text_color=stock_fg, font=ctk.CTkFont(size=8)
        ).pack(side="left", padx=(8, 4))
        ctk.CTkLabel(
            pill,
            text=stock_txt,
            text_color=stock_fg,
            font=ctk.CTkFont(size=11, weight="bold"),
        ).pack(side="left", padx=(0, 10), pady=3)

        # Col 5: proveedor
        lbl = tk.Label(
            inner,
            text=self.data["supplier_name"] or "—",
            font=("Segoe UI", 11),
            fg=TEXTO_SECUNDARIO,
            bg=self._bg,
            anchor="w",
        )
        lbl.grid(row=0, column=5, sticky="ew", padx=(8, 4))
        self._tk_labels.append(lbl)

        # Col 6: botón editar grupo
        ctk.CTkButton(
            inner,
            text="⚙ Editar grupo",
            width=110,
            height=26,
            command=lambda: (
                self._on_edit_group(self.data) if self._on_edit_group else None
            ),
            fg_color=AZUL_MARINO,
            hover_color=AZUL_NOCHE,
            text_color="white",
            font=ctk.CTkFont(size=11, weight="bold"),
            border_width=0,
        ).grid(row=0, column=6, padx=(4, 8))

    def _bind_hover(self):
        def enter(e):
            self.configure(fg_color=FONDO_BADGE)
            self._inner.configure(bg=FONDO_BADGE)
            for w in self._tk_labels:
                w.configure(bg=FONDO_BADGE)

        def leave(e):
            self.configure(fg_color=self._bg)
            self._inner.configure(bg=self._bg)
            for w in self._tk_labels:
                w.configure(bg=self._bg)

        for w in [self] + self._descendants():
            w.bind("<Enter>", enter, add="+")
            w.bind("<Leave>", leave, add="+")

    def _descendants(self):
        result = []

        def collect(w):
            for c in w.winfo_children():
                result.append(c)
                collect(c)

        collect(self)
        return result

    def _toggle(self):
        self.is_open = not self.is_open
        self.chevron.configure(text="▾" if self.is_open else "▸")
        self._on_toggle(self)


# ── Diálogos ─────────────────────────────────────────────────────────────────


class _GroupEditDialog(ctk.CTkToplevel):
    def __init__(self, parent, group_data, on_save, on_add_more=None, on_delete=None):
        super().__init__(parent)
        self.title("Editar Grupo")
        self.geometry("450x560")
        self.resizable(False, False)
        self.configure(fg_color=BLANCO_CALIDO)
        self.transient(parent)
        self.on_save = on_save
        self.on_add_more = on_add_more
        self.on_delete = on_delete
        self._group_data = group_data

        suppliers = get_all_suppliers()
        self._supplier_map = {"Sin proveedor": None}
        self._supplier_map.update(
            {f"{s['name']} (ID:{s['id']})": s["id"] for s in suppliers}
        )
        sup_names = ["Sin proveedor"] + [
            f"{s['name']} (ID:{s['id']})" for s in suppliers
        ]

        hdr = ctk.CTkFrame(self, fg_color=AZUL_NOCHE, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text="EDITAR GRUPO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=14)

        body = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        ctk.CTkLabel(
            body,
            text=f"Se actualizarán {group_data['unit_count']} unidad(es)",
            font=ctk.CTkFont(size=12),
            text_color=TEXTO_SECUNDARIO,
        ).pack(anchor="w", padx=14, pady=(10, 6))

        def _lbl(text):
            ctk.CTkLabel(
                body,
                text=text,
                anchor="w",
                text_color=AZUL_NOCHE,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(fill="x", padx=14, pady=(8, 2))

        def _entry(val=""):
            e = ctk.CTkEntry(
                body,
                height=36,
                text_color=AZUL_NOCHE,
                fg_color=BLANCO_CALIDO,
                font=ctk.CTkFont(size=13),
                border_width=1,
                border_color=AZUL_MARINO,
            )
            if val:
                e.insert(0, val)
            e.pack(fill="x", padx=14)
            return e

        _lbl("Nombre del modelo *")
        self._name_e = _entry(group_data["name"])
        _lbl("Marca")
        self._brand_e = _entry(group_data["brand"] or "")
        _lbl("Proveedor")
        self._sup_opt = ctk.CTkOptionMenu(
            body,
            height=36,
            font=ctk.CTkFont(size=13),
            values=sup_names,
            text_color="white",
            button_color=AZUL_MARINO,
            button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO,
            dropdown_font=ctk.CTkFont(size=13),
        )
        current_sup = next(
            (
                k
                for k, v in self._supplier_map.items()
                if v == group_data["supplier_id"]
            ),
            "Sin proveedor",
        )
        self._sup_opt.set(current_sup)
        self._sup_opt.pack(fill="x", padx=14, pady=(0, 8))

        btns = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        btns.pack(fill="x", padx=16, pady=(0, 12))

        if self.on_add_more:
            ctk.CTkButton(
                btns,
                text="⊕  Agregar Productos a este Modelo",
                height=38,
                corner_radius=8,
                font=ctk.CTkFont(size=13, weight="bold"),
                fg_color=AZUL_CERULEO,
                hover_color=HOVER_CERULEO,
                text_color="white",
                command=self._open_add_more,
            ).pack(fill="x", pady=(0, 6))

        row2 = ctk.CTkFrame(btns, fg_color="transparent")
        row2.pack(fill="x", pady=(0, 6))
        ctk.CTkButton(
            row2,
            text="✓ GUARDAR",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=AZUL_MARINO,
            hover_color=AZUL_NOCHE,
            text_color="white",
            command=self._save,
        ).pack(side="left", fill="x", expand=True, padx=(0, 6))
        ctk.CTkButton(
            row2,
            text="✕ CANCELAR",
            height=38,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=NARANJA_INTENSO,
            hover_color=HOVER_NARANJA_INT,
            text_color="white",
            command=self.destroy,
        ).pack(side="left", fill="x", expand=True)

        if self.on_delete:
            ctk.CTkButton(
                btns,
                text="🗑  ELIMINAR GRUPO COMPLETO",
                height=36,
                corner_radius=8,
                font=ctk.CTkFont(size=12, weight="bold"),
                fg_color=NARANJA_INTENSO,
                hover_color=HOVER_NARANJA_INT,
                text_color="white",
                command=self._delete_group,
            ).pack(fill="x")

        center_dialog(self)
        self.after(50, self.grab_set)

    def _delete_group(self):
        g = self._group_data
        count = g["unit_count"]
        name = g["name"]
        # Primera confirmación
        d1 = ConfirmDialog(
            self,
            "⚠ Eliminar grupo",
            f"Estás a punto de eliminar el grupo «{name}» con {count} unidad(es).\n\n"
            "Las unidades sin movimientos serán borradas permanentemente.\n"
            "Las unidades con movimientos quedarán inactivas.\n\n"
            "¿Continuar?",
            is_danger=True,
        )
        self.wait_window(d1)
        if not d1.result:
            return
        # Segunda confirmación — acción irreversible
        d2 = ConfirmDialog(
            self,
            "⛔ Confirmar eliminación definitiva",
            f"ÚLTIMA ADVERTENCIA\n\n"
            f"Eliminarás permanentemente el grupo «{name}».\n"
            "Esta acción NO se puede deshacer.\n\n"
            "¿Estás seguro?",
            is_danger=True,
        )
        self.wait_window(d2)
        if not d2.result:
            return
        self.destroy()
        self.on_delete()

    def _open_add_more(self):
        g = self._group_data
        _ProductDialog(
            self,
            "Agregar Equipos",
            on_save=self.on_add_more,
            prefill={
                "name": g["name"],
                "brand": g["brand"] or "",
                "supplier_id": g["supplier_id"],
                "unit": g["unit"] or "und",
            },
        )

    def _save(self):
        name = self._name_e.get().strip()
        if not name:
            MessageDialog(self, "Aviso", "El nombre es obligatorio.")
            return
        brand = self._brand_e.get().strip()
        supplier_id = self._supplier_map.get(self._sup_opt.get())
        self.destroy()
        self.on_save({"name": name, "brand": brand, "supplier_id": supplier_id})


class _BarcodeScanDialog(ctk.CTkToplevel):
    def __init__(self, parent, on_scan):
        super().__init__(parent)
        self.title("Escanear Código de Barras")
        self.geometry("400x200")
        self.resizable(False, False)
        self.configure(fg_color=BLANCO_CALIDO)
        self.transient(parent)
        self.on_scan = on_scan

        ctk.CTkLabel(
            self,
            text="Escanee o ingrese el código de barras",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(pady=(20, 10))

        self.barcode_entry = ctk.CTkEntry(
            self,
            height=50,
            font=ctk.CTkFont(size=20),
            placeholder_text="Código de barras...",
            text_color=AZUL_NOCHE,
        )
        self.barcode_entry.pack(pady=10, padx=20, fill="x")
        self.barcode_entry.focus()

        ctk.CTkButton(
            self,
            text="Aceptar",
            command=self._on_accept,
            fg_color=AZUL_CERULEO,
            hover_color=HOVER_FILTRO_DISP,
            text_color="white",
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(pady=10)

        self.barcode_entry.bind("<Return>", lambda e: self._on_accept())
        center_dialog(self)
        self.after(50, self.grab_set)

    def _center_and_grab(self):
        center_dialog(self)
        self.grab_set()

    def _on_accept(self):
        barcode = self.barcode_entry.get().strip()
        if barcode:
            self.destroy()
            self.on_scan(barcode)


class _ProductDialog(ctk.CTkToplevel):
    def __init__(self, parent, title, on_save, initial=None, prefill=None):
        super().__init__(parent)
        self.title(title)
        self.resizable(True, True)
        self.configure(fg_color=BLANCO_CALIDO)
        self.transient(parent)
        self.on_save = on_save
        self._is_add = initial is None
        self._prefill = prefill or {}
        self._rows = []
        d = initial or {}

        suppliers = get_all_suppliers()
        self._supplier_map = {"Sin proveedor": None}
        self._supplier_map.update(
            {f"{s['name']} (ID:{s['id']})": s["id"] for s in suppliers}
        )
        sup_names = ["Sin proveedor"] + [
            f"{s['name']} (ID:{s['id']})" for s in suppliers
        ]

        if self._is_add:
            self.geometry("900x660")
            self.minsize(800, 560)
            self._build_add_mode(sup_names)
        else:
            self.geometry("500x550")
            self.minsize(420, 480)
            self._build_edit_mode(sup_names, d)

        self.after(50, self.grab_set)

    # ── ADD MODE ──────────────────────────────────────────────────────────────

    def _build_add_mode(self, sup_names):
        def _e(parent, placeholder="", width=0, **kw):
            return ctk.CTkEntry(
                parent,
                height=34,
                font=ctk.CTkFont(size=13),
                fg_color=BLANCO_CALIDO,
                border_width=1,
                border_color=AZUL_MARINO,
                text_color=AZUL_NOCHE,
                placeholder_text=placeholder,
                **({"width": width} if width else {}),
                **kw,
            )

        def _lbl(parent, text):
            ctk.CTkLabel(
                parent,
                text=text,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=GRIS_AZULADO,
            ).grid(sticky="w")

        hdr = ctk.CTkFrame(self, fg_color=AZUL_NOCHE, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text="REGISTRAR PRODUCTO",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=14)
        self._counter_lbl = ctk.CTkLabel(
            hdr, text="1 equipo", font=ctk.CTkFont(size=13), text_color=AZUL_CIELO
        )
        self._counter_lbl.pack(side="right", padx=20)

        cf = ctk.CTkFrame(self, fg_color="white", corner_radius=8)
        cf.pack(fill="x", padx=14, pady=(10, 6))

        ctk.CTkLabel(
            cf, text="DATOS COMUNES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AZUL_MARINO,
        ).pack(anchor="w", padx=14, pady=(10, 6))

        p = self._prefill
        if p.get("name"):
            # Modo "agregar a modelo existente": nombre/marca bloqueados
            banner = ctk.CTkFrame(cf, fg_color=FONDO_SUBHEADER, corner_radius=6)
            banner.pack(fill="x", padx=14, pady=(0, 10))
            ctk.CTkLabel(banner, text="Modelo:", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=AZUL_MARINO).pack(side="left", padx=(12, 4), pady=8)
            ctk.CTkLabel(banner, text=p["name"], font=ctk.CTkFont(size=13, weight="bold"),
                         text_color=AZUL_NOCHE).pack(side="left", padx=(0, 20))
            ctk.CTkLabel(banner, text="Marca:", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=AZUL_MARINO).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(banner, text=p.get("brand") or "—", font=ctk.CTkFont(size=13),
                         text_color=GRIS_AZULADO).pack(side="left")
            self._locked_name = p["name"]
            self._locked_brand = p.get("brand") or ""
        else:
            row_nb = ctk.CTkFrame(cf, fg_color="transparent")
            row_nb.pack(fill="x", padx=14, pady=(0, 10))

            col_name = ctk.CTkFrame(row_nb, fg_color="transparent")
            col_name.pack(side="left", padx=(0, 12))
            ctk.CTkLabel(col_name, text="Nombre *", font=ctk.CTkFont(size=12),
                         text_color=GRIS_AZULADO).pack(anchor="w", pady=(0, 2))
            self.name_e = _e(col_name, "Router TP-Link...", 230)
            self.name_e.pack()

            col_brand = ctk.CTkFrame(row_nb, fg_color="transparent")
            col_brand.pack(side="left")
            ctk.CTkLabel(col_brand, text="Marca", font=ctk.CTkFont(size=12),
                         text_color=GRIS_AZULADO).pack(anchor="w", pady=(0, 2))
            self.brand_e = _e(col_brand, "TP-Link...", 160)
            self.brand_e.pack()

        row_su = ctk.CTkFrame(cf, fg_color="transparent")
        row_su.pack(fill="x", padx=14, pady=(0, 10))

        if p.get("name"):
            # Prefill mode: proveedor y unidad solo lectura
            sup_name_display = next(
                (k for k, v in self._supplier_map.items() if v == p.get("supplier_id")),
                "Sin proveedor",
            )
            info_su = ctk.CTkFrame(row_su, fg_color=FONDO_SUBHEADER, corner_radius=6)
            info_su.pack(fill="x")
            ctk.CTkLabel(info_su, text="Proveedor:", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=AZUL_MARINO).pack(side="left", padx=(12, 4), pady=8)
            ctk.CTkLabel(info_su, text=sup_name_display, font=ctk.CTkFont(size=12),
                         text_color=GRIS_AZULADO).pack(side="left", padx=(0, 24))
            ctk.CTkLabel(info_su, text="Unidad:", font=ctk.CTkFont(size=12, weight="bold"),
                         text_color=AZUL_MARINO).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(info_su, text=p.get("unit") or "und", font=ctk.CTkFont(size=12),
                         text_color=GRIS_AZULADO).pack(side="left")
            self._locked_supplier_id = p.get("supplier_id")
            self._locked_unit = p.get("unit") or "und"
        else:
            col_sup = ctk.CTkFrame(row_su, fg_color="transparent")
            col_sup.pack(side="left", padx=(0, 12))
            ctk.CTkLabel(col_sup, text="Proveedor", font=ctk.CTkFont(size=12),
                         text_color=GRIS_AZULADO).pack(anchor="w", pady=(0, 2))
            self.sup_opt = ctk.CTkOptionMenu(
                col_sup, height=34, width=200, values=sup_names,
                font=ctk.CTkFont(size=12), text_color="white",
                fg_color=AZUL_MARINO, button_color=AZUL_MARINO,
                button_hover_color=AZUL_NOCHE,
            )
            self.sup_opt.pack()

            col_unit = ctk.CTkFrame(row_su, fg_color="transparent")
            col_unit.pack(side="left")
            ctk.CTkLabel(col_unit, text="Unidad", font=ctk.CTkFont(size=12),
                         text_color=GRIS_AZULADO).pack(anchor="w", pady=(0, 2))
            self.unit_opt = ctk.CTkOptionMenu(
                col_unit, height=34, width=100,
                values=["und", "m", "cm", "kg", "g", "L", "ml", "rollo", "caja", "par"],
                font=ctk.CTkFont(size=12), text_color="white",
                fg_color=AZUL_MARINO, button_color=AZUL_MARINO,
                button_hover_color=AZUL_NOCHE,
            )
            self.unit_opt.pack()

        row_gen = ctk.CTkFrame(cf, fg_color=FONDO_SCROLL, corner_radius=6)
        row_gen.pack(fill="x", padx=14, pady=(0, 12))
        ctk.CTkLabel(row_gen, text="Cantidad de equipos:",
                     font=ctk.CTkFont(size=12, weight="bold"),
                     text_color=AZUL_MARINO).pack(side="left", padx=(12, 8), pady=8)
        self._qty_gen_e = ctk.CTkEntry(
            row_gen, width=70, height=34,
            font=ctk.CTkFont(size=13), fg_color=BLANCO_CALIDO,
            border_width=1, border_color=AZUL_MARINO,
            text_color=AZUL_NOCHE, placeholder_text="ej: 5",
        )
        self._qty_gen_e.pack(side="left", padx=(0, 8))
        self._qty_gen_e.bind("<Return>", lambda e: self._generate_rows())
        ctk.CTkButton(
            row_gen, text="▶ Generar filas", height=34, width=140,
            fg_color=AZUL_CERULEO, hover_color=HOVER_CERULEO,
            text_color="white", font=ctk.CTkFont(size=13, weight="bold"),
            command=self._generate_rows,
        ).pack(side="left")
        ctk.CTkLabel(row_gen, text="(genera filas automáticamente)",
                     font=ctk.CTkFont(size=11), text_color=TEXTO_SECUNDARIO,
                     ).pack(side="left", padx=8)

        th = ctk.CTkFrame(self, fg_color=AZUL_MARINO, height=32, corner_radius=0)
        th.pack(fill="x", padx=14)
        th.pack_propagate(False)
        for col_txt, w in [
            ("#", 36),
            ("Serial", 260),
            ("MAC  (AA-BB-CC-DD-EE-FF)", 280),
            ("", 44),
        ]:
            ctk.CTkLabel(
                th,
                text=col_txt,
                width=w,
                anchor="w",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="white",
            ).pack(side="left", padx=6)

        self._scroll = ctk.CTkScrollableFrame(
            self, fg_color=FONDO_SCROLL, corner_radius=0
        )
        self._scroll.pack(fill="both", expand=True, padx=14, pady=(0, 4))

        footer = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        footer.pack(fill="x", padx=14, pady=(0, 10))
        ctk.CTkButton(
            footer,
            text="+ Agregar equipo",
            width=150,
            height=34,
            fg_color=AZUL_CERULEO,
            hover_color=HOVER_CERULEO,
            text_color="white",
            font=ctk.CTkFont(size=13),
            command=self._add_row,
        ).pack(side="left")
        ctk.CTkButton(
            footer,
            text="✕ Cancelar",
            width=120,
            height=34,
            fg_color=NARANJA_INTENSO,
            hover_color=HOVER_NARANJA_INT,
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self.destroy,
        ).pack(side="right", padx=(8, 0))
        ctk.CTkButton(
            footer,
            text="✓ Guardar",
            width=140,
            height=34,
            fg_color=AZUL_MARINO,
            hover_color=AZUL_NOCHE,
            text_color="white",
            font=ctk.CTkFont(size=13, weight="bold"),
            command=self._save_add,
        ).pack(side="right")

        self._add_row()

    def _generate_rows(self):
        try:
            n = int(self._qty_gen_e.get().strip())
        except ValueError:
            return
        if n < 1 or n > 200:
            MessageDialog(self, "Aviso", "Cantidad debe ser entre 1 y 200.")
            return
        for r in list(self._rows):
            r["frame"].destroy()
        self._rows.clear()
        for _ in range(n):
            self._add_row()

    def _add_row(self):
        idx = len(self._rows) + 1
        rf = ctk.CTkFrame(self._scroll, fg_color="white", corner_radius=6, height=42)
        rf.pack(fill="x", pady=2)
        rf.pack_propagate(False)

        ctk.CTkLabel(
            rf,
            text=str(idx),
            width=36,
            font=ctk.CTkFont(size=13),
            text_color=AZUL_MARINO,
        ).pack(side="left", padx=4)

        serial_e = ctk.CTkEntry(
            rf,
            width=260,
            height=30,
            font=ctk.CTkFont(size=13),
            fg_color=BLANCO_CALIDO,
            border_width=1,
            border_color=AZUL_MARINO,
            text_color=AZUL_NOCHE,
            placeholder_text="SN-XXXXXXXXXX",
        )
        serial_e.pack(side="left", padx=(0, 6))

        mac_var = ctk.StringVar()
        _upd = [False]

        def _fmt(*_):
            if _upd[0]:
                return
            raw = mac_var.get()
            clean = "".join(c for c in raw if c.isalnum())[:12].upper()
            _upd[0] = True
            mac_var.set("-".join(clean[i : i + 2] for i in range(0, len(clean), 2)))
            _upd[0] = False

        mac_var.trace_add("write", _fmt)
        mac_e = ctk.CTkEntry(
            rf,
            width=260,
            height=30,
            font=ctk.CTkFont(size=13),
            fg_color=BLANCO_CALIDO,
            border_width=1,
            border_color=AZUL_MARINO,
            text_color=AZUL_NOCHE,
            textvariable=mac_var,
            placeholder_text="AA-BB-CC-DD-EE-FF",
        )
        mac_e.pack(side="left", padx=(0, 6))

        row = {"frame": rf, "serial": serial_e, "mac_var": mac_var}
        self._rows.append(row)

        ctk.CTkButton(
            rf,
            text="✕",
            width=30,
            height=28,
            fg_color=NARANJA_INTENSO,
            hover_color=HOVER_NARANJA_INT,
            text_color="white",
            font=ctk.CTkFont(size=11),
            command=lambda r=row: self._remove_row(r),
        ).pack(side="left")
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

        if hasattr(self, "_locked_name"):
            name = self._locked_name
            brand = self._locked_brand
        else:
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
                MessageDialog(
                    self,
                    "Aviso",
                    f"Fila {i}: MAC inválida.\nUsa formato AA-BB-CC-DD-EE-FF",
                )
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

        if hasattr(self, "_locked_supplier_id"):
            supplier_id = self._locked_supplier_id
            unit = self._locked_unit
        else:
            supplier_id = self._supplier_map.get(self.sup_opt.get())
            unit = self.unit_opt.get()
        common = {
            "name": name,
            "brand": brand,
            "supplier_id": supplier_id,
            "unit": unit,
        }
        self.destroy()
        self.on_save(common, items)

    # ── EDIT MODE ─────────────────────────────────────────────────────────────

    def _build_edit_mode(self, sup_names, d):
        main = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        main.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main, fg_color=AZUL_NOCHE, height=60)
        header.pack(fill="x", pady=(0, 10))
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text="EDITAR UNIDAD",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=15)

        # Info del grupo (solo lectura)
        info = ctk.CTkFrame(main, fg_color=FONDO_SUBHEADER, corner_radius=8)
        info.pack(fill="x", padx=20, pady=(0, 10))
        for label, val in [
            ("Modelo:", d.get("name", "—")),
            ("Marca:", d.get("brand", "—") or "—"),
        ]:
            row = ctk.CTkFrame(info, fg_color="transparent")
            row.pack(side="left", padx=14, pady=8)
            ctk.CTkLabel(
                row,
                text=label,
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=AZUL_MARINO,
            ).pack(side="left", padx=(0, 4))
            ctk.CTkLabel(
                row,
                text=val,
                font=ctk.CTkFont(size=12),
                text_color=GRIS_AZULADO,
            ).pack(side="left")

        body = ctk.CTkFrame(main, fg_color="white", corner_radius=10)
        body.pack(fill="both", expand=True, padx=20)

        def _lbl(text):
            ctk.CTkLabel(
                body,
                text=text,
                anchor="w",
                text_color=AZUL_NOCHE,
                font=ctk.CTkFont(size=13, weight="bold"),
            ).pack(fill="x", padx=15, pady=(12, 2))

        def _entry(val="", placeholder=""):
            e = ctk.CTkEntry(
                body,
                height=38,
                text_color=AZUL_NOCHE,
                fg_color=BLANCO_CALIDO,
                font=ctk.CTkFont(size=13),
                border_width=1,
                border_color=AZUL_MARINO,
                placeholder_text=placeholder,
            )
            if val:
                e.insert(0, val)
            e.pack(fill="x", padx=15)
            return e

        ctk.CTkLabel(
            body,
            text="CAMPOS EDITABLES",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=AZUL_MARINO,
        ).pack(anchor="w", padx=15, pady=(14, 4))

        _lbl("Serial")
        self.serial_e = _entry(d.get("serial", ""), "SN-XXXXXXXXXX")
        _lbl("MAC")
        self.mac_e = _entry(d.get("mac", ""), "AA-BB-CC-DD-EE-FF")
        _lbl("Código de Barras")
        self.barcode_e = _entry(d.get("barcode", ""), "código...")
        _lbl("Estado")
        self.status_opt = ctk.CTkOptionMenu(
            body,
            height=38,
            font=ctk.CTkFont(size=13),
            values=["disponible", "no disponible", "inactivo"],
            text_color="white",
            button_color=AZUL_MARINO,
            button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO,
            dropdown_font=ctk.CTkFont(size=13),
        )
        self.status_opt.set(d.get("status", "disponible"))
        self.status_opt.pack(fill="x", padx=15)

        btns = ctk.CTkFrame(main, fg_color=BLANCO_CALIDO)
        btns.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(
            btns,
            text="✓ GUARDAR",
            font=ctk.CTkFont(size=14, weight="bold"),
            command=self._save_edit,
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

    def _save_edit(self):
        import re

        serial = self.serial_e.get().strip()
        mac = self.mac_e.get().strip()
        barcode = self.barcode_e.get().strip()

        if mac and not re.match(r"^([A-Za-z0-9]{2}[:\-]){5}[A-Za-z0-9]{2}$", mac):
            MessageDialog(self, "Aviso", "MAC inválida. Usa formato AA-BB-CC-DD-EE-FF.")
            return
        if barcode and not re.match(r"^[a-zA-Z0-9\-]+$", barcode):
            MessageDialog(self, "Aviso", "Código de barras inválido.")
            return

        self.on_save(
            {
                "serial": serial or None,
                "mac": mac.upper() if mac else None,
                "barcode": barcode or None,
                "status": self.status_opt.get(),
            }
        )
        self.destroy()

import tkinter as tk
import tkinter.font as tkfont
import customtkinter as ctk
from datetime import datetime
from tkinter import filedialog, ttk
from PIL import Image, ImageTk

from ui.colors import *
from ui.widgets import (
    BaseDialog,
    ConfirmDialog,
    MessageDialog,
    show_centered,
)
from database.repository import (
    get_movement,
    get_movement_detail,
    query_movements_view,
    get_movements_flat,
    get_all_employees,
    get_all_vehicles,
    get_movement_available_products,
    get_products_pending_return_grouped,
    get_serials_pending_return,
    get_products_brief,
    create_compound_movement,
    update_movement,
    delete_movement,
)
from core.export import export_movements


TYPE_STYLES = {
    "todos": ("Todos", AZUL_MARINO, AZUL_NOCHE),
    "entrada": ("Entrada", AZUL_CERULEO, HOVER_FILTRO_DISP),
    "salida": ("Salida", NARANJA_SELECCION, HOVER_NARANJA_SEL),
    "devolucion": ("Devolución", AMARILLO_AMBAR, HOVER_AMBAR),
    "asignacion": ("Asignación", AZUL_CIELO, HOVER_MOV_ASIG),
    "eliminacion": ("Eliminación", INACTIVO_BG, HOVER_MOV_CANCEL),
    "modificacion": ("Modificación", AZUL_MARINO, AZUL_NOCHE),
}


def _pick_mono_family(widget):
    try:
        families = set(tkfont.families(widget))
        for name in ("Consolas", "DejaVu Sans Mono", "Liberation Mono",
                     "Menlo", "Courier New"):
            if name in families:
                return name
    except Exception:
        pass
    return "TkFixedFont"


_SANS_FAMILY = None


def _sans_family():
    """Familia sans del sistema, resuelta una sola vez (se usa en filas tk)."""
    global _SANS_FAMILY
    if _SANS_FAMILY is None:
        try:
            _SANS_FAMILY = tkfont.nametofont("TkDefaultFont").actual("family")
        except Exception:
            _SANS_FAMILY = "TkDefaultFont"
    return _SANS_FAMILY


def _split_ts(ts):
    """Separa 'YYYY-MM-DD HH:MM:SS' en (fecha, hora)."""
    if not ts:
        return "—", "—"
    s = str(ts).strip()
    if " " in s:
        date, time_ = s.split(" ", 1)
        return date, time_[:8]
    return s, "—"


class MovementsView(ctk.CTkFrame):
    """Ventana Movimientos rediseñada (design_handoff_movimientos).

    El cuerpo usa un ttk.Treeview nativo para evitar tirones de carga;
    conserva el chrome (título, filtros plegables, chips, pie con
    paginación) y toda la funcionalidad de registrar/editar/eliminar.
    """
    PER_PAGE = 25
    MOV_STYLE = "Mov.Treeview"

    # Columnas físicas: gutters simétricos (18 px) a ambos lados para que el
    # contenido nunca quede pegado a los bordes.
    COLS = ["pad_l", "id", "tipo", "fecha", "cant", "product", "reg", "acc", "pad_r"]
    COL_ANCHOR = {
        "pad_l": "w", "id": "w", "tipo": "center", "fecha": "w", "cant": "center",
        "product": "w", "reg": "w", "acc": "e", "pad_r": "w",
    }
    COL_MINS = [18, 60, 120, 150, 140, 160, 110, 104, 18]
    COL_WEIGHTS = [0, 1, 3, 4, 4, 6, 3, 1, 0]
    SUM_WEIGHTS = sum(COL_WEIGHTS)
    SUM_FIXED = sum(COL_MINS)
    SCROLL_RESERVE = 16
    # Indicador lateral de tipo: columna #0 del tree con una barrita de color
    STRIP_W = 30          # ancho reservado para la columna #0
    STRIP_PX = 10         # grosor visible de la franja
    ROW_H = 46            # alto de fila (debe coincidir con el estilo)
    ACCENTS = {
        "entrada": DSG_BADGE_ENTRADA_FG,
        "salida": DSG_BADGE_SALIDA_FG,
        "devolucion": DSG_BADGE_DEVOLUCION_FG,
        "asignacion": DSG_BADGE_ASIGNACION_FG,
        "modificacion": DSG_BADGE_MODIFICACION_FG,
        "eliminacion": DSG_BADGE_ELIMINACION_FG,
        "eliminacion_grupo": DSG_BADGE_ELIMINACION_FG,
    }
    HEADERS = [
        (1, "ID", "w"), (2, "Tipo", "center"), (3, "Fecha / hora", "w"),
        (4, "Cant.", "center"), (5, "Producto", "w"),
        (6, "Registrado", "w"), (7, "Acciones", "e"),
    ]

    CHIPS = [
        ("todos", "Todos", DSG_DOT_TODOS),
        ("entrada", "Entrada", DSG_DOT_ENTRADA),
        ("salida", "Salida", DSG_DOT_SALIDA),
        ("devolucion", "Devolución", DSG_DOT_DEVOLUCION),
        ("modificacion", "Modificación", DSG_DOT_MODIFICACION),
        ("eliminacion", "Eliminación", DSG_DOT_ELIMINACION),
    ]
    # tipo real en BD -> (etiqueta visible, fondo de fila, texto de fila)
    BADGES = {
        "entrada": ("entrada", DSG_BADGE_ENTRADA_BG, DSG_TEXT),
        "salida": ("salida", DSG_BADGE_SALIDA_BG, DSG_TEXT),
        "devolucion": ("devolución", DSG_BADGE_DEVOLUCION_BG, DSG_TEXT),
        "asignacion": ("asignación", DSG_BADGE_ASIGNACION_BG, DSG_TEXT),
        "modificacion": ("modificación", DSG_BADGE_MODIFICACION_BG, DSG_TEXT),
        "eliminacion": ("eliminación", DSG_BADGE_ELIMINACION_BG, DSG_TEXT),
        "eliminacion_grupo": ("elim. grupo", DSG_BADGE_ELIMINACION_BG, DSG_TEXT),
    }
    TYPE_ALIASES = {
        "entrada": ["entrada"],
        "salida": ["salida"],
        "devolucion": ["devolucion"],
        "modificacion": ["modificacion"],
        "eliminacion": ["eliminacion", "eliminacion_grupo"],
    }

    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color=DSG_BG)
        self.current_user = current_user
        self.app = app
        self._mono = _pick_mono_family(self)
        _fam = tkfont.nametofont("TkDefaultFont").actual("family")
        self._ui_family = _fam
        self._fonts = self._build_fonts()
        self._widgets_built = False

        # Estado (State Management del handoff)
        self._tipo = None
        self._busqueda = ""
        self._pagina = 1
        self._total = 0
        self._counts = {}
        self._last_update = ""
        self._flash_id = None
        self._flash_type = None
        self._reload_job = None
        self._suppress_search = False
        self._filters_expanded = True
        self._resize_job = None
        self._card_last_w = 0
        self._ctx_id = None
        self._last_sub = None
        self._last_hint = None
        self._last_footer = None
        self._last_pager_sig = None
        self._last_chip_vals = {}

        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self._configure_tree_style()
        self.refresh()

    # ── construcción de UI ──────────────────────────────────────────────
    def _build_fonts(self):
        return {
            "title": ctk.CTkFont(size=27, weight="bold"),
            "sub": ctk.CTkFont(size=13),
            "btn": ctk.CTkFont(size=13, weight="bold"),
            "btn_sec": ctk.CTkFont(size=13),
            "chip": ctk.CTkFont(size=13, weight="normal"),
            "chip_sel": ctk.CTkFont(size=13, weight="bold"),
            "chip_count": ctk.CTkFont(family=self._mono, size=11),
            "header": ctk.CTkFont(size=16, weight="bold"),
            "footer": ctk.CTkFont(size=13),
            "pager": ctk.CTkFont(size=13, weight="bold"),
            "pager_off": ctk.CTkFont(size=13),
            "icon": ctk.CTkFont(size=14),
        }

    def _build(self):
        # ── Bloque de título ──
        title_row = ctk.CTkFrame(self, fg_color=DSG_BG)
        title_row.grid(row=0, column=0, sticky="ew", padx=24, pady=(22, 14))
        ctk.CTkLabel(
            title_row, text="Movimientos", font=self._fonts["title"],
            text_color=DSG_TEXT, anchor="w",
        ).pack(side="left", anchor="s")
        self._subtitle_var = ctk.StringVar(value="")
        ctk.CTkLabel(
            title_row, textvariable=self._subtitle_var, font=self._fonts["sub"],
            text_color=DSG_TEXT_SEC2,
        ).pack(side="left", anchor="s", padx=(14, 0), pady=(0, 6))

        acc = ctk.CTkFrame(title_row, fg_color=DSG_BG)
        acc.pack(side="right")
        self._export_btn = ctk.CTkButton(
            acc, text="↓  Exportar PDF", font=self._fonts["btn_sec"],
            fg_color=DSG_SURF, hover_color=DSG_ROW_HOVER,
            border_color=DSG_BORDER_CTRL, border_width=1,
            text_color=DSG_TEXT_BODY, corner_radius=9, height=36,
            command=self._export,
        )
        self._export_btn.pack(side="left", padx=(0, 10))
        ctk.CTkButton(
            acc, text="+  Registrar movimiento", font=self._fonts["btn"],
            fg_color=DSG_PRIMARY, hover_color=DSG_PRIMARY_HOVER,
            text_color="white", corner_radius=9, height=38,
            command=self._register_dialog,
        ).pack(side="left")

        # ── Filtros (barra resumen + panel plegable) ──
        self._filters_container = ctk.CTkFrame(self, fg_color=DSG_BG)
        self._filters_container.grid(row=1, column=0, sticky="ew", padx=24,
                                     pady=(0, 14))
        bar = ctk.CTkFrame(self._filters_container, fg_color=DSG_BG)
        bar.pack(fill="x")
        self._filters_bar = bar
        ctk.CTkLabel(
            bar, text="Filtros", font=self._fonts["btn"], text_color=DSG_TEXT,
            anchor="w",
        ).pack(side="left")
        self._filter_hint = ctk.CTkLabel(
            bar, text="", font=self._fonts["sub"], text_color=DSG_TEXT_SEC2,
            anchor="w", cursor="hand2",
        )
        self._filter_hint.pack(side="left", padx=(10, 0))
        self._filter_hint.bind("<Button-1>", lambda e: self._open_filters())

        bar_right = ctk.CTkFrame(bar, fg_color=DSG_BG)
        bar_right.pack(side="right")
        self._clear_btn = ctk.CTkButton(
            bar_right, text="✕  Limpiar", font=self._fonts["btn_sec"],
            fg_color="transparent", hover_color=DSG_ROW_HOVER,
            text_color=DSG_BRAND, corner_radius=7, height=28,
            command=self._clear_filters,
        )
        self._filter_toggle = ctk.CTkButton(
            bar_right, text="▴ Ocultar", font=self._fonts["btn_sec"],
            fg_color="transparent", hover_color=DSG_ROW_HOVER,
            text_color=DSG_TEXT_BODY, corner_radius=7, height=28,
            command=self._toggle_filters,
        )

        self._filters_panel = ctk.CTkFrame(self._filters_container, fg_color=DSG_BG)
        search_line = ctk.CTkFrame(self._filters_panel, fg_color=DSG_BG)
        search_line.pack(fill="x")
        self._search = ctk.StringVar()
        self._search.trace_add("write", self._on_search_changed)
        search_box = ctk.CTkFrame(
            search_line, fg_color=DSG_SURF, border_color=DSG_BORDER_CTRL,
            border_width=1, corner_radius=9, height=38, width=380,
        )
        search_box.pack(side="left")
        search_box.pack_propagate(False)
        ctk.CTkLabel(search_box, text="⌕", font=self._fonts["icon"],
                     text_color=DSG_TEXT_MUTED).pack(side="left", padx=(13, 6))
        self._search_entry = ctk.CTkEntry(
            search_box, textvariable=self._search, border_width=0,
            fg_color="transparent", text_color=DSG_TEXT,
            placeholder_text="Buscar producto, empleado o nota…",
            placeholder_text_color=DSG_TEXT_MUTED, font=self._fonts["sub"],
        )
        self._search_entry.pack(side="left", fill="x", expand=True,
                                padx=(0, 12), pady=8)

        chips_line = ctk.CTkFrame(self._filters_panel, fg_color=DSG_BG)
        chips_line.pack(fill="x", pady=(10, 0))
        self._chips = {}
        self._chip_counts = {}
        for key, label, dot in self.CHIPS:
            chip = self._make_chip(chips_line, key, label, dot)
            chip.pack(side="left", padx=(0, 7))
            self._chips[key] = chip
            self._chip_counts[key] = chip.count_label
        self._filters_panel.pack(fill="x")

        # ── Tarjeta de la tabla ──
        card = ctk.CTkFrame(self, fg_color=DSG_SURF, border_color=DSG_BORDER,
                            border_width=1, corner_radius=12)
        card.grid(row=2, column=0, sticky="nsew", padx=24, pady=(0, 24))
        card.grid_rowconfigure(1, weight=1)
        card.grid_columnconfigure(0, weight=1)
        self._card = card
        self._card.bind("<Configure>", self._on_card_configure)

        # Cabecera fija (no se desplaza con las filas)
        header = ctk.CTkFrame(card, fg_color=DSG_BRAND, corner_radius=0, height=54)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_propagate(False)
        self._style_header_grid(header)
        self._build_header(header)

        # Cuerpo: Treeview nativo + scrollbar
        body = ctk.CTkFrame(card, fg_color=DSG_SURF, corner_radius=0)
        body.grid(row=1, column=0, sticky="nsew")
        body.grid_rowconfigure(0, weight=1)
        body.grid_columnconfigure(0, weight=1)
        self._body = body

        self._tree = ttk.Treeview(
            body, columns=self.COLS, show="tree", style=self.MOV_STYLE,
            selectmode="browse",
        )
        # Columna #0: barrita lateral de color por tipo (franja fina)
        self._tree.column("#0", width=self.STRIP_W, minwidth=self.STRIP_W,
                          stretch=False, anchor="center")
        for c in self.COLS:
            self._tree.column(c, width=60, minwidth=20, stretch=False,
                              anchor=self.COL_ANCHOR[c])
            self._tree.heading(c, text="")
        self._tree.grid(row=0, column=0, sticky="nsew")
        self._sb = ttk.Scrollbar(body, orient="vertical", command=self._tree.yview)
        self._tree.configure(yscrollcommand=self._sb.set)
        self._sb.grid(row=0, column=1, sticky="ns")
        self._type_images = {}

        # Estado vacío (superpuesto)
        empty = ctk.CTkFrame(body, fg_color=DSG_SURF, corner_radius=0)
        self._empty_title = ctk.CTkLabel(
            empty, text="Sin movimientos",
            font=ctk.CTkFont(size=15, weight="bold"), text_color=DSG_TEXT_BODY,
        )
        self._empty_title.pack(pady=(80, 4))
        self._empty_msg = ctk.CTkLabel(
            empty, text="", font=self._fonts["sub"], text_color=DSG_TEXT_TER,
        )
        self._empty_msg.pack()
        link = ctk.CTkLabel(
            empty, text="Limpiar filtros", font=self._fonts["btn_sec"],
            text_color=DSG_BRAND, cursor="hand2",
        )
        link.pack(pady=(12, 0))
        link.bind("<Button-1>", lambda e: self._clear_filters())
        self._empty = empty

        # Pie
        footer = ctk.CTkFrame(card, fg_color=DSG_SURF_SUB, corner_radius=0, height=44)
        footer.grid(row=2, column=0, sticky="ew")
        footer.grid_propagate(False)
        self._footer_left = ctk.CTkLabel(
            footer, text="", font=self._fonts["footer"], text_color=DSG_TEXT_TER,
            anchor="w",
        )
        self._footer_left.pack(side="left", padx=18)
        self._pager_host = ctk.CTkFrame(footer, fg_color=DSG_SURF_SUB)
        self._pager_host.pack(side="right", padx=18)

        # Interacciones de la tabla
        self._tree.bind("<Double-1>", self._on_double_click)
        self._tree.bind("<Button-3>", self._on_right_click)
        self._tree.bind("<Delete>", self._on_delete_key)
        self._tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        self._ctx_menu = tk.Menu(self, tearoff=0, font=self._fonts["sub"])
        self._ctx_menu.add_command(label="✎ Editar", command=self._edit_ctx)
        self._ctx_menu.add_separator()
        self._ctx_menu.add_command(
            label="✕ Eliminar", foreground=DSG_DANGER, command=self._delete_ctx
        )

        self._widgets_built = True
        self.after(40, lambda: self._ensure_widths(0))

    def _style_header_grid(self, frame):
        # Columna 0 replica la franja #0 del tree; las columnas de datos van +1
        frame.grid_columnconfigure(0, weight=0, minsize=self.STRIP_W)
        for i, m in enumerate(self.COL_MINS):
            frame.grid_columnconfigure(i + 1, weight=self.COL_WEIGHTS[i],
                                       minsize=m)

    def _column_widths(self, width):
        extra = max(width - self.SUM_FIXED, 0)
        widths = []
        for i, (m, wgt) in enumerate(zip(self.COL_MINS, self.COL_WEIGHTS)):
            delta = (extra * wgt) // self.SUM_WEIGHTS
            widths.append(m + delta)
        # Redondeo: reparte lo que falte en la columna de producto (más ancha)
        rest = extra - sum(w - m for w, m in zip(widths, self.COL_MINS))
        if rest:
            widths[self.COLS.index("product")] += rest
        return widths

    def _build_header(self, header):
        for col, text, anchor in self.HEADERS:
            gcol = col + 1  # +1 por la columna 0 que replica la franja #0
            ctk.CTkLabel(
                header, text=text, font=self._fonts["header"],
                text_color="white", anchor=anchor,
            ).grid(row=0, column=gcol, sticky="nswe",
                   padx=(0 if col == 1 else 8, 8 if col != 7 else 0))
        # Reservar espacio a la derecha para la barra de scroll
        header.grid_columnconfigure(len(self.COLS) + 1, weight=0,
                                    minsize=self.SCROLL_RESERVE)

    def _configure_tree_style(self):
        st = ttk.Style(self)
        st.configure(
            self.MOV_STYLE,
            background=DSG_SURF,
            fieldbackground=DSG_SURF,
            foreground=DSG_TEXT,
            rowheight=self.ROW_H,
            font=(self._ui_family, 13),
            borderwidth=0,
            relief="flat",
            indent=0,
        )
        st.map(
            self.MOV_STYLE,
            background=[("selected", DSG_ROW_HOVER)],
            foreground=[("selected", DSG_TEXT)],
        )
        self._tree.tag_configure("row_even", background=DSG_SURF)
        self._tree.tag_configure("row_odd", background=DSG_ROW_ALT)
        self._tree.tag_configure("sel", background=DSG_ROW_HOVER)
        self._tree.tag_configure("flash", background=DSG_FLASH_BG)

    def _type_strip_image(self, mtype):
        """Barrita vertical de color para la fila (columna #0). Cachea por tipo."""
        img = self._type_images.get(mtype)
        if img is not None:
            return img
        color = self.ACCENTS.get(mtype, DSG_BRAND)
        pil = Image.new("RGB", (self.STRIP_PX, self.ROW_H), color=color)
        img = ImageTk.PhotoImage(pil)
        self._type_images[mtype] = img
        return img

    # ── chips ────────────────────────────────────────────────────────────
    def _make_chip(self, parent, key, label, dot_color):
        chip = ctk.CTkFrame(parent, fg_color=DSG_SURF, corner_radius=20,
                            border_width=1, border_color=DSG_BORDER_CHIP,
                            height=34)
        chip.pack_propagate(False)
        dot = ctk.CTkLabel(chip, text="", width=7, height=7, corner_radius=4,
                           fg_color=dot_color)
        dot.pack(side="left", padx=(12, 7), pady=0)
        text = ctk.CTkLabel(chip, text=label, font=self._fonts["chip"],
                            text_color=DSG_TEXT_BODY)
        text.pack(side="left")
        count = ctk.CTkLabel(chip, text="0", font=self._fonts["chip_count"],
                             text_color=DSG_LABEL_UP)
        count.pack(side="left", padx=(6, 12))
        chip.text_label = text
        chip.count_label = count
        chip.key = key
        for w in (chip, dot, text, count):
            w.bind("<Button-1>", lambda e, k=key: self._select_chip(k))
            w.bind("<Enter>", lambda e, c=chip: c.configure(
                border_color=DSG_BORDER_CTRL_HOVER))
            w.bind("<Leave>", lambda e, c=chip: self._refresh_chip_border(c))
        return chip

    def _refresh_chip_border(self, chip):
        active = self._tipo == chip.key
        chip.configure(border_color=DSG_BRAND if active else DSG_BORDER_CHIP)

    def _select_chip(self, key):
        if (self._tipo is None) == (key == "todos"):
            if key == "todos" or self._tipo == key:
                return
        self._tipo = None if key == "todos" else key
        self._pagina = 1
        self._render_chips()
        self._reload()

    def _render_chips(self):
        for key, chip in self._chips.items():
            active = (key == "todos" and self._tipo is None) or (self._tipo == key)
            chip.configure(
                fg_color=DSG_HOVER_BLUE_BG if active else DSG_SURF,
                border_color=DSG_BRAND if active else DSG_BORDER_CHIP,
            )
            chip.text_label.configure(
                text_color=DSG_BRAND if active else DSG_TEXT_BODY,
                font=self._fonts["chip_sel"] if active else self._fonts["chip"],
            )

    def set_type_filter(self, key):
        """Aplica el filtro de tipo. Lo usa el dashboard al tocar una tarjeta."""
        if key in {k for (k, _label, _dot) in self.CHIPS}:
            self._select_chip(key)

    # ── filtros plegables ────────────────────────────────────────────────
    def _toggle_filters(self):
        self._set_filters_visible(not self._filters_expanded)

    def _open_filters(self):
        self._set_filters_visible(True)

    def _set_filters_visible(self, visible):
        self._filters_expanded = visible
        if visible:
            self._filters_panel.pack(fill="x")
            self._filter_toggle.configure(text="▴ Ocultar")
            self.after(60, lambda: self._search_entry.focus_set())
        else:
            self._filters_panel.pack_forget()
            self._filter_toggle.configure(text="▾ Búsqueda y filtros")
        self._update_filter_summary()

    def _active_desc(self):
        parts = []
        if self._busqueda:
            parts.append(f'busca "{self._busqueda}"')
        if self._tipo is not None:
            label = next((lb for (k, lb, _) in self.CHIPS if k == self._tipo),
                         self._tipo)
            parts.append(f"tipo: {label.lower()}")
        return " · ".join(parts)

    def _update_filter_summary(self):
        active = self._active_desc()
        if self._filters_expanded:
            hint = active or "sin filtros activos"
            cursor = "arrow"
        else:
            hint = f"▸ {active or 'sin filtros · clic para buscar o filtrar'}"
            cursor = "hand2"
        if hint != self._last_hint:
            self._filter_hint.configure(text=hint, cursor=cursor)
            self._last_hint = hint
        self._filter_toggle.pack_forget()
        if active:
            self._clear_btn.pack(side="left", padx=(0, 6))
        else:
            self._clear_btn.pack_forget()
        self._filter_toggle.pack(side="left")

    # ── consultas y recarga ──────────────────────────────────────────────
    def _warehouse_id(self):
        return self.app.current_warehouse_id if self.app else None

    def _on_search_changed(self, *_, **__):
        if getattr(self, "_suppress_search", False):
            return
        if self._reload_job:
            self.after_cancel(self._reload_job)
        self._reload_job = self.after(250, self._do_search_reload)

    def _do_search_reload(self):
        self._reload_job = None
        self._busqueda = self._search.get()
        self._pagina = 1
        self._reload()

    def refresh(self):
        self._reload()

    def _reload(self):
        wh = self._warehouse_id()
        types = None if self._tipo is None else self.TYPE_ALIASES[self._tipo]
        try:
            data = query_movements_view(
                warehouse_id=wh, search=self._busqueda,
                movement_types=types, page=self._pagina, per_page=self.PER_PAGE,
            )
        except Exception as e:
            MessageDialog(self, "Error",
                          f"No se pudieron cargar los movimientos:\n{e}",
                          is_error=True)
            return
        self._total = data["total"]
        pages = max((self._total + self.PER_PAGE - 1) // self.PER_PAGE, 1)
        if self._pagina > pages:
            self._pagina = pages
            return self._reload()
        self._counts = data["counts"]
        self._last_update = data["last_update"]
        self._rows = data["rows"]
        if self._flash_id and not any(
            r["id"] == self._flash_id for r in self._rows
        ):
            self._flash_id = None
            self._flash_type = None
        self._update_subtitle()
        self._update_chip_counts()
        self._update_filter_summary()
        self._update_footer()
        self._refresh_table()

    def _overall_total(self):
        return sum(self._counts.values())

    def _update_subtitle(self):
        text = (f"{self._overall_total()} registros · última actualización "
                f"{self._fmt_short(self._last_update)}")
        if text != self._last_sub:
            self._subtitle_var.set(text)
            self._last_sub = text

    def _update_chip_counts(self):
        counts = self._counts
        values = {
            "todos": sum(counts.values()),
            "entrada": counts.get("entrada", 0),
            "salida": counts.get("salida", 0),
            "devolucion": counts.get("devolucion", 0),
            "asignacion": counts.get("asignacion", 0),
            "modificacion": counts.get("modificacion", 0),
            "eliminacion": counts.get("eliminacion", 0)
                          + counts.get("eliminacion_grupo", 0),
        }
        for key, lbl in self._chip_counts.items():
            v = str(values.get(key, 0))
            if self._last_chip_vals.get(key) != v:
                lbl.configure(text=v)
                self._last_chip_vals[key] = v

    # ── tabla (Treeview) ─────────────────────────────────────────────────
    def _refresh_table(self):
        if not self._widgets_built:
            return
        rows = getattr(self, "_rows", [])
        self._tree.delete(*self._tree.get_children())
        if not rows:
            filtered = bool(self._busqueda) or self._tipo is not None
            self._empty_title.configure(
                text="Sin resultados" if filtered else "Sin movimientos")
            self._empty_msg.configure(
                text=("No hay registros que coincidan con el filtro"
                      if filtered else
                      "No hay movimientos registrados en este almacén"))
            self._tree.grid_remove()
            self._sb.grid_remove()
            self._empty.grid(row=0, column=0, sticky="nsew")
            return
        self._empty.grid_remove()
        self._tree.grid()
        self._sb.grid()
        for idx, r in enumerate(rows):
            mtype = r["type"]
            label, _, _ = self.BADGES.get(mtype, (mtype, DSG_SURF, DSG_TEXT))
            fecha, hora = _split_ts(r["timestamp"])
            row_tag = self._row_tag_for_index(idx)
            self._tree.insert(
                "", "end", iid=str(r["id"]),
                image=self._type_strip_image(mtype),
                tags=(row_tag,),
                values=(
                    "",  # pad_l (margen izquierdo)
                    str(r["id"]),
                    label,
                    f"{fecha} · {hora}",
                    r.get("cant_display") or str(r["quantity"] or ""),
                    r["product"] or "—",
                    r["registered_by"] or "",
                    "✎  ✕",
                    "",  # pad_r (margen derecho)
                ),
            )
        if self._flash_id:
            fid = self._flash_id
            iid = str(fid)
            if self._tree.exists(iid):
                self._tree.item(iid, tags=("flash",))
                self._tree.see(iid)
                self.after(650, lambda i=iid: self._finish_flash(i))
            self._flash_id = None
            self._flash_type = None
        self._ensure_widths(0)

    def _row_tag_for_index(self, idx):
        return "row_even" if idx % 2 == 0 else "row_odd"

    def _on_tree_select(self, _event=None):
        """Realza la fila seleccionada sin perder el patrón zebra."""
        try:
            for idx, iid in enumerate(self._tree.get_children()):
                if self._tree.exists(iid):
                    self._tree.item(iid, tags=(self._row_tag_for_index(idx),))
            sel = self._tree.selection()
            if sel and self._tree.exists(sel[0]):
                self._tree.item(sel[0], tags=("sel",))
        except Exception:
            pass

    def _finish_flash(self, iid):
        try:
            if self._tree.exists(iid):
                children = self._tree.get_children()
                if iid in self._tree.selection():
                    self._tree.item(iid, tags=("sel",))
                elif iid in children:
                    idx = children.index(iid)
                    self._tree.item(iid, tags=(self._row_tag_for_index(idx),))
        except Exception:
            pass

    def _ensure_widths(self, attempts=0):
        if not self._widgets_built:
            return
        w = self._tree.winfo_width()
        if w > 60:
            self._apply_widths(w)
        elif attempts < 20:
            self.after(60, lambda: self._ensure_widths(attempts + 1))

    def _apply_widths(self, width=None):
        if not self._widgets_built:
            return
        w = width or self._tree.winfo_width()
        if w < 60:
            return
        self._tree.column("#0", width=self.STRIP_W, minwidth=self.STRIP_W,
                          stretch=False, anchor="center")
        # El ancho disponible para datos excluye la columna #0
        usable = max(w - self.STRIP_W, 60)
        widths = self._column_widths(usable)
        for col, cw in zip(self.COLS, widths):
            self._tree.column(col, width=cw, minwidth=max(20, cw // 2),
                              stretch=False, anchor=self.COL_ANCHOR[col])

    def _on_card_configure(self, event):
        if not self._widgets_built:
            return
        w = event.width
        if abs(w - self._card_last_w) < 8:
            return
        self._card_last_w = w
        if self._resize_job:
            self.after_cancel(self._resize_job)
        self._resize_job = self.after(120, self._flush_resize)

    def _flush_resize(self):
        self._resize_job = None
        if self._rows:
            self._apply_widths()

    # ── acciones sobre filas ─────────────────────────────────────────────
    def _item_under(self, event):
        iid = self._tree.identify_row(event.y)
        return iid

    def _on_double_click(self, event):
        iid = self._tree.identify_row(event.y)
        if iid:
            self._open_info(int(iid))

    def _open_info(self, mid):
        _MovementInfoDialog(
            self,
            movement_id=mid,
            on_edit=lambda m=mid: self._edit_movement(m),
        )

    def _on_right_click(self, event):
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        self._ctx_id = int(iid)
        self._ctx_menu.post(event.x_root, event.y_root)

    def _on_delete_key(self, event):
        sel = self._tree.selection()
        if not sel:
            return "break"
        self._delete_movement(int(sel[0]))
        return "break"

    def _edit_ctx(self):
        if self._ctx_id is not None:
            self._edit_movement(self._ctx_id)

    def _delete_ctx(self):
        if self._ctx_id is not None:
            self._delete_movement(self._ctx_id)

    def _edit_movement(self, mid):
        if self.current_user.get("role") != "admin":
            MessageDialog(self, "Aviso",
                          "Solo un administrador puede editar movimientos.")
            return
        rows = getattr(self, "_rows", [])
        row = next((r for r in rows if r["id"] == mid), None)
        if row and (
            (row.get("item_count") or 0) > 1 or row.get("product_id") in (0, None)
        ):
            MessageDialog(
                self, "Aviso",
                "Los movimientos con varios productos no se pueden editar.\n"
                "Elimínalo y regístralo de nuevo.",
            )
            return
        try:
            mov = get_movement(mid)
        except Exception as e:
            MessageDialog(self, "Error",
                          f"No se pudo cargar el movimiento:\n{e}", is_error=True)
            return
        if not mov:
            return
        _MovementEditDialog(
            self,
            movement=dict(mov),
            current_user=self.current_user,
            on_save=lambda: self.refresh(),
        )

    def _delete_movement(self, mid):
        if self.current_user.get("role") != "admin":
            MessageDialog(self, "Aviso",
                          "Solo un administrador puede eliminar movimientos.")
            return
        rows = getattr(self, "_rows", [])
        row = next((r for r in rows if r["id"] == mid), None)
        label = f"#{mid}" + (f" · {row['product']}" if row else "")
        d = ConfirmDialog(
            self,
            "Eliminar movimiento",
            f"¿Eliminar el movimiento {label}?\nEl stock se reajustará automáticamente.",
            is_danger=True,
        )
        self.wait_window(d)
        if d.result:
            try:
                delete_movement(mid)
                self.refresh()
                MessageDialog(self, "Éxito",
                              "Movimiento eliminado y stock reajustado.")
            except Exception as e:
                MessageDialog(self, "Error", str(e), is_error=True)

    def _register_dialog(self):
        def _on_save():
            if self._reload_job:
                self.after_cancel(self._reload_job)
                self._reload_job = None
            self._suppress_search = True
            try:
                self._search.set("")
            finally:
                self._suppress_search = False
            self._busqueda = ""
            self._tipo = None
            self._pagina = 1
            self._reload()
            if self._rows:
                first = self._rows[0]
                self._flash_id = first["id"]
                self._flash_type = first["type"]
                self._refresh_table()
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

    def _clear_filters(self):
        self._suppress_search = True
        try:
            self._search.set("")
        finally:
            self._suppress_search = False
        self._busqueda = ""
        self._tipo = None
        self._pagina = 1
        self._render_chips()
        self._reload()

    # ── pie / paginación ─────────────────────────────────────────────────
    def _update_footer(self):
        shown = len(getattr(self, "_rows", []))
        text = f"Mostrando {shown} de {self._total} movimientos"
        if text != self._last_footer:
            self._footer_left.configure(text=text)
            self._last_footer = text
        pages = max((self._total + self.PER_PAGE - 1) // self.PER_PAGE, 1)
        sig = (pages, min(self._pagina, pages))
        if sig != self._last_pager_sig:
            self._last_pager_sig = sig
            self._rebuild_pager()

    def _rebuild_pager(self):
        for w in self._pager_host.winfo_children():
            w.destroy()
        pages = max((self._total + self.PER_PAGE - 1) // self.PER_PAGE, 1)
        if pages <= 1:
            return

        def _page_btn(label, target, active=False, enabled=True, kind="page"):
            b = ctk.CTkButton(
                self._pager_host, text=label,
                font=self._fonts["pager"] if active else self._fonts["pager_off"],
                fg_color=DSG_BRAND if active else DSG_SURF,
                hover_color=DSG_BRAND if active else DSG_ROW_HOVER,
                text_color="white" if active else DSG_TEXT_SEC,
                border_width=1 if not active else 0,
                border_color=DSG_BORDER_CHIP,
                corner_radius=7, width=44 if kind != "page" else 34, height=30,
                state="normal" if enabled else "disabled",
            )
            if enabled:
                b.configure(command=lambda p=target: self._goto(p))
            b.pack(side="left", padx=(0, 4))
            return b

        _page_btn("Anterior", self._pagina - 1,
                  enabled=self._pagina > 1, kind="nav")
        lo = max(1, self._pagina - 2)
        hi = min(pages, lo + 4)
        lo = max(1, hi - 4)
        nums = list(range(lo, hi + 1))
        if lo > 1:
            _page_btn("1", 1)
            if lo > 2:
                _page_btn("…", None, enabled=False, kind="nav")
        for n in nums:
            _page_btn(str(n), n, active=(n == self._pagina))
        if hi < pages:
            if hi < pages - 1:
                _page_btn("…", None, enabled=False, kind="nav")
            _page_btn(str(pages), pages)
        _page_btn("Siguiente", self._pagina + 1,
                  enabled=self._pagina < pages, kind="nav")

    def _goto(self, page):
        if page < 1:
            return
        self._pagina = page
        self._reload()

    def _warehouse_name(self):
        if not self.app:
            return ""
        for w in getattr(self.app, "_warehouses", []) or []:
            if w["id"] == self.app.current_warehouse_id:
                return w["name"]
        return ""

    def _export(self):
        wh = self._warehouse_id()
        types = None if self._tipo is None else self.TYPE_ALIASES[self._tipo]
        self._set_export_busy(True)
        self.update_idletasks()
        try:
            rows = get_movements_flat(
                warehouse_id=wh, search=self._busqueda, movement_types=types
            )
        finally:
            self._set_export_busy(False)
        if not rows:
            MessageDialog(self, "Aviso",
                          "No hay movimientos para exportar con el filtro actual.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
            initialfile="movimientos.pdf",
        )
        if not path:
            return
        self._set_export_busy(True)
        self.update_idletasks()
        try:
            export_movements(
                path,
                movements=rows,
                warehouse_name=self._warehouse_name(),
                filters_text=self._active_desc(),
                generated_by=self.current_user.get("username", ""),
            )
        except Exception as e:
            MessageDialog(self, "Error", f"No se pudo generar el PDF:\n{e}")
            return
        finally:
            self._set_export_busy(False)
        MessageDialog(self, "Éxito", f"Reporte PDF generado en:\n{path}")

    def _set_export_busy(self, busy):
        self._export_btn.configure(
            state="disabled" if busy else "normal",
            text="Generando…" if busy else "↓  Exportar PDF",
        )

    # ── utilidades ───────────────────────────────────────────────────────
    @staticmethod
    def _fmt_short(ts):
        if not ts:
            return "—"
        try:
            dt = datetime.strptime(str(ts)[:19], "%Y-%m-%d %H:%M:%S")
            return dt.strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return str(ts)[:16]





class _MovementInfoDialog(BaseDialog):
    """Ventana de información detallada de un movimiento (doble clic).

    Diseño en dos columnas con cabecera teñida por el tipo, botón copiar y
    cierre con Escape.
    """
    EDITABLE = {"entrada", "salida", "devolucion", "asignacion"}

    # mtype -> (etiqueta, descripción, efecto en inventario, fondo, texto)
    TYPE_META = {
        "entrada": ("Entrada",
                    "Ingreso de mercancía o material al inventario.",
                    "Aumenta el stock del producto",
                    DSG_BADGE_ENTRADA_BG, DSG_BADGE_ENTRADA_FG),
        "salida": ("Salida",
                   "Entrega de material a un empleado.",
                   "Reduce el stock del producto",
                   DSG_BADGE_SALIDA_BG, DSG_BADGE_SALIDA_FG),
        "devolucion": ("Devolución",
                       "Retorno de material que estaba entregado.",
                       "Aumenta el stock del producto",
                       DSG_BADGE_DEVOLUCION_BG, DSG_BADGE_DEVOLUCION_FG),
        "asignacion": ("Asignación",
                       "Asignación de material o vehículo a personal.",
                       "Reduce el stock (quedó asignado)",
                       DSG_BADGE_ASIGNACION_BG, DSG_BADGE_ASIGNACION_FG),
        "modificacion": ("Modificación",
                         "Corrección o ajuste de datos de un registro.",
                         "No cambia el stock",
                         DSG_BADGE_MODIFICACION_BG, DSG_BADGE_MODIFICACION_FG),
        "eliminacion": ("Eliminación",
                        "Baja de un producto o de unidades del inventario.",
                        "Registro eliminado / sin stock",
                        DSG_BADGE_ELIMINACION_BG, DSG_BADGE_ELIMINACION_FG),
        "eliminacion_grupo": ("Eliminación de grupo",
                              "Baja de un grupo o lote de productos.",
                              "Registro eliminado / sin stock",
                              DSG_BADGE_ELIMINACION_BG, DSG_BADGE_ELIMINACION_FG),
    }

    def __init__(self, parent, movement_id, on_edit=None):
        super().__init__(parent)
        self.title("Detalle de movimiento")
        self.geometry("960x800")
        self.minsize(840, 580)
        self.configure(fg_color=DSG_BG)
        self.transient(parent)
        self._on_edit = on_edit

        try:
            detail = get_movement_detail(movement_id)
        except Exception as e:
            MessageDialog(self, "Error",
                          f"No se pudo cargar el movimiento:\n{e}", is_error=True)
            self.destroy()
            return
        if not detail:
            MessageDialog(self, "Error", "No se encontró el movimiento.",
                          is_error=True)
            self.destroy()
            return
        self._detail = detail
        mtype = detail["type"]
        tlabel, tdesc, teffect, tbg, tfg = self.TYPE_META.get(
            mtype, (mtype, "", "", DSG_HOVER_BLUE_BG, DSG_BRAND))

        # ── Cabecera teñida por el tipo ──
        header = ctk.CTkFrame(self, fg_color=tfg, height=136, corner_radius=0)
        header.pack(fill="x")
        header.pack_propagate(False)
        pill = ctk.CTkFrame(header, fg_color=DSG_SURF, corner_radius=6)
        pill.pack(anchor="w", padx=20, pady=(18, 6))
        ctk.CTkLabel(pill, text="●", font=ctk.CTkFont(size=12),
                     text_color=tfg).pack(side="left", padx=(8, 4), pady=4)
        ctk.CTkLabel(pill, text=tlabel, font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=tfg).pack(side="left", padx=(0, 12), pady=4)
        ctk.CTkLabel(
            header, text=f"Movimiento #{detail['id']}",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color="white", anchor="w",
        ).pack(anchor="w", padx=20)
        ctk.CTkLabel(
            header, text=f"{detail['type']}  ·  {detail['timestamp']}",
            font=ctk.CTkFont(size=15), text_color=DSG_SURF_SUB, anchor="w",
        ).pack(anchor="w", padx=20, pady=(6, 18))

        # ── Cuerpo a dos columnas ──
        body = ctk.CTkScrollableFrame(self, fg_color=DSG_BG, corner_radius=0)
        body.pack(fill="both", expand=True, padx=20, pady=16)
        outer = ctk.CTkFrame(body, fg_color=DSG_BG)
        outer.pack(fill="x")

        left = self._card(outer)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = self._card(outer)
        right.pack(side="right", fill="both", expand=True, padx=(8, 0))

        # ── Columna izquierda ──
        self._section(left, "Tipo de movimiento")
        self._add_pill_row(left, "Tipo", tbg, tfg, tlabel)
        self._add_row(left, "Efecto", teffect, wrap=250, color=DSG_BRAND)
        if tdesc:
            self._add_row(left, "Descripción", tdesc, wrap=300)

        self._section(left, "Movimiento")
        items = detail.get("items") or []
        q_label = "Cantidades" if len(items) > 1 else "Cantidad"
        self._add_row(left, "Fecha / hora", detail["timestamp"] or "—", wrap=300)
        self._add_row(left, q_label, self._quantity_text(detail) or "—",
                      wrap=300)
        self._add_row(left, "Empleado", self._employee_text(detail), wrap=300)
        self._add_row(left, "Registrado por",
                      detail.get("registered_by") or "—")
        self._add_row(left, "Almacén", detail.get("warehouse") or "—")

        # ── Columna derecha ──
        self._section(right, "Productos" if items else "Producto")
        if items:
            for it in items:
                self._item_line(right, it)
        else:
            product = detail.get("product") or "—"
            brand = detail.get("brand") or ""
            unit = detail.get("unit") or ""
            if brand:
                product = f"{product} · {brand}"
            if unit:
                product = f"{product} ({unit})"
            self._add_row(right, "Producto", product, product=True, wrap=380)

        self._section(right, "Notas")
        notes = detail.get("notes") or "Sin notas"
        box = ctk.CTkFrame(right, fg_color=FONDO_MULTISELECT, corner_radius=8)
        box.pack(fill="x", padx=16, pady=(8, 16))
        ctk.CTkLabel(
            box, text=str(notes), font=ctk.CTkFont(size=16),
            text_color=DSG_TEXT_SEC, justify="left", anchor="w",
            wraplength=390,
        ).pack(fill="x", padx=12, pady=10)

        # ── Pie de acciones ──
        foot = ctk.CTkFrame(self, fg_color=DSG_SURF_SUB, corner_radius=0, height=64)
        foot.pack(fill="x")
        foot.pack_propagate(False)

        if on_edit is not None and mtype in self.EDITABLE:
            ctk.CTkButton(
                foot, text="✎  Editar", font=ctk.CTkFont(size=15, weight="bold"),
                fg_color=DSG_SURF, hover_color=DSG_ROW_HOVER,
                border_width=1, border_color=DSG_BORDER_CTRL,
                text_color=DSG_BRAND, corner_radius=9, height=40,
                command=self._edit,
            ).pack(side="left", padx=(20, 8), pady=12)
        ctk.CTkButton(
            foot, text="⧉  Copiar", font=ctk.CTkFont(size=15),
            fg_color=DSG_SURF, hover_color=DSG_ROW_HOVER,
            border_width=1, border_color=DSG_BORDER_CTRL,
            text_color=DSG_TEXT_SEC, corner_radius=9, height=40,
            command=self._copy,
        ).pack(side="left", padx=(8, 8), pady=12)
        ctk.CTkButton(
            foot, text="Cerrar", font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=DSG_BRAND, hover_color=DSG_BRAND_DARK,
            text_color="white", corner_radius=9, height=40,
            command=self.destroy,
        ).pack(side="right", padx=20, pady=12)

        self.bind("<Escape>", lambda e: self.destroy())
        show_centered(self)
        self.after(60, self.grab_set)

    # ── contenido ────────────────────────────────────────────────────────
    def _card(self, parent):
        card = ctk.CTkFrame(parent, fg_color=DSG_SURF, corner_radius=12,
                            border_width=1, border_color=DSG_BORDER)
        return card

    def _section(self, card, text):
        ctk.CTkLabel(
            card, text=text.upper(), font=ctk.CTkFont(size=15, weight="bold"),
            text_color=DSG_BRAND, anchor="w",
        ).pack(anchor="w", padx=16, pady=(18, 0))
        ctk.CTkFrame(card, fg_color=DSG_ROW_SEP, height=1, corner_radius=0,
                     ).pack(fill="x", padx=16, pady=(5, 0))

    @staticmethod
    def _quantity_text(detail):
        """Cantidades agrupadas por unidad (nunca un número sin su unidad)."""
        items = detail.get("items") or []
        if items:
            totals = {}
            order = []
            for it in items:
                unit = it.get("unit") or "und"
                qty = it.get("qty")
                try:
                    qty = int(qty) if qty not in (None, "") else 0
                except (TypeError, ValueError):
                    qty = 0
                totals[unit] = totals.get(unit, 0) + qty
                if unit not in order:
                    order.append(unit)
            if order:
                return " · ".join(f"{totals[u]} {u}" for u in order)
        # Sin ítems (legacy): usar la cantidad de cabecera
        qty = detail.get("quantity")
        unit = detail.get("unit") or ""
        text = str(qty) if qty is not None else "—"
        return f"{text} {unit}".strip() if unit else text

    @staticmethod
    def _employee_text(detail):
        emp = detail.get("employee")
        cargo = detail.get("cargo") or ""
        if not emp or emp == "-":
            return "—"
        return f"{emp} ({cargo})" if cargo else emp

    def _add_pill_row(self, parent, label, bg, fg, text):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(12, 0))
        ctk.CTkLabel(
            row, text=label, font=ctk.CTkFont(size=14, weight="bold"),
            text_color=DSG_TEXT_SEC, anchor="w", width=110,
        ).pack(side="left", anchor="n")
        pill = ctk.CTkFrame(row, fg_color=bg, corner_radius=6)
        pill.pack(side="left", padx=(8, 0))
        ctk.CTkLabel(pill, text="●", font=ctk.CTkFont(size=12),
                     text_color=fg).pack(side="left", padx=(7, 3), pady=3)
        ctk.CTkLabel(pill, text=text, font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=fg).pack(side="left", padx=(0, 10), pady=3)

    def _item_line(self, parent, item):
        name = item.get("name") or "—"
        brand = item.get("brand") or ""
        qty = item.get("qty")
        unit = item.get("unit") or ""
        head = name if not brand else f"{name} · {brand}"
        label = f"{qty} {unit}".strip() if qty not in (None, "") else "—"
        seriales = item.get("seriales")
        sub = ""
        if seriales:
            sub = f"\nSerial(es): {seriales}"
        text = f"{label} · {head}{sub}"
        self._add_row(parent, "", text, wrap=390, full=True)

    def _add_row(self, parent, label, value, wrap=None, full=False,
                 product=False, color=None):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=16, pady=(11, 0))
        if not full and label:
            ctk.CTkLabel(
                row, text=label, font=ctk.CTkFont(size=14, weight="bold"),
                text_color=DSG_TEXT_SEC, anchor="w", width=110,
            ).pack(side="left", anchor="n")
        kwargs = {"font": (ctk.CTkFont(size=16, weight="bold")
                           if product else ctk.CTkFont(size=16)),
                  "text_color": color or (DSG_BRAND if product else DSG_TEXT),
                  "anchor": "w", "justify": "left", "fg_color": "transparent"}
        if wrap:
            kwargs["wraplength"] = wrap
        val = ctk.CTkLabel(row, text=str(value) or "—", **kwargs)
        val.pack(side="left", fill="x", expand=True, padx=(10, 0))
        return val

    def _copy(self):
        d = self._detail
        mtype = d["type"]
        tlabel, tdesc, teffect, _, _ = self.TYPE_META.get(
            mtype, (mtype, "", "", DSG_HOVER_BLUE_BG, DSG_BRAND))
        items = d.get("items") or []
        q_label = "Cantidades" if len(items) > 1 else "Cantidad"
        lines = [
            f"Movimiento #{d['id']}",
            f"Tipo: {tlabel} ({d['type']})",
            f"Fecha/hora: {d['timestamp']}",
            f"{q_label}: {self._quantity_text(d)}",
            f"Producto: {d.get('product') or '—'}",
            f"Empleado: {self._employee_text(d)}",
            f"Registrado por: {d.get('registered_by') or '—'}",
            f"Almacén: {d.get('warehouse') or '—'}",
        ]
        for it in items:
            name = it.get("name") or "—"
            brand = it.get("brand") or ""
            qty = it.get("qty")
            unit = it.get("unit") or ""
            seg = f"{qty} {unit}".strip() if qty not in (None, "") else ""
            desc = name if not brand else f"{name} · {brand}"
            lines.append(f"Detalle: {seg} {desc}".strip())
            if it.get("seriales"):
                lines.append(f"Serial(es): {it['seriales']}")
        lines.append(f"Efecto: {teffect}")
        lines.append(f"Descripción: {tdesc}")
        if d.get("notes"):
            lines.append(f"Notas: {d['notes']}")
        try:
            self.clipboard_clear()
            self.clipboard_append("\n".join(lines))
        except Exception:
            pass

    def _edit(self):
        self.destroy()
        if self._on_edit:
            self._on_edit()


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
        right_text_fn=None,
        single=False,
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._items = [dict(item) for item in items]
        self._item_key = item_key
        self._item_label = item_label
        self._right_text_fn = right_text_fn
        self._selected = set()
        self._quantities = {}
        self._show_quantity = show_quantity
        self._single = single
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

        self._row_marks = {}
        self._qty_entries = {}
        self._display_items = []
        self._render_limit = 40
        self._filter_items()

    def _save_quantities(self):
        """Guarda los valores escritos en las casillas antes de reconstruir."""
        for item_id, entry in self._qty_entries.items():
            try:
                val = int(entry.get().strip())
                if val >= 1:
                    self._quantities[item_id] = val
            except (ValueError, TypeError):
                pass

    def _filter_items(self):
        self._save_quantities()
        for w in self._list_frame.winfo_children():
            w.destroy()
        self._row_marks = {}
        self._qty_entries = {}

        search = self.search_var.get().lower()
        matches = [
            item for item in self._items if search in self._item_label(item).lower()
        ]
        self._display_items = matches[: self._render_limit]

        sans = _sans_family()
        for item in self._display_items:
            item_id = item[self._item_key]
            selected = item_id in self._selected
            bg = FONDO_ROW_PAR if selected else "white"

            row = tk.Frame(self._list_frame, bg=bg)
            row.pack(fill="x", pady=1)

            mark = tk.Label(
                row,
                text="☑" if selected else "☐",
                bg=bg,
                fg=AZUL_MARINO if selected else GRIS_AZULADO,
                font=(sans, 15),
            )
            mark.pack(side="left", padx=(6, 4))

            name = tk.Label(
                row,
                text=self._item_label(item)[:40],
                bg=bg,
                fg=TEXTO_MOV_FIELD,
                font=(sans, 12),
                anchor="w",
            )
            name.pack(side="left", fill="x", expand=True)

            if self._show_quantity:
                unit = tk.Label(
                    row,
                    text=str(item.get("unit") or "und"),
                    bg=bg,
                    fg=GRIS_AZULADO,
                    font=(sans, 11, "bold"),
                )
                unit.pack(side="right", padx=(0, 6))
                qty_entry = tk.Entry(
                    row, width=5, justify="center", relief="solid", bd=1,
                    highlightthickness=0,
                )
                qty_entry.insert(0, str(self._quantities.get(item_id, 1)))
                qty_entry.pack(side="right", padx=(0, 4), pady=3)
                self._qty_entries[item_id] = qty_entry

            if self._right_text_fn is not None:
                chip = tk.Label(
                    row,
                    text=self._right_text_fn(item),
                    bg=FONDO_MULTI_QTY,
                    fg=GRIS_AZULADO,
                    font=(sans, 11),
                    padx=6,
                )
                chip.pack(side="right", padx=(0, 4), pady=3)

            for w in (row, mark, name):
                w.bind("<Button-1>", lambda e, i=item_id: self._toggle(i))
            self._row_marks[item_id] = (row, mark)

        if len(matches) > self._render_limit:
            rest = len(matches) - self._render_limit
            ctk.CTkButton(
                self._list_frame,
                text=f"Ver más ({rest})",
                height=28,
                fg_color=FONDO_MULTI_QTY,
                text_color=TEXTO_MOV_FIELD,
                hover_color=FONDO_ROW_PAR,
                command=self._show_more,
            ).pack(fill="x", pady=4)

    def _show_more(self):
        self._render_limit += 40
        self._filter_items()

    def _toggle(self, item_id):
        if item_id in self._selected:
            self._selected.discard(item_id)
            selected = False
        else:
            if self._single:
                for other in list(self._selected):
                    self._selected.discard(other)
                    m = self._row_marks.get(other)
                    if m:
                        r, mk = m
                        r.configure(bg="white")
                        mk.configure(text="☐", bg="white", fg=GRIS_AZULADO)
                self._selected.clear()
            self._selected.add(item_id)
            self._quantities.setdefault(item_id, 1)
            selected = True
        self._count_label.configure(text=f"{len(self._selected)} seleccionados")
        marks = self._row_marks.get(item_id)
        if marks:
            row, mark = marks
            bg = FONDO_ROW_PAR if selected else "white"
            row.configure(bg=bg)
            mark.configure(
                text="☑" if selected else "☐",
                bg=bg,
                fg=AZUL_MARINO if selected else GRIS_AZULADO,
            )

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


class _MovementDialog(BaseDialog):
    def __init__(self, parent, current_user, on_save, warehouse_id=None):
        super().__init__(parent)
        self.warehouse_id = warehouse_id
        self.title("Registrar Movimiento")
        self.geometry("900x750")
        self.minsize(860, 650)
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
        self._left = left
        self._right = right

        # La botonera se crea primero (anclada al pie) y la ventana se
        # muestra de inmediato; el contenido pesado se construye en el
        # siguiente ciclo para que la apertura se sienta instantánea.
        btns = ctk.CTkFrame(main, fg_color=FONDO_BTN_PIE)
        btns.pack(side="bottom", fill="x", padx=20, pady=15)
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

        show_centered(self)
        self.after(50, self.grab_set)
        self.after(20, self._build_content)

    def _build_content(self):
        if not self.winfo_exists():
            return
        left = self._left
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
        ).pack(side="left", padx=(0, 10))
        self._mov_type = ctk.StringVar(value="salida")
        self._mov_btns = {}
        for val in ("salida", "devolucion"):
            label, fg, hover = TYPE_STYLES[val]
            btn = ctk.CTkButton(
                type_frame,
                text=label,
                width=130,
                height=32,
                fg_color=fg,
                hover_color=hover,
                text_color="white",
                font=ctk.CTkFont(size=13, weight="bold"),
                command=lambda v=val: self._set_movement_type(v),
            )
            btn.pack(side="left", padx=(0, 8))
            self._mov_btns[val] = btn
        self._update_movement_type_buttons()

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

        # Lista de productos (se llena según el tipo de movimiento)
        self._prod_select = _SearchableMultiSelect(
            left,
            [],
            "key",
            lambda g: "",
            placeholder="Buscar producto...",
            fg_color=FONDO_MULTISELECT,
            show_quantity=True,
        )
        self._prod_select.pack(fill="both", expand=True, padx=15, pady=(0, 15))


        self.after(30, self._build_content_right)

    def _build_content_right(self):
        if not self.winfo_exists():
            return
        right = self._right
        self._right_heading = ctk.CTkLabel(
            right,
            text="ASIGNACIÓN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        )
        self._right_heading.pack(anchor="w", padx=15, pady=(15, 10))

        self._emp_frame = ctk.CTkFrame(right, fg_color="transparent")
        self._emp_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(
            self._emp_frame,
            text="👤 Empleado",
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
            single=True,
        )
        self._emp_select.pack(fill="x")

        self.after(30, self._build_content_tail)

    def _build_content_tail(self):
        if not self.winfo_exists():
            return
        right = self._right
        self._veh_frame = ctk.CTkFrame(right, fg_color="transparent")
        self._veh_frame.pack(fill="x", padx=15, pady=(0, 10))
        ctk.CTkLabel(
            self._veh_frame,
            text="🚚 Vehículo",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        ).pack(anchor="w", pady=(5, 5))
        vehicle_names = [
            f"{v['brand']} - {v['plate']}" for v in self._vehicles
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

        self._notes_heading = ctk.CTkLabel(
            right,
            text="📝 NOTAS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        )
        self._notes_heading.pack(anchor="w", padx=15, pady=(15, 5))
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
        self._apply_movement_layout(self._mov_type.get())

    def _ensure_serials_ui(self):
        if getattr(self, "_serial_frame", None) is not None:
            return
        left = self._left
        self._serial_frame = ctk.CTkFrame(left, fg_color="transparent")
        self._serial_heading = ctk.CTkLabel(
            self._serial_frame,
            text="SERIALES PENDIENTES DE DEVOLUCIÓN",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXTO_MOV_FIELD,
        )
        self._serial_heading.pack(anchor="w", pady=(10, 5))
        search_serial_frame = ctk.CTkFrame(self._serial_frame, fg_color="white")
        search_serial_frame.pack(fill="x")
        ctk.CTkLabel(
            search_serial_frame, text="🔍", text_color=TEXTO_SECUNDARIO
        ).pack(side="left", padx=(6, 2))
        self._serial_search_var = ctk.StringVar()
        self._serial_search_var.trace_add("write", lambda *_: self._load_serials_pending())
        ctk.CTkEntry(
            search_serial_frame,
            textvariable=self._serial_search_var,
            placeholder_text="Buscar por nombre o serial...",
            border_width=0,
            fg_color="white",
            text_color=TEXTO_MOV_FIELD,
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))
        self._serial_inner = ctk.CTkScrollableFrame(
            self._serial_frame, fg_color="white", height=200
        )
        self._serial_inner.pack(fill="both", expand=True, pady=(5, 0))
        self._serial_checkvars = {}
        self._serial_frame.pack_forget()  # oculto hasta seleccionar devolucion




    def _autosize(self):
        """Ajusta al tamaño cómodo sin contraer por debajo del mínimo."""
        self.update_idletasks()
        w = max(self.winfo_reqwidth(), 900)
        h = max(self.winfo_reqheight(), 720)
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        w, h = min(w, sw - 60), min(h, sh - 120)
        x, y = self.winfo_x(), self.winfo_y()
        self.geometry(f"{w}x{h}+{max(x, 0)}+{max(y, 0)}")

    def _update_movement_type_buttons(self):
        active = self._mov_type.get()
        for val, btn in self._mov_btns.items():
            if val == active:
                btn.configure(
                    border_width=2,
                    border_color="white",
                    font=ctk.CTkFont(size=13, weight="bold"),
                )
            else:
                btn.configure(
                    border_width=0,
                    font=ctk.CTkFont(size=13, weight="normal"),
                )

    def _set_movement_type(self, type_):
        if self._mov_type.get() == type_:
            return
        self._mov_type.set(type_)
        self._update_movement_type_buttons()
        self._apply_movement_layout(type_)

    def _load_product_options(self, type_):
        """Carga los grupos de producto disponibles según el tipo (salida/devolución)."""
        if type_ == "salida":
            grouped = get_movement_available_products(warehouse_id=self.warehouse_id)
            metric = "available"
            suffix = "disp."
        else:
            grouped = get_products_pending_return_grouped(
                warehouse_id=self.warehouse_id
            )
            metric = "pending"
            suffix = "pend."

        products = []
        self._group_items = {}
        for g in grouped:
            d = dict(g)
            d["key"] = f"{g['name']}||{g['brand']}"
            self._group_items[d["key"]] = d
            products.append(d)

        def label_fn(g):
            brand = f"{g['brand']}" if g.get("brand") else ""
            return f"{g['name']}{' · ' + brand if brand else ''}"

        def chip_fn(g, m=metric, s=suffix):
            unit = g.get("unit") or "und"
            return f"{g.get(m, 0)} {unit} {s}"

        self._prod_select._items = products
        self._prod_select._item_label = label_fn
        self._prod_select._right_text_fn = chip_fn
        self._prod_select._selected = set()
        self._prod_select._quantities = {}
        self._prod_select._filter_items()

    def _apply_movement_layout(self, type_):
        """Reorganiza el panel según el tipo: en salida pide empleado/vehículo;
        en devolución pide cantidad o seriales pendientes."""
        self._prod_select.pack_forget()
        if getattr(self, "_serial_frame", None) is not None:
            self._serial_frame.pack_forget()
        if type_ == "salida":
            self._emp_frame.pack(
                before=self._notes_heading, fill="x", padx=15, pady=(0, 10)
            )
            self._veh_frame.pack(
                before=self._notes_heading, fill="x", padx=15, pady=(0, 10)
            )
            self._prod_select.pack(fill="both", expand=True, padx=15, pady=(0, 15))
            self._right_heading.configure(text="ASIGNACIÓN A EMPLEADO")
        else:
            self._emp_frame.pack_forget()
            self._veh_frame.pack_forget()
            self._prod_select.pack(fill="x", padx=15, pady=(0, 5))
            self._ensure_serials_ui()
            self._serial_frame.pack(fill="both", expand=True, padx=15, pady=(0, 10))
            self._right_heading.configure(text="MATERIAL A DEVOLVER")
            self._load_serials_pending()
        self._load_product_options(type_)
        self.after(30, self._autosize)

    def _load_serials_pending(self):
        """Carga la lista de seriales en estado 'no disponible' (pendientes de devolucion)."""
        for w in self._serial_inner.winfo_children():
            w.destroy()
        self._serial_checkvars = {}

        search = self._serial_search_var.get().strip() if hasattr(self, "_serial_search_var") else ""
        serials = [dict(s) for s in get_serials_pending_return(
            search=search, warehouse_id=self.warehouse_id
        )]
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

    def _save(self):
        if not hasattr(self, "_prod_select"):
            MessageDialog(self, "Aviso",
                          "La ventana aún se está cargando. Intenta de nuevo.")
            return
        type_ = self._mov_type.get()
        notes_w = getattr(self, "notes_e", None)
        notes = notes_w.get().strip() if notes_w is not None else ""
        selected_employees = (
            self._emp_select.get_selected() if hasattr(self, "_emp_select") else []
        )

        items = []
        try:
            if type_ == "salida":
                if not selected_employees:
                    MessageDialog(
                        self, "Aviso", "Selecciona al menos un empleado para salida."
                    )
                    return
                selected_raw = self._prod_select.get_selected()
                if not selected_raw:
                    MessageDialog(self, "Aviso", "Selecciona al menos un producto.")
                    return
                for key, quantity in selected_raw:
                    if quantity < 1:
                        continue
                    g = self._group_items.get(key)
                    if not g:
                        continue
                    is_serial = (
                        g.get("unit") == "und"
                        and g.get("has_serial")
                        and not g.get("total_quantity")
                    )
                    items.append({
                        "name": g["name"],
                        "brand": g.get("brand", ""),
                        "qty": quantity,
                        "unit": g.get("unit") or "und",
                        "kind": "serial" if is_serial else "quantity",
                    })
                if not items:
                    MessageDialog(
                        self, "Aviso",
                        "Ingresa cantidades válidas para al menos un producto.",
                    )
                    return
                create_compound_movement(
                    "salida", self.current_user["id"], items, notes,
                    warehouse_id=self.warehouse_id,
                    employee_id=selected_employees[0],
                )
            else:
                selected_raw = self._prod_select.get_selected()
                has_qty = bool(selected_raw)
                has_serials = any(
                    v.get() for v in self._serial_checkvars.values()
                ) if hasattr(self, "_serial_checkvars") else False

                if not has_qty and not has_serials:
                    MessageDialog(
                        self, "Aviso",
                        "Selecciona productos por cantidad o marca seriales a devolver.",
                    )
                    return

                if has_qty:
                    for key, quantity in selected_raw:
                        if quantity < 1:
                            continue
                        g = self._group_items.get(key)
                        if not g:
                            continue
                        items.append({
                            "name": g["name"],
                            "brand": g.get("brand", ""),
                            "qty": quantity,
                            "unit": g.get("unit") or "und",
                            "kind": "quantity",
                        })

                if has_serials:
                    checked = [
                        pid for pid, var in self._serial_checkvars.items() if var.get()
                    ]
                    if checked:
                        brief = {
                            dict(b)["id"]: dict(b)
                            for b in get_products_brief(checked)
                        }
                        grouped = {}
                        for pid in checked:
                            b = brief.get(pid)
                            if not b:
                                continue
                            key = (b["name"], b["brand"] or "")
                            grouped.setdefault(key, []).append(pid)
                        for (nm, br), ids in grouped.items():
                            items.append({
                                "name": nm, "brand": br, "qty": len(ids),
                                "unit": "und", "kind": "serial", "product_ids": ids,
                            })

                if not items:
                    MessageDialog(self, "Aviso", "No hay nada para devolver.")
                    return

                create_compound_movement(
                    "devolucion", self.current_user["id"], items, notes,
                    warehouse_id=self.warehouse_id,
                )
        except ValueError as e:
            MessageDialog(self, "Error", str(e), is_error=True)
            return
        except Exception as e:
            MessageDialog(
                self, "Error", f"No se pudo registrar el movimiento:\n{e}",
                is_error=True,
            )
            return

        self.on_save()
        self.destroy()


class _MovementEditDialog(BaseDialog):
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
            info,
            text=str(movement["product"]),
            font=ctk.CTkFont(size=13),
            text_color=GRIS_AZULADO,
            justify="left",
            wraplength=430,
        ).pack(side="left", padx=12, pady=8)

        _lbl("Tipo")
        editable_types = ["entrada", "salida", "devolucion"]
        current_type = movement["type"]
        if current_type not in editable_types:
            editable_types = [current_type] + editable_types
        self.type_opt = ctk.CTkOptionMenu(
            body, height=36,
            font=ctk.CTkFont(size=13), text_color="white",
            button_color=AZUL_MARINO, button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO, dropdown_font=ctk.CTkFont(size=13),
            values=editable_types,
        )
        self.type_opt.set(current_type)
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

        show_centered(self)
        self.after(50, self.grab_set)

    def _save(self):
        try:
            qty = int(self.qty_e.get().strip() or 1)
        except ValueError:
            MessageDialog(self, "Aviso", "Cantidad inválida.")
            return
        if qty < 1:
            MessageDialog(self, "Aviso", "La cantidad debe ser mayor a 0.")
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
            MessageDialog(self, "Error", str(e), is_error=True)
            return
        self.on_save()
        self.destroy()

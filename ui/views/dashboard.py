import customtkinter as ctk
from ui.colors import *

try:
    from PIL import Image
except ImportError:
    Image = None

from ui.dashboard_widgets import (
    make_dashboard_movements_list,
    setup_dashboard_movements_style,
)
from database.repository import get_dashboard_stats


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, current_user, on_navigate=None, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)  # Fondo Base
        self.current_user = current_user
        self.app = app
        self._on_navigate = on_navigate
        self.last_refresh_time = 0  # Timestamp of last refresh
        self.min_refresh_interval = (
            2000  # Minimum interval between refreshes in milliseconds
        )
        self.loading_label = (
            None  # Indicador de carga (se inicializa cuando se necesita)
        )
        setup_dashboard_movements_style()
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _go(self, view_name: str, filter_fn=None):
        if self._on_navigate:
            self._on_navigate(view_name, filter_fn)

    def _make_card_clickable(self, card, action, accent_color):
        """Aplica hover + cursor + click a card y todos sus hijos."""
        def _bind(w):
            try:
                w.configure(cursor="hand2")
            except Exception:
                pass
            w.bind("<Enter>", on_enter)
            w.bind("<Leave>", on_leave)
            w.bind("<Button-1>", on_click)
            for child in w.winfo_children():
                _bind(child)

        def on_enter(_e):
            card.configure(fg_color=FONDO_ROW_IMPAR, border_color=accent_color)

        def on_leave(_e):
            card.configure(fg_color="white", border_color="white")

        def on_click(_e):
            action()

        _bind(card)

    def _build(self):
        # Header container for padding
        header_container = ctk.CTkFrame(self, fg_color="transparent")
        header_container.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))

        # Header with rounded corners inside the container
        hdr = ctk.CTkFrame(header_container, fg_color=AZUL_NOCHE, corner_radius=10)
        hdr.pack(fill="both", expand=True)

        if Image:
            try:
                logo_dash = ctk.CTkImage(
                    Image.open("img/logo_dashboard.png"), size=(140, 100)
                )
                ctk.CTkLabel(hdr, image=logo_dash, text="").pack(
                    side="left", padx=10, pady=8
                )
            except Exception:
                pass

        title_frame = ctk.CTkFrame(hdr, fg_color="transparent")
        title_frame.pack(side="left", fill="x", expand=True)
        ctk.CTkLabel(
            title_frame,
            text="Dashboard",
            font=ctk.CTkFont(size=25, weight="bold"),
            text_color=BLANCO_CALIDO,
        ).pack(anchor="w", padx=(0, 20), pady=(12, 2))
        ctk.CTkLabel(
            title_frame,
            text="Resumen del inventario de productos",
            text_color=AZUL_CIELO,
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", padx=(0, 20), pady=(0, 10))

        # Stat cards - all 4 stats in a single row
        cards_frame = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        cards_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # Configure grid for all stats in a single row (5 columns)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        cards_frame.grid_columnconfigure(3, weight=1)
        cards_frame.grid_columnconfigure(4, weight=1)

        self._stat_vars = {}

        # (key, title, icon_color, hover_border, icon, action)
        all_stat_defs = [
            ("disponible",      "Productos Disponibles", HOVER_EXPORT, HOVER_EXPORT, "✅",
             lambda: self._go("products", lambda v: v.set_status_filter("disponible"))),
            ("entrada_count",   "Entradas",              AZUL_CERULEO, NARANJA_SELECCION, "📥",
             lambda: self._go("movements", lambda v: v.set_type_filter("entrada"))),
            ("salida_count",    "Salidas",               NARANJA_SELECCION, NARANJA_SELECCION, "📤",
             lambda: self._go("movements", lambda v: v.set_type_filter("salida"))),
            ("devolucion_count","Devoluciones",           HOVER_EXPORT, NARANJA_SELECCION, "↩️",
             lambda: self._go("movements", lambda v: v.set_type_filter("devolucion"))),
            ("asignacion_count","Asignaciones",           AZUL_CIELO, HOVER_MOV_ASIG, "📋",
             lambda: self._go("movements", lambda v: v.set_type_filter("asignacion"))),
        ]

        for i, (key, title, icon_color, hover_border, icon, action) in enumerate(all_stat_defs):
            card = ctk.CTkFrame(
                cards_frame, corner_radius=14, fg_color="white",
                border_width=2, border_color="white",
            )
            card.grid(row=0, column=i, padx=10, pady=8, sticky="ew")

            hint = ctk.CTkLabel(
                card, text="Ver →",
                font=ctk.CTkFont(size=11), text_color=TEXTO_DASH_HINT,
            )
            hint.pack(anchor="e", padx=10, pady=(6, 0))

            ctk.CTkLabel(
                card, text=icon, font=ctk.CTkFont(size=32), text_color=icon_color
            ).pack(pady=(0, 0))
            lbl = ctk.CTkLabel(
                card, text="0",
                font=ctk.CTkFont(size=40, weight="bold"), text_color=AZUL_NOCHE,
            )
            lbl.pack()
            self._stat_vars[key] = lbl
            ctk.CTkLabel(
                card, text=title, font=ctk.CTkFont(size=14), text_color=AZUL_NOCHE
            ).pack(pady=(0, 10))

            self._make_card_clickable(card, action, hover_border)

        # Recent movements section with card-based design
        movements_frame = ctk.CTkFrame(
            self,
            fg_color=DASHBOARD_BG,
            corner_radius=12,
            border_width=3,
            border_color=NARANJA_SELECCION,
        )
        movements_frame.grid(row=2, column=0, sticky="nsew", padx=20, pady=(10, 10))
        movements_frame.grid_rowconfigure(1, weight=1)
        movements_frame.grid_columnconfigure(0, weight=1)

        # Header for movements section
        movements_header = ctk.CTkFrame(
            movements_frame, fg_color="transparent", height=50
        )
        movements_header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 10))
        movements_header.grid_propagate(False)

        ctk.CTkLabel(
            movements_header,
            text="Movimientos Recientes",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(anchor="w")

        # Subheader with count or last update info
        self.movements_subheader = ctk.CTkLabel(
            movements_header,
            text="Últimos 50 movimientos",
            font=ctk.CTkFont(size=14),
            text_color=AZUL_NOCHE,
        )
        self.movements_subheader.pack(anchor="w", pady=(2, 0))

        # Container for movements list (will be populated in refresh)
        self.movements_container = ctk.CTkFrame(movements_frame, fg_color="transparent")
        self.movements_container.grid(
            row=1, column=0, sticky="nsew", padx=15, pady=(0, 15)
        )
        self.movements_container.grid_rowconfigure(0, weight=1)
        self.movements_container.grid_columnconfigure(0, weight=1)

        self.movements_content = ctk.CTkFrame(
            self.movements_container, fg_color="transparent"
        )
        self.movements_content.grid(row=0, column=0, sticky="nsew")

        self.loading_indicator = ctk.CTkFrame(
            self.movements_container, fg_color="transparent"
        )
        self.loading_indicator.grid(row=0, column=0, sticky="nsew")
        self.loading_indicator.grid_rowconfigure(0, weight=1)
        self.loading_indicator.grid_columnconfigure(0, weight=1)

        self.loading_label = ctk.CTkLabel(
            self.loading_indicator,
            text="Cargando movimientos...",
            font=ctk.CTkFont(size=18),
            text_color=TEXTO_DASH_SEC,
        )
        self.loading_label.grid(row=0, column=0)

        # Initially hide the loading indicator
        self.loading_indicator.grid_remove()

    def refresh(self):
        import time
        current_ms = time.time() * 1000
        if current_ms - self.last_refresh_time < self.min_refresh_interval:
            return
        self.last_refresh_time = current_ms

        # Placeholder inmediato — no bloquear la UI
        for lbl in self._stat_vars.values():
            lbl.configure(text="—")
        self.movements_subheader.configure(text="Cargando...")

        # Cancelar carga previa pendiente, si existe
        if hasattr(self, "_load_after_id") and self._load_after_id:
            self.after_cancel(self._load_after_id)
        self._load_after_id = self.after(10, self._load_data)

    def _show_movement_detail(self, mov):
        """Ventana con detalle completo de un movimiento."""
        from ui.widgets import center_dialog
        type_colors = {
            "entrada": (AZUL_CERULEO, "📥"),
            "salida": (NARANJA_SELECCION, "📤"),
            "devolucion": (AMARILLO_AMBAR, "↩️"),
            "asignacion": (AZUL_CIELO, "📋"),
        }
        tc = type_colors.get(mov.get("type", ""), (AZUL_MARINO, "📋"))
        d = ctk.CTkToplevel(self)
        d.title("Detalle del Movimiento")
        d.geometry("520x380")
        d.resizable(False, False)
        d.configure(fg_color=BLANCO_CALIDO)
        d.transient(self)

        hdr = ctk.CTkFrame(d, fg_color=AZUL_NOCHE, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text=f"{tc[1]}  {mov.get('type', '').upper()}  #{mov.get('id', '')}",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=20, pady=14)

        body = ctk.CTkFrame(d, fg_color="white", corner_radius=8)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        info = [
            ("Producto", mov.get("product", "—")),
            ("Cantidad", str(mov.get("quantity", 0))),
            ("Empleado", mov.get("employee", "—")),
            ("Registrado por", mov.get("registered_by", "—")),
            ("Fecha/Hora", mov.get("timestamp", "—")),
            ("Notas", mov.get("notes", "—") or "—"),
        ]
        for label, val in info:
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", padx=14, pady=4)
            ctk.CTkLabel(
                row, text=label + ":",
                font=ctk.CTkFont(size=13, weight="bold"),
                text_color=AZUL_MARINO, width=120, anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row, text=val,
                font=ctk.CTkFont(size=13),
                text_color=GRIS_AZULADO, anchor="w",
            ).pack(side="left", padx=(8, 0))

        ctk.CTkButton(
            d, text="✕ Cerrar", height=36,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=NARANJA_INTENSO, hover_color=HOVER_NARANJA_INT,
            text_color="white",
            command=d.destroy,
        ).pack(padx=16, pady=(0, 12))

        center_dialog(d)
        d.after(50, d.grab_set)

    def _load_data(self):
        """Fetch real data async (deferred via after). Runs off the critical path."""
        self.loading_indicator.grid()
        self.update_idletasks()
        try:
            wh_id = self.app.current_warehouse_id if self.app else None
            stats = get_dashboard_stats(warehouse_id=wh_id)
            product_counts = stats["product_counts"]
            movement_counts = stats["movement_counts"]
            movements = stats["recent_movements"]

            movement_key_map = {
                "entrada_count": "entrada",
                "salida_count": "salida",
                "devolucion_count": "devolucion",
                "asignacion_count": "asignacion",
            }
            counts = {**product_counts, **movement_counts}
            self._recent_movements = [dict(m) for m in movements]
            for key, lbl in self._stat_vars.items():
                lookup_key = movement_key_map.get(key, key)
                val = int(counts.get(lookup_key) or 0)
                lbl.configure(text=str(val))

            for widget in self.movements_content.winfo_children():
                widget.destroy()

            make_dashboard_movements_list(
                self.movements_content, movements,
                on_click=self._show_movement_detail,
            )
            self.movements_subheader.configure(
                text=f"Mostrando {len(movements)} movimientos recientes"
            )
        finally:
            self.loading_indicator.grid_remove()
            self._load_after_id = None

import customtkinter as ctk

try:
    from PIL import Image
except ImportError:
    Image = None

from ui.dashboard_widgets import (
    make_dashboard_movements_list,
    setup_dashboard_movements_style,
)
from database.repository import (
    get_product_counts,
    get_movement_counts,
    get_all_movements,
)


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, current_user, on_navigate=None, app=None):
        super().__init__(parent, fg_color="#F7F5FB")  # Fondo Base
        self.current_user = current_user
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
            card.configure(fg_color="#F0F7FF", border_color=accent_color)

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
        hdr = ctk.CTkFrame(header_container, fg_color="#031D44", corner_radius=10)
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
            text_color="#F7F5FB",
        ).pack(anchor="w", padx=(0, 20), pady=(12, 2))
        ctk.CTkLabel(
            title_frame,
            text="Resumen del inventario de productos",
            text_color="#8ECAE6",
            font=ctk.CTkFont(size=14),
        ).pack(anchor="w", padx=(0, 20), pady=(0, 10))

        # Stat cards - all 4 stats in a single row
        cards_frame = ctk.CTkFrame(self, fg_color="#F7F5FB")
        cards_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)

        # Configure grid for all stats in a single row (4 columns)
        cards_frame.grid_columnconfigure(0, weight=1)
        cards_frame.grid_columnconfigure(1, weight=1)
        cards_frame.grid_columnconfigure(2, weight=1)
        cards_frame.grid_columnconfigure(3, weight=1)

        self._stat_vars = {}

        # (key, title, icon_color, hover_border, icon, action)
        all_stat_defs = [
            ("disponible",      "Productos Disponibles", "#F9AB55", "#F9AB55", "✅",
             lambda: self._go("products", lambda v: v.set_status_filter("disponible"))),
            ("entrada_count",   "Entradas",              "#219EBC", "#F58A07", "📥",
             lambda: self._go("products")),
            ("salida_count",    "Salidas",               "#F58A07", "#F58A07", "📤",
             lambda: self._go("movements", lambda v: v.set_type_filter("salida"))),
            ("devolucion_count","Devoluciones",           "#F9AB55", "#F58A07", "↩️",
             lambda: self._go("movements", lambda v: v.set_type_filter("devolucion"))),
        ]

        for i, (key, title, icon_color, hover_border, icon, action) in enumerate(all_stat_defs):
            card = ctk.CTkFrame(
                cards_frame, corner_radius=14, fg_color="white",
                border_width=2, border_color="white",
            )
            card.grid(row=0, column=i, padx=10, pady=8, sticky="ew")

            hint = ctk.CTkLabel(
                card, text="Ver →",
                font=ctk.CTkFont(size=11), text_color="#CCCCCC",
            )
            hint.pack(anchor="e", padx=10, pady=(6, 0))

            ctk.CTkLabel(
                card, text=icon, font=ctk.CTkFont(size=32), text_color=icon_color
            ).pack(pady=(0, 0))
            lbl = ctk.CTkLabel(
                card, text="0",
                font=ctk.CTkFont(size=40, weight="bold"), text_color="#031D44",
            )
            lbl.pack()
            self._stat_vars[key] = lbl
            ctk.CTkLabel(
                card, text=title, font=ctk.CTkFont(size=14), text_color="#031D44"
            ).pack(pady=(0, 10))

            self._make_card_clickable(card, action, hover_border)

        # Recent movements section with card-based design
        movements_frame = ctk.CTkFrame(
            self,
            fg_color="#F8F9FA",
            corner_radius=12,
            border_width=3,
            border_color="#F58A07",
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
            text_color="#031D44",
        ).pack(anchor="w")

        # Subheader with count or last update info
        self.movements_subheader = ctk.CTkLabel(
            movements_header,
            text="Últimos 50 movimientos",
            font=ctk.CTkFont(size=14),
            text_color="#031D44",
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
            text_color="#6C757D",
        )
        self.loading_label.grid(row=0, column=0)

        # Initially hide the loading indicator
        self.loading_indicator.grid_remove()

    def refresh(self):
        # Implementar throttling para evitar refreshes demasiado frecuentes
        import time

        current_time = time.time() * 1000  # Convertir a milisegundos

        # Si ha pasado menos tiempo que el intervalo mínimo, salir
        if current_time - self.last_refresh_time < self.min_refresh_interval:
            return

        self.last_refresh_time = current_time

        # Mostrar indicador de carga
        self.loading_indicator.grid()

        # Forzar actualización de la UI para mostrar el indicador de carga inmediatamente
        self.update_idletasks()

        try:
            # Obtener conteos de productos
            product_counts = get_product_counts()
            movement_counts = get_movement_counts()

            # Map movement keys to stat keys
            movement_key_map = {
                "entrada_count": "entrada",
                "salida_count": "salida",
                "devolucion_count": "devolucion",
            }

            # Combinar ambos diccionarios
            counts = {**product_counts, **movement_counts}

            for key, lbl in self._stat_vars.items():
                lookup_key = movement_key_map.get(key, key)
                val = int(counts.get(lookup_key) or 0)
                lbl.configure(text=str(val))

            # Limpiar contenedor de movimientos anteriores, pero preservar el indicador de carga
            for widget in self.movements_content.winfo_children():
                widget.destroy()

            # Obtener datos de movimientos (solo los 50 más recientes para el dashboard)
            movements = get_all_movements(limit=50)

            # Crear nueva lista de movimientos
            make_dashboard_movements_list(self.movements_content, movements)

            # Actualizar subheader con el conteo real
            self.movements_subheader.configure(
                text=f"Mostrando {len(movements)} movimientos recientes"
            )
        finally:
            # Ocultar indicador de carga (siempre se ejecuta, incluso si hay error)
            self.loading_indicator.grid_remove()

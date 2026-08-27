import customtkinter as ctk
import queue
import threading
from ui.colors import *

try:
    from PIL import Image
except ImportError:
    Image = None

from ui.dashboard_widgets import (
    make_dashboard_movements_list,
    setup_dashboard_movements_style,
)
from database.repository import get_dashboard_stats, get_movement_detail


class DashboardView(ctk.CTkFrame):
    def __init__(self, parent, current_user, on_navigate=None, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)  # Fondo Base
        self.current_user = current_user
        self.app = app
        self._on_navigate = on_navigate
        self._load_gen = 0
        self._load_pending = False
        self._load_queue = queue.Queue()
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
            (
                "disponible",
                "Productos Disponibles",
                HOVER_EXPORT,
                HOVER_EXPORT,
                "✅",
                lambda: self._go(
                    "products", lambda v: v.set_status_filter("disponible")
                ),
            ),
            (
                "entrada_count",
                "Entradas",
                AZUL_CERULEO,
                NARANJA_SELECCION,
                "📥",
                lambda: self._go("movements", lambda v: v.set_type_filter("entrada")),
            ),
            (
                "salida_count",
                "Salidas",
                NARANJA_SELECCION,
                NARANJA_SELECCION,
                "📤",
                lambda: self._go("movements", lambda v: v.set_type_filter("salida")),
            ),
            (
                "devolucion_count",
                "Devoluciones",
                HOVER_EXPORT,
                NARANJA_SELECCION,
                "↩️",
                lambda: self._go(
                    "movements", lambda v: v.set_type_filter("devolucion")
                ),
            ),
            (
                "asignacion_count",
                "Asignaciones",
                AZUL_CIELO,
                HOVER_MOV_ASIG,
                "📋",
                lambda: self._go(
                    "movements", lambda v: v.set_type_filter("asignacion")
                ),
            ),
        ]

        for i, (key, title, icon_color, hover_border, icon, action) in enumerate(
            all_stat_defs
        ):
            card = ctk.CTkFrame(
                cards_frame,
                corner_radius=14,
                fg_color="white",
                border_width=2,
                border_color="white",
            )
            card.grid(row=0, column=i, padx=10, pady=8, sticky="ew")

            hint = ctk.CTkLabel(
                card,
                text="Ver →",
                font=ctk.CTkFont(size=11),
                text_color=TEXTO_DASH_HINT,
            )
            hint.pack(anchor="e", padx=10, pady=(6, 0))

            ctk.CTkLabel(
                card, text=icon, font=ctk.CTkFont(size=32), text_color=icon_color
            ).pack(pady=(0, 0))
            lbl = ctk.CTkLabel(
                card,
                text="0",
                font=ctk.CTkFont(size=40, weight="bold"),
                text_color=AZUL_NOCHE,
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
        if self._load_pending:
            return
        self._load_pending = True
        self._load_gen += 1

        # Placeholder inmediato — no bloquear la UI
        for lbl in self._stat_vars.values():
            lbl.configure(text="—")
        self.movements_subheader.configure(text="Cargando...")
        self.loading_indicator.grid()
        self.after(10, self._start_load)

    def _show_movement_detail(self, mov):
        """Ventana con detalle completo de un movimiento."""
        detail = None
        try:
            detail = get_movement_detail(mov.get("id"))
        except Exception:
            detail = None
        if detail is None:
            detail = dict(mov)

        type_colors = {
            "entrada": (AZUL_CERULEO, "📥"),
            "salida": (NARANJA_SELECCION, "📤"),
            "devolucion": (AMARILLO_AMBAR, "↩️"),
            "asignacion": (AZUL_CIELO, "📋"),
        }
        tc = type_colors.get(detail.get("type", ""), (AZUL_MARINO, "📋"))
        d = ctk.CTkToplevel(self)
        d.title("Detalle del Movimiento")
        d.geometry("720x780")
        d.minsize(560, 560)
        d.configure(fg_color=BLANCO_CALIDO)
        d.transient(self)
        d.withdraw()  # oculto hasta centrar -> evita salto de posición

        hdr = ctk.CTkFrame(d, fg_color=AZUL_NOCHE, height=64)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        ctk.CTkLabel(
            hdr,
            text=f"{tc[1]}  {detail.get('type', '').upper()}  #{detail.get('id', '')}",
            font=ctk.CTkFont(size=23, weight="bold"),
            text_color="white",
        ).pack(side="left", padx=22, pady=16)

        body = ctk.CTkScrollableFrame(
            d, fg_color="white", corner_radius=8, label_text=""
        )
        body.pack(fill="both", expand=True, padx=20, pady=14)

        def _on_wheel(event):
            body._parent_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        def _bind_wheel(widget):
            try:
                widget.bind("<MouseWheel>", _on_wheel, add="+")
                widget.bind(
                    "<Button-4>",
                    lambda e: body._parent_canvas.yview_scroll(-1, "units"),
                    add="+",
                )
                widget.bind(
                    "<Button-5>",
                    lambda e: body._parent_canvas.yview_scroll(1, "units"),
                    add="+",
                )
            except Exception:
                pass
            for child in widget.winfo_children():
                _bind_wheel(child)

        def _section(title):
            ctk.CTkLabel(
                body,
                text=title,
                font=ctk.CTkFont(size=17, weight="bold"),
                text_color=AZUL_MARINO,
            ).pack(anchor="w", padx=16, pady=(14, 6))

        def _meta_row(label, value):
            row = ctk.CTkFrame(body, fg_color="transparent")
            row.pack(fill="x", padx=16, pady=5)
            ctk.CTkLabel(
                row,
                text=label + ":",
                font=ctk.CTkFont(size=15, weight="bold"),
                text_color=AZUL_MARINO,
                width=160,
                anchor="w",
            ).pack(side="left")
            ctk.CTkLabel(
                row,
                text=value or "—",
                font=ctk.CTkFont(size=15),
                text_color=GRIS_AZULADO,
                anchor="w",
                justify="left",
            ).pack(side="left", padx=(10, 0))

        # Productos — desglose preciso por item
        _section("📦 Productos")
        items = detail.get("items") or []
        if items:
            for it in items:
                line = f"{it['qty']} {it['unit']} {it['name']}"
                if it.get("brand"):
                    line += f"  ·  {it['brand']}"
                item_row = ctk.CTkFrame(
                    body,
                    fg_color="white",
                    corner_radius=6,
                    border_width=1,
                    border_color=DASHBOARD_CARD_BORDER_SEC,
                )
                item_row.pack(fill="x", padx=16, pady=4)
                ctk.CTkLabel(
                    item_row,
                    text="🔹",
                    font=ctk.CTkFont(size=15),
                ).pack(side="left", padx=(12, 8), pady=8)
                ctk.CTkLabel(
                    item_row,
                    text=line,
                    font=ctk.CTkFont(size=16, weight="bold"),
                    text_color=AZUL_NOCHE,
                    anchor="w",
                ).pack(side="left", padx=(0, 6), pady=8)
        else:
            product = detail.get("product") or detail.get("notes") or "—"
            _meta_row("Producto", product)
            if detail.get("brand"):
                _meta_row("Marca", detail["brand"])

        _section("Información :")
        emp = detail.get("employee")
        if emp in ("-", "", None):
            emp = None
        _meta_row("Empleado", emp)
        if detail.get("cargo"):
            _meta_row("Cargo", detail["cargo"])
        _meta_row("Registrado por", detail.get("registered_by"))
        if detail.get("warehouse"):
            _meta_row("Almacén", detail["warehouse"])
        _meta_row("Fecha/Hora", detail.get("timestamp"))
        if detail.get("notes"):
            _meta_row("Notas", detail["notes"])

        _bind_wheel(body)

        ctk.CTkButton(
            d,
            text="✕ Cerrar",
            height=42,
            font=ctk.CTkFont(size=15, weight="bold"),
            fg_color=NARANJA_INTENSO,
            hover_color=HOVER_NARANJA_INT,
            text_color="white",
            command=d.destroy,
        ).pack(padx=20, pady=(0, 16))

        # Centrar sobre la ventana principal usando tamaño conocido
        dw, dh = 720, 780
        root = self.winfo_toplevel()
        root.update_idletasks()
        rx, ry = root.winfo_rootx(), root.winfo_rooty()
        rw, rh = root.winfo_width(), root.winfo_height()
        x = rx + max((rw - dw) // 2, 0)
        y = ry + max((rh - dh) // 2, 0)
        sw, sh = d.winfo_screenwidth(), d.winfo_screenheight()
        if x < 0:
            x = 0
        if y < 0:
            y = 0
        if x + dw > sw:
            x = max(sw - dw, 0)
        if y + dh > sh:
            y = max(sh - dh, 0)
        d.geometry(f"{dw}x{dh}+{x}+{y}")
        d.deiconify()
        d.after(50, d.grab_set)

    def _start_load(self):
        """Corre get_dashboard_stats en un thread; el resultado se entrega
        via cola para no bloquear la UI. Nunca toca widgets desde el thread."""
        if not self._load_pending or not self.winfo_exists():
            return
        self.update_idletasks()
        gen = self._load_gen
        wh_id = self.app.current_warehouse_id if self.app else None
        q = self._load_queue

        def worker():
            try:
                stats = get_dashboard_stats(warehouse_id=wh_id)
            except Exception as exc:
                stats, exc = None, exc
            else:
                exc = None
            q.put((gen, stats, exc))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_load)

    def _poll_load(self):
        if not self._load_pending or not self.winfo_exists():
            return
        try:
            gen, stats, exc = self._load_queue.get_nowait()
        except queue.Empty:
            self.after(100, self._poll_load)
            return
        self._apply_stats(gen, stats, exc)

    def _apply_stats(self, gen, stats, exc):
        if not self.winfo_exists() or gen != self._load_gen:
            return
        self._load_pending = False
        self.loading_indicator.grid_remove()

        if exc is not None:
            self.movements_subheader.configure(
                text="Error al cargar los datos. Intenta de nuevo."
            )
            return

        product_counts = stats["product_counts"]
        movement_counts = stats["movement_counts"]
        movements = stats["recent_movements"][:10]

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
            self.movements_content,
            movements,
            on_click=self._show_movement_detail,
        )
        self.movements_subheader.configure(
            text=f"Mostrando {len(movements)} movimientos recientes"
        )

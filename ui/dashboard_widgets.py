import customtkinter as ctk
from datetime import datetime
from ui.colors import *


def setup_dashboard_movements_style():
    pass


def create_movement_card(parent, movement_data, index):
    movement_data = dict(movement_data)

    type_colors = {
        "entrada":    {"bg": MOV_ENTRADA_BG, "fg": MOV_ENTRADA_FG, "icon": "📥"},
        "salida":     {"bg": MOV_SALIDA_BG, "fg": MOV_SALIDA_FG, "icon": "📤"},
        "asignacion": {"bg": MOV_ASIGNACION_BG, "fg": MOV_ASIGNACION_FG, "icon": "👤"},
        "devolucion": {"bg": MOV_DEVOLUCION_BG, "fg": MOV_DEVOLUCION_FG, "icon": "↩️"},
    }

    movement_type = movement_data["type"].lower()
    type_info = type_colors.get(
        movement_type, {"bg": MOV_DEFAULT_BG, "fg": TEXTO_DASH_SEC, "icon": "📋"}
    )

    card = ctk.CTkFrame(
        parent,
        fg_color="white",
        corner_radius=12,
        border_width=1,
        border_color=DASHBOARD_CARD_BORDER_SEC,
    )
    card.pack(fill="x", padx=10, pady=8)

    card.grid_columnconfigure(0, weight=0, minsize=4)
    card.grid_columnconfigure(1, weight=1)

    color_stripe = ctk.CTkFrame(
        card,
        fg_color=type_info["bg"],
        corner_radius=2,
        width=30,
    )
    color_stripe.grid(row=0, column=0, sticky="ns", padx=0, pady=0)
    color_stripe.grid_propagate(False)

    content_frame = ctk.CTkFrame(card, fg_color="transparent")
    content_frame.grid(row=0, column=1, sticky="nsew", padx=(15, 25), pady=20)
    content_frame.grid_columnconfigure(1, weight=1)

    icon_label = ctk.CTkLabel(
        content_frame, text=type_info["icon"], font=ctk.CTkFont(size=30), width=40
    )
    icon_label.grid(row=0, column=0, rowspan=2, padx=(0, 15), pady=2)

    type_label = ctk.CTkLabel(
        content_frame,
        text=movement_data["type"].upper(),
        font=ctk.CTkFont(size=22, weight="bold"),
        text_color=type_info["fg"],
    )
    type_label.grid(row=0, column=1, sticky="w", pady=(0, 6))

    try:
        timestamp_str = movement_data["timestamp"]
        if isinstance(timestamp_str, str):
            dt = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            time_display = dt.strftime("%d/%m/%Y %H:%M")
        else:
            time_display = str(timestamp_str)
    except Exception:
        time_display = str(movement_data["timestamp"])

    time_label = ctk.CTkLabel(
        content_frame,
        text=time_display,
        font=ctk.CTkFont(size=16),
        text_color=TEXTO_DASH_SEC,
    )
    time_label.grid(row=1, column=1, sticky="w", pady=(2, 0))

    product_label = ctk.CTkLabel(
        content_frame,
        text=f"📦 {movement_data['product']}",
        font=ctk.CTkFont(size=18),
        text_color=TEXTO_DASH_LABEL,
        anchor="w",
    )
    product_label.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(12, 6))

    employee = movement_data.get("employee") or ""
    if employee and employee.strip() and employee != "-":
        ctk.CTkLabel(
            content_frame,
            text=f"👤 {employee}",
            font=ctk.CTkFont(size=17),
            text_color=TEXTO_DASH_LABEL,
            anchor="w",
        ).grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 6))

    registered = movement_data.get("registered_by") or ""
    if registered:
        ctk.CTkLabel(
            content_frame,
            text=f"📝 {registered}",
            font=ctk.CTkFont(size=16),
            text_color=TEXTO_DASH_SEC,
            anchor="w",
        ).grid(row=4, column=0, columnspan=2, sticky="ew", pady=(0, 6))


def make_dashboard_movements_list(parent, movements_data, bg_color="#FFFFFF"):
    container = ctk.CTkFrame(
        parent,
        fg_color=bg_color,
        border_width=2,
        border_color=AZUL_NOCHE,
        corner_radius=12,
    )
    container.pack(fill="both", expand=True, padx=2, pady=2)

    scrollable_frame = ctk.CTkScrollableFrame(
        container, fg_color="transparent", corner_radius=0
    )
    scrollable_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def _on_mousewheel(event):
        scrollable_frame._parent_canvas.yview_scroll(
            int(-1 * (event.delta / 120)), "units"
        )

    scrollable_frame.bind("<MouseWheel>", _on_mousewheel)
    scrollable_frame.bind("<Button-4>",
        lambda e: scrollable_frame._parent_canvas.yview_scroll(-1, "units"))
    scrollable_frame.bind("<Button-5>",
        lambda e: scrollable_frame._parent_canvas.yview_scroll(1, "units"))

    if not movements_data:
        ctk.CTkLabel(
            scrollable_frame,
            text="No hay movimientos recientes",
            font=ctk.CTkFont(size=20),
            text_color=TEXTO_DASH_SEC,
        ).pack(pady=100)
        return container

    for i, movement in enumerate(movements_data):
        create_movement_card(scrollable_frame, movement, i)

    return container


def clear_dashboard_movements_list(container):
    pass

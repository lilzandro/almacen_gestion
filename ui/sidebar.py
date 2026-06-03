import customtkinter as ctk
from ui.colors import *

try:
    from PIL import Image
except ImportError:
    Image = None


class Sidebar(ctk.CTkFrame):
    def __init__(self, parent, current_user: dict, on_navigate, on_logout):
        super().__init__(
            parent, width=300, corner_radius=0, fg_color=AZUL_NOCHE
        )  # Primario (Dark)
        self.pack_propagate(False)
        self.on_navigate = on_navigate
        self._buttons = {}
        self._active = None

        # Logo
        logo = ctk.CTkFrame(self, fg_color="transparent")
        logo.pack(fill="x", padx=15, pady=(15, 5))
        if Image:
            try:
                self.logo_img = ctk.CTkImage(
                    Image.open("img/logo_sidebar.png"), size=(100, 80)
                )
                ctk.CTkLabel(logo, image=self.logo_img, text="").pack()
            except Exception:
                ctk.CTkLabel(
                    logo, text="📠", font=ctk.CTkFont(size=40), text_color=BLANCO_CALIDO
                ).pack()
        else:
            ctk.CTkLabel(
                logo, text="📠", font=ctk.CTkFont(size=40), text_color=BLANCO_CALIDO
            ).pack()
        ctk.CTkLabel(
            logo,
            text="DigiCable",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=BLANCO_CALIDO,
        ).pack()
        ctk.CTkLabel(
            logo,
            text="Sistema de Control de Inventarios",
            font=ctk.CTkFont(size=14),
            text_color=AZUL_CIELO,
        ).pack()

        ctk.CTkFrame(self, height=1, fg_color=AZUL_MARINO).pack(
            fill="x", padx=12, pady=14
        )

        # Barra indicadora activa (deslizante)
        self._indicator = ctk.CTkFrame(self, fg_color=NARANJA_SELECCION, width=5, corner_radius=2)
        self._indicator_y = 0

        # Nav items
        items = [
            ("🏠  Dashboard", "dashboard"),
            ("📦  Productos", "products"),
            ("🚛  Proveedores", "suppliers"),
            ("👤  Empleados", "employees"),
            ("🚗  Vehículos", "vehicles"),
            ("↕️  Movimientos", "movements"),
        ]
        if current_user["role"] == "admin":
            items.append(("⚙️  Usuarios", "users"))

        for label, view in items:
            btn = ctk.CTkButton(
                self,
                text=label,
                anchor="w",
                height=42,
                corner_radius=8,
                font=ctk.CTkFont(size=18),
                fg_color="transparent",
                hover_color=AZUL_NOCHE,  # Match sidebar background for no visual change on hover
                text_color=BLANCO_CALIDO,
                command=lambda v=view: self._nav(v),
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._buttons[view] = btn
            # Bind hover events for text color change
            btn.bind("<Enter>", lambda e, b=btn: self._on_button_enter(b))
            btn.bind("<Leave>", lambda e, b=btn: self._on_button_leave(b))
            # Highlight default - active state should match hover effect
            if view == "dashboard":
                btn.configure(
                    fg_color="transparent", text_color=NARANJA_SELECCION
                )  # selección (matches hover effect)
                self._active = btn

        # Spacer
        ctk.CTkFrame(self, fg_color="transparent").pack(fill="both", expand=True)
        ctk.CTkFrame(self, height=1, fg_color=AZUL_MARINO).pack(fill="x", padx=12, pady=5)

        # User info
        info = ctk.CTkFrame(self, fg_color="transparent")
        info.pack(fill="x", padx=12, pady=(4, 14))
        role_txt = "🛡️ Admin" if current_user["role"] == "admin" else "👤 Supervisor"
        ctk.CTkLabel(
            info,
            text=current_user["username"],
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color=BLANCO_CALIDO,
        ).pack(anchor="w")
        ctk.CTkLabel(
            info, text=role_txt, font=ctk.CTkFont(size=15), text_color=BLANCO_CALIDO
        ).pack(anchor="w")
        ctk.CTkButton(
            info,
            text="Cerrar Sesión",
            height=34,
            fg_color=NARANJA_SELECCION,  # Acción / Resaltado
            hover_color=HOVER_NARANJA_SEL,
            text_color="white",
            font=ctk.CTkFont(size=17),
            command=on_logout,
        ).pack(fill="x", pady=(8, 0))

        self.after(0, lambda: self._nav("dashboard"))

    def _on_button_enter(self, button):
        """Establece el color del texto al pasar el mouse por encima"""
        if button == self._active:
            # Mantener el botón activo en naranja
            button.configure(text_color=NARANJA_SELECCION)
        else:
            # Cambiar botones inactivos a naranja al hacer hover
            button.configure(text_color=NARANJA_SELECCION)

    def _on_button_leave(self, button):
        """Restaura el color del texto al salir el mouse"""
        if button == self._active:
            # Mantener el botón activo en naranja
            button.configure(text_color=NARANJA_SELECCION)
        else:
            # Restaurar botones inactivos a blanco
            button.configure(text_color=BLANCO_CALIDO)

    def _nav(self, view: str):
        if self._active:
            self._active.configure(fg_color="transparent", text_color=BLANCO_CALIDO)
        if view in self._buttons:
            btn = self._buttons[view]
            btn.configure(fg_color="transparent", text_color=NARANJA_SELECCION)
            self._active = btn
            self._slide_indicator(btn)
        self.on_navigate(view)

    def _slide_indicator(self, target_btn):
        self.update_idletasks()
        target_btn.update_idletasks()

        target_y = target_btn.winfo_y()
        target_h = target_btn.winfo_height() or 42

        if target_y <= 0:
            self._indicator.place(x=0, y=0, width=5, height=target_h)
            self._indicator_y = 0
            return

        start_y = float(self._indicator_y)
        end_y = float(target_y)
        steps = 10
        interval = 16  # ~60fps

        def _step(i):
            t = min(i / steps, 1.0)
            eased = 1 - (1 - t) ** 3
            y = int(start_y + (end_y - start_y) * eased)
            try:
                self._indicator.place(x=0, y=y, width=5, height=target_h)
            except Exception:
                return
            if i < steps:
                self._indicator.after(interval, _step, i + 1)

        _step(0)
        self._indicator_y = int(end_y)

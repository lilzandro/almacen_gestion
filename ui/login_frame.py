import customtkinter as ctk
from core.auth import login, change_password
from ui.colors import *

try:
    from PIL import Image
except ImportError:
    Image = None


class LoginFrame(ctk.CTkFrame):
    def __init__(self, parent, on_login_success):
        super().__init__(parent, fg_color=BLANCO_CALIDO)  # Fondo Base
        self.on_login_success = on_login_success

        # Centered card
        card = ctk.CTkFrame(
            self, width=420, height=520, corner_radius=20, fg_color="white"
        )
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)

        self.logo_img = None
        if Image:
            try:
                self.logo_img = ctk.CTkImage(
                    Image.open("img/logo_login.png"), size=(150, 110)
                )
                ctk.CTkLabel(card, image=self.logo_img, text="").pack(pady=(30, 10))
            except Exception:
                ctk.CTkLabel(
                    card, text="📡", font=ctk.CTkFont(size=62), text_color=AZUL_MARINO
                ).pack(pady=(40, 4))
        else:
            ctk.CTkLabel(
                card, text="📡", font=ctk.CTkFont(size=62), text_color=AZUL_MARINO
            ).pack(pady=(40, 4))
        ctk.CTkLabel(
            card,
            text="DigiCable",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack()
        ctk.CTkLabel(
            card,
            text="Sistema de Control de Inventario",
            font=ctk.CTkFont(size=14),
            text_color=AZUL_MARINO,
        ).pack(pady=(2, 28))

        self.user_entry = ctk.CTkEntry(
            card,
            width=320,
            height=46,
            placeholder_text="Usuario",
            font=ctk.CTkFont(size=15),
            text_color=AZUL_NOCHE,
            placeholder_text_color=TEXTO_PLACEHOLDER_LOGIN,
            fg_color=BLANCO_CALIDO,
        )
        self.user_entry.pack(pady=5)

        self.pass_entry = ctk.CTkEntry(
            card,
            width=320,
            height=46,
            placeholder_text="Contraseña",
            show="•",
            font=ctk.CTkFont(size=15),
            text_color=AZUL_NOCHE,
            placeholder_text_color=TEXTO_PLACEHOLDER_LOGIN,
            fg_color=BLANCO_CALIDO,
        )
        self.pass_entry.pack(pady=5)

        self.err_lbl = ctk.CTkLabel(
            card,
            text="",
            text_color=NARANJA_SELECCION,  # Acción / Resaltado
            font=ctk.CTkFont(size=14),
        )
        self.err_lbl.pack(pady=4)

        ctk.CTkButton(
            card,
            text="Iniciar Sesión",
            width=320,
            height=46,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=AZUL_MARINO,  # Secundario
            hover_color=SIDEBAR_HOVER,
            text_color="white",
            command=self._do_login,
        ).pack()

        ctk.CTkLabel(
            card,
            text="DigiCable © Inventario",
            text_color=TEXTO_PLACEHOLDER_LOGIN,
            font=ctk.CTkFont(size=11),
        ).pack(pady=(18, 0))

        self.user_entry.bind("<Return>", lambda e: self.pass_entry.focus())
        self.pass_entry.bind("<Return>", lambda e: self._do_login())
        self.user_entry.focus()

    def _do_login(self):
        username = self.user_entry.get().strip()
        password = self.pass_entry.get()
        if not username or not password:
            self.err_lbl.configure(text="Completa todos los campos.")
            return
        user = login(username, password)
        if user:
            if user.get("must_change_password"):
                _ForceChangePasswordDialog(self, user, self.on_login_success)
            else:
                self.on_login_success(user)
        else:
            self.err_lbl.configure(text="Usuario o contraseña incorrectos.")
            self.pass_entry.delete(0, "end")


class _ForceChangePasswordDialog(ctk.CTkToplevel):
    """Diálogo obligatorio al primer login — bloquea acceso hasta cambiar contraseña."""

    MIN_LEN = 8

    def __init__(self, parent, user: dict, on_done):
        super().__init__(parent)
        self.title("Cambio de contraseña requerido")
        self.geometry("400x380")
        self.resizable(False, False)
        self.configure(fg_color=BLANCO_CALIDO)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", lambda: None)  # No se puede cerrar sin cambiar

        self._user = user
        self._on_done = on_done

        ctk.CTkFrame(self, fg_color=AZUL_NOCHE, height=56).pack(fill="x")
        ctk.CTkLabel(self, text="🔒  Debes cambiar tu contraseña",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=AZUL_NOCHE).pack(pady=(14, 2))
        ctk.CTkLabel(self, text=f"Mínimo {self.MIN_LEN} caracteres.",
                     font=ctk.CTkFont(size=12), text_color=TEXTO_SECUNDARIO).pack()

        def _entry(ph):
            return ctk.CTkEntry(self, width=300, height=42, show="•",
                                placeholder_text=ph, font=ctk.CTkFont(size=14),
                                fg_color="white", border_width=1, border_color=AZUL_MARINO,
                                text_color=AZUL_NOCHE)

        self._new_e = _entry("Nueva contraseña")
        self._new_e.pack(pady=(16, 6))
        self._confirm_e = _entry("Confirmar contraseña")
        self._confirm_e.pack(pady=(0, 6))

        self._err = ctk.CTkLabel(self, text="", text_color=NARANJA_INTENSO,
                                 font=ctk.CTkFont(size=13))
        self._err.pack()

        ctk.CTkButton(self, text="Guardar y continuar", width=300, height=42,
                      fg_color=AZUL_MARINO, hover_color=AZUL_NOCHE, text_color="white",
                      font=ctk.CTkFont(size=14, weight="bold"),
                      command=self._save).pack(pady=(10, 0))

        self._new_e.focus()
        self._confirm_e.bind("<Return>", lambda e: self._save())

    def _save(self):
        new_pw = self._new_e.get()
        confirm = self._confirm_e.get()
        if len(new_pw) < self.MIN_LEN:
            self._err.configure(text=f"Mínimo {self.MIN_LEN} caracteres.")
            return
        if new_pw != confirm:
            self._err.configure(text="Las contraseñas no coinciden.")
            return
        change_password(self._user["id"], new_pw)
        self._user["must_change_password"] = 0
        self.destroy()
        self._on_done(self._user)

import customtkinter as ctk
from tkinter import messagebox
from ui.colors import *
from ui.widgets import make_table, clear_tree, setup_treeview_style
from database.repository import get_all_users, create_user, update_user, delete_user
from core.auth import hash_password


class UsersView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        super().__init__(parent, fg_color=BLANCO_CALIDO)  # Fondo Base
        self.current_user = current_user
        setup_treeview_style()
        self.grid_rowconfigure(2, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build()
        self.refresh()

    def _build(self):
        hdr = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        hdr.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 5))
        ctk.CTkLabel(
            hdr,
            text="Gestión de Usuarios",
            font=ctk.CTkFont(size=26, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(side="left")
        ctk.CTkLabel(
            hdr, text="⚙️ Solo Admin", text_color=HOVER_EXPORT, font=ctk.CTkFont(size=14)
        ).pack(side="left", padx=10)
        ctk.CTkButton(
            hdr,
            text="+ Agregar Usuario",
            height=36,
            command=self._add_dialog,
            fg_color=NARANJA_SELECCION,
            hover_color=HOVER_NARANJA_SEL,
            text_color="white",
        ).pack(side="right")

        tf = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        tf.grid(row=2, column=0, sticky="nsew", padx=20, pady=5)
        tf.grid_rowconfigure(0, weight=1)
        tf.grid_columnconfigure(0, weight=1)
        cols = [("id", "ID", 50), ("username", "Usuario", 200), ("role", "Rol", 120)]
        self.tree = make_table(tf, cols, bg_color="white")

        af = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        af.grid(row=3, column=0, sticky="ew", padx=20, pady=(4, 10))
        ctk.CTkButton(
            af,
            text="✏️ Editar",
            width=120,
            height=34,
            command=self._edit_dialog,
            fg_color=AZUL_MARINO,
            hover_color=SIDEBAR_HOVER,
            text_color="white",
        ).pack(side="left", padx=4)
        ctk.CTkButton(
            af,
            text="🗑️ Eliminar",
            width=120,
            height=34,
            fg_color=AZUL_MARINO,  # Secundario
            hover_color=SIDEBAR_HOVER,
            text_color="white",
            command=self._delete,
        ).pack(side="left", padx=4)

    def refresh(self):
        clear_tree(self.tree)
        for r in get_all_users():
            self.tree.insert(
                "", "end", iid=r["id"], values=(r["id"], r["username"], r["role"])
            )

    def _selected(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un usuario.")
        return sel or None

    def _add_dialog(self):
        _UserDialog(
            self,
            "Agregar Usuario",
            on_save=lambda d: (
                create_user(d["username"], hash_password(d["password"]), d["role"]),
                self.refresh(),
            ),
        )

    def _edit_dialog(self):
        iid = self._selected()
        if not iid:
            return
        vals = self.tree.item(iid, "values")
        _UserDialog(
            self,
            "Editar Usuario",
            edit_mode=True,
            initial={"username": vals[1], "role": vals[2]},
            on_save=lambda d: (
                update_user(
                    int(iid),
                    d["username"],
                    d["role"],
                    hash_password(d["password"]) if d.get("password") else None,
                ),
                self.refresh(),
            ),
        )

    def _delete(self):
        iid = self._selected()
        if not iid:
            return
        if int(iid) == self.current_user["id"]:
            messagebox.showwarning("Aviso", "No puedes eliminarte a ti mismo.")
            return
        if messagebox.askyesno("Confirmar", "¿Eliminar este usuario?"):
            delete_user(int(iid))
            self.refresh()


class _UserDialog(ctk.CTkToplevel):
    ROLES = ["admin", "supervisor"]

    def __init__(self, parent, title, on_save, initial=None, edit_mode=False):
        super().__init__(parent)
        self.title(title)
        self.geometry("500x420")
        self.minsize(400, 350)
        self.resizable(True, True)
        self.after_idle(self.grab_set)
        self.on_save = on_save
        d = initial or {}
        self.edit_mode = edit_mode

        main = ctk.CTkFrame(self, fg_color=BLANCO_CALIDO)
        main.pack(fill="both", expand=True)

        header = ctk.CTkFrame(main, fg_color=AZUL_NOCHE, height=60)
        header.pack(fill="x", pady=(0, 15))
        header.pack_propagate(False)
        ctk.CTkLabel(
            header,
            text=title.upper(),
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
            text="CREDENCIALES",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            left,
            text="Usuario *",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.user_e = ctk.CTkEntry(
            left,
            height=38,
            text_color=AZUL_NOCHE,
            placeholder_text_color=TEXTO_PLACEHOLDER_LOGIN,
            fg_color=BLANCO_CALIDO,
            border_width=1,
            border_color=AZUL_MARINO,
            font=ctk.CTkFont(size=14),
        )
        if d.get("username"):
            self.user_e.insert(0, d["username"])
        self.user_e.pack(fill="x", padx=15)

        lbl_pass = (
            "Contraseña (dejar vacío para no cambiar)" if edit_mode else "Contraseña *"
        )
        ctk.CTkLabel(
            left,
            text=lbl_pass,
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(10, 0))
        self.pass_e = ctk.CTkEntry(
            left,
            height=38,
            show="•",
            text_color=AZUL_NOCHE,
            placeholder_text_color=TEXTO_PLACEHOLDER_LOGIN,
            fg_color=BLANCO_CALIDO,
            border_width=1,
            border_color=AZUL_MARINO,
            font=ctk.CTkFont(size=14),
        )
        self.pass_e.pack(fill="x", padx=15)

        ctk.CTkLabel(
            right,
            text="PERMISOS",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=AZUL_NOCHE,
        ).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            right,
            text="Rol",
            anchor="w",
            text_color=AZUL_NOCHE,
            font=ctk.CTkFont(size=14),
        ).pack(fill="x", padx=15, pady=(5, 0))
        self.role_opt = ctk.CTkOptionMenu(
            right,
            values=self.ROLES,
            text_color="white",
            button_color=AZUL_MARINO,
            button_hover_color=AZUL_NOCHE,
            fg_color=AZUL_MARINO,
            font=ctk.CTkFont(size=14),
        )
        if d.get("role"):
            self.role_opt.set(d["role"])
        self.role_opt.pack(fill="x", padx=15)

        btns = ctk.CTkFrame(main, fg_color=BLANCO_CALIDO)
        btns.pack(fill="x", padx=20, pady=15)
        ctk.CTkButton(
            btns,
            text="✓ GUARDAR",
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
            hover_color=HOVER_NARANJA_SEL,
            text_color="white",
            height=45,
            command=self.destroy,
        ).pack(side="left", expand=True, padx=5)

    def _save(self):
        import re

        username = self.user_e.get().strip()
        if not username:
            messagebox.showwarning("Aviso", "El usuario es obligatorio.", parent=self)
            return
        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username):
            messagebox.showwarning(
                "Aviso",
                "Usuario inválido (3-20 caracteres, letras, números y _).",
                parent=self,
            )
            return

        password = self.pass_e.get()
        if not self.edit_mode and not password:
            messagebox.showwarning(
                "Aviso", "La contraseña es obligatoria.", parent=self
            )
            return
        if password and len(password) < 4:
            messagebox.showwarning(
                "Aviso", "La contraseña debe tener al menos 4 caracteres.", parent=self
            )
            return

        self.on_save(
            {"username": username, "password": password, "role": self.role_opt.get()}
        )
        self.destroy()

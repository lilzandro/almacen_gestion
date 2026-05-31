import customtkinter as ctk
from ui.login_frame import LoginFrame
from ui.sidebar import Sidebar
from database.repository import get_all_warehouses


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Inventario de almacén")
        self.geometry("1400x900")
        self.minsize(1000, 720)
        self.current_user = None
        self.current_warehouse_id = None
        self._warehouses = []
        self._views = {}
        self._current_view_name = None
        self._show_login()

    def _show_login(self):
        self._login = LoginFrame(self, on_login_success=self._on_login)
        self._login.pack(fill="both", expand=True)

    def _on_login(self, user):
        self.current_user = user
        self._warehouses = get_all_warehouses()
        self.current_warehouse_id = self._warehouses[0]["id"] if self._warehouses else None
        self._login.destroy()

        self._sidebar = Sidebar(
            self,
            current_user=user,
            on_navigate=self._navigate,
            on_logout=self._logout,
        )
        self._sidebar.pack(side="left", fill="y")

        # Panel derecho: top bar + contenido
        right = ctk.CTkFrame(self, fg_color="transparent")
        right.pack(side="right", fill="both", expand=True)
        right.grid_rowconfigure(1, weight=1)
        right.grid_columnconfigure(0, weight=1)

        self._build_warehouse_bar(right)

        self._content = ctk.CTkFrame(right, fg_color="transparent")
        self._content.grid(row=1, column=0, sticky="nsew")
        self._content.grid_rowconfigure(0, weight=1)
        self._content.grid_columnconfigure(0, weight=1)

    def _build_warehouse_bar(self, parent):
        bar = ctk.CTkFrame(parent, fg_color="#F7F5FB", height=54, corner_radius=0)
        bar.grid(row=0, column=0, sticky="ew")
        bar.grid_propagate(False)
        bar.grid_columnconfigure(1, weight=1)

        # Ícono + label
        ctk.CTkLabel(
            bar,
            text="🏪",
            font=ctk.CTkFont(size=20),
        ).grid(row=0, column=0, padx=(16, 6), pady=10)
        ctk.CTkLabel(
            bar,
            text="Almacén activo:",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#2D3748",
        ).grid(row=0, column=1, sticky="w", pady=10)

        # Selector
        wh_names = [w["name"] for w in self._warehouses]
        self._wh_seg = ctk.CTkSegmentedButton(
            bar,
            values=wh_names,
            command=self._on_warehouse_change_by_name,
            fg_color="#E2EFF8",
            selected_color="#219EBC",
            selected_hover_color="#1976A1",
            unselected_color="#E2EFF8",
            unselected_hover_color="#C5DFF0",
            text_color="#2D3748",
            font=ctk.CTkFont(size=13, weight="bold"),
            height=34,
        )
        self._wh_seg.grid(row=0, column=2, padx=(8, 16), pady=10)
        self._wh_seg.set(wh_names[0] if wh_names else "")

        # Línea separadora inferior
        ctk.CTkFrame(parent, height=2, fg_color="#8ECAE6", corner_radius=0).grid(
            row=0, column=0, sticky="sew"
        )

    def _on_warehouse_change_by_name(self, name: str):
        wh = next((w for w in self._warehouses if w["name"] == name), None)
        if not wh:
            return
        self.current_warehouse_id = wh["id"]
        # Invalidar caché de vistas que dependen del almacén
        for key in ("products", "movements", "dashboard"):
            self._views.pop(key, None)
        if self._current_view_name:
            self._navigate(self._current_view_name)

    def _navigate(self, view_name: str):
        self._navigate_filtered(view_name)

    def _navigate_filtered(self, view_name: str, filter_fn=None):
        self._current_view_name = view_name
        for v in self._views.values():
            v.grid_remove()

        if view_name not in self._views:
            view_cls = self._get_view_class(view_name)
            kwargs = {"current_user": self.current_user, "app": self}
            if view_name == "dashboard":
                kwargs["on_navigate"] = self._navigate_filtered
            v = view_cls(self._content, **kwargs)
            v.grid(row=0, column=0, sticky="nsew")
            self._views[view_name] = v
        else:
            self._views[view_name].grid()
            self._views[view_name].refresh()

        if filter_fn and view_name in self._views:
            filter_fn(self._views[view_name])

    def _get_view_class(self, name: str):
        from ui.views.dashboard import DashboardView
        from ui.views.products import ProductsView
        from ui.views.suppliers import SuppliersView
        from ui.views.employees import EmployeesView
        from ui.views.vehicles import VehiclesView
        from ui.views.movements import MovementsView
        from ui.views.users import UsersView

        return {
            "dashboard": DashboardView,
            "products": ProductsView,
            "suppliers": SuppliersView,
            "employees": EmployeesView,
            "vehicles": VehiclesView,
            "movements": MovementsView,
            "users": UsersView,
        }[name]

    def _logout(self):
        self.current_user = None
        self._views.clear()
        for w in self.winfo_children():
            w.destroy()
        self._show_login()

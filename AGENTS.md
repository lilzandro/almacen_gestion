# AGENTS.md — DigiCable Inventory System

**Stack:** Python 3.10+, CustomTkinter (UI), SQLite (DB), reportlab (PDF), Pillow (logo)

## Commands

| Command | Purpose |
|---------|---------|
| `python main.py` | Run app |
| `pip install -r requirements.txt` | Install deps |
| `xhost +local:docker && docker compose up --build` | Run via Docker (Linux) |
| `docker compose down` | Stop container |

No test framework, no CI, no linter config file currently in the repo.

## Architecture (3-layer, strict separation)

```
main.py → initialize_db() → App (mainloop)
database/connection.py   → get_connection(), initialize_db() [WAL, FK ON]
database/repository.py   → all CRUD per entity (no SQL from views)
core/auth.py             → login(), hash_password() [pbkdf2_hmac + salt]
core/export.py           → export_movements(), export_inventory() [reportlab]
core/pdf_export.py       → render PDF (reportlab, import perezoso)
ui/app.py                → App: view router via _navigate() / _get_view_class()
ui/colors.py             → entire color palette as named constants
ui/widgets.py            → make_table(), clear_tree(), setup_treeview_style(), MessageDialog, ConfirmDialog, center_dialog
ui/dashboard_widgets.py  → dashboard stats widgets
ui/animations.py         → animate_counter(), dialog_open(), slide_in_frame()
ui/views/                → one view per entity
```

Views are cached in `App._views{}`. Navigation (`_navigate()`) instantiates if missing, otherwise calls `refresh()`. Switching warehouses in the segmented bar invalidates `products`, `movements`, `dashboard` cache keys.

## View Contract

All views accept `__init__(self, parent, current_user, app=None)`. Dashboard also accepts `on_navigate`. Each must implement `refresh()`.

```python
class XView(ctk.CTkFrame):
    def __init__(self, parent, current_user, app=None):
        self.current_user = current_user
        self.app = app
        self._build()
        self.refresh()
    def refresh(self): ...
```

Register in `App._get_view_class()` and add sidebar button in `Sidebar.__init__()`.

## Database

- **DB file:** `inventory.db` at project root by default; configurable via `INVENTORY_DB` (Docker uses `/app/data/inventory.db`). Auto-created on first run
- **Connection:** `get_connection()` returns `sqlite3.Row` — access columns by name
- **Password hashing:** pbkdf2_hmac with salt (`core/auth.py`), NOT plain SHA-256. Legacy SHA-256 hashes auto-migrate on next login.
- **Baja de productos:** `deactivate_product()` marca `status='inactivo'`. `delete_product()` borra físicamente y respalda snapshots en `movement_items` para conservar el historial de Movimientos. Las consultas por defecto excluyen `status='inactivo'`.
- **Unique fields:** `barcode` (products), `cedula` (employees), `plate` (vehicles) — catch `IntegrityError` in views.
- **Movement types:** `entrada`/`devolucion` → positive quantity change; `salida`/`asignacion` → negative (applied automatically by `create_movement()`).
- **Suppliers/Employees have a simple TTL cache** (5s) in repository.py — invalidated on writes.
- **Product groups:** `get_products_grouped()` aggregates by (name, brand). `get_units_by_model()` returns individual units.

## UI Conventions

- **Background:** views use `fg_color="#F7F5FB"` (BLANCO_CALIDO), header bars `fg_color="#031D44"` (AZUL_NOCHE)
- **Tables:** always use `make_table()` from `ui/widgets.py` with style `"Inv.Treeview"`
- **Dialogs:** use `MessageDialog` / `ConfirmDialog` from `ui/widgets.py`, not tkinter messagebox directly
- **Animations:** `dialog_open()` from `ui/animations.py` for CTkToplevel fade-in; `slide_in_frame()` for view transitions
- **Colors:** import from `ui.colors` — never hardcode hex values in views
- **Products view also imports** from `ventanaejemplo.theme`, `ventanaejemplo.data`, `ventanaejemplo.widgets` (legacy migration package)

## Users & Roles

- Default: `admin` / `admin123` (first run creates user with `must_change_password=1`)
- Roles: `admin` (full access, sees "Usuarios" nav item) | `supervisor` (limited)
- `current_user` is a dict with keys: `id, username, password_hash, role, must_change_password`

## Docker

- Linux: `xhost +local:docker && docker compose up --build`
- Windows: requires VcXsrv; `docker compose -f docker-compose.windows.yml up --build`
- macOS: requires XQuartz; `xhost +localhost && docker compose -f docker-compose.macos.yml up --build`
- DB persistida en `./data/inventory.db` (bind mount), sobrevive reinicios
- Guías: `docs/GUIA_DOCKER_CLIENTE.md` (uso) y `docs/GUIA_DOCKER_SOPORTE.md` (técnica)

## Constraints

- No CI, no tests, no pre-commit hooks, no pyproject.toml
- No ruff config — if linting, use default ruff rules
- `ventanaejemplo/` is a legacy migration package; ProductsView still depends on its widgets/theme/data
- App uses light mode only (`ctk.set_appearance_mode("light")` in main.py)

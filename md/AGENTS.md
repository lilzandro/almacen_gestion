# AGENTS.md

This file provides guidance to agents when working with code in this repository.

## Project Overview

**ScanStock** is a desktop inventory management system for warehouse scanners. Built with Python, CustomTkinter, and SQLite.

## Commands

| Command | Description |
|---------|-------------|
| `python main.py` | Run the application |
| `ruff check .` | Lint all Python files |
| `ruff format .` | Format all Python files |
| `ruff check <file>` | Lint a single file |
| `pytest tests/` | Run all tests (if tests exist) |

## Code Style Guidelines

### Naming Conventions
- **Files**: snake_case (e.g., `movements.py`, `scanner_widgets.py`)
- **Classes**: PascalCase (e.g., `ScannersView`, `App`)
- **Functions/Variables**: snake_case (e.g., `get_all_scanners`, `current_user`)
- **Constants**: SCREAMING_SNAKE_CASE (e.g., `STATUSES`, `DEFAULT_PAGE_SIZE`)

### Imports
- Use absolute imports from project root (e.g., `from database.repository import ...`)
- Group imports in this order: stdlib → third-party → local
- Sort alphabetically within groups
```python
import sys
from tkinter import messagebox

import customtkinter as ctk

from core.export import export_scanners_to_excel
from database.repository import get_all_scanners
```

### Formatting
- Use Black-compatible formatting (handled by `ruff format`)
- Maximum line length: 88 characters (default for Ruff)
- Use f-strings for string formatting
- Use type hints for function parameters and return types when obvious

### Type Annotations
```python
def get_all_scanners(search: str = "", include_retired: bool = False) -> list:
    ...

def create_scanner(model: str, serial_number: str, supplier_id: int | None) -> int:
    ...
```

### Error Handling
- Use explicit try/finally for database operations to ensure connections close
- Use `messagebox.showerror()` for user-facing errors in UI code
- Raise specific exceptions with clear messages
```python
def delete_scanner(scanner_id: int):
    conn = None
    try:
        conn = get_connection()
        # ... operations ...
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
```

### Database Patterns
- **Always close explicitly**: `conn.commit()` then `conn.close()` (no context manager)
- Use parameterized queries: `WHERE id=?` to prevent SQL injection
- Access row values by column name: `row["column_name"]`

### UI Components (CustomTkinter)
- Use the Prussian Blue color palette (see below)
- Views must accept `__init__(self, parent, current_user)` and implement `refresh(self)`
- Use `messagebox` for user feedback (warnings, confirmations, errors)
- Use CTkToplevel for dialogs

### Color Palette (Prussian Blue Theme)
| Color | Hex | Usage |
|-------|-----|-------|
| Prussian Blue | `#023047` | Main background, sidebar |
| Cerulean Blue | `#219EBC` | Primary buttons |
| Sky Blue | `#8ECAE6` | Cards, containers, table backgrounds |
| Amber | `#FFB703` | Warnings, stock minimum |
| Orange | `#FB8500` | Critical actions (delete, logout) |
| Blue Gray | `#2D3748` | Primary text |

### View System
1. **Registration**: Add view class to `ui/app.py` `_get_view_class()` dict
2. **Required constructor**: `__init__(self, parent, current_user)`
3. **Required method**: `refresh(self)` to reload data after CRUD
4. **Navigation**: Call `app._navigate(view_name)` to switch views

### Security
- **Password hashing**: SHA-256 via `hashlib.sha256()` (not bcrypt/argon2)
- Default login: `admin` / `admin123`
- Check `current_user["role"]` for permission-gated actions

## Project Structure

```
scanner_inventory/
├── main.py              # Entry point
├── database/
│   ├── connection.py    # DB connection, initialize_db()
│   └── repository.py   # CRUD functions
├── core/
│   ├── auth.py          # Authentication, password hashing
│   └── export.py        # Excel export functions
├── ui/
│   ├── app.py           # Main window, view router
│   ├── login_frame.py   # Login screen
│   ├── sidebar.py       # Navigation sidebar
│   ├── widgets.py       # Reusable UI components
│   └── views/           # Feature-specific views
│       ├── dashboard.py
│       ├── scanners.py
│       ├── suppliers.py
│       ├── employees.py
│       ├── movements.py
│       └── users.py
└── requirements.txt     # Dependencies
```

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Application entry point |
| `database/connection.py` | SQLite connection, schema initialization |
| `database/repository.py` | All CRUD operations |
| `core/auth.py` | Login, password verification |
| `core/export.py` | Excel export with openpyxl |
| `ui/app.py` | Main window, navigation router |
| `ui/views/scanners.py` | Scanner CRUD with delete/retire logic |

## Common Patterns

### Creating a New View
```python
class MyView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent, fg_color="#F7F5FB")
        self.current_user = current_user
        self._build()
        self.refresh()

    def _build(self):
        # UI construction
        pass

    def refresh(self):
        # Data loading
        pass
```

### Registering a View
In `ui/app.py`, add to `_get_view_class()`:
```python
from ui.views.myview import MyView
return {
    ...
    "myview": MyView,
}
```

### Database Operations
```python
from database.repository import get_all_scanners, create_scanner

# Read
rows = get_all_scanners(search="search term")

# Write
create_scanner("Model X", "SN123", supplier_id=1)
```

## Testing

Currently no tests exist. If adding tests:
- Use `pytest`
- Place tests in `tests/` directory
- Use `pytest tests/` to run all tests

## Linting

The project uses Ruff. Run:
- `ruff check .` - Check all files
- `ruff check <file>` - Check single file
- `ruff format .` - Format all files

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Información del Proyecto

**DigiCable - Sistema de Control de Inventarios** es una aplicación de escritorio para gestionar inventario de almacén. Permite registrar productos, proveedores, empleados, vehículos, movimientos de stock y exportar reportes Excel.

**Stack:**
- Python 3.10+, CustomTkinter (UI), SQLite (BD), openpyxl (Excel), Pillow (logo)

**Ejecución:**
```bash
python main.py
```

**Instalación:**
```bash
pip install -r requirements.txt
```

**Credenciales por defecto:** usuario `admin`, contraseña `admin123`

---

## Arquitectura

Tres capas con separación estricta — nunca ejecutar SQL directamente desde las vistas:

```
main.py              → initialize_db() → App (mainloop)
database/
  connection.py      → get_connection(), initialize_db()  [WAL mode, FK ON]
  repository.py      → todas las funciones CRUD por entidad
core/
  auth.py            → login(), hash_password()
  export.py          → export_movements(), export_products()  [openpyxl]
ui/
  app.py             → App: router de vistas via _navigate() / _get_view_class()
  login_frame.py     → LoginFrame
  sidebar.py         → Sidebar (navegación, logo DigiCable)
  widgets.py         → make_table(), clear_tree(), setup_treeview_style(),
                       MessageDialog, ConfirmDialog, center_dialog
  dashboard_widgets.py → widgets de estadísticas para el dashboard
  views/
    dashboard.py     → DashboardView
    products.py      → ProductsView  (CRUD + baja lógica)
    suppliers.py     → SuppliersView
    employees.py     → EmployeesView
    vehicles.py      → VehiclesView
    movements.py     → MovementsView
    users.py         → UsersView  (solo admin)
```

**Flujo de navegación:** `App._navigate(view_name)` → instancia la vista si no existe, o llama `refresh()` si ya existe. Las vistas se cachean en `self._views{}`.

**Contrato de cada vista:**
```python
class MiVista(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        super().__init__(parent)
        self.current_user = current_user
        self._build()
        self.refresh()

    def refresh(self):   # Recarga datos desde BD y actualiza Treeview
        pass
```

Para agregar una vista nueva: crearla en `ui/views/`, registrarla en `App._get_view_class()`, y agregar botón en `Sidebar`.

---

## Esquema de Base de Datos

```
users(id, username, password_hash, role)
  role: 'admin' | 'supervisor'

suppliers(id, name, contact, rif, created_at)

employees(id, name, cedula UNIQUE, cargo, created_at)

vehicles(id, brand, model, plate UNIQUE, created_at)

products(id, name, barcode UNIQUE, brand, serial, mac, quantity,
         status, supplier_id→suppliers, created_at, updated_at)
  status: 'disponible' | 'no disponible' | 'inactivo'
  Baja lógica: usar deactivate_product() — no eliminar si tiene movimientos
  Eliminación física: delete_product() lanza ValueError si hay movimientos

movements(id, type, product_id→products, employee_id→employees,
          user_id→users, quantity, notes, timestamp)
  type: 'entrada' | 'salida' | 'devolucion' | 'asignacion'
  entrada/devolucion → quantity_change positivo
  salida/asignacion  → quantity_change negativo (aplicado automáticamente en create_movement)
```

---

## Paleta de Colores

| Hex      | Nombre         | Uso                                         |
|----------|----------------|---------------------------------------------|
| `#031D44`| Azul Noche     | Sidebar, headers de vista, color principal  |
| `#084887`| Azul Marino    | Encabezados Treeview, bordes de tabla       |
| `#219EBC`| Azul Cerúleo   | Botones primarios                           |
| `#8ECAE6`| Azul Cielo     | Subtítulos, bordes secundarios              |
| `#F7F5FB`| Blanco Cálido  | Fondo de vistas (`fg_color="#F7F5FB"`)      |
| `#FFB703`| Amarillo Ámbar | Botones de advertencia, alertas de stock    |
| `#FB8500`| Naranja Intenso| Botones de peligro / eliminar               |
| `#2D3748`| Gris Azulado   | Texto principal                             |
| `#F58A07`| Naranja Selección | Color de selección en Treeview           |

**Reglas de aplicación:**
- Vistas: `fg_color="#F7F5FB"` (fondo), header frame `fg_color="#031D44"`
- Botones primarios: `fg_color="#219EBC"`, `hover_color="#1976A1"`
- Botones peligro: `fg_color="#FB8500"`, `hover_color="#E67600"`
- Treeview: siempre usar `make_table()` de `ui/widgets.py` con estilo `"Inv.Treeview"`

---

## Patrones Clave

**Llamadas a la BD** — usar siempre el patrón try/finally de repository.py:
```python
conn = get_connection()
try:
    rows = conn.execute("SELECT ...", params).fetchall()
    conn.commit()  # solo en escrituras
    return rows
finally:
    conn.close()
```
`get_connection()` retorna `sqlite3.Row`, así que los resultados son accesibles por nombre de columna.

**Crear tabla en una vista:**
```python
from ui.widgets import make_table, clear_tree, setup_treeview_style
setup_treeview_style()  # llamar una vez en __init__
self._tree = make_table(container, columns=[("col_id", "Columna", 120), ...])
# En refresh():
clear_tree(self._tree)
for row in get_all_X():
    self._tree.insert("", "end", values=(...))
```

**Diálogos:**
```python
from ui.widgets import MessageDialog, ConfirmDialog
MessageDialog(self, "Título", "Mensaje")
if ConfirmDialog(self, "¿Eliminar?").result:
    delete_x(id)
```

**Exportación Excel** — agregar función en `core/export.py`, llamar desde botón:
```python
from core.export import export_movements
export_movements(filepath)
```

---

## Consideraciones

- **Permisos**: verificar `current_user["role"]` antes de habilitar botones. `UsersView` solo es accesible para `admin`.
- **IntegrityError**: campos únicos (`barcode`, `cedula`, `plate`) lanzarán error si se duplican — capturar en la vista.
- **Soft delete de productos**: productos con movimientos NO se pueden eliminar físicamente. Usar `deactivate_product()` que pone `status='inactivo'`. El filtro por defecto en `get_all_products()` excluye inactivos.
- **Logo**: `img/logo_sidebar.png` — si no existe, Sidebar cae en un emoji de fallback.
- **Modo de apariencia**: `main.py` usa `ctk.set_appearance_mode("light")`.

---

## Convenciones

- Archivos: snake_case | Clases: PascalCase | Funciones/variables: snake_case
- Comentarios en español
- Commits en inglés (conventional commits)

---

## Reglas de Eficiencia (ahorro de tokens)

1. Lee archivos relevantes ANTES de escribir código. Si falta contexto, pregunta.
2. Respuestas 1-3 oraciones. Sin preámbulos ni resumen final.
3. Usa `Edit` (parcial), NUNCA `Write` en archivos existentes salvo >80% de cambio.
4. No releer archivos ya leídos en la conversación.
5. Valida (compila/ejecuta) antes de declarar hecho.
6. Cero frases aduladoras. Directo al trabajo.
7. Mínimo que resuelve el problema. Sin abstracciones no pedidas.
8. Si el usuario dice "hazlo así", hazlo. Concern en 1 oración máximo.
9. Lee solo la sección necesaria: usa `offset`/`limit`. No leas archivos completos innecesariamente.
10. No narres el plan antes de ejecutar. Solo ejecuta.
11. Paraleliza tool calls independientes en un solo mensaje.
12. No copies en texto lo que ya está en el diff/archivo editado.
13. No uses `Agent` cuando `Grep`/`Read` basta.

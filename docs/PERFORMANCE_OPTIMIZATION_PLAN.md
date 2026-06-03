# Plan de Optimización de Rendimiento — DigiCable Inventory

## Problema

El sistema se siente lento al iniciar sesión y al navegar entre vistas. Cada `refresh()` ejecuta consultas completas a la base de datos y reconstruye el Treeview desde cero, incluso cuando los datos no han cambiado.

---

## 1. Diagnóstico Inicial

Antes de cualquier cambio, medir para tener línea base:

```python
# Añadir en refresh() de cada vista lenta
import time
start = time.time()
# ... código existente ...
elapsed = time.time() - start
print(f"[PERF] {self.__class__.__name__}.refresh: {elapsed:.3f}s")
```

También ejecutar `EXPLAIN QUERY PLAN` sobre las consultas más frecuentes en `database/repository.py` para detectar falta de índices.

---

## 2. Índices de Base de Datos

Agregar en `initialize_db()` dentro de `database/connection.py`:

```sql
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_status ON products(status);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand);
CREATE INDEX IF NOT EXISTS idx_movements_timestamp ON movements(timestamp);
CREATE INDEX IF NOT EXISTS idx_movements_product_id ON movements(product_id);
```

> Las columnas `barcode`, `cedula` y `plate` ya son UNIQUE, por lo que SQLite les crea un índice automáticamente.

---

## 3. Optimización de Consultas en repository.py

| Problema | Solución |
|----------|----------|
| `SELECT *` en queries de listado | Seleccionar solo columnas necesarias |
| Joins sin índices en FK | Asegurados con los índices del paso 2 |
| Consultas que devuelven filas inactivas sin necesidad | Agregar `WHERE status != 'inactivo'` donde aplique |

### Ejemplo de cambio

```python
# Antes
rows = conn.execute("SELECT * FROM products ORDER BY name").fetchall()

# Después
rows = conn.execute(
    "SELECT id, name, barcode, brand, status, quantity FROM products ORDER BY name"
).fetchall()
```

---

## 4. Caching Inteligente en Vistas

Agregar un timestamp de última modificación y solo refrescar si pasó suficiente tiempo o si hubo cambios:

```python
# En cada vista
class ProductsView(ctk.CTkFrame):
    def __init__(self, parent, current_user):
        ...
        self._last_refresh = 0

    def refresh(self, force=False):
        now = time.time()
        if not force and (now - self._last_refresh) < 2.0:
            return
        self._last_refresh = now
        # ... resto del refresh existente ...
```

---

## 5. Sistema de Notificación de Cambios (Opcional, Alto Impacto)

Implementar un bus de eventos simple para que las vistas solo se refresquen cuando los datos que les interesan cambien realmente.

```python
# core/events.py
class EventBus:
    _subscribers = {}

    @classmethod
    def subscribe(cls, event, callback):
        cls._subscribers.setdefault(event, []).append(callback)

    @classmethod
    def publish(cls, event, data=None):
        for cb in cls._subscribers.get(event, []):
            cb(data)
```

**Uso en repository.py:**

```python
def create_product(data):
    conn = get_connection()
    try:
        conn.execute("INSERT INTO products ...", params)
        conn.commit()
        EventBus.publish("products_changed")
    finally:
        conn.close()
```

**Uso en la vista:**

```python
class ProductsView:
    def __init__(self, ...):
        EventBus.subscribe("products_changed", lambda _: self.refresh(force=True))
```

Cuando `App._navigate()` cambie a una vista ya existente, omitir `refresh()` si no hay cambios pendientes.

---

## 6. Optimización del Treeview

El patrón `clear_tree()` + insert individual es costoso con muchos registros:

```python
# En ui/widgets.py — optimizar clear_tree
def clear_tree(tree):
    children = tree.get_children()
    if children:
        tree.delete(*children)

# En views — deshabilitar actualización visual durante la carga
def refresh(self):
    self._tree.configure(displaycolumns="#all")  # congelar render
    clear_tree(self._tree)
    for row in data:
        self._tree.insert("", "end", values=row)
    self._tree.configure(displaycolumns="#all")  # descongelar
```

---

## 7. Cache de Consultas Frecuentes (TTL Corto)

Para datos que cambian poco (proveedores, empleados):

```python
# database/repository.py
_cache = {}
_CACHE_TTL = 5  # segundos

def get_all_suppliers_cached():
    now = time.time()
    if "suppliers" in _cache and (now - _cache["suppliers"][0]) < _CACHE_TTL:
        return _cache["suppliers"][1]
    data = get_all_suppliers()
    _cache["suppliers"] = (now, data)
    return data
```

---

## 8. Plan de Implementación

| Paso | Cambio | Archivos | Prioridad |
|------|--------|----------|-----------|
| 1 | Agregar índices SQL | `database/connection.py` | Alta |
| 2 | Optimizar queries (SELECT columnas) | `database/repository.py` | Alta |
| 3 | Medir tiempos de refresh | Cada vista en `ui/views/` | Alta |
| 4 | Cache TTL corto (proveedores, empleados) | `database/repository.py` | Media |
| 5 | Timestamp de refresh en vistas | `ui/views/*.py` | Media |
| 6 | Sistema de notificación EventBus | `core/events.py` + vistas | Baja |
| 7 | Optimización Treeview | `ui/widgets.py`, vistas | Baja |

---

## 9. Validación

1. Medir tiempo de navegación entre 3 vistas diferentes (5 repeticiones cada una)
2. Verificar que los datos se muestren correctamente después de cada CRUD
3. Confirmar que no hay regresiones visuales (colores, layout, scroll)
4. Probar con una base de datos poblada con 500+ productos para verificar escalabilidad

---

## 10. Riesgos y Mitigaciones

| Riesgo | Mitigación |
|--------|------------|
| Cache TTL muestre datos obsoletos | Usar TTL corto (2-5s) e invalidar en escritura |
| Treeview optimizado no se actualice visualmente | Hacer `update_idletasks()` después del batch insert |
| EventBus complique el flujo de datos | Implementar como capa opcional encima de refresh() existente |
| Índices ralenticen escrituras | Las escrituras son poco frecuentes vs. lecturas |

---

*Documento generado a partir del análisis de rendimiento del sistema DigiCable Inventory.*

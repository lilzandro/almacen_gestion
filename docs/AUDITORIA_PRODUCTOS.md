# Auditoría — Ventana Productos

## 1. Resumen ejecutivo

La ventana Productos está funcionalmente completa y con las correcciones
recientes ya aplicadas (alta masiva agrupada, validaciones de alta/edición,
campo Modelo persistido, render por lotes e índices). Quedan **7 hallazgos
nuevos: 2 de severidad alta, 3 media y 2 baja**; además se revisaron dos
frentes sin hallazgos (inyección SQL y doble envío). El riesgo más importante
es la **alta parcial en modo Cantidad** (el producto queda creado sin su
movimiento de entrada si falla el registro de stock) y la **fuga del handler
de escaneo** al cerrar el diálogo de escaneo continuo junto con su padre.

## 2. Alcance y metodología

**Archivos revisados**

- `ui/views/products.py` completo: `ProductsView`, `_GroupRow`, `_ChildRow`,
  `_StatusPill`, `_GroupEditDialog`, `_BarcodeScanDialog`, `_ScanRowDialog`,
  `_PhoneScanHelpDialog`, `_ScanResultDialog`, `_RegistrarProductoDialog`,
  `_ProductDialog`.
- `database/repository.py`: se confirmó contra el `import` real de
  `products.py` que usa **15** funciones: `get_products_grouped`,
  `get_units_by_model`, `get_all_suppliers`, `create_supplier`,
  `create_product`, `update_product_unit`, `update_product_group`,
  `delete_product`, `delete_product_group`, `product_group_exists`,
  `get_product_by_id`, `lookup_product_by_code`, `reactivate_product`,
  `create_movement`, `bulk_create_products`. Se revisaron también sus ayudantes
  (`_backfill_movement_snapshots`, `_adjust_product_stock`,
  `_clean_product_label`) y `get_product_by_barcode` (usada internamente por
  `lookup_product_by_code`). **No** están importadas desde Productos:
  `get_all_products`, `update_product`, `deactivate_product`,
  `reactivate_product_group`.
- `ventanaejemplo/widgets.py` y `ventanaejemplo/theme.py`: `LabeledEntry`,
  `LabeledSelect`, `InventoryToggle`, `SerialTable`, `section_header`.
- `ui/widgets.py`: `MessageDialog`, `ConfirmDialog`, `BaseDialog`,
  `show_centered`/`center_dialog`, y los helpers de borde de error.
- Cruce con `ui/views/dashboard.py`, `ui/dashboard_widgets.py`,
  `ui/views/movements.py` (cómo se ven los movimientos generados desde
  Productos).
- Esquema e índices en `database/connection.py`.

**Metodología**

Lectura de código con verificación por `grep`/AST, ejecución de harness de
Tkinter sobre copia de la BD para los flujos de alta/edición, y
`python -m pytest tests/ -q` (**16/16**). No se modificó código de producción.

**No cubierto**

Pruebas con hardware de escaneo real, concurrencia entre máquinas físicas y
pruebas de accesibilidad con lector de pantalla (se evaluó solo foco/teclado
por lectura de código).

## 3. Hallazgos ya conocidos — estado actual confirmado

| Hallazgo | Sección de CLAUDE.md donde se originó | Estado real hoy |
|---|---|---|
| Alta masiva crea un solo movimiento agrupado | "Alta masiva crea movimientos separados…" | **Resuelto.** `bulk_create_products` inserta un solo `movements` + `movement_items` (`repository.py:104-141`). |
| Render por lotes + índices de rendimiento | "Rendimiento: UI más ágil…" | **Resuelto.** `refresh()` y `_open_group()` usan `after()` por lotes (`products.py:562-590`, `699-722`); índices presentes (`connection.py:186,189`). |
| Campo "Modelo" sin uso real | "Qué campos son obligatorios…" (Hallazgo 0) | **Resuelto.** Columna `products.modelo` + persistencia + campo visible en Equipos de Red/Herramientas (`connection.py:70,116-119`; `products.py:2565`, `:2846`). |
| "Ficha técnica" (`specs`) sin renderizar | "Casos de error en las demás categorías…" | **Pendiente.** `self.spec_widgets = {}` se inicializa y no se usa (`products.py:2349`); `on_categoria_change()` no construye campos desde `specs`. |
| Cantidad decimal se guarda como 0 | "Validación de formularios en Productos" (Hallazgo 1) | **Resuelto.** Se rechaza con aviso (`products.py:3052-3056`). |
| Alta por lote no valida MAC/Código | "Validación de formularios…" (Hallazgo 2) | **Resuelto.** Regex en `guardar()` (`products.py:2965-2977`). |
| Editar unidad no exige Serial/MAC | "Qué campos son obligatorios…" (Hallazgo 1) | **Resuelto.** Con MAC: Serial+MAC; Herramientas: Serial (`products.py:3311-3327`). |
| Fila con solo Código de Barras se descarta sin avisar | "Casos de error en las demás categorías…" (Hallazgo C) | **Resuelto.** Avisa y no guarda (`products.py:2979-2985`). |
| Regla "Serial O MAC" vs "Serial Y MAC" | "Alta por lote acepta filas incompletas…" (Causa B) | **Resuelto: Y.** Equipos de Red exige Serial+MAC+Código (`products.py:2990-3010`). |

## 4. Hallazgos nuevos

### [Severidad: alto] Alta parcial en modo Cantidad/Volumen

- **Archivo:línea:** `ui/views/products.py:3070` (`create_product`) y
  `:3092` (`create_movement`).
- **Descripción:** en la rama cantidad, primero se crea el producto y luego se
  registra el movimiento de entrada. Si `create_movement` falla, se muestra el
  error y se hace `return` **sin borrar el producto** ni cerrar el diálogo. El
  producto queda con stock 0 y sin movimiento de auditoría.
- **Ejemplo / cómo reproducirlo:** categoría Cableado, código y cantidad
  válidos; forzar un fallo de `create_movement` (BD bloqueada / mock del
  repositorio) → el producto aparece en la tabla con stock 0; al reintentar el
  alta, el código de barras ya existe y da `IntegrityError`.
- **Impacto:** inventario con productos sin trazabilidad; reintentos
  confusos; datos inconsistentes entre Productos y Movimientos.
- **Posible solución:** crear producto + movimiento en una sola transacción
  (función de repositorio), o borrar el producto si falla el movimiento.

### [Severidad: alto] Fuga del handler de escaneo en `_ScanRowDialog`

- **Archivo:línea:** `ui/views/products.py:1805` (push) y `:1889` (`_close`);
  no hay bind `<Destroy>`.
- **Descripción:** `_ScanRowDialog` registra `self._phone_code` en
  `app._scan_handlers` y solo lo quita en `_close` (protocolo WM_DELETE). Si el
  diálogo se destruye como hijo del `_RegistrarProductoDialog` (al cerrar el
  Registrar) o si la construcción falla después del push, el handler queda
  "fantasma".
- **Ejemplo / cómo reproducirlo:** abrir Nuevo Producto → "Escanear" (abre
  `_ScanRowDialog`) → cerrar el Registrar con "Cancelar"/Alt+F4 → enviar un
  código desde el teléfono. `App._dispatch_scan` llama al handler de una
  ventana destruida y salta un `TclError`.
- **Impacto:** el escaneo deja de funcionar o lanza excepciones; los handlers se
  acumulan.
- **Posible solución:** bindear `<Destroy>` para hacer `pop_scan_handler`
  (como ya hace `_RegistrarProductoDialog` en `:2340-2341`) y/o quitar el
  handler al cerrar el padre.

### [Severidad: medio] Permisos inconsistentes: editar grupo sin gate y borrados solo por UI

- **Archivo:línea:** `ui/views/products.py:731-783` (`_edit_group`: `is_admin`
  solo se usa para eliminar), `:1003` (`_delete`), `:1620` (`_delete_group`),
  `:1411-1424` (botón "⚙ Editar grupo" siempre visible).
- **Descripción:** un `supervisor` puede **editar grupos** (nombre/marca/
  proveedor). Además, `_delete`, `_delete_group` y `_edit_group` no verifican
  el rol dentro del método: el gating es solo ocultar el botón. `reactivar` sí
  muestra el aviso de admin (`_ScanResultDialog._is_admin`, `:2019,2095`).
- **Ejemplo / cómo reproducirlo:** iniciar sesión como `supervisor` →
  Productos → "⚙ Editar grupo" (disponible); guardar cambios de nombre/marca.
  Alternativamente, invocar `view._delete(...)` por código sin ser admin.
- **Impacto:** edición/borrado no autorizado si se llega por otra vía
  (atajos, futuras pantallas); inconsistencia con la regla de roles.
- **Posible solución:** decidir si "editar grupo" es admin; agregar chequeo de
  rol al inicio de `_edit_group`, `_delete` y `_delete_group` (defensa en
  profundidad).

### [Severidad: medio] Condiciones de carrera de stock (múltiples instancias)

- **Archivo:línea:** `database/repository.py:1240-1300` (`create_movement`
  valida stock con un `SELECT` y luego actualiza), `:675`
  (`update_product_unit`).
- **Descripción:** la validación de disponibilidad y la actualización no están
  en una transacción con `BEGIN IMMEDIATE` ni hay bloqueo optimista. El
  `busy_timeout` evita errores de bloqueo, pero no el sobre-giro.
- **Ejemplo / cómo reproducirlo:** dos instancias de la app con el mismo
  producto (stock 10); ambas registran salida de 8 "al mismo tiempo" → ambas
  validan contra 10 y el stock termina en -6.
- **Impacto:** stock negativo / actualizaciones perdidas entre ventanas o
  equipos.
- **Posible solución:** transacción inmediata con revalidación dentro, o
  `UPDATE ... SET quantity = quantity - ? WHERE id=? AND quantity >= ?` y
  verificar `rowcount`.

### [Severidad: medio] Búsqueda de productos con comodín inicial (`LIKE '%q%'`)

- **Archivo:línea:** `database/repository.py:416-417`
  (`get_products_grouped`), disparada desde `products.py:376` (trace del
  buscador) y `:543` (refresh, con throttle de 1.5 s).
- **Descripción:** el `%` inicial impide usar índices; con catálogos grandes
  cada búsqueda recorre la tabla completa. El throttle mitiga la frecuencia,
  pero no el costo de cada consulta.
- **Ejemplo / cómo reproducirlo:** cargar un catálogo grande (miles de filas)
  y escribir en el buscador; la UI se siente pesada en cada pausa del throttle.
- **Impacto:** lentitud perceptible en Productos con datos reales.
- **Posible solución:** búsqueda por prefijo (`q%`) o FTS5; debounce explícito
  del input.

### [Severidad: bajo] Mensajes de error inconsistentes (título/ícono)

- **Archivo:línea:** `ui/views/products.py:3002` (validación de fila con
  título **"Error"**) frente a `:3304` (validación de MAC con **"Aviso"**);
  varios `MessageDialog(..., "Error", ...)` no pasan `is_error=True`, por lo
  que muestran el ícono de confirmación (✓) en vez del de error.
- **Descripción:** el mismo tipo de problema (validación de un campo) usa
  títulos distintos; los "Error" sin `is_error=True` muestran ícono de éxito.
- **Ejemplo / cómo reproducirlo:** en Equipos de Red dejar una fila vacía
  ("Error") vs editar una unidad con MAC inválida ("Aviso"); ambos son
  validaciones, pero se ven distinto.
- **Impacto:** feedback confuso; parece un error del sistema cuando es una
  validación.
- **Posible solución:** convención: validaciones → "Aviso" + borde rojo;
  fallos del sistema → "Error" + `is_error=True`.

### [Severidad: bajo] Teclado y foco en los formularios principales

- **Archivo:línea:** `_RegistrarProductoDialog` (`:2327`), `_ProductDialog`
  (`:3118`), `_GroupEditDialog` (`:1463`): sin `focus_set()` inicial ni binds
  de Enter/Escape. Los diálogos de escaneo sí los tienen
  (`:1725,1755,1822,1824`).
- **Descripción:** al abrir los formularios, el foco no está en el primer
  campo y no se puede guardar/cerrar solo con teclado.
- **Ejemplo / cómo reproducirlo:** abrir Nuevo Producto y presionar Enter o
  Escape: no ocurre nada; hay que usar el mouse para todo.
- **Impacto:** usabilidad/accesibilidad; más clics para operar.
- **Posible solución:** foco al primer campo; `Return` → guardar,
  `Escape` → cerrar.

### [Severidad: —] Revisado, sin hallazgos: inyección SQL

Todas las consultas alcanzables desde Productos usan placeholders `?`. Las
f-strings solo arman la *forma* de la cláusula con literales internos
(`repository.py:416-429`, `:464-485`, `:978-990`); los valores del usuario van
siempre en `params`. No se encontró interpolación de texto de usuario en SQL.

### [Severidad: —] Revisado, sin hallazgos: doble envío / doble clic

Los handlers de guardado corren en el hilo de Tk y destruyen el diálogo antes
de volver (`products.py:3109-3116` en cantidad, `:3350` en edición de unidad,
`:1693` en edición de grupo). Un segundo clic se procesa recién cuando el
primero termina, sobre un widget ya destruido. No se observó doble inserción.
No hay deshabilitado explícito del botón: si en el futuro `on_save` pasara a
ser asíncrono, habría que agregarlo.

## 5. Ventajas / cosas bien hechas

- Conexiones SQLite siempre con `try/finally` y `close()`
  (`repository.py`, patrón general).
- Borrado de productos conserva historial vía snapshots en `movement_items`
  (`_backfill_movement_snapshots`, `repository.py:826-855`).
- Alta masiva con **un solo** movimiento agrupado
  (`bulk_create_products`, `repository.py:104-141`).
- Render por lotes con guarda de generación (`products.py:562-590`,
  `699-722`).
- Índices `idx_products_name_brand` e `idx_movement_items_movement`
  (`connection.py:186,189`).
- Confirmaciones antes de acciones destructivas (`ConfirmDialog` en
  `products.py:1018-1035`, `_delete_group`).
- Borde rojo centralizado para errores de campo
  (`ui/widgets.py::marcar_error_campo`).
- Cache TTL para proveedores y grupos (`_cached`, `repository.py:26-42`).
- Uso de `movement_items` en lugar de depender de `movements.product_id` para
  el detalle (dashboard/movimientos).

## 6. Desventajas / riesgos de diseño

- **`product_id=0` como convención** para movimientos compuestos: obliga a
  recordar el caso en cada consulta/actualización; es fácil introducir
  regresiones (ya pasó con borrar/editar).
- **"Ficha técnica" (`specs`) sin implementar**: los datos declarados por
  categoría no se muestran ni se guardan; el formulario es idéntico entre
  categorías.
- **Modelo persistido pero no visible/editable**: se guarda en el alta, pero
  la tabla de Productos sigue mostrando el nombre en la columna "Modelo /
  Equipo" y "Editar grupo" no permite modificarlo.
- **Gating de roles solo en UI**: no hay verificación en los métodos de
  servicio/vista.
- **Sin tests de UI**: las validaciones de formularios se prueban a mano; no
  hay cobertura automatizada de diálogos.
- **Convención de mensajes no unificada** (Aviso/Error/ícono).
- **SQLite mono-escritor**: no hay soporte real para múltiples instancias
  concurrentes.
- **`_rebind_mousewheel`** recorre y bindea todos los hijos del cuerpo en cada
  `set_control` (`products.py:2497`), trabajo O(n) repetido.

## 7. Tabla resumen priorizada

| Hallazgo | Severidad | Esfuerzo estimado | ¿Depende de decisión del usuario? |
|---|---|---|---|
| Alta parcial en modo Cantidad | Alto | Bajo/Medio | No |
| Fuga de handler en `_ScanRowDialog` | Alto | Bajo | No |
| Permisos: editar grupo / gating solo UI | Medio | Bajo | Sí (rol de "editar grupo") |
| Carreras de stock multi-instancia | Medio | Medio | No |
| Búsqueda `LIKE '%q%'` | Medio | Medio | No |
| Mensajes de error inconsistentes | Bajo | Bajo | No |
| Foco/teclado en formularios | Bajo | Bajo | No |
| Inyección SQL | — (sin hallazgos) | — | No |
| Doble envío | — (sin hallazgos) | — | No |
| "Ficha técnica" (`specs`) | Diseño | Alto | Sí |
| Mostrar/editar Modelo en tabla/grupo | Diseño | Medio | Sí |

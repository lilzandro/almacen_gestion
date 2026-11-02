# Reportes por filtro de tipo y por selección manual — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Dos funcionalidades nuevas en el diálogo "📊 Reportes" de
Movimientos: (1) que los reportes Diario/Semanal/Mensual se puedan generar
filtrados a un solo tipo de movimiento (ej. "solo salidas"), y (2) que el
usuario pueda seleccionar manualmente filas específicas de la lista y
generar un reporte con exactamente esas, sin importar fecha ni tipo.

**Architecture:** La capa de datos (`database/repository.py::_movement_filters`)
ya soporta filtrar por `movement_types`; solo falta exponerlo en la UI del
diálogo de Reportes. Para la selección manual, se cambia el `ttk.Treeview`
de `selectmode="browse"` (una fila) a `"extended"` (selección múltiple
nativa de Tkinter, con Ctrl/Shift+clic) — **no** se agregan casillas ni
botones superpuestos por fila (esa vía ya se probó frágil y se abandonó en
un plan anterior de este mismo archivo). El diálogo de Reportes lee
`self._view._tree.selection()` para el nuevo tipo de reporte "Selección
actual".

**Tech Stack:** Python, SQLite (`database/repository.py`), CustomTkinter/
Tkinter (`ui/views/movements.py`), pytest.

**Spec:** No hay spec separado. Pedido del usuario: "poder reportar por
filtros (ej. solo salidas)" + "elegir/seleccionar qué movimientos o
cuántos, el mismo usuario, para sacarle un reporte". Contexto de por qué
NO se usan botones/casillas por fila: ver en `CLAUDE.md` las secciones
"Quitar la columna 'acc' de Movimientos..." y las 2 anteriores sobre
botones de fila frágiles.

## Global Constraints

- No agregar dependencias nuevas.
- No tocar el mecanismo de botones de acción por fila que ya se decidió
  quitar (`CLAUDE.md`, plan "Quitar la columna 'acc'...") — si ese plan
  todavía no se aplicó al empezar este, aplicarlo primero o, como mínimo,
  no construir nada nuevo sobre `ttk.Treeview.bbox()`/`.place()` por fila.
- Reusar `_movement_filters`/`get_movements_flat` (`database/repository.py`)
  en vez de escribir una consulta SQL nueva — ya soportan casi todo lo que
  hace falta.
- `python -m pytest tests/ -q` debe pasar después de cada tarea.
- Pruebas de UI real con el gate ya usado:
  `@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)")`.
- El filtro por tipo solo aplica a los reportes Diario/Semanal/Mensual (listas
  planas de movimientos) — "Crítico de cierre" y "Por producto (ranking)"
  son resúmenes agregados de todos los tipos a propósito; no se les agrega
  este filtro (fuera de alcance, confirmarlo explícitamente si se duda).

## Review Focus

- **0 movimientos seleccionados y el usuario elige "Selección actual" y
  aprieta Generar:** debe avisar, no generar un PDF vacío ni crashear.
- **Filtro de tipo = "Todos" en Diario/Semanal/Mensual:** debe comportarse
  exactamente igual que hoy (sin filtro) — no es una regresión para el caso
  por defecto.
- **Seleccionar varias filas con Ctrl+clic y que el resaltado visual
  muestre TODAS como seleccionadas**, no solo la última (bug concreto que
  ya existe en el código de resaltado, ver Tarea 2).
- **El filtro de tipo del diálogo de Reportes debe partir del filtro que
  ya está activo en la lista** (si el usuario tiene el chip "Salida"
  activo y abre Reportes, que arranque en "Salida", no en "Todos") — es
  parte de lo que pidió el usuario, no un detalle menor.
- **Generar un reporte de selección con movimientos de distintos tipos
  mezclados** (ej. 2 entradas + 1 salida seleccionadas a mano) — debe
  listarlos todos tal cual están, sin intentar agruparlos ni resumirlos
  distinto a como ya hace `export_movements` con cualquier lista de filas.

---

### Task 1: `_movement_filters`/`get_movements_flat` aceptan una lista explícita de IDs

**Files:**
- Modify: `database/repository.py:1048` (`_movement_filters`), `:1188`
  (`get_movements_flat`)
- Test: `tests/test_movements.py`

**Interfaces:**
- Consumes: nada nuevo (reusa la conexión/patrón try-finally ya existente).
- Produces: `_movement_filters(search="", movement_types=None,
  warehouse_id=None, date_from=None, date_to=None, ids=None)`,
  `get_movements_flat(warehouse_id=None, search="", movement_types=None,
  limit=1000000, date_from=None, date_to=None, ids=None)` — la Tarea 4
  los usa con `ids=[lista de int]` y el resto de los parámetros en su
  default.

- [ ] **Step 1: Escribir la prueba que falla**

```python
def test_get_movements_flat_filtra_por_lista_de_ids(db, q):
    repo = db["repo"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "uno")
    m1 = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "dos")
    m2 = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "tres")

    rows = repo.get_movements_flat(ids=[m1, m2])
    assert {r["id"] for r in rows} == {m1, m2}
```

- [ ] **Step 2: Correr la prueba para confirmar que falla**

Run: `.venv/bin/python -m pytest tests/test_movements.py -k filtra_por_lista_de_ids -v`
Expected: FAIL con `TypeError: get_movements_flat() got an unexpected keyword argument 'ids'`.

- [ ] **Step 3: Implementar el filtro `ids`**

En `_movement_filters`, agregar el parámetro `ids=None` y, si viene:
```python
if ids:
    ph = ",".join("?" for _ in ids)
    clauses.append(f"m.id IN ({ph})")
    params.extend(ids)
```
En `get_movements_flat`, agregar `ids=None` a la firma y pasarlo a
`_movement_filters(search, movement_types, warehouse_id, date_from, date_to, ids)`.

- [ ] **Step 4: Correr la prueba para confirmar que pasa**

Run: `.venv/bin/python -m pytest tests/test_movements.py -k filtra_por_lista_de_ids -v`
Expected: PASS

- [ ] **Step 5: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add database/repository.py tests/test_movements.py
git commit -m "feat: filtrar movimientos por una lista explicita de ids"
```

---

### Task 2: Selección múltiple nativa en la lista de Movimientos

**Files:**
- Modify: `ui/views/movements.py:641` (`selectmode="browse"`),
  `ui/views/movements.py:1003-1013` (`_on_tree_select`)
- Test: `tests/test_movements_view.py`

**Interfaces:**
- Consumes: ninguna nueva.
- Produces: `self._tree.selection()` ahora puede devolver más de un id —
  es lo que consume la Tarea 4.

- [ ] **Step 1: Escribir la prueba que falla**

```python
def test_on_tree_select_resalta_todas_las_filas_seleccionadas():
    from ui.views.movements import MovementsView

    tagged = {}

    class _Tree:
        def get_children(self):
            return ["1", "2", "3"]

        def exists(self, iid):
            return True

        def selection(self):
            return ("1", "3")  # selección múltiple

        def item(self, iid, tags=None):
            tagged[iid] = tags[0]

    class _View:
        _tree = _Tree()
        _row_tag_for_index = MovementsView._row_tag_for_index

    MovementsView._on_tree_select(_View())
    assert tagged["1"] == "sel"
    assert tagged["3"] == "sel"
    assert tagged["2"] != "sel"
```

- [ ] **Step 2: Correr la prueba para confirmar que falla**

Run: `.venv/bin/python -m pytest tests/test_movements_view.py -k resalta_todas_las_filas -v`
Expected: FAIL — hoy `_on_tree_select` solo le pone el tag `"sel"` a
`sel[0]` ("1"), así que `tagged["3"] == "sel"` no se cumple.

- [ ] **Step 3: Implementar**

En `ui/views/movements.py:641`, cambiar `selectmode="browse"` por
`selectmode="extended"`.

En `_on_tree_select` (línea ~1003-1013), reemplazar el cuerpo por:
```python
def _on_tree_select(self, _event=None):
    """Realza TODAS las filas seleccionadas sin perder el patrón zebra."""
    try:
        sel = set(self._tree.selection())
        for idx, iid in enumerate(self._tree.get_children()):
            if self._tree.exists(iid):
                tag = "sel" if iid in sel else self._row_tag_for_index(idx)
                self._tree.item(iid, tags=(tag,))
    except Exception:
        pass
```

- [ ] **Step 4: Correr la prueba para confirmar que pasa**

Run: `.venv/bin/python -m pytest tests/test_movements_view.py -k resalta_todas_las_filas -v`
Expected: PASS

- [ ] **Step 5: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 6: Verificación manual (no automatizable sin GUI real)**

Abrir Movimientos, hacer clic en una fila, Ctrl+clic en otras 2 — las 3
deben quedar resaltadas iguales (mismo color de selección), no solo la
última. Clic simple en cualquier fila debe volver a dejar solo esa
seleccionada (comportamiento nativo de `extended`, no hay que programarlo
a mano).

- [ ] **Step 7: Commit**

```bash
git add ui/views/movements.py tests/test_movements_view.py
git commit -m "feat: seleccion multiple nativa en la lista de movimientos"
```

---

### Task 3: Filtro de tipo en los reportes Diario/Semanal/Mensual

**Files:**
- Modify: `ui/views/movements.py` — `_ReportsDialog._build`
  (línea ~147-254), `_on_type_changed` (buscar el método que hoy solo
  muestra/oculta `self._dates_frame`), `_build_pdf` (línea ~333-345)
- Test: `tests/test_movements_view.py`

**Interfaces:**
- Consumes: `MovementsView.CHIPS` (lista `(key, label, color)`,
  línea ~432), `MovementsView.TYPE_ALIASES` (línea ~450),
  `get_movements_flat(..., movement_types=...)` (ya existe).
- Produces: `_ReportsDialog` gana un atributo `self._tipo_filtro`
  (`ctk.StringVar`, guarda la **clave** del tipo — "todos", "entrada",
  "salida", etc., no la etiqueta visible) que la Tarea 4 no necesita pero
  no debe pisar.

- [ ] **Step 1: Escribir la prueba que falla**

```python
def test_reportes_arranca_con_el_filtro_de_tipo_activo_en_la_lista():
    from ui.views.movements import _ReportsDialog

    class _View:
        _tipo = "salida"
        current_user = {"username": "admin"}
        def _warehouse_id(self):
            return None
        def _warehouse_name(self):
            return ""

    root = tk.Tk()
    try:
        dlg = _ReportsDialog(root, _View())
        assert dlg._tipo_filtro.get() == "salida"
    finally:
        root.destroy()
```
(usa `tk.Tk()` real porque `_ReportsDialog` construye widgets de verdad en
`__init__` — agregar el gate `@pytest.mark.skipif(not os.environ.get("DISPLAY"), ...)`.)

- [ ] **Step 2: Correr la prueba para confirmar que falla**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_movements_view.py -k arranca_con_el_filtro_de_tipo -v`
Expected: FAIL — `AttributeError: '_ReportsDialog' object has no attribute '_tipo_filtro'`.

- [ ] **Step 3: Agregar el selector de tipo**

En `_ReportsDialog.__init__`, inicializar
`self._tipo_filtro = ctk.StringVar(value=getattr(view, "_tipo", None) or "todos")`
(antes de `self._build()`).

En `_build()`, debajo del selector "Tipo de reporte" y antes de
`self._dates_frame`, agregar un nuevo bloque (mismo estilo que el de tipo
de reporte):
```python
ctk.CTkLabel(
    body, text="Filtrar por tipo de movimiento", anchor="w",
    font=ctk.CTkFont(size=13, weight="bold"), text_color=DSG_TEXT,
).pack(fill="x", padx=16, pady=(12, 4))
self._tipo_labels = {"todos": "Todos"}
self._tipo_labels.update({k: lb for k, lb, _ in MovementsView.CHIPS if k != "todos"})
self._tipo_keys_by_label = {v: k for k, v in self._tipo_labels.items()}
self._tipo_menu = ctk.CTkOptionMenu(
    body, values=list(self._tipo_labels.values()),
    font=ctk.CTkFont(size=13), height=36,
    fg_color=DSG_BRAND, button_color=DSG_BRAND,
    button_hover_color=DSG_PRIMARY_HOVER,
    dropdown_font=ctk.CTkFont(size=13),
    command=lambda label: self._tipo_filtro.set(self._tipo_keys_by_label[label]),
)
self._tipo_menu.set(self._tipo_labels[self._tipo_filtro.get()])
self._tipo_menu.pack(fill="x", padx=16)
self._tipo_filtro_frame = self._tipo_menu  # para mostrar/ocultar en el Step 4
```
(`MovementsView.CHIPS` debe quedar importable/accesible desde
`_ReportsDialog` — ambas clases viven en el mismo módulo, no hace falta
importar nada nuevo).

- [ ] **Step 4: Mostrar el selector solo para Diario/Semanal/Mensual**

Buscar el método que hoy decide `self._dates_frame.pack(...)` /
`pack_forget()` según `kind` (el callback de `_on_type_changed` o
similar) y agregarle la misma condición para `self._tipo_menu`:
```python
if kind in ("Diario", "Semanal", "Mensual"):
    self._tipo_menu.pack(fill="x", padx=16)
else:
    self._tipo_menu.pack_forget()
```
(colocar la línea de `pack`/`pack_forget` en el mismo lugar donde ya se
decide lo mismo para `self._dates_frame`, no crear un callback nuevo).

- [ ] **Step 5: Usar el filtro al generar el PDF**

En `_build_pdf` (línea ~333-345), cambiar:
```python
rows = get_movements_flat(
    warehouse_id=wh_id, date_from=d1s, date_to=d2s
)
```
por:
```python
tipo_key = self._tipo_filtro.get()
movement_types = None if tipo_key == "todos" else self.TYPE_ALIASES_ALL.get(tipo_key, [tipo_key])
rows = get_movements_flat(
    warehouse_id=wh_id, date_from=d1s, date_to=d2s, movement_types=movement_types
)
```
y agregar al `filters_text` la etiqueta del tipo cuando no es "todos":
```python
filtro_txt = f" · Tipo: {self._tipo_labels[tipo_key]}" if tipo_key != "todos" else ""
...
filters_text=(f"Período {kind}: {d1:%d/%m/%Y} a {d2:%d/%m/%Y}{filtro_txt}"),
```
**Nota:** `MovementsView.TYPE_ALIASES` (línea ~450) no tiene entrada para
`"salida"`/`"asignacion"`/`"devolucion"` más que sí mismas — confirmar al
implementar si alcanza con pasar `[tipo_key]` directo en vez de buscar en
`TYPE_ALIASES` (la única clave con alias real es `"eliminacion"` →
`["eliminacion", "eliminacion_grupo"]`); usar
`self.TYPE_ALIASES.get(tipo_key, [tipo_key])` referenciando el diccionario
que ya existe, no uno nuevo (`TYPE_ALIASES_ALL` del borrador de arriba no
existe, es solo ilustrativo — usar el real).

- [ ] **Step 6: Correr la prueba para confirmar que pasa**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_movements_view.py -k arranca_con_el_filtro_de_tipo -v`
Expected: PASS

- [ ] **Step 7: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 8: Verificación manual**

Con el chip "Salida" activo en la lista, abrir Reportes → el selector de
tipo debe arrancar en "Salida". Generar un reporte Semanal con ese filtro
→ el PDF debe listar solo salidas del período, y el subtítulo debe decir
"Tipo: Salida". Cambiar el selector a "Todos" y generar de nuevo → debe
verse igual que antes de este cambio (todas las filas del período, sin
mención de tipo en el subtítulo).

- [ ] **Step 9: Commit**

```bash
git add ui/views/movements.py tests/test_movements_view.py
git commit -m "feat: filtrar por tipo de movimiento los reportes diario/semanal/mensual"
```

---

### Task 4: Nuevo tipo de reporte "Selección actual"

**Files:**
- Modify: `ui/views/movements.py:40` (`REPORT_TYPES`), `_ReportsDialog`
  (`_on_type_changed`/equivalente, `_build_pdf`, `_generate`)
- Test: `tests/test_movements_view.py`

**Interfaces:**
- Consumes: `self._view._tree.selection()` (de la Tarea 2, ahora puede
  traer varios ids), `get_movements_flat(ids=...)` (de la Tarea 1).
- Produces: nada que otra tarea necesite — es la última.

- [ ] **Step 1: Escribir la prueba que falla**

```python
def test_reporte_de_seleccion_sin_filas_seleccionadas_avisa_y_no_genera(monkeypatch):
    from ui.views.movements import _ReportsDialog

    class _Tree:
        def selection(self):
            return ()

    class _View:
        _tree = _Tree()
        current_user = {"username": "admin"}
        def _warehouse_id(self):
            return None
        def _warehouse_name(self):
            return ""

    root = tk.Tk()
    avisos = []
    monkeypatch.setattr(
        "ui.views.movements.MessageDialog",
        lambda *a, **k: avisos.append(a),
    )
    try:
        dlg = _ReportsDialog(root, _View())
        dlg._kind.set("Selección actual")
        dlg._generate()  # no debe pedir archivo ni crashear
        assert avisos  # avisó algo en vez de seguir
    finally:
        root.destroy()
```

- [ ] **Step 2: Correr la prueba para confirmar que falla**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_movements_view.py -k sin_filas_seleccionadas_avisa -v`
Expected: FAIL — `"Selección actual"` no existe en `REPORT_TYPES`, el
`_type_menu`/flujo de `_generate` no lo reconoce.

- [ ] **Step 3: Agregar el tipo de reporte**

En `REPORT_TYPES` (línea 40), agregar `"Selección actual"` a la lista.

En el método que oculta/muestra `self._dates_frame` según `kind` (mismo
lugar que la Tarea 3, Step 4), agregar que para `"Selección actual"`
también se oculten `self._dates_frame` y `self._tipo_menu` (no aplican):
```python
if kind == "Selección actual":
    self._dates_frame.pack_forget()
    self._tipo_menu.pack_forget()
    n = len(self._view._tree.selection())
    self._status.configure(text=f"{n} movimiento(s) seleccionado(s).")
```
(agregar esta rama junto a las que ya existen para los otros `kind`, antes
de la rama genérica de Diario/Semanal/Mensual/Crítico/Ranking).

- [ ] **Step 4: Generar el PDF a partir de la selección**

En `_generate()` (línea ~293), antes de pedir fechas (`self._parse_dates()`
solo tiene sentido para los otros tipos), agregar al principio:
```python
if self._kind.get() == "Selección actual":
    ids = [int(i) for i in self._view._tree.selection()]
    if not ids:
        MessageDialog(self, "Aviso",
                      "Seleccioná al menos un movimiento de la lista "
                      "(Ctrl+clic para elegir varios).", is_warning=True)
        return
    path = filedialog.asksaveasfilename(
        defaultextension=".pdf", filetypes=[("PDF", "*.pdf")],
        initialfile=f"reporte_seleccion_{len(ids)}.pdf",
    )
    if not path:
        return
    rows = get_movements_flat(ids=ids)
    try:
        export_movements(
            path, movements=rows,
            warehouse_name=self._view._warehouse_name(),
            filters_text=f"Selección manual: {len(ids)} movimiento(s)",
            generated_by=self._view.current_user.get("username", ""),
        )
    except Exception as e:
        MessageDialog(self, "Error", f"No se pudo generar el PDF:\n{e}")
        return
    MessageDialog(self._view, "Éxito", f"Reporte PDF generado en:\n{path}")
    self.destroy()
    return
# ... resto del método _generate tal como está hoy para los demás kind
```

- [ ] **Step 5: Correr la prueba para confirmar que pasa**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_movements_view.py -k sin_filas_seleccionadas_avisa -v`
Expected: PASS

- [ ] **Step 6: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 7: Verificación manual**

Seleccionar 3 movimientos de distinto tipo con Ctrl+clic → abrir Reportes
→ elegir "Selección actual" → debe mostrar "3 movimiento(s)
seleccionado(s)" y ocultar fechas/tipo → Generar → el PDF debe listar
exactamente esos 3, sin importar su fecha o tipo real. Repetir con 0
seleccionados → debe avisar sin pedir dónde guardar el archivo.

- [ ] **Step 8: Commit**

```bash
git add ui/views/movements.py tests/test_movements_view.py
git commit -m "feat: reporte PDF a partir de movimientos seleccionados a mano"
```

---

## Self-Review

**1. Cobertura del pedido:** "reportar por filtros (ej. solo salidas)" →
Tarea 3. "Elegir/seleccionar qué movimientos, el usuario mismo, para
sacarle un reporte" → Tareas 2 (selección) + 4 (reporte de esa selección).
Sin gaps.

**2. Revisión de pasos:** cada step deja una sola cosa por escribir. El
Step 5 de la Tarea 3 incluye una nota explícita señalando una
inconsistencia de nombres a resolver con el código real (`TYPE_ALIASES`)
en vez de inventar un diccionario (`TYPE_ALIASES_ALL`) que no existe —
evita que el implementador transcriba un nombre que no está en el código.

**3. Consistencia de tipos/nombres:** `get_movements_flat(..., ids=None)`
se define igual en la Tarea 1 y se consume igual en la Tarea 4.
`self._tipo_filtro`/`self._tipo_menu`/`self._tipo_labels` se nombran igual
en la Tarea 3 (donde se crean) y no se repiten con otro nombre en la
Tarea 4 (que los deja intactos, solo los oculta).

**4. Review Focus:** las 5 líneas de esa sección tienen su tarea: "0
seleccionados" → Tarea 4 Step 1/4; "filtro Todos sin regresión" → Tarea 3
Step 8; "Ctrl+clic resalta todas" → Tarea 2; "arranca con el filtro
activo" → Tarea 3 Step 1; "selección con tipos mezclados" → Tarea 4 Step 7
(verificación manual, ya que `export_movements` no distingue tipos al
listar, no hace falta una prueba automatizada nueva para esto, es el mismo
camino que ya usa cualquier lista de filas).

**5. Proporción:** 4 tareas para 2 pedidos del usuario, cada una con
test-primero porque son cambios concretos y acotados (no hay una parte
"a auditar primero" como en el plan anterior) — el tamaño es proporcional
a lo pedido, no a una exploración.

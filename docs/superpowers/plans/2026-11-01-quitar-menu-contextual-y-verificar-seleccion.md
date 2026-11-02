# Quitar menú contextual de Movimientos y verificar selección múltiple Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Eliminar el menú contextual (clic derecho → "✎ Editar"/"✕ Eliminar") de la lista de Movimientos, ahora redundante porque esas acciones ya viven en `_MovementInfoDialog` (doble clic); y verificar que la selección múltiple nativa (`selectmode="extended"`) resalta todas las filas elegidas sin importar el orden en que el usuario las haga clic.

**Architecture:** Cambio 1 es una eliminación acotada en `ui/views/movements.py`: quitar el bind `<Button-3>`, la construcción de `self._ctx_menu`, la inicialización de `self._ctx_id`, y los 3 métodos (`_on_right_click`, `_edit_ctx`, `_delete_ctx`) — sin tocar `_edit_movement`/`_delete_movement`, que son las implementaciones reales y siguen siendo llamadas desde `_MovementInfoDialog` y desde `<Delete>`. Cambio 2 no modifica código de producción: `_on_tree_select` ya convierte `self._tree.selection()` a un `set` y tagea por pertenencia, así que el orden de clic nunca importa; se agrega un test que fija esa garantía explícitamente (selección en orden distinto al de aparición en el árbol) en vez de inventar un fix para un bug que no existe.

**Tech Stack:** Python 3.10+, Tkinter/ttk (`Treeview`, `tk.Menu`), pytest.

**Spec:** Pedido del usuario en esta conversación — sin spec/doc separado; el `CLAUDE.md` del proyecto documenta el contrato de cada vista y el historial de decisiones (sección "Plan pendiente para el ejecutor — Quitar la columna 'acc'...", ya ejecutada, que dejó Editar/Eliminar únicamente en `_MovementInfoDialog`, el menú contextual y `Supr` como accesos alternativos que explícitamente no se tocaron en ese momento).

## Global Constraints

- No modificar `_edit_movement`/`_delete_movement`/`_edit_ctx`'s destino final de lógica — solo se quita el *acceso* vía clic derecho, no la funcionalidad de editar/eliminar en sí.
- `Supr` (tecla Delete, `_on_delete_key`) y el botón "✕ Eliminar"/"✎ Editar" dentro de `_MovementInfoDialog` quedan intactos — no están en el alcance de este plan.
- No tocar `selectmode="extended"` ni la lógica de `_on_tree_select` si la Tarea 2 confirma que ya funciona correctamente — este plan no inventa un fix para un problema que no existe.
- `python -m pytest tests/ -q` en verde después de cada tarea.

## Review Focus

- Clic derecho sobre una fila después del cambio: no debe lanzar `AttributeError` (por ejemplo si algo externo invoca `_on_right_click` o referencia `self._ctx_menu`/`self._ctx_id` que ya no existen) — se verifica con grep antes de borrar y con la suite de tests después.
- Selección múltiple con Ctrl+clic en orden "hacia atrás" (p. ej. clic en la fila 5 y luego en la fila 2, no 2 y luego 5) — debe resaltar ambas igual que si se hiciera en orden ascendente, porque `_on_tree_select` no depende del orden de `self._tree.selection()`.
- Selección múltiple con Shift+clic (rango contiguo) seguida de un Ctrl+clic que *deselecciona* una fila ya elegida — el test ya existente cubre selección, pero no deselección; se agrega ese caso para confirmar que una fila que sale de `selection()` también pierde el tag `"sel"` y vuelve a su tag zebra normal.
- Que no quede ningún test en `tests/test_movements_view.py` referenciando `_ctx_menu`/`_edit_ctx`/`_delete_ctx`/`_on_right_click` tras el borrado (ninguno los referencia hoy, confirmado por grep, pero se re-verifica tras el cambio).
- Que `_on_delete_key` (tecla Supr) siga funcionando igual — no depende de nada que se borre en este plan, pero se corre la suite completa para confirmarlo, no solo los tests nuevos.

---

### Task 1: Quitar el menú contextual de clic derecho

**Files:**
- Modify: `ui/views/movements.py:565` (init `self._ctx_id = None`)
- Modify: `ui/views/movements.py:772` (bind `<Button-3>`)
- Modify: `ui/views/movements.py:775-779` (construcción de `self._ctx_menu`)
- Modify: `ui/views/movements.py:1168-1174` (`_on_right_click`)
- Modify: `ui/views/movements.py:1182-1188` (`_edit_ctx`, `_delete_ctx`)
- Test: `tests/test_movements_view.py`

**Interfaces:**
- Consumes: `MovementsView._edit_movement(self, mid)` y `MovementsView._delete_movement(self, mid)` — ya existen, no cambian de firma, siguen siendo las implementaciones reales invocadas desde `_MovementInfoDialog`.
- Produces: nada nuevo — esta tarea solo retira código muerto de acceso. Ninguna otra tarea ni archivo depende de `self._ctx_menu`/`self._ctx_id`/`_on_right_click`/`_edit_ctx`/`_delete_ctx` (confirmado por grep en `ui/views/movements.py` y `tests/test_movements_view.py` antes de este plan).

- [ ] **Step 1: Confirmar con grep que no queda ninguna otra referencia externa**

Run: `grep -rn "_ctx_menu\|_ctx_id\|_on_right_click\|_edit_ctx\|_delete_ctx" ui/ tests/`
Expected: solo las líneas ya listadas arriba en `ui/views/movements.py`. Ninguna en `tests/` ni en otros archivos de `ui/`. Si aparece algo inesperado, detener y re-evaluar antes de continuar.

- [ ] **Step 2: Escribir el test que fija el comportamiento esperado tras el borrado**

```python
def test_clic_derecho_ya_no_dispara_menu_contextual():
    """Tras quitar _ctx_menu, la clase no debe tener rastros del mecanismo viejo."""
    from ui.views.movements import MovementsView
    assert not hasattr(MovementsView, "_on_right_click")
    assert not hasattr(MovementsView, "_edit_ctx")
    assert not hasattr(MovementsView, "_delete_ctx")
```

- [ ] **Step 3: Run test to verify it fails**

Run: `pytest tests/test_movements_view.py::test_clic_derecho_ya_no_dispara_menu_contextual -v`
Expected: FAIL — los 3 métodos todavía existen en la clase.

- [ ] **Step 4: Borrar el bind, la construcción del menú, la inicialización de `_ctx_id`, y los 3 métodos**

Quitar exactamente:
```python
self._tree.bind("<Button-3>", self._on_right_click)
```
```python
self._ctx_menu = tk.Menu(self, tearoff=0, font=self._fonts["sub"])
self._ctx_menu.add_command(label="✎ Editar", command=self._edit_ctx)
self._ctx_menu.add_separator()
self._ctx_menu.add_command(
    label="✕ Eliminar", foreground=DSG_DANGER, command=self._delete_ctx
)
```
```python
self._ctx_id = None
```
```python
def _on_right_click(self, event):
    iid = self._tree.identify_row(event.y)
    if not iid:
        return
    self._ctx_id = int(iid)
    self._ctx_menu.post(event.x_root, event.y_root)
```
```python
def _edit_ctx(self):
    if self._ctx_id is not None:
        self._edit_movement(self._ctx_id)

def _delete_ctx(self):
    if self._ctx_id is not None:
        self._delete_movement(self._ctx_id)
```
No tocar `_on_delete_key` (queda justo entre `_on_right_click` y `_edit_ctx` en el archivo actual — borrar alrededor, no el método en sí) ni ninguna otra línea del bloque de binds (`<Double-1>`, `<Delete>`, `<<TreeviewSelect>>` se quedan igual).

- [ ] **Step 5: Run test to verify it passes**

Run: `pytest tests/test_movements_view.py::test_clic_derecho_ya_no_dispara_menu_contextual -v`
Expected: PASS

- [ ] **Step 6: Run full suite**

Run: `python -m pytest tests/ -q`
Expected: todos los tests pasan (mismo conteo que antes, +1 por el test nuevo de este paso).

- [ ] **Step 7: Commit**

```bash
git add ui/views/movements.py tests/test_movements_view.py
git commit -m "fix: quitar menu contextual redundante de Movimientos

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: Verificar que la selección múltiple resalta todas las filas sin importar el orden de clic

**Files:**
- Test: `tests/test_movements_view.py` (junto a `test_on_tree_select_resalta_todas_las_filas_seleccionadas`, línea ~225)

**Interfaces:**
- Consumes: `MovementsView._on_tree_select(self, _event=None)` y `MovementsView._row_tag_for_index` — ya existen, sin cambios de firma (confirmado leyendo el código actual: itera `self._tree.get_children()` por índice, construye `sel = set(self._tree.selection())`, y tagea `"sel"` si el iid pertenece al set, o el tag zebra normal si no).
- Produces: nada — esta tarea es de verificación. Si el Step 2 revela un gap real, se añade un Step de fix antes de continuar; si no, se documenta que no hace falta.

- [ ] **Step 1: Escribir un test que seleccione filas en orden distinto al de aparición en el árbol, incluyendo una deselección**

```python
def test_on_tree_select_resalta_sin_importar_el_orden_de_clic():
    """Ctrl+clic en la fila 5 y luego en la 2 (orden 'hacia atrás') debe
    resaltar ambas igual que si se hubiera hecho en orden ascendente —
    _on_tree_select no debe depender del orden de selection()."""
    from ui.views.movements import MovementsView

    tagged = {}

    class _Tree:
        def get_children(self):
            return ["1", "2", "3", "4", "5"]

        def exists(self, iid):
            return True

        def selection(self):
            # Tkinter puede devolver la selección en cualquier orden interno;
            # aquí se simula deliberadamente "5 antes que 2" para probar que
            # el método no asume orden ascendente.
            return ("5", "2")

        def item(self, iid, tags=None):
            tagged[iid] = tags[0]

    class _View:
        _tree = _Tree()
        _row_tag_for_index = MovementsView._row_tag_for_index

    MovementsView._on_tree_select(_View())
    assert tagged["2"] == "sel"
    assert tagged["5"] == "sel"
    assert tagged["1"] != "sel"
    assert tagged["3"] != "sel"
    assert tagged["4"] != "sel"


def test_on_tree_select_deselecciona_fila_que_sale_de_selection():
    """Si una fila deja de estar en selection() (el usuario la deselecciona
    con otro Ctrl+clic), debe volver a su tag zebra normal, no quedar
    marcada 'sel' para siempre."""
    from ui.views.movements import MovementsView

    tagged = {}

    class _Tree:
        def get_children(self):
            return ["1", "2", "3"]

        def exists(self, iid):
            return True

        def selection(self):
            return ("1",)  # "2" ya no está seleccionada

        def item(self, iid, tags=None):
            tagged[iid] = tags[0]

    class _View:
        _tree = _Tree()
        _row_tag_for_index = MovementsView._row_tag_for_index

    MovementsView._on_tree_select(_View())
    assert tagged["1"] == "sel"
    assert tagged["2"] != "sel"
    assert tagged["3"] != "sel"
```

- [ ] **Step 2: Run tests to verify current behavior**

Run: `pytest tests/test_movements_view.py::test_on_tree_select_resalta_sin_importar_el_orden_de_clic tests/test_movements_view.py::test_on_tree_select_deselecciona_fila_que_sale_de_selection -v`
Expected: **PASS en ambos, sin tocar `_on_tree_select`** — el método ya usa `set(self._tree.selection())` y chequea pertenencia por iid, no por posición ni por orden de la tupla devuelta por `selection()`. Si alguno de los dos falla, hay un gap real: leer `_on_tree_select` de nuevo y agregar un Step 3 de fix antes de hacer commit (no se anticipa código de fix acá porque no se espera que falle).

- [ ] **Step 3: Run full suite**

Run: `python -m pytest tests/ -q`
Expected: todos los tests pasan, incluidos los 2 nuevos.

- [ ] **Step 4: Commit**

```bash
git add tests/test_movements_view.py
git commit -m "test: fijar que la seleccion multiple de movimientos no depende del orden de clic

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Self-Review

1. **Spec coverage:** Parte (a) del pedido (quitar menú contextual) → Task 1. Parte (b) (revisar selección en cualquier orden) → Task 2. Ambas cubiertas.
2. **Step scan:** cada step deja una sola acción verificable (borrar un bloque exacto, correr un comando con salida esperada, commitear). El Step 2 de la Tarea 2 contempla explícitamente el caso de que la verificación revele un gap real (no asume de antemano que todo está bien, pero tampoco inventa un fix no necesario).
3. **Type consistency:** `_on_tree_select`, `_row_tag_for_index`, `_edit_movement`, `_delete_movement` se nombran igual que en el código actual (confirmado por grep/lectura directa antes de escribir el plan).
4. **Review Focus:** las 4 líneas de la sección de arriba (AttributeError tras borrar, orden "hacia atrás", deselección, tests huérfanos) tienen su test o verificación en las tareas correspondientes.
5. **Proporción:** plan breve, acorde a un cambio de eliminación acotada + una verificación sin código de producción nuevo — no hay transcripción de código salvo los bloques exactos a borrar (necesarios para que el ejecutor los ubique sin ambigüedad) y los 2 tests nuevos (cortos, con nombres y aserciones concretas).

---

Plan completo y guardado en `docs/superpowers/plans/2026-11-01-quitar-menu-contextual-y-verificar-seleccion.md`. Por favor revísalo. ¿Qué método de ejecución prefieres?

- **Subagent-driven** — un subagente fresco implementa cada tarea y un revisor fresco la chequea antes de pasar a la siguiente, más una revisión final de toda la rama. Más riguroso; cuesta un contexto nuevo por tarea y por revisión.
- **Native** — se implementa todo en esta misma sesión, como ya viene haciendo el ejecutor (opencode) entre turnos, con una revisión final de toda la rama al terminar. Más barato y rápido; sin revisión independiente hasta el final.

Para este plan recomiendo **Native**: son 2 tareas cortas, desacopladas entre sí (una borra código, la otra solo agrega tests de verificación sin tocar producción), y el costo de un error sería mínimo (en el peor caso, un test de más que falla y se corrige al toque) — no justifica el overhead de un subagente+revisor por tarea. ¿El plan refleja lo que querés, y con qué método seguimos?

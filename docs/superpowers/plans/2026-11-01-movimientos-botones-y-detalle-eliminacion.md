# Botones de fila y detalle de eliminación en Movimientos — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Corregir dos problemas reportados por el usuario en la ventana de
Movimientos: (1) los botones reales de Editar/Eliminar por fila no se ven de
forma confiable, y (2) cerrar la brecha de cobertura que deja sin probar si
el detalle de un movimiento de eliminación realmente *muestra en pantalla*
los productos eliminados (el dato ya se guarda y se devuelve correctamente,
pero nunca se verificó que la UI lo pinte).

**Architecture:** `ui/views/movements.py::MovementsView` usa un
`ttk.Treeview` nativo para la lista (por rendimiento) con botones
`ctk.CTkButton` reales superpuestos vía `.place()` sobre la celda "acc" de
cada fila visible (patrón ya implementado en el commit `b745472`). El
detalle de un movimiento (`_MovementInfoDialog`) itera
`detail["items"]` (ya devuelto por `get_movement_detail()`) y crea una fila
visual (`_item_line`) por cada ítem. No se cambia esta arquitectura — se
corrige un bug de sincronización de temporización en la primera y se agrega
la prueba de UI que falta en la segunda.

**Tech Stack:** Python, CustomTkinter, `tkinter.ttk.Treeview`, pytest
(pruebas de UI con gate `DISPLAY` existente en `tests/test_movements_view.py`).

**Spec:** No hay un documento de spec separado. El contexto completo está en
`CLAUDE.md` (secciones "Rediseño del diálogo 'Editar Movimiento'..." y
"Comprobante automático al registrar Salida o Devolución", y los commits
`064dc21`/`b745472` que ya implementaron la base de ambas funcionalidades).
Este plan documenta el diagnóstico hecho ahora, leyendo el código actual:

- **Problema 1 (botones no visibles):** `MovementsView._refresh_table()`
  (`ui/views/movements.py:955-1007`) llama `self._ensure_widths(0)` y luego
  `self.after_idle(self._sync_row_buttons)` **en la misma pasada**.
  `_ensure_widths` (línea 1036-1043) solo aplica el ancho real de columnas
  (`_apply_widths`) si `self._tree.winfo_width() > 60`; si todavía no (muy
  probable justo después de abrir la vista, antes de que la ventana termine
  de mapearse), se reprograma con `self.after(60, ...)` y **no** aplica el
  ancho ahora. Pero el `after_idle(self._sync_row_buttons)` de la línea 1007
  corre de todas formas, con la columna `"acc"` todavía en su ancho inicial
  genérico (`width=60` fijado al crear el Treeview, línea ~647), no en su
  ancho real (`COL_MINS` tiene 150 para `"acc"`). `_sync_row_buttons`
  (línea 1110-1138) no comprueba esto — coloca los botones usando el ancho
  que haya en ese momento, aunque esté mal, y **no hay ningún mecanismo que
  vuelva a corregir esa posición específica** salvo que, por casualidad,
  `_ensure_widths` termine su propio reintento y dispare
  `_queue_row_button_sync()` después. El resultado observable: en el primer
  render de la vista, los botones pueden no aparecer donde corresponde (o no
  aparecer en una posición visible dentro de la tarjeta).
- **Problema 2 (detalle de eliminación):** el commit `b745472` ya agregó
  snapshots en `movement_items` para `delete_product`/`delete_product_group`
  y ya hay tests de `database/repository.py::get_movement_detail` que
  confirman que el *dato* vuelve bien (`tests/test_movements.py`, pasan los
  59 tests actuales). Lo que **no existe** es una prueba que confirme que
  `_MovementInfoDialog` (la ventana que el usuario realmente mira)
  efectivamente convierte esos ítems en filas visibles en pantalla — es una
  brecha de cobertura real, no una certeza de que haya un bug en el
  renderizado (la lectura del código de `_MovementInfoDialog`, líneas
  1544-1558, sugiere que sí funciona). Esta tarea cierra esa brecha con una
  prueba real; si la prueba falla, revela el bug exacto a corregir; si pasa,
  confirma que el problema que ve el usuario es con datos **anteriores** al
  commit `b745472` (eliminaciones viejas, sin snapshot, que es una
  limitación de datos históricos ya documentada y aceptada, no corregible
  sin inventar información que nunca se guardó).

## Global Constraints

- Python 3.10+, CustomTkinter, `ttk`/`tkinter` estándar — no agregar
  dependencias nuevas.
- No tocar `database/repository.py` en este plan — ya está corregido y
  probado (commit `b745472`); si la Tarea 2 revela un bug, está en
  `ui/views/movements.py`, no en la capa de datos.
- Las pruebas de UI con Tkinter real van en `tests/test_movements_view.py`,
  con el mismo gate ya usado: `@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)")`.
- `python -m pytest tests/ -q` debe pasar (59 tests hoy) después de cada
  tarea.
- Seguir el patrón de reintento ya establecido en `_ensure_widths`
  (`self.after(60, ...)`, tope de intentos) para cualquier espera de
  geometría — no inventar un patrón nuevo.
- Commits en inglés (conventional commits), comentarios en código en
  español — convención ya documentada en `CLAUDE.md`.

## Review Focus

- **Primer render de la vista (ventana recién abierta, antes de que el
  Treeview termine de mapearse):** los botones deben aparecer en su
  posición correcta sin que el usuario tenga que redimensionar, hacer
  scroll o cambiar de pestaña — este es el bug reportado. Cubierto en
  Tarea 1.
- **Columna "acc" todavía con su ancho inicial genérico (60px) cuando se
  intenta posicionar un botón:** no debe colocarse con datos de geometría
  obsoletos — debe reintentar hasta que el ancho real esté aplicado.
  Cubierto en Tarea 1.
- **Movimiento de eliminación de grupo con varios productos:** el detalle
  debe mostrar **cada** producto eliminado, no solo uno. Cubierto en
  Tarea 2.
- **Movimiento de eliminación sin `movement_items` (dato histórico, de
  antes del commit `b745472`):** el detalle no debe quedar en blanco ni
  crashear — debe caer al texto de `notes`. Ya cubierto por
  `test_eliminacion_heredada_sin_items_muestra_la_nota` existente; no se
  repite, solo se confirma que sigue pasando.
- **Filas que salen de la vista por scroll/paginación:** sus botones deben
  ocultarse (`place_forget`), no quedar flotando sobre otra fila. Ya
  implementado (`_sync_row_buttons`, líneas 1135-1138); no es una regresión
  de este plan, pero la Tarea 1 no debe romperlo — se agrega verificación
  manual en esa tarea.

---

### Task 1: `_sync_row_buttons` espera a que la columna "acc" tenga su ancho real antes de posicionar botones

**Files:**
- Modify: `ui/views/movements.py:1110-1138` (`_sync_row_buttons`)
- Test: `tests/test_movements_view.py`

**Interfaces:**
- Consumes: `MovementsView.COLS`, `MovementsView.COL_MINS` (ya existen,
  líneas 403 y 406 — `COL_MINS` tiene el ancho mínimo real de `"acc"`,
  150px), `self._tree.column(col, option)` (API estándar de
  `ttk.Treeview`, ya usada en el archivo).
- Produces: `_sync_row_buttons(self, attempts=0)` — mismo nombre, nueva
  firma con `attempts` opcional (todos los llamadores actuales
  —`after_idle(self._sync_row_buttons)`, `_queue_row_button_sync`,
  `_on_scroll`— siguen funcionando sin cambios porque `attempts` tiene
  default).

- [ ] **Step 1: Escribir la prueba que falla**

```python
def test_sync_row_buttons_reintenta_si_la_columna_acc_no_tiene_su_ancho_real():
    """Si 'acc' todavía está en su ancho inicial (no el real, de COL_MINS),
    _sync_row_buttons no debe posicionar botones con esa geometría
    obsoleta — debe reprogramarse con self.after(60, ...)."""
    from ui.views.movements import MovementsView

    calls = []

    class _Tree:
        def column(self, col, option=None):
            assert col == "acc"
            return 60  # ancho inicial genérico, no el real (150)

        def get_children(self):
            raise AssertionError(
                "no debería llegar a iterar filas con el ancho sin aplicar"
            )

    class _View:
        COLS = MovementsView.COLS
        COL_MINS = MovementsView.COL_MINS
        _widgets_built = True
        _tree = _Tree()
        _row_buttons = {}

        def after(self, ms, fn):
            calls.append(ms)

    MovementsView._sync_row_buttons(_View())
    assert calls == [60]
```

- [ ] **Step 2: Correr la prueba para confirmar que falla**

Run: `.venv/bin/python -m pytest tests/test_movements_view.py -k acc_no_tiene_su_ancho -v`
Expected: FAIL — hoy `_sync_row_buttons` no comprueba el ancho de `"acc"`
antes de llamar `self._tree.get_children()`, así que la aserción del stub
(`raise AssertionError(...)`) se dispara.

- [ ] **Step 3: Implementar el guard en `_sync_row_buttons`**

En `ui/views/movements.py`, cambiar la firma a
`def _sync_row_buttons(self, attempts=0):` y agregar, como primera
comprobación después del `if not self._widgets_built: return` ya existente:
```python
min_w = self.COL_MINS[self.COLS.index("acc")]
if self._tree.column("acc", "width") < min_w:
    if attempts < 20:
        self.after(60, lambda: self._sync_row_buttons(attempts + 1))
    return
```
(mismo tope de 20 intentos / 60ms que ya usa `_ensure_widths`, línea 1036 —
no inventar otro número). El resto del cuerpo del método (el loop de
`get_children()` y posicionamiento) queda exactamente igual, debajo de este
guard nuevo.

- [ ] **Step 4: Correr la prueba para confirmar que pasa**

Run: `.venv/bin/python -m pytest tests/test_movements_view.py -k acc_no_tiene_su_ancho -v`
Expected: PASS

- [ ] **Step 5: Correr toda la suite para confirmar que no se rompió nada**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS (60 tests — los 59 actuales + el nuevo de este paso)

- [ ] **Step 6: Verificación manual (no automatizable sin GUI real)**

Abrir la app (`python main.py`), ir directo a Movimientos como primera
pantalla después de iniciar sesión, y confirmar que los botones "Editar"/
"Eliminar" aparecen sobre cada fila **de inmediato**, sin tener que
redimensionar la ventana ni hacer scroll. Repetir cambiando de página y
haciendo scroll — los botones deben seguir las filas visibles y
desaparecer de las que salen de la vista (comportamiento ya existente, solo
confirmar que sigue igual).

- [ ] **Step 7: Commit**

```bash
git add ui/views/movements.py tests/test_movements_view.py
git commit -m "fix: esperar el ancho real de la columna acc antes de ubicar los botones de fila"
```

---

### Task 2: Prueba de UI para el detalle de un movimiento de eliminación de grupo (varios productos)

**Files:**
- Test: `tests/test_movements_view.py`
- Modify (solo si el Step 2 revela un bug real): `ui/views/movements.py`
  (método `_MovementInfoDialog`, sección "Productos", líneas ~1554-1558)

**Interfaces:**
- Consumes: `ui.views.movements._MovementInfoDialog(parent, movement_id, on_edit=None)`,
  y el módulo-level `get_movement_detail` que ese archivo importa de
  `database.repository` (monkeypatcheable como
  `ui.views.movements.get_movement_detail`).
- Produces: ninguna interfaz nueva — esta tarea solo agrega cobertura.

- [ ] **Step 1: Escribir la prueba**

```python
@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_detalle_de_eliminacion_de_grupo_muestra_cada_producto(monkeypatch):
    import ui.views.movements as movements_mod

    detail = {
        "id": 42,
        "type": "eliminacion_grupo",
        "timestamp": "2026-11-01 10:00:00",
        "quantity": 2,
        "notes": "Grupo eliminado: AP (TP-Link). 2 eliminados",
        "product": "",
        "brand": "",
        "unit": "",
        "employee": "-",
        "cargo": "",
        "registered_by": "admin",
        "warehouse": "",
        "items": [
            {"name": "AP", "brand": "TP-Link", "qty": 1, "unit": "und",
             "seriales": "AP-1"},
            {"name": "AP", "brand": "TP-Link", "qty": 1, "unit": "und",
             "seriales": "AP-2"},
        ],
    }
    monkeypatch.setattr(movements_mod, "get_movement_detail", lambda mid: detail)

    root = tk.Tk()
    root.withdraw()
    try:
        dlg = movements_mod._MovementInfoDialog(root, movement_id=42)
        texts = [
            w.cget("text")
            for w in dlg.winfo_children()
            for w in w.winfo_children()
            for w in w.winfo_children()
            if hasattr(w, "cget") and "text" in w.keys()
        ]
        assert sum("AP-1" in t for t in texts) == 1
        assert sum("AP-2" in t for t in texts) == 1
    finally:
        dlg.destroy()
        root.destroy()
```
**Nota para quien implemente:** la búsqueda de `texts` recorre 3 niveles de
hijos porque `_item_line` anida `CTkFrame` (fila) → `CTkLabel` (texto) — si
al correr la prueba la profundidad real es otra, ajustar la cantidad de
`for w in w.winfo_children()` hasta que encuentre las etiquetas (es un
detalle de implementación del árbol de widgets, no algo que este plan deba
fijar de antemano).

- [ ] **Step 2: Correr la prueba**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_movements_view.py -k detalle_de_eliminacion_de_grupo -v`
(ajustar `DISPLAY` al valor real del entorno si no es `:0`)

**Dos resultados posibles, ambos informativos — no asumir cuál va a pasar:**
- **Si PASA:** confirma que el renderizado de `_MovementInfoDialog` ya
  funciona bien para datos nuevos, y que lo que el usuario vio
  corresponde a una eliminación **anterior** al commit `b745472` (sin
  `movement_items` guardados — limitación de datos históricos, no de
  código). En ese caso: no tocar `movements.py`, ir directo al Step 4 y
  dejar constancia de esta conclusión en el mensaje del commit.
- **Si FALLA:** revela un bug real de renderizado. Ir al Step 3 para
  corregirlo antes de continuar.

- [ ] **Step 3 (solo si el Step 2 falló): corregir el renderizado**

Revisar `_MovementInfoDialog` líneas 1544-1558 (`items = detail.get("items") or []`,
loop `for it in items: self._item_line(right, it)`) contra el mensaje de
fallo exacto de la prueba — el fix depende de qué reveló el fallo
específico (ej. un `self._section(...)` que se llama una sola vez y
sobrescribe en vez de acumular, un límite de filas no documentado, etc.).
No hay una corrección única que anticipar aquí sin ver el fallo real.

- [ ] **Step 4: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tests/test_movements_view.py
# (agregar también ui/views/movements.py si el Step 3 aplicó)
git commit -m "test: cubrir que el detalle de eliminacion de grupo muestra cada producto"
```

---

## Self-Review

**1. Cobertura del "spec":** los 2 problemas reportados por el usuario
tienen cada uno su tarea (Tarea 1 = botones no visibles, Tarea 2 = detalle
de eliminación). Sin gaps.

**2. Revisión de pasos:** cada step deja exactamente una cosa por escribir
(el stub de la Tarea 1 está completo porque la firma de `_sync_row_buttons`
y el valor de `COL_MINS`/`"acc"` son datos fijos del código actual, no una
decisión abierta). El Step 3 de la Tarea 2 queda deliberadamente abierto
porque, a diferencia de la Tarea 1, no hay certeza de que exista un bug —
fijar un fix de antemano sería inventar una solución a un problema que
quizás no está ahí.

**3. Consistencia de tipos/nombres:** `_sync_row_buttons(self, attempts=0)`
se usa igual en la Tarea 1 (definición) y no se vuelve a nombrar distinto
en ningún otro lado del plan. `COL_MINS`/`COLS` se usan con los mismos
nombres que ya tiene la clase real (confirmado leyendo
`ui/views/movements.py`, no inventados).

**4. Review Focus:** las 4 líneas de esa sección tienen cada una su tarea o
su confirmación explícita (la de filas fuera de vista ya está cubierta por
código existente, se verifica manualmente en la Tarea 1 en vez de
duplicar una prueba automatizada que ya no haría falta).

**5. Proporción:** el plan es más largo que el diff esperado (2 guards +
2 tests) porque incluye el diagnóstico completo con números de línea reales
—necesario para que quien lo implemente no tenga que releer todo
`movements.py` para encontrar el bug exacto—, no porque describa el código
línea por línea. Los cuerpos de función se dieron completos solo donde la
firma/test no los determinan por sí solos (el guard de la Tarea 1 es un
algoritmo concreto que hay que fijar; el Step 3 de la Tarea 2 se dejó sin
cuerpo a propósito, por la razón del punto 2).

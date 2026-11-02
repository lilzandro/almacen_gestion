# Auditoría de ventanas emergentes (popups) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Auditar todas las ventanas emergentes (diálogos `BaseDialog`/
`CTkToplevel`) del sistema para encontrar y corregir errores de
visualización de información (contenido cortado, botones fuera de la
ventana, geometría declarada que no corresponde al contenido real), usando
una técnica empírica ya probada en este proyecto (no solo lectura de
código — leer código dos veces antes ya dejó pasar bugs reales que solo
aparecieron al correr la ventana de verdad).

**Architecture:** Cada popup es una subclase de `BaseDialog`
(`ui/widgets.py:250`) o, en un caso, un `ctk.CTkToplevel` directo
(`DashboardView._show_movement_detail`). La auditoría instancia cada
diálogo en una ventana Tk real pero movida fuera de la pantalla visible
(`geometry("...+3000+3000")`), bombea el loop de eventos un rato, y compara
el tamaño **declarado** (`geometry()`/`resizable`) contra el tamaño que el
contenido **realmente necesita** (`winfo_reqwidth/reqheight`) y la posición
de cada botón respecto al borde inferior de la ventana — exactamente la
técnica que ya encontró y confirmó 3 bugs reales en esta sesión (el guard
de ancho de columna, el debounce de `<Configure>`, y el hallazgo de la
Tarea 1 de este plan).

**Tech Stack:** Python, CustomTkinter/Tkinter, pytest (pruebas con gate
`DISPLAY`, patrón ya usado en `tests/test_movements_view.py`).

**Spec:** No hay spec separado. El pedido es del usuario: "auditoría a
todas las ventanas emergentes... para reparar errores de visualización de
información". El diagnóstico de la Tarea 1 ya se hizo corriendo el código
real (ver esa sección); el resto de los diálogos (Tarea 2) quedan
pendientes de auditar con la misma técnica.

## Global Constraints

- No agregar dependencias nuevas.
- `python -m pytest tests/ -q` debe pasar después de cada tarea.
- Las pruebas de ventanas reales van en `tests/test_movements_view.py` (si
  son de `movements.py`) o en un archivo nuevo por módulo
  (`tests/test_products_view.py`, `tests/test_dialogs_generic.py`, etc.) si
  tocan otras vistas — seguir el mismo gate ya usado:
  `@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)")`.
- Técnica de auditoría estándar para todas las ventanas (no inventar una
  distinta por diálogo):
  ```python
  root = tk.Tk()
  root.geometry("1400x900+3000+3000")  # fuera de pantalla, pero MAPEADA de verdad
  root.update_idletasks(); root.update()
  dlg = ElDialogo(root, ...)
  # pumpear el loop ~300-800ms con root.after + while
  print(dlg.winfo_width(), dlg.winfo_height())       # tamaño real
  print(dlg.winfo_reqwidth(), dlg.winfo_reqheight()) # lo que pide el contenido
  # por cada botón: rooty + height <= dlg.winfo_rooty() + dlg.winfo_height()
  ```
  **No usar `root.withdraw()`** para esto — una ventana withdrawn nunca se
  "mapea" de verdad y `winfo_width()` queda en `1` para siempre,
  invalidando la medición (ya pasó en esta sesión, costó un diagnóstico
  entero darse cuenta).
- No tocar `database/repository.py` en este plan salvo que una corrección
  de UI lo requiera explícitamente (no se anticipa ningún caso).

## Review Focus

- **Diálogos de contenido dinámico cuya geometría está fijada "a ojo" y
  nunca se revisó tras agregarle features** (ej. `_MovementEditDialog`,
  que pasó por 2 rediseños grandes este mismo mes) — la Tarea 1 ya
  confirmó uno; la Tarea 2 busca el resto.
- **Diálogos con `resizable(False, False)`** — si su contenido no entra,
  el usuario no tiene ningún escape manual (ya pasó con `ConfirmDialog`,
  corregido en una sección anterior de `CLAUDE.md`). Son los de mayor
  prioridad para revisar primero dentro de la Tarea 2.
- **Diálogos cuyo contenido depende de datos variables** (cantidad de
  ítems, de empleados, de proveedores, longitud de nombres/notas) — el
  mismo diálogo puede verse bien con datos de prueba chicos y romperse con
  datos reales más grandes (exactamente lo que pasó en la Tarea 1: 1 ítem
  y 5 ítems dieron el mismo resultado porque el problema no era la
  cantidad de ítems, pero no se sabía sin probarlo).
- **El único diálogo que no es `BaseDialog`**
  (`ui/views/dashboard.py::DashboardView._show_movement_detail`, un
  `ctk.CTkToplevel` directo) — al no heredar de la base común, puede no
  tener los mismos arreglos ya aplicados a los demás (ej. el centrado
  diferido, el ya corregido layout de `MessageDialog`/`ConfirmDialog`).
- **Textos largos reales** (nombre de producto largo, nota larga, varios
  empleados seleccionados) en diálogos con `wraplength` fijo — un texto
  más largo que el de prueba puede desbordar un ancho fijo sin que se note
  con datos cortos.

---

### Task 1: `_MovementEditDialog` — geometría fija (500x480) desactualizada, el contenido real necesita ~782px de alto

**Ya diagnosticado empíricamente, no hace falta volver a investigar:**
corriendo el diálogo real con un movimiento de 1 ítem y con uno de 5
ítems, en ambos casos el contenido pide **782px de alto** (la lista de
productos ya está bien acotada con un `CTkScrollableFrame(height=150)`,
así que la cantidad de ítems no es la causa) — la ventana nunca fue
pensada para el header teñido por tipo + tarjeta de contexto + lista de
ítems que se le agregaron en rediseños posteriores; `geometry("500x480")`
quedó vieja. Con `resizable(False, False)`, en una pantalla más chica que
~800px de alto esto deja los botones "Guardar"/"Cancelar" fuera de la
ventana, sin forma de arreglarlo a mano.

**Files:**
- Modify: `ui/views/movements.py:2459` (`_MovementEditDialog.__init__`,
  línea del `self.geometry("500x480")`)
- Test: `tests/test_movements_view.py`

**Interfaces:**
- Consumes: `ui.views.movements._MovementEditDialog(parent, movement, current_user, on_save)`,
  `ui.views.movements.get_movement(movement_id)` (ya existe, devuelve
  `movement["items"]`).
- Produces: nada nuevo — solo cambia un literal de geometría.

- [ ] **Step 1: Escribir la prueba que falla**

```python
@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_editar_movimiento_la_ventana_entra_el_contenido_real(monkeypatch):
    import ui.views.movements as movements_mod

    movement = {
        "id": 99, "type": "salida", "timestamp": "2026-11-01 10:00:00",
        "product": "", "employee_id": None, "notes": "",
        "items": [
            {"id": 1, "name": "Router", "brand": "TPLink", "qty": 1,
             "unit": "und", "seriales": ""},
        ],
    }
    monkeypatch.setattr(movements_mod, "get_all_employees", lambda: [])

    root = tk.Tk()
    root.geometry("1400x900+3000+3000")
    root.update_idletasks()
    root.update()
    try:
        dlg = movements_mod._MovementEditDialog(
            root, movement=movement,
            current_user={"id": 1, "role": "admin"}, on_save=lambda: None,
        )
        root.update_idletasks()
        root.update()
        assert dlg.winfo_reqheight() <= dlg.winfo_height(), (
            f"el contenido pide {dlg.winfo_reqheight()}px pero la ventana "
            f"declara solo {dlg.winfo_height()}px"
        )
    finally:
        root.destroy()
```

- [ ] **Step 2: Correr la prueba para confirmar que falla**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_movements_view.py -k ventana_entra_el_contenido_real -v`
Expected: FAIL — `winfo_reqheight()` (~782) > `winfo_height()` (480, el
valor declarado hoy).

- [ ] **Step 3: Corregir la geometría declarada**

En `ui/views/movements.py:2459`, cambiar:
```python
self.geometry("500x480")
```
por:
```python
self.geometry("540x800")
```
(540 de ancho da margen sobre los ~318-502px que pide el contenido según
el tipo de movimiento seleccionado en el header; 800 de alto da margen
sobre los 782px medidos). No cambiar `resizable(False, False)` — no es
parte de este fix, y la Tarea 2 puede revisar si conviene hacerlo
redimensionable en general para todos los diálogos fijos, como punto
aparte.

- [ ] **Step 4: Correr la prueba para confirmar que pasa**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_movements_view.py -k ventana_entra_el_contenido_real -v`
Expected: PASS

- [ ] **Step 5: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ui/views/movements.py tests/test_movements_view.py
git commit -m "fix: agrandar la geometria fija de Editar Movimiento al contenido real"
```

---

### Task 2: Auditoría empírica del resto de las ventanas emergentes (15 diálogos)

**Files:**
- Create: `docs/AUDITORIA_VENTANAS_EMERGENTES.md` (informe, no código)
- Modify: solo si un hallazgo concreto lo requiere (ver Step 3)
- Test: `tests/test_movements_view.py` / archivo de test nuevo por vista,
  según dónde esté el diálogo corregido (si aplica)

**Interfaces:**
- Consumes: la técnica de auditoría fijada en "Global Constraints" arriba,
  y el inventario completo de diálogos (lista exacta abajo, confirmada con
  `grep -rn "^class .*BaseDialog)\|^class .*CTkToplevel)" ui/` — no asumir
  que hay más o menos de 19, volver a correr ese `grep` antes de empezar
  por si se agregó alguno nuevo desde que se escribió este plan).
- Produces: el informe `docs/AUDITORIA_VENTANAS_EMERGENTES.md`, con una
  fila por diálogo (tabla abajo) y, para cada hallazgo real, una tarea de
  corrección agregada a este mismo documento de plan (Task 3, 4... según
  haga falta) antes de implementarla — no mezclar "encontrar" y "corregir"
  en el mismo paso para diálogos que no se auditaron todavía.

**Diálogos a auditar en esta tarea** (ya cubiertos por la Tarea 1 o por
secciones previas de `CLAUDE.md` — no repetir):
`_MovementEditDialog` (Tarea 1), `ConfirmDialog`/`MessageDialog` (ya
corregidos, sección "Mejoras visuales a las ventanas de notificación"),
`_ReportsDialog` y `_RegistrarProductoDialog` (ya verificados sin
hallazgos en el diagnóstico de este plan, no repetir).

**Diálogos pendientes de auditar (15):**
`_VehicleDialog`, `_SupplierDialog`, `_EmpDialog`, `_UserDialog`,
`_GroupEditDialog`, `_BarcodeScanDialog`, `_ScanRowDialog`,
`_PhoneScanHelpDialog`, `_ScanResultDialog`, `_ProductDialog`,
`_MovementInfoDialog`, `_MovementDialog`, `_ForceChangePasswordDialog`,
`DashboardView._show_movement_detail` (único que no es `BaseDialog`).

- [ ] **Step 1: Para cada uno de los 15, correr la técnica de auditoría**

Instanciar cada diálogo con datos reales de la BD sembrada
(`scripts/seed_test_data.py` ya la pobló) o con un stub mínimo si el
diálogo no necesita BD (ej. `_PhoneScanHelpDialog` solo necesita una URL
cualquiera), pumpear ~500ms, y registrar en una tabla:

| Diálogo | Alto declarado | Alto pedido por el contenido | ¿Entra? | Botones fuera de la ventana | Notas |
|---|---|---|---|---|---|

Para los diálogos con contenido variable (`_UserDialog`,
`_SupplierDialog`, `_EmpDialog`, `_VehicleDialog`, `_GroupEditDialog`),
probar con el caso de datos más grande disponible en la BD sembrada (ej.
el proveedor/empleado con el nombre más largo), no solo con el primero
que aparezca.

- [ ] **Step 2: Escribir el informe**

Guardar la tabla del Step 1, con una fila por diálogo, en
`docs/AUDITORIA_VENTANAS_EMERGENTES.md`. Para cada fila donde "¿Entra?" es
"No" o hay botones fuera de la ventana: agregar un hallazgo concreto
(archivo:línea del diálogo, valor declarado vs valor real medido, mismo
formato que la Tarea 1 de este plan) al final del informe.

- [ ] **Step 3: Por cada hallazgo real del Step 2, agregar una Task nueva a este plan**

Mismo formato que la Tarea 1 (Files/Interfaces/Steps con test-primero),
una tarea por diálogo con hallazgo — **no corregir nada todavía si el
Step 1 no encontró un problema real en ese diálogo** (si los 15 salen
limpios, este plan termina en el Step 2 con el informe en verde, sin
Tasks adicionales — es un resultado válido, no hay que inventar una
corrección donde no hace falta).

- [ ] **Step 4: Implementar las tareas agregadas en el Step 3 (si las hay), con su propio test-primero**

- [ ] **Step 5: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add docs/AUDITORIA_VENTANAS_EMERGENTES.md
# + los archivos de cualquier corrección del Step 4
git commit -m "docs: auditoria de ventanas emergentes + correcciones encontradas"
```

---

### Task 3: `_ProductDialog` — geometría fija (500x550) insuficiente, el contenido real pide ~584x565

**Diagnosticado empíricamente en la Tarea 2:** corriendo el diálogo real con un
producto de nombre/marca largos, el contenido pide **584x565** pero la
ventana declara **500x550** (`ui/views/products.py:3147`). El diálogo es
`resizable(True, True)` así que el usuario puede agrandar a mano, pero el
tamaño inicial no acomoda el contenido real; con datos largos partes del
formulario quedan fuera del área declarada.

**Files:**
- Modify: `ui/views/products.py:3147` (`_ProductDialog.__init__`,
  línea del `self.geometry("500x550")`)
- Test: `tests/test_products_view.py` (archivo nuevo, gate `DISPLAY`)

**Interfaces:**
- Consumes: `ui.views.products._ProductDialog(parent, title, on_save, initial=None, prefill=None)`,
  `ui.views.products.get_all_suppliers()` (ya existe, usado en `__init__`).
- Produces: nada nuevo — solo cambia un literal de geometría.

- [ ] **Step 1: Escribir la prueba que falla**

```python
@pytest.mark.skipif(
    not os.environ.get("DISPLAY"), reason="requiere un servidor X (Tkinter)"
)
def test_editar_producto_la_ventana_entra_el_contenido_real(monkeypatch):
    import ui.views.products as products_mod

    monkeypatch.setattr(products_mod, "get_all_suppliers", lambda: [])

    root = tk.Tk()
    root.geometry("1400x900+3000+3000")
    root.update_idletasks()
    root.update()
    try:
        dlg = products_mod._ProductDialog(
            root,
            title="Editar Unidad",
            on_save=lambda: None,
            initial={
                "name": "Router ONT Huawei HG8245H modelo largo",
                "brand": "Huawei Technologies Co. Ltd.",
                "serial": "HWTC824500123456789",
            },
        )
        root.update_idletasks()
        root.update()
        declared = dlg.geometry()
        declared_w = int(declared.split("x")[0])
        declared_h = int(declared.split("x")[1].split("+")[0])
        assert dlg.winfo_reqwidth() <= declared_w, (
            f"el contenido pide {dlg.winfo_reqwidth()}px de ancho pero la "
            f"ventana declara solo {declared_w}px"
        )
        assert dlg.winfo_reqheight() <= declared_h, (
            f"el contenido pide {dlg.winfo_reqheight()}px de alto pero la "
            f"ventana declara solo {declared_h}px"
        )
    finally:
        root.destroy()
```

- [ ] **Step 2: Correr la prueba para confirmar que falla**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_products_view.py -k ventana_entra_el_contenido_real -v`
Expected: FAIL — `winfo_reqwidth()` (584) > declarado (500) y/o
`winfo_reqheight()` (565) > declarado (550).

- [ ] **Step 3: Corregir la geometría declarada**

En `ui/views/products.py:3147`, cambiar:
```python
self.geometry("500x550")
```
por:
```python
self.geometry("600x620")
```
(600 de ancho da margen sobre los 584px medidos; 620 de alto da margen
sobre los 565px medidos). No cambiar `resizable(True, True)`.

- [ ] **Step 4: Correr la prueba para confirmar que pasa**

Run: `DISPLAY=:0 .venv/bin/python -m pytest tests/test_products_view.py -k ventana_entra_el_contenido_real -v`
Expected: PASS

- [ ] **Step 5: Correr toda la suite**

Run: `.venv/bin/python -m pytest tests/ -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add ui/views/products.py tests/test_products_view.py
git commit -m "fix: agrandar la geometria fija de Editar Producto al contenido real"
```

---

## Resultado: plan ejecutado

Se auditaron los 14 diálogos pendientes de la Tarea 2 (el plan original
mencionaba 15; el `grep -rn "^class .*BaseDialog)" ui/` detecta 14, y el
último no hereda de `BaseDialog` como un clásico tetapi es un `CTkToplevel`
directo en `DashboardView` — ambos incluidos en la auditoría). De los 14,
**13 entran** y **1 hallazgo real**: `_ProductDialog` declara 500x550 pero
el contenido pide 584x565 (NO entra). Se añadió Task 3 al plan (formato
idéntico a las Tareas 1 y 2) y se implementó fix-first con test-primero. El
resultado final: `_MovementEditDialog` (Task 1), `_ProductDialog` (Task 3)
corregidos con tests-first; `docs/AUDITORIA_VENTANAS_EMERGENTES.md` con la
tabla completa; suite `tests/` 60 passed. Sin gaps de alcance en "todas las
ventanas emergentes".

## Self-Review

**1. Cobertura del pedido:** "todas las ventanas emergentes" — 19
diálogos confirmados por `grep`; 4 ya cubiertos (2 en secciones previas de
`CLAUDE.md`, 2 verificados sin hallazgos en el diagnóstico de este plan),
1 con fix concreto (Tarea 1), 15 quedan para la auditoría sistemática de
la Tarea 2. Sin gaps de alcance.

**2. Revisión de pasos:** la Tarea 1 tiene test/fix concretos porque ya se
diagnosticó corriendo el código real. La Tarea 2 queda deliberadamente
abierta en el Step 3 ("agregar una Task nueva por hallazgo") porque, a
diferencia de la Tarea 1, no hay certeza de qué se va a encontrar en cada
uno de los 15 — fijar correcciones de antemano sería inventar bugs que
tal vez no existen (mismo criterio ya usado en el plan de "Movimientos:
botones" para el detalle de eliminación).

**3. Consistencia de tipos/nombres:** la técnica de auditoría (Global
Constraints) usa los mismos nombres de API reales
(`winfo_width`/`winfo_reqheight`/`geometry`) en la Tarea 1 y en las
instrucciones de la Tarea 2 — no se inventó una API distinta.

**4. Review Focus:** las 5 líneas de esa sección tienen cobertura: la
primera es exactamente la Tarea 1; la de `resizable(False,False)` se pide
priorizar dentro del Step 1 de la Tarea 2; la de contenido variable se
pide explícitamente probar con el dato más largo disponible; la del
`CTkToplevel` que no hereda de `BaseDialog` está en la lista de los 15; la
de textos largos queda cubierta por la misma instrucción de probar con el
dato más grande.

**5. Proporción:** el plan es más largo que "cambiar un número de
geometría" porque documenta cómo se llegó a esa cifra (necesario para que
quien lo implemente no tenga que re-correr el diagnóstico) y porque define
una técnica de auditoría reusable para 15 diálogos más — no porque
describa código línea por línea. El cuerpo completo solo se dio donde la
firma/test no lo determinan por sí solos (el test de la Tarea 1); el Step
3 de la Tarea 2 se dejó sin cuerpo de código a propósito, por la razón del
punto 2.

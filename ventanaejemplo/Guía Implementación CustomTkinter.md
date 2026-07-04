# Guía de implementación — Registrar Producto (Opción C) en CustomTkinter

Esta guía explica cómo está construida la **Opción C** (formulario en una sola
columna con scroll) del prototipo, portada a **Python + CustomTkinter**, y cómo
adaptarla a tu sistema de inventario de redes/fibra.

La implementación de referencia ya está lista y es **ejecutable**:

```
customtkinter/
├── theme.py                 # paleta + fuentes (mapeo 1:1 del CSS)
├── data.py                  # categorías, unidades y specs dinámicas
├── widgets.py               # componentes reutilizables
├── registrar_producto.py    # ventana principal (ejecuta esto)
└── Guía Implementación CustomTkinter.md
```

---

## 1. Requisitos y ejecución

```bash
python -m pip install customtkinter        # >= 5.2.0
cd customtkinter
python registrar_producto.py
```

> **Python 3.9+** recomendado. CustomTkinter trae Tkinter (incluido en la
> instalación estándar de Python en Windows/macOS; en Linux instala
> `sudo apt install python3-tk`).

---

## 2. Tipografía (IBM Plex con *fallback* automático)

El prototipo usa **IBM Plex Sans** (texto) e **IBM Plex Mono** (códigos: SKU,
MAC, serial). Tkinter solo puede usar fuentes **instaladas en el sistema
operativo**, así que:

1. **Recomendado** — instala las fuentes una sola vez:
   - Descárgalas de Google Fonts (IBM Plex Sans / IBM Plex Mono) e instálalas
     en el SO (doble clic → *Instalar*), o en Linux:
     `sudo apt install fonts-ibm-plex`.
2. Si no están instaladas, `theme.make_fonts()` **elige automáticamente** la
   primera familia disponible de cada lista (`SANS_STACK` / `MONO_STACK`):
   Segoe UI / Helvetica para texto y Consolas / Menlo para mono. La app
   funciona igual, solo cambia la fuente.

> `CTkFont` debe crearse **después** de `CTk()` (necesita un intérprete Tk
> activo). Por eso `make_fonts()` se llama dentro del `__init__` de la ventana,
> no a nivel de módulo.

---

## 3. Sistema visual: mapeo CSS → CustomTkinter

Los tokens viven en `theme.py` con los **mismos valores** del prototipo. En CTk
no hay CSS: cada propiedad se pasa como argumento al widget.

| Concepto (CSS)            | Token            | Cómo se aplica en CTk                                   |
|---------------------------|------------------|---------------------------------------------------------|
| `background` cabecera     | `NAVY`           | `CTkFrame(fg_color=NAVY)`                               |
| acción primaria           | `BLUE`/`BLUE_D`  | `CTkButton(fg_color=BLUE, hover_color=BLUE_D)`          |
| cancelar / `*` / alerta   | `ORANGE`         | `text_color` + `border_color` naranja                   |
| texto / etiqueta / hint   | `INK`/`INK_2`/`INK_3` | `text_color=`                                      |
| borde de campo            | `LINE`           | `border_color=LINE, border_width=1`                     |
| fondo del cuerpo          | `BG`             | `CTkScrollableFrame(fg_color=BG)`                       |
| radios                    | `RADIUS_*`       | `corner_radius=`                                        |
| `:focus` (anillo azul)    | —                | `bind("<FocusIn>/<FocusOut>")` → cambia `border_color`  |

**Diferencias clave frente a CSS** (a tener en cuenta al ajustar):

- No existe `letter-spacing`: los títulos de sección se muestran en
  **MAYÚSCULAS** (`title.upper()`) para lograr el mismo efecto.
- No hay degradados nativos en frames: la cabecera usa un `NAVY` plano (puedes
  simular degradado con un `CTkCanvas` si lo necesitas).
- El "select" claro con borde se logra metiendo un `CTkOptionMenu` dentro de un
  `CTkFrame` con borde (ver `LabeledSelect`), porque `CTkOptionMenu` no tiene
  `border_width` propio.

---

## 4. Anatomía de la ventana

```
RegistrarProducto(ctk.CTk)
├── _build_header()      Cabecera NAVY + pill contador (num + unidad)
├── _build_body()        CTkScrollableFrame  ← scroll de una sola columna
│     ├── Sección 1  Identificación e info básica
│     ├── (divisor)
│     ├── Sección 2  Control de existencias y trazabilidad
│     ├── (divisor)
│     └── Sección 3  Ficha técnica y especificaciones
└── _build_footer()      Cancelar (naranja) + Guardar (azul)
```

Cada sección se crea con `_section(num, titulo)`, que devuelve un `CTkFrame`
con dos columnas (`columnconfigure((0,1), weight=1, uniform="col")`). Los campos
se colocan con el helper `_place(widget, fila, col, span)`.

---

## 5. La lógica dinámica (lo importante)

### a) Cambio de categoría → `on_categoria_change(nombre)`

```python
cfg = CATEGORIAS[nombre]          # de data.py
self.in_unidad.set(...)           # sugiere unidad por defecto
self.inv_toggle.set(cfg["control"])   # sugiere control por defecto
self.set_control(cfg["control"])      # reconstruye sección 2
self.render_specs(cfg["specs"])       # reconstruye specs de sección 3
```

Para **añadir una categoría o un campo técnico nuevo**, edita únicamente
`data.py` → `CATEGORIAS`. No toques la UI: `render_specs()` lee la lista de
`specs` y crea los widgets según su `type` (`select`, `text`, `chips`, `seg`).

### b) Tipo de control de inventario → `set_control(mode)`

Es el corazón del formulario. Destruye el área dinámica y la reconstruye:

- **`serie`** → inserta la `SerialTable` (tabla de equipos con serial/MAC,
  "Generar filas", "Agregar/Quitar equipo", casilla "Sin Serial/MAC").
- **`cantidad`** → inserta *Cantidad actual en stock* + *Punto de pedido*, con
  **alerta automática** cuando `stock ≤ mínimo`.

### c) Contador de cabecera → `update_counter()`

- En modo `serie`: número de filas de la tabla (`"3 EQUIPOS"`).
- En modo `cantidad`: valor de stock + unidad (`"1500 M"`).

Se dispara desde los callbacks de la tabla (`on_count_change`) y del campo de
stock (`on_change`).

---

## 6. Componentes reutilizables (`widgets.py`)

| Componente        | Equivale en el HTML a…           | API                          |
|-------------------|----------------------------------|------------------------------|
| `LabeledEntry`    | `.rp-field` + `input`            | `.get()` / `.set(v)`         |
| `LabeledSelect`   | `.rp-select`                     | `.get()` / `.set(v)` / `.set_values()` |
| `ChipGroup`       | `.rp-chips` (multi)              | `.get()` → lista             |
| `SegSingle`       | `.rp-chips` (single)            | `.get()`                     |
| `InventoryToggle` | las dos tarjetas `.rp-seg-opt`   | `.get()` / `.set(mode)`      |
| `SerialTable`     | `.rp-table` + generador          | `.count()`, `.rows`          |

Todos exponen `.get()` para que `recolectar()` arme el `dict` final del
producto de forma uniforme.

---

## 7. Guardar los datos

`recolectar()` ya devuelve un diccionario completo y normalizado:

```python
{
  "nombre": "...", "sku": "...", "categoria": "Equipos de Red",
  "marca": "...", "modelo": "...", "proveedor": "...",
  "unidad": "und", "ubicacion": "...", "control": "serie",
  "descripcion": "...",
  "specs": {"puerto_tipo": "Gigabit (10/100/1000)", "bandas": ["5 GHz"], ...},
  "equipos": [{"serial": "...", "mac": "...", "sin": False}, ...]
  # o, en modo cantidad:
  "stock": "1500", "minimo": "300"
}
```

Conecta tu persistencia dentro de `guardar()` (ahora solo valida e imprime):

```python
def guardar(self):
    data = self.recolectar()
    # ... validación ...
    mi_repositorio.insertar_producto(data)   # SQLite, SQLAlchemy, API, etc.
    self.destroy()
```

---

## 8. Usarlo como ventana **modal** (no como app principal)

El prototipo es un diálogo "Registrar Producto". Para abrirlo encima de tu app:

```python
class RegistrarProductoDialog(ctk.CTkToplevel):
    # copia el cuerpo de RegistrarProducto pero hereda de CTkToplevel
    ...

dlg = RegistrarProductoDialog(self)
dlg.transient(self)     # se mantiene sobre la ventana padre
dlg.grab_set()          # modal: bloquea la app de fondo
self.wait_window(dlg)   # espera a que se cierre
```

> En `CTk` la barra de título la pone el sistema operativo, por eso **no** se
> dibuja la barra falsa del prototipo. Si la quieres exacta (titlebar oscura con
> botones), usa `overrideredirect(True)` y dibújala con un `CTkFrame`, pero
> pierdes el arrastre nativo de ventana (hay que reimplementarlo).

---

## 9. Notas y *gotchas* verificados

- **Scroll anidado:** la `SerialTable` **no** lleva su propio scroll; sus filas
  se apilan y el scroll del cuerpo (`CTkScrollableFrame`) las absorbe. Esto
  evita el conflicto clásico de rueda del ratón entre dos áreas scrollables.
- **Reparentar widgets:** en Tkinter no se puede cambiar el `master` de un
  widget ya creado. Por eso los controles `chips`/`seg` se crean **dentro** de
  su contenedor con etiqueta (ver `render_specs`), no se "envuelven" después.
- **Filtrado numérico:** `stock` y `mínimo` filtran no-dígitos en `KeyRelease`
  (`LabeledEntry(numeric=True)`).
- **`CTkOptionMenu` con placeholder:** el texto inicial se fija con la
  `StringVar`; al leer, si sigue siendo "Seleccionar…" trátalo como vacío.
- **Versiones de CustomTkinter:** algunos nombres de argumento de color
  (`selected_color`, `dropdown_hover_color`, etc.) son de la rama 5.x. Si usas
  una versión distinta y un argumento no existe, simplemente quítalo.

---

## 10. Próximos pasos sugeridos

- Persistencia real (SQLite + una tabla `productos` y otra `equipos`).
- Validación de formato de MAC (`AA-BB-CC-DD-EE-FF`) al salir del campo.
- Autogeneración de SKU a partir de categoría + correlativo.
- Modo edición (precargar `recolectar()` inverso con `.set()` en cada widget).
```

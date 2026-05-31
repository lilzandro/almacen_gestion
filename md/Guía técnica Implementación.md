Markdown# Guía Técnica: Implementación de Sistema de Inventario
**Stack:** Python 3.10+ + CustomTkinter 5.2+ (Sin dependencias web)

Este documento detalla cómo trasladar el rediseño de un Sistema de Inventario a una aplicación de escritorio real en Python utilizando la librería CustomTkinter, mapeando cada componente visual del prototipo a su equivalente en código.

---

## 01. Stack y Dependencias

CustomTkinter cubre la gran mayoría de las necesidades del diseño visual. Para garantizar la consistencia multiplataforma en diferentes sistemas operativos, se recomiendan las siguientes pautas:
* **Fuentes:** Para mantener tipografías consistentes en cualquier SO, es conveniente cargarlas mediante `tkextrafont` o registrar los archivos TTF al inicio de la aplicación.
* **Iconos:** Se sugiere utilizar la librería `Pillow` combinada con un set de imágenes SVG o PNG, o cargar fuentes de iconos como Lucide o Tabler en formato TTF.

### Archivo: `requirements.txt`
```text
customtkinter==5.2.2
Pillow==10.4.0
tkextrafont==0.6.3  # Opcional, para cargar fuentes TTF en runtime
02. Estructura del ProyectoSe sugiere organizar el código fuente bajo la siguiente estructura modular de archivos y carpetas:Plaintextinventario/
├── app.py                  # Bootstrap de la aplicación + ventana principal
├── theme.py                # Definición de tokens de diseño y temas (Light/Dark)
├── store.py                # Gestión de estado + persistencia (SQLite o JSON)
├── widgets/
│   ├── __init__.py
│   ├── status_pill.py      # Componente visual para las etiquetas de estado
│   ├── group_row.py        # Fila de grupo principal (expandible)
│   ├── child_row.py        # Filas hijas secundarias
│   ├── stat_card.py        # Tarjetas de estadísticas del header
│   ├── toast.py            # Notificaciones flotantes temporales
│   ├── context_menu.py     # Menú contextual personalizado
│   └── icons.py            # Gestión y carga de iconos de la app
├── views/
│   ├── inventory_view.py   # Vista general y composición principal del inventario
│   ├── equipment_modal.py  # Ventana modal para añadir/editar equipos
│   ├── detail_drawer.py    # Panel lateral deslizable de detalles
│   └── confirm_dialog.py   # Diálogo para confirmación de acciones críticas
└── assets/
    ├── fonts/              # Archivos de fuentes tipográficas (TTF)
    └── icons/              # Assets de iconos (PNG/SVG)
03. Tokens de Diseño (theme.py)Centralizar los colores y los radios de curvatura en un archivo theme.py permite que cualquier modificación estética global o cambio de acento se realice desde un único punto de edición.Paleta de Colores BaseAccent (Acción principal): #E97B1FOk (Éxito / Activo): #2F8A55Info (Información): #1D4ED8Warn (Advertencia): #B45309Danger (Peligro / Eliminación): #B42318Implementación del Sistema de TemasPythonfrom dataclasses import dataclass

@dataclass(frozen=True)
class Theme:
    bg:           str
    surface:      str
    surface_2:    str
    border:       str
    text:         str
    text_muted:   str
    text_faint:   str
    accent:       str
    accent_soft:  str
    accent_text:  str
    ok:           str
    ok_soft:      str
    warn:         str
    warn_soft:    str
    info:         str
    info_soft:    str
    danger:       str
    danger_soft:  str
    row_hover:    str
    row_selected: str
    radius:       int = 10
    radius_sm:    int = 7

LIGHT = Theme(
    bg="#F3F4F6", surface="#FFFFFF", surface_2="#F7F8FA",
    border="#E3E6EB", text="#1B1F24",
    text_muted="#6B7280", text_faint="#9AA1AC",
    accent="#E97B1F", accent_soft="#FDECD9", accent_text="#B45A0A",
    ok="#2F8A55", ok_soft="#DFF1E6",
    warn="#B45309", warn_soft="#FDECC8",
    info="#1D4ED8", info_soft="#DDE8FF",
    danger="#B42318", danger_soft="#FDE2E0",
    row_hover="#F5F7FB", row_selected="#FFF4E6",
)

DARK = Theme(
    bg="#0F1115", surface="#1A1F26", surface_2="#1F242C",
    border="#2A313A", text="#ECEDEF",
    text_muted="#9AA3AF", text_faint="#6B7280",
    accent="#E97B1F", accent_soft="#3A2412", accent_text="#F6A059",
    ok="#3FB57A", ok_soft="#143323",
    warn="#D08442", warn_soft="#3A2A10",
    info="#5B8DEF", info_soft="#16224A",
    danger="#E5594F", danger_soft="#3A1816",
    row_hover="#1D232B", row_selected="#2A1F12",
)
Tip de CustomTkinter: Prácticamente cualquier parámetro de color acepta una tupla con formato ("#light", "#dark"). Al pasar la tupla directamente, el widget cambiará de color de manera automática en tiempo de ejecución al invocar ctk.set_appearance_mode("dark") o viceversa.04. Ventana Principal (app.py)Pythonimport customtkinter as ctk
from views.inventory_view import InventoryView

ctk.set_appearance_mode("light")        # Modos válidos: "light" | "dark" | "system"
ctk.set_default_color_theme("blue")      # Lo sobreescribiremos de forma manual por cada widget

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Sistema de Inventario")
        self.geometry("1320x820")
        self.minsize(1100, 680)
        self.configure(fg_color=("#F3F4F6", "#0F1115"))

        self.view = InventoryView(self)
        self.view.pack(fill="both", expand=True, padx=24, pady=24)

if __name__ == "__main__":
    App().mainloop()
05. Header y Stat Cards (widgets/stat_card.py)Pythonimport customtkinter as ctk

class StatCard(ctk.CTkFrame):
    def __init__(self, parent, label, value, suffix="", dot_color="#2F8A55"):
        super().__init__(parent, corner_radius=8,
                         fg_color=("#F7F8FA", "#1F242C"),
                         border_width=1,
                         border_color=("#E3E6EB", "#2A313A"))
        
        # Etiqueta de la tarjeta en mayúsculas
        ctk.CTkLabel(self, text=label.upper(),
                     font=("DM Sans", 10, "bold"),
                     text_color=("#6B7280", "#9AA3AF")
        ).pack(anchor="w", padx=14, pady=(10, 2))

        row = ctk.CTkFrame(self, fg_color="transparent")
        row.pack(anchor="w", padx=14, pady=(0, 10))

        # El indicador visual de estado ("punto") se emula con un CTkLabel vacío y color de fondo
        dot = ctk.CTkLabel(row, text="", width=8, height=8,
                           corner_radius=4, fg_color=dot_color)
        dot.pack(side="left", padx=(0, 6))

        # Valor numérico principal
        ctk.CTkLabel(row, text=str(value),
                     font=("DM Sans", 20, "bold")
        ).pack(side="left")

        # Texto de sufijo opcional (ej. "unidades")
        if suffix:
            ctk.CTkLabel(row, text=suffix,
                         text_color=("#9AA1AC", "#6B7280"),
                         font=("DM Sans", 11)
            ).pack(side="left", padx=(4, 0))
06. Toolbar y BúsquedaLos chips de filtrado pueden resolverse utilizando un componente CTkSegmentedButton o, si requieres agregar contadores numéricos dinámicos en cada pestaña, mediante CTkButton individuales personalizados.Python# Campo de entrada para búsquedas
search = ctk.CTkEntry(
    toolbar,
    placeholder_text="Buscar por modelo, marca, serial o MAC…",
    height=36,
    corner_radius=8,
    border_width=1,
    border_color=("#E3E6EB", "#2A313A"),
    fg_color=("#F7F8FA", "#1F242C"),
)
search.pack(side="left", fill="x", expand=True, padx=(0, 10))
search.bind("<KeyRelease>", self._on_search)

# Botón de acción primario para creación
new_btn = ctk.CTkButton(
    toolbar, text="+ Nuevo equipo",
    fg_color="#E97B1F", hover_color="#D26C12",
    text_color="white", corner_radius=8, height=36,
    command=self.open_new_modal,
)
new_btn.pack(side="right")
07. Tabla AgrupadaNota Crítica sobre el Rendimiento: CustomTkinter no cuenta con un widget de tabla nativo. Para su implementación existen dos enfoques técnicos viables:ttk.Treeview con estilos personalizados: Es más rápido en renderizado masivo, pero limita drásticamente la inclusión de botones interactivos, imágenes o pills por fila.CTkScrollableFrame con filas estructuradas mediante CTkFrame: Demanda mayor volumen de código, pero habilita comportamientos avanzados del prototipo como estados hover nativos, botones embebidos, pills de colores y desplegables dinámicos. (Opción Recomendada).Composición en views/inventory_view.pyPython# Contenedor con scroll para la tabla
self.table = ctk.CTkScrollableFrame(
    self, corner_radius=0,
    fg_color=("#FFFFFF", "#161A20"),
)
self.table.pack(fill="both", expand=True)

# Header fijo superior: Se construye mediante un CTkFrame independiente sobre el scrollable
self._build_table_header()

# Renderizado de la información por cada fila de grupo
for row_data in self.store.rows:
    group = GroupRow(self.table, row_data,
                     on_toggle=self._toggle_row,
                     on_select=self._select_row,
                     on_open_detail=self._open_detail)
    group.pack(fill="x")
08. Fila de Grupo Expandible (widgets/group_row.py)Pythonimport customtkinter as ctk
from widgets.status_pill import StatusPill

class GroupRow(ctk.CTkFrame):
    def __init__(self, parent, data, on_toggle, on_select, on_open_detail):
        super().__init__(parent, fg_color="transparent", height=52)
        self.data = data
        self.open = False
        self.selected = False

        # Configuración de columnas con pesos (weights) y anchos mínimos específicos
        self.grid_columnconfigure(0, weight=0, minsize=38)   # Flecha / chevron
        self.grid_columnconfigure(1, weight=2)               # Información de modelo
        self.grid_columnconfigure(2, weight=1)               # Marca del equipo
        self.grid_columnconfigure(3, weight=0, minsize=110)  # Conteo de unidades
        self.grid_columnconfigure(4, weight=0, minsize=140)  # Estado (Pill)
        self.grid_columnconfigure(5, weight=1)               # Proveedor
        self.grid_columnconfigure(6, weight=0, minsize=110)  # Contenedor de acciones

        # Botón tipo Chevron para alternar visibilidad de filas hijas
        self.chevron = ctk.CTkButton(self, text="▸", width=22, height=22,
                                     fg_color="transparent", hover_color=("#EEF0F3", "#262C35"),
                                     text_color=("#6B7280", "#9AA3AF"),
                                     command=self.toggle)
        self.chevron.grid(row=0, column=0, padx=(14, 0))

        # Celda combinada: Modelo + Metadatos (Categoría · ID único)
        cell = ctk.CTkFrame(self, fg_color="transparent")
        cell.grid(row=0, column=1, sticky="w", padx=14)
        ctk.CTkLabel(cell, text=data.model, anchor="w",
                     font=("DM Sans", 13, "bold")).pack(anchor="w")
        ctk.CTkLabel(cell, text=f"{data.category.upper()} · EQ-{data.id:04d}",
                     text_color=("#9AA1AC", "#6B7280"),
                     font=("JetBrains Mono", 10)).pack(anchor="w")

        # Celda: Marca
        ctk.CTkLabel(self, text=data.brand, font=("DM Sans", 13, "bold")
        ).grid(row=0, column=2, sticky="w", padx=14)

        # Celda: Contador de Unidades (Badge customizado)
        units_pill = ctk.CTkLabel(self, text=f"{data.units}  {'unidad' if data.units==1 else 'uds.'}",
                                  fg_color=("#EEF0F3", "#262C35"),
                                  corner_radius=12, padx=10, pady=3,
                                  font=("DM Sans", 12, "bold"))
        units_pill.grid(row=0, column=3, padx=14)

        # Celda: Status Pill decorativo e informativo
        StatusPill(self, data.status, data.status_label).grid(
            row=0, column=4, padx=14, sticky="w")

        # Celda de Acciones: Botones transparentes con iconos descriptivos (Ver, Editar, Más)
        actions = ctk.CTkFrame(self, fg_color="transparent")
        actions.grid(row=0, column=6, padx=14, sticky="e")
        for ico, cb in [("eye", on_open_detail), ("edit", self._edit), ("more", self._menu)]:
            ctk.CTkButton(actions, text="", image=icon(ico), width=28, height=28,
                          fg_color="transparent",
                          hover_color=("#EEF0F3", "#262C35"),
                          command=lambda c=cb: c(self.data)
            ).pack(side="left", padx=1)

        # Bindeo recursivo de eventos click y hover a toda la estructura de la fila
        self.bind_all_children(self, "<Button-1>", lambda e: on_select(self))
        self.bind_all_children(self, "<Enter>", self._hover_in)
        self.bind_all_children(self, "<Leave>", self._hover_out)

    def bind_all_children(self, w, evt, cb):
        w.bind(evt, cb, add="+")
        for ch in w.winfo_children():
            self.bind_all_children(ch, evt, cb)

    def toggle(self):
        self.open = not self.open
        self.chevron.configure(text="▾" if self.open else "▸")
        self.event_generate("<<GroupToggled>>")
09. Filas Hijas (Expansión Dinámica)Cuando un grupo se expande, se instancia un CTkFrame con fondo atenuado abajo de la fila padre y se rellena dinámicamente con los componentes ChildRow.Pythondef _toggle_row(self, group_row):
    if group_row.open and group_row.data.id not in self._expanded:
        container = ctk.CTkFrame(
            self.table,
            fg_color=("#FAFBFD", "#181D24"),
        )
        container.pack(fill="x", after=group_row)
        
        # Desfasar las filas hijas a la derecha para denotar jerarquía
        for c in group_row.data.children:
            ChildRow(container, c,
                     on_cycle_status=self._cycle_status,
                     on_delete=self._delete_unit).pack(fill="x", padx=(64, 14))
        self._expanded[group_row.data.id] = container
        
    elif not group_row.open and group_row.data.id in self._expanded:
        # Destrucción física del contenedor secundario al contraerse
        self._expanded.pop(group_row.data.id).destroy()
10. Status Pill (widgets/status_pill.py)Pythonimport customtkinter as ctk

# Mapeo estructurado de estados visuales (Fondo, Texto/Indicador)
COLORS = {
    "ok":     (("#DFF1E6", "#143323"), ("#2F8A55", "#3FB57A")),
    "warn":   (("#FDECC8", "#3A2A10"), ("#B45309", "#D08442")),
    "info":   (("#DDE8FF", "#16224A"), ("#1D4ED8", "#5B8DEF")),
    "danger": (("#FDE2E0", "#3A1816"), ("#B42318", "#E5594F")),
}

class StatusPill(ctk.CTkFrame):
    def __init__(self, parent, status, label, on_click=None):
        bg, fg = COLORS[status]
        super().__init__(parent, fg_color=bg, corner_radius=12)
        
        # Punto decorativo indicador de estado
        ctk.CTkLabel(self, text="●", text_color=fg,
                     font=("DM Sans", 8)).pack(side="left", padx=(8, 4))
        
        # Texto principal del estado
        ctk.CTkLabel(self, text=label, text_color=fg,
                     font=("DM Sans", 12, "bold")).pack(side="left", padx=(0, 10))
        
        # En caso de requerir interacción clickeable
        if on_click:
            for w in [self] + self.winfo_children():
                w.bind("<Button-1>", lambda e: on_click())
                w.configure(cursor="hand2")
11. Drawer de Detalle Lateral (views/detail_drawer.py)Estrategias para Drawers: Al no existir un soporte nativo para contenedores deslizantes, se presentan dos soluciones de ingeniería:Crear un overlay mediante un CTkFrame usando coordenadas absolutas place(), animando dinámicamente su propiedad relx a través de bucles after().Utilizar una ventana secundaria CTkToplevel desprovista de bordes del sistema operativo, fijando sus coordenadas de posicionamiento x/y sobre el lateral derecho de la ventana principal. (Método Recomendado por simplicidad).Pythonimport customtkinter as ctk

class DetailDrawer(ctk.CTkToplevel):
    def __init__(self, master, row, on_action):
        super().__init__(master)
        self.overrideredirect(True)                # Desactiva decoraciones nativas de ventana
        self.attributes("-topmost", True)          # Asegura el foco en el primer plano
        self.configure(fg_color=("#FFFFFF", "#161A20"))

        # Forzar el acoplamiento milimétrico en el costado derecho del layout padre
        master.update_idletasks()
        w, h = 440, master.winfo_height()
        x = master.winfo_rootx() + master.winfo_width() - w
        y = master.winfo_rooty()
        self.geometry(f"{w}x{h}+{x}+{y}")

        self._build(row, on_action)
        self.bind("<Escape>", lambda e: self.destroy())
12. Modal de Nuevo Equipo (views/equipment_modal.py)Pythonimport customtkinter as ctk

class EquipmentModal(ctk.CTkToplevel):
    def __init__(self, master, initial=None, on_save=None):
        super().__init__(master)
        self.title("Nuevo equipo" if not initial else "Editar equipo")
        self.geometry("560x540")
        self.transient(master)            # Enlaza jerárquicamente la ventana al padre
        self.grab_set()                   # Bloquea interacciones externas hasta que se resuelva
        self.resizable(False, False)

        # Variables reactivas para el mapeo del formulario
        self.vars = {
            "model":    ctk.StringVar(value=initial.model if initial else ""),
            "brand":    ctk.StringVar(value=initial.brand if initial else ""),
            "category": ctk.StringVar(value=initial.category if initial else "Redes"),
            "units":    ctk.IntVar(value=1),
            "status":   ctk.StringVar(value="ok"),
        }

        self._build_form()
        self._build_actions(on_save)

        # Validación reactiva en tiempo real al escribir en los campos obligatorios
        for v in (self.vars["model"], self.vars["brand"]):
            v.trace_add("write", lambda *a: self._validate())
Regla de oro para modales en Tkinter: grab_set() es el estándar para forzar el comportamiento modal de una ventana. Si abres múltiples modales de manera consecutiva o programática, invoca explícitamente grab_release() antes de llamar a destroy().13. Ventanas de ConfirmaciónPuedes invocar las alertas por defecto del sistema de la siguiente forma:Pythonfrom tkinter import messagebox

def confirm_delete(self, equipo):
    ok = messagebox.askyesno(
        "Eliminar equipo",
        f"Se eliminarán {len(equipo.children)} unidades.\n¿Continuar?",
        icon="warning", parent=self,
    )
    if ok:
        self.store.delete(equipo.id)
Sin embargo, para preservar una consistencia estética completa (especialmente al usar temas oscuros), es preferible emplear un componente personalizado basado en CTkToplevel (siguiendo el mismo patrón que el modal de equipo) en lugar del cuadro messagebox nativo del SO.14. Toasts / Notificaciones (widgets/toast.py)Pythonimport customtkinter as ctk

class Toast(ctk.CTkToplevel):
    def __init__(self, master, message, kind="ok", ttl=3500):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color="#1B1F24")

        ctk.CTkLabel(self, text=message,
                     text_color="#FFFFFF",
                     font=("DM Sans", 12, "bold")
        ).pack(padx=16, pady=10)

        # Centrar el toast horizontalmente en la zona inferior de la ventana padre
        master.update_idletasks()
        self.update_idletasks()
        x = master.winfo_rootx() + (master.winfo_width() - self.winfo_width()) // 2
        y = master.winfo_rooty() + master.winfo_height() - 60
        self.geometry(f"+{x}+{y}")
        
        # Desvanecimiento / auto-dismiss programado por tiempo limite (TTL)
        self.after(ttl, self.destroy)
15. Menú Contextual (widgets/context_menu.py)El componente nativo tk.Menu es directo, pero quiebra la estética moderna de la UI. Para conservar el estilo gráfico del prototipo, se emplea una mini-ventana CTkToplevel sin decoraciones poblada de botones planos.Pythonimport customtkinter as ctk

class ContextMenu(ctk.CTkToplevel):
    def __init__(self, master, x, y, items):
        super().__init__(master)
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=("#FFFFFF", "#1A1F26"),
                       border_width=1,
                       border_color=("#E3E6EB", "#2A313A"))

        for it in items:
            if it.get("divider"):
                ctk.CTkFrame(self, height=1,
                            fg_color=("#E3E6EB", "#2A313A")
                ).pack(fill="x", padx=6, pady=3)
                continue
    
            ctk.CTkButton(self,
                          text="  " + it["label"],
                          anchor="w", height=28,
                          fg_color="transparent",
                          text_color="#B42318" if it.get("danger") else None,
                          hover_color=("#F7F8FA", "#1F242C"),
                          command=lambda i=it: (i["on_click"](), self.destroy())
            ).pack(fill="x", padx=4, pady=1)

        self.geometry(f"+{x}+{y}")
        self.bind("<FocusOut>", lambda e: self.destroy()) # Destruir si pierde el foco de usuario
        self.focus_set()
16. Atajos de Teclado GlobalesInserta estos bindeos dentro del método constructor principal de la vista (InventoryView.__init__):Pythonself.bind_all("<Control-n>", lambda e: self.open_new_modal())
self.bind_all("<Control-f>", lambda e: self.search.focus_set())
self.bind_all("<slash>",     lambda e: self.search.focus_set())
self.bind_all("<Escape>",    lambda e: self._close_overlays())
self.bind_all("<Down>",      lambda e: self._move_selection(+1))
self.bind_all("<Up>",        lambda e: self._move_selection(-1))
self.bind_all("<Right>",     lambda e: self._expand_selected(True))
self.bind_all("<Left>",      lambda e: self._expand_selected(False))
self.bind_all("<Return>",    lambda e: self._open_detail_of_selected())
17. Tema y Persistencia (Tweaks de UI)Para recrear el comportamiento de un panel de personalización o menú de preferencias:Almacena las elecciones del usuario en un documento estructurado JSON local utilizando rutas del estándar del SO via appdirs (appdirs.user_config_dir(...)/settings.json) e inicialízalas al arrancar la app:Pythonctk.set_appearance_mode(settings["theme"]) # Alterna dinámicamente "light" o "dark"
Nota sobre colores de acento: CustomTkinter no provee un API nativo global para cambiar colores de acento en caliente. Se debe propagar la nueva configuración al objeto Theme y redibujar el árbol de componentes activos, o bien implementar un EventBus personalizado al que cada widget se suscriba para actualizar sus colores individuales de forma proactiva.18. Tabla de Diagnóstico Técnico y "Gotchas"Concepto TécnicoDetalle y Estrategia de SoluciónRender de filas masivoCon colecciones superiores a 200 registros, el componente CTkScrollableFrame disminuye su tasa de refresco significativamente. Implementa una estrategia de virtualización en la carga (renderizar únicamente el subset visible) o migra los datos hacia un componente nativo estilizado ttk.Treeview.Flicker en HoverTkinter no dispone de selectores o pseudoclases CSS :hover. Debes enlazar los eventos <Enter> y <Leave> directamente sobre el Frame de la fila y en cada uno de sus elementos hijos de forma recursiva para erradicar el parpadeo visual al pasar el cursor por encima de textos o iconos.Manejo de IconosConvierte los assets vectoriales SVG a mapas de bits PNG renderizados a escalas @1x y @2x. Cárgalos mediante la clase CTkImage(light_image=..., dark_image=..., size=(16,16)) para asegurar la nitidez y el correcto reescalado automático en pantallas HiDPI.Fuentes en RuntimeTipografías como DM Sans o JetBrains Mono no forman parte de los sistemas estándar. Es mandatorio empaquetar los archivos .ttf dentro de tu directorio assets/fonts/ e inicializarlos al arranque de la aplicación usando tkextrafont.Font(file=...).Márgenes en PillsCTkLabel carece de soporte para paddings internos. Diseña la píldora de estado delegando el espaciado en la propiedad padx/pady de su contenedor padre (CTkFrame) y configúrale un radio redondeado mediante corner_radius.Sombras ComplejasEl motor de renderizado de Tkinter no genera efectos de sombra. Mitiga esta limitación usando sutiles contornos perimetrales de 1px combinados con una variación leve en la tonalidad de fondo del componente superficial. El diseño del prototipo suprime las sombras por esta razón.Animaciones FluidasPara orquestar transiciones complejas (ej. la entrada sutil de un cajón lateral o expansiones), recurre a la función nativa .after() calculando manualmente la interpolación de posiciones absolutas con place(relx=...) o alterando alturas fijas. Restringe los tiempos de ejecución para que sean ≤ 200 ms.Alta densidad en WindowsAgrega la siguiente instrucción de bajo nivel antes de inicializar la interfaz principal para evitar distorsiones o textos borrosos causados por las directivas de escalado del SO Windows:import ctypes; ctypes.windll.shcore.SetProcessDpiAwareness(1)Estrategia de PersistenciaEl uso del motor embebido sqlite3 es la opción ideal por ligereza y rendimiento. Su compatibilidad con sentencias JOIN es óptima para consolidar de manera lógica colecciones de unidades agrupadas bajo especificaciones de modelos. Estructura sugerida: equipos (id, modelo, marca, categoría, proveedor) + unidades (id, equipo_id, serial, mac, status, loc).Lotes de PruebasAl iterar frecuentemente en fases de diseño, mantén un archivo independiente preview.py que cargue y aísle componentes visuales de manera individual. Esto acelera la puesta a punto de márgenes y geometrías sin procesar toda la aplicación corporativa.19. Mapeo de Equivalencias Directas: Prototipo ➔ CustomTkinterComponente del PrototipoEquivalente en Widget RealVentana de Aplicaciónctk.CTkTarjeta Estadística (Stat Card)CTkFrame con bordes de 1px + 2 elementos de tipo CTkLabelInput de Entrada / BuscadorCTkEntry alimentado mediante la propiedad placeholder_textSelectores de Pestañas / FiltrosCTkSegmentedButton o un arreglo lineal de CTkButton customizadosBotón de Acción PrincipalCTkButton(fg_color=accent)Estructura General de la TablaContenedor CTkScrollableFrame + filas instanciadas con CTkFrameSelectores MúltiplesCTkCheckBoxPíldoras Informativas (Pill)CTkFrame con color contextual + un widget CTkLabel integradoAcciones Contextuales por FilaCTkButton en formato transparente alimentado con un CTkImage(...)Ventana Emergente (Modal)Instancia de CTkToplevel con la directiva modal activa via grab_set()Cajón de Datos Deslizable (Drawer)CTkToplevel desprovisto de bordes nativos alineado en los límites del layout padreAlerta Temporal (Toast)CTkToplevel autogestionado con la función síncrona .after() para auto-dismissMenú del Botón "Más"Componente de tipo CTkToplevel libre de bordes o uso directo de tk.MenuInformación de Atajo (Tooltip)Elemento CTkLabel con bordes finos, gatillado en hover mediante un delay con after(500, ...)

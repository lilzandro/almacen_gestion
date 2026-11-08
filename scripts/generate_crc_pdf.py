"""Genera el PDF de Tarjetas CRC del sistema DigiCable.

Uso:
    python scripts/generate_crc_pdf.py [salida.pdf]

Por defecto escribe docs/TARJETAS_CRC.pdf, deja una copia en el Escritorio y
actualiza docs/TARJETAS_CRC.md como fuente editable.
"""

from __future__ import annotations

import hashlib
import os
import shutil
import sys
from xml.sax.saxutils import escape

from reportlab.lib.colors import HexColor, white
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    CondPageBreak,
    Frame,
    FrameBreak,
    HRFlowable,
    KeepTogether,
    LongTable,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)
from reportlab.platypus.tableofcontents import TableOfContents

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_OUT = os.path.join(ROOT, "docs", "TARJETAS_CRC.pdf")
DEFAULT_MD = os.path.join(ROOT, "docs", "TARJETAS_CRC.md")
DESKTOP = os.path.join(
    os.path.expanduser("~"), "Desktop", "Tarjetas CRC - DigiCable.pdf"
)

# ── Paleta ──────────────────────────────────────────────────────────────────
NAVY = HexColor("#123B5D")
NAVY_DARK = HexColor("#0B2A4A")
ORANGE = HexColor("#E67E22")
INK = HexColor("#1F2937")
MUTED = HexColor("#5B6B82")
LIGHT = HexColor("#E8EEF5")
SOFT = HexColor("#F6F8FB")
GRID = HexColor("#D5DEE8")
GREEN = HexColor("#1A7F37")
PURPLE = HexColor("#6B4FA0")
CYAN = HexColor("#219EBC")
RED = HexColor("#B42318")

PAGE_W, PAGE_H = A4
MARGIN_X = 56.7
CONTENT_W = PAGE_W - 2 * MARGIN_X
FRAME_H = PAGE_H - 70 - 60
CARD_FRAME_H = 340
CARD_TARGET_H = 330
CARD_GAP = 12
CARD_TOP_Y = 60 + CARD_FRAME_H + CARD_GAP
CARD_BOTTOM_Y = 60

LAYER_COLORS = {
    "Dominio": CYAN,
    "Servicios": ORANGE,
    "Interfaz": PURPLE,
}

# ── Tipografía ──────────────────────────────────────────────────────────────
FONT = "SegoeUI"
FONT_B = "SegoeUI-Bold"
FONT_I = "SegoeUI-Italic"


def _register_fonts() -> None:
    """Registra Segoe UI si está disponible; si no, usa Helvetica."""
    global FONT, FONT_B, FONT_I
    candidates = {
        FONT: r"C:\Windows\Fonts\segoeui.ttf",
        FONT_B: r"C:\Windows\Fonts\segoeuib.ttf",
        FONT_I: r"C:\Windows\Fonts\segoeuii.ttf",
    }
    for name, path in candidates.items():
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
            except Exception:  # noqa: BLE001, S112
                continue
    available = set(pdfmetrics.getRegisteredFontNames())
    if FONT not in available:
        FONT, FONT_B, FONT_I = "Helvetica", "Helvetica-Bold", "Helvetica-Oblique"


_register_fonts()

# ── Estilos ─────────────────────────────────────────────────────────────────
BODY = ParagraphStyle(
    "Body",
    fontName=FONT,
    fontSize=9.4,
    leading=13.4,
    textColor=INK,
    alignment=TA_JUSTIFY,
    spaceAfter=7,
)
BODY_LEFT = ParagraphStyle(
    "BodyLeft",
    parent=BODY,
    alignment=TA_LEFT,
)
SMALL = ParagraphStyle(
    "Small",
    fontName=FONT,
    fontSize=8.2,
    leading=11.2,
    textColor=MUTED,
    alignment=TA_LEFT,
    spaceAfter=4,
)
BULLET = ParagraphStyle(
    "Bullet",
    fontName=FONT,
    fontSize=9.2,
    leading=12.6,
    textColor=INK,
    leftIndent=12,
    bulletIndent=2,
    spaceAfter=3,
)
H1 = ParagraphStyle(
    "H1",
    fontName=FONT_B,
    fontSize=18,
    leading=23,
    textColor=NAVY_DARK,
    spaceBefore=2,
    spaceAfter=6,
)
H2 = ParagraphStyle(
    "H2",
    fontName=FONT_B,
    fontSize=12.5,
    leading=16,
    textColor=NAVY,
    spaceBefore=12,
    spaceAfter=4,
)
H3 = ParagraphStyle(
    "H3",
    fontName=FONT_B,
    fontSize=10.2,
    leading=13,
    textColor=NAVY,
    spaceBefore=8,
    spaceAfter=3,
)
TOCTitle = ParagraphStyle(
    "TOCTitle",
    fontName=FONT_B,
    fontSize=18,
    leading=22,
    textColor=NAVY_DARK,
    spaceAfter=8,
)
TOC0 = ParagraphStyle(
    "TOC0",
    fontName=FONT_B,
    fontSize=10.5,
    leading=15,
    textColor=NAVY_DARK,
    leftIndent=0,
    firstLineIndent=0,
    spaceBefore=7,
)
TOC1 = ParagraphStyle(
    "TOC1",
    fontName=FONT_B,
    fontSize=9.4,
    leading=13,
    textColor=NAVY,
    leftIndent=14,
    firstLineIndent=0,
    spaceBefore=2,
)
TABLE_HEAD = ParagraphStyle(
    "TableHead",
    fontName=FONT_B,
    fontSize=8.0,
    leading=10,
    textColor=white,
    alignment=TA_LEFT,
)
TABLE_CELL = ParagraphStyle(
    "TableCell",
    fontName=FONT,
    fontSize=7.9,
    leading=10.4,
    textColor=INK,
    alignment=TA_LEFT,
)
TABLE_CELL_B = ParagraphStyle(
    "TableCellB",
    parent=TABLE_CELL,
    fontName=FONT_B,
)
CARD_NAME = ParagraphStyle(
    "CardName",
    fontName=FONT_B,
    fontSize=13.5,
    leading=16,
    textColor=white,
)
CARD_BADGE = ParagraphStyle(
    "CardBadge",
    fontName=FONT_B,
    fontSize=7.2,
    leading=9,
    textColor=white,
    alignment=TA_CENTER,
)
CARD_PURPOSE = ParagraphStyle(
    "CardPurpose",
    fontName=FONT,
    fontSize=8.7,
    leading=11.4,
    textColor=INK,
    alignment=TA_LEFT,
)
CARD_SECTION = ParagraphStyle(
    "CardSection",
    fontName=FONT_B,
    fontSize=7.6,
    leading=9.4,
    textColor=NAVY,
    alignment=TA_LEFT,
)
CARD_SECTION_SUB = ParagraphStyle(
    "CardSectionSub",
    fontName=FONT_I,
    fontSize=6.9,
    leading=8.4,
    textColor=MUTED,
    alignment=TA_LEFT,
    spaceAfter=2,
)
CARD_BULLET = ParagraphStyle(
    "CardBullet",
    fontName=FONT,
    fontSize=7.9,
    leading=10.1,
    textColor=INK,
    leftIndent=8,
    bulletIndent=0,
    spaceAfter=1.4,
)
CARD_FOOT_LABEL = ParagraphStyle(
    "CardFootLabel",
    fontName=FONT_B,
    fontSize=6.8,
    leading=8.6,
    textColor=MUTED,
)
CARD_FOOT = ParagraphStyle(
    "CardFoot",
    fontName=FONT,
    fontSize=7.1,
    leading=9.2,
    textColor=INK,
)
CARD_CODE = ParagraphStyle(
    "CardCode",
    fontName=FONT,
    fontSize=6.8,
    leading=8.8,
    textColor=NAVY,
)

# ── Portada ─────────────────────────────────────────────────────────────────
COVER_KICKER = ParagraphStyle(
    "CoverKicker",
    fontName=FONT_B,
    fontSize=9,
    leading=12,
    textColor=HexColor("#BFD3E6"),
    alignment=TA_LEFT,
)
COVER_TITLE = ParagraphStyle(
    "CoverTitle",
    fontName=FONT_B,
    fontSize=29,
    leading=34,
    textColor=white,
    alignment=TA_LEFT,
)
COVER_SUB = ParagraphStyle(
    "CoverSub",
    fontName=FONT,
    fontSize=14,
    leading=19,
    textColor=HexColor("#DCE8F4"),
    alignment=TA_LEFT,
)
COVER_BODY = ParagraphStyle(
    "CoverBody",
    fontName=FONT,
    fontSize=9.2,
    leading=13,
    textColor=HexColor("#D7E4F0"),
    alignment=TA_LEFT,
)
COVER_LABEL = ParagraphStyle(
    "CoverLabel",
    fontName=FONT_B,
    fontSize=7.6,
    leading=10,
    textColor=MUTED,
)
COVER_VALUE = ParagraphStyle(
    "CoverValue",
    fontName=FONT,
    fontSize=8.8,
    leading=12,
    textColor=INK,
)
COVER_STAT_NUM = ParagraphStyle(
    "CoverStatNum",
    fontName=FONT_B,
    fontSize=23,
    leading=25,
    textColor=NAVY_DARK,
    alignment=TA_CENTER,
)
COVER_STAT_LABEL = ParagraphStyle(
    "CoverStatLabel",
    fontName=FONT,
    fontSize=7.4,
    leading=9.5,
    textColor=MUTED,
    alignment=TA_CENTER,
)
COVER_NOTE = ParagraphStyle(
    "CoverNote",
    fontName=FONT,
    fontSize=8.0,
    leading=11.4,
    textColor=MUTED,
    alignment=TA_LEFT,
)


def esc(text: object) -> str:
    """Escapa texto para los párrafos de ReportLab."""
    return escape(str(text))


def layer_color(layer: str):
    return LAYER_COLORS.get(layer, NAVY)


CARDS = [
    {
        "name": "Usuario",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Representar a la persona que inicia sesión y determinar sus "
            "permisos dentro del sistema."
        ),
        "responsibilities": [
            (
                "Conocer su identificador, nombre de usuario, rol y estado de "
                "cambio de contraseña."
            ),
            (
                "Diferenciar el rol administrador del rol supervisor para "
                "habilitar acciones."
            ),
            "Solicitar la validación de credenciales y el cambio de contraseña.",
            "Servir como contexto de seguridad para las vistas y operaciones.",
        ],
        "collaborators": [
            ("AutenticacionService", "valida credenciales y actualiza la contraseña."),
            ("App", "conserva current_user y controla el ciclo de sesión."),
            ("Sidebar", "muestra el usuario, su rol y las opciones permitidas."),
            (
                "UsersView / _UserDialog",
                "administra altas, edición y baja de usuarios.",
            ),
            ("RepositorioDatos", "persiste la tabla users."),
        ],
        "attributes": "id, username, role, password_hash, must_change_password",
        "trace": "Tabla users · core/auth.py · ui/views/users.py · ui/sidebar.py",
    },
    {
        "name": "Almacen",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Representar una ubicación física u organizacional que agrupa "
            "inventario y movimientos."
        ),
        "responsibilities": [
            "Conocer su identificador, nombre y ubicación.",
            "Delimitar las consultas de productos, movimientos y estadísticas.",
            "Ser seleccionado como almacén activo de la sesión.",
            "Separar el inventario entre almacén Central y Secundario.",
        ],
        "collaborators": [
            ("App", "lo selecciona y conserva como almacén activo."),
            ("Producto", "clasifica cada unidad o modelo por almacén."),
            ("Movimiento", "registra el almacén donde ocurrió el cambio."),
            ("RepositorioDatos", "consulta y filtra por warehouse_id."),
            ("DashboardView / ProductsView / MovementsView", "aplican el filtro."),
        ],
        "attributes": "id, name, location",
        "trace": "Tabla warehouses · get_all_warehouses · App.current_warehouse_id",
    },
    {
        "name": "Producto",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Representar un ítem o modelo inventariable, controlado por "
            "cantidad o por unidades serializadas."
        ),
        "responsibilities": [
            (
                "Conocer nombre, marca, modelo, código, serial/MAC, cantidad, "
                "unidad, estado, proveedor y almacén."
            ),
            "Determinar si está disponible, no disponible o inactivo.",
            "Agrupar sus unidades por nombre y marca para la vista de inventario.",
            "Validar la disponibilidad de stock antes de una salida o asignación.",
            "Conservar la trazabilidad de sus cambios y de su proveedor.",
        ],
        "collaborators": [
            ("UnidadInventario", "representa cada unidad física del modelo."),
            ("Movimiento / DetalleMovimiento", "registran entradas y salidas."),
            ("Proveedor", "identifica el origen del producto."),
            ("Almacen", "ubica el stock en una sede."),
            ("RepositorioDatos", "persiste y consulta la tabla products."),
            ("ProductsView / _RegistrarProductoDialog", "lo muestran y editan."),
        ],
        "attributes": (
            "id, name, brand, modelo, barcode, serial, mac, quantity, unit, "
            "status, supplier_id, warehouse_id"
        ),
        "trace": (
            "Tabla products · get_products_grouped · create_product · "
            "update_product · ui/views/products.py"
        ),
    },
    {
        "name": "UnidadInventario",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Representar una unidad física individual, especialmente cuando el "
            "producto se controla por serial o MAC."
        ),
        "responsibilities": [
            "Conocer serial, MAC, código de barras, estado y fecha de registro.",
            "Permitir la rastreabilidad de una unidad dentro de un modelo.",
            "Reflejar si la unidad está disponible, no disponible o inactiva.",
            "Colaborar con el escaneo para localizar y seleccionar la unidad.",
        ],
        "collaborators": [
            ("Producto", "define el modelo al que pertenece la unidad."),
            ("DetalleMovimiento", "conserva el serial afectado por el movimiento."),
            ("ProductsView / _ChildRow", "la muestran dentro del grupo expandido."),
            ("_ScanResultDialog", "la localiza a partir de un código escaneado."),
            ("RepositorioDatos", "consulta por serial, MAC o código de barras."),
        ],
        "attributes": "id, serial, mac, barcode, status, created_at",
        "trace": (
            "Filas de products con serial/MAC · get_units_by_model · "
            "lookup_product_by_code · _ChildRow"
        ),
    },
    {
        "name": "Movimiento",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Registrar un cambio de inventario: entrada, salida, devolución, "
            "asignación, modificación o eliminación."
        ),
        "responsibilities": [
            "Conocer tipo, fecha, cantidad, notas, almacén, usuario y empleado.",
            "Aplicar o revertir el efecto del movimiento sobre el stock.",
            "Validar que exista stock suficiente en salidas y asignaciones.",
            "Agrupar varios productos o unidades en un movimiento compuesto.",
            "Mantener el historial y la auditoría de cada cambio.",
        ],
        "collaborators": [
            ("DetalleMovimiento", "guarda el desglose por producto o unidad."),
            ("Producto", "recibe el ajuste de cantidad y estado."),
            ("Empleado", "recibe o devuelve los equipos."),
            ("Usuario", "identifica quién autorizó el movimiento."),
            ("Almacen", "indica la sede del cambio."),
            ("ServicioMovimientos", "coordina reglas y transacciones."),
            ("MovementsView", "lo lista, filtra y muestra en detalle."),
        ],
        "attributes": (
            "id, type, product_id, employee_id, user_id, quantity, notes, "
            "timestamp, warehouse_id"
        ),
        "trace": (
            "Tabla movements · create_movement · create_compound_movement · "
            "update_movement · delete_movement"
        ),
    },
    {
        "name": "DetalleMovimiento",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Guardar el desglose por producto o unidad de un movimiento "
            "compuesto y preservar el snapshot histórico."
        ),
        "responsibilities": [
            (
                "Conocer movement_id, product_id, nombre, marca, cantidad, unidad "
                "y seriales."
            ),
            "Permitir que un movimiento incluya varios productos o unidades.",
            "Conservar los datos aunque el producto cambie o se elimine.",
            "Alimentar los reportes y comprobantes de movimiento.",
        ],
        "collaborators": [
            ("Movimiento", "es su cabecera y le da contexto."),
            ("Producto", "referencia el ítem original del detalle."),
            ("ServicioMovimientos", "lo crea y lo adjunta a la transacción."),
            ("RepositorioDatos", "persiste la tabla movement_items."),
            ("ServicioReportes / PDFExporter", "lo incluyen en los PDF."),
        ],
        "attributes": "id, movement_id, product_id, name, brand, qty, unit, seriales",
        "trace": (
            "Tabla movement_items · _attach_item_summaries · "
            "get_movement_detail · export_single_movement"
        ),
    },
    {
        "name": "Proveedor",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": "Representar la empresa o persona que suministra productos.",
        "responsibilities": [
            "Conocer nombre, contacto y RIF.",
            "Asociarse a uno o varios productos del inventario.",
            "Mantener un catálogo consultable y editable.",
            "Validar los datos obligatorios antes de guardar.",
        ],
        "collaborators": [
            ("Producto", "referencia al proveedor que lo suministra."),
            ("RepositorioDatos", "persiste la tabla suppliers."),
            ("SuppliersView", "lo lista y administra."),
            ("_SupplierDialog", "captura y valida sus datos."),
            ("ProductsView", "lo muestra y permite seleccionarlo."),
        ],
        "attributes": "id, name, contact, rif, created_at",
        "trace": "Tabla suppliers · CRUD en repository.py · ui/views/suppliers.py",
    },
    {
        "name": "Empleado",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Representar al colaborador que recibe, devuelve o tiene asignado "
            "un equipo."
        ),
        "responsibilities": [
            "Conocer nombre, cédula y cargo.",
            "Asociarse a movimientos de salida, asignación y devolución.",
            "Mantener un catálogo de empleados actualizado.",
            "Validar que la cédula sea única.",
        ],
        "collaborators": [
            ("Movimiento", "lo referencia como receptor o responsable."),
            ("RepositorioDatos", "persiste la tabla employees."),
            ("EmployeesView", "lo lista y administra."),
            ("_EmpDialog", "captura y valida sus datos."),
            ("MovementsView", "lo muestra en el detalle del movimiento."),
        ],
        "attributes": "id, name, cedula, cargo, created_at",
        "trace": "Tabla employees · CRUD en repository.py · ui/views/employees.py",
    },
    {
        "name": "Vehiculo",
        "stereotype": "Entidad",
        "layer": "Dominio",
        "purpose": (
            "Representar un vehículo de la empresa dentro del catálogo de "
            "apoyo logístico."
        ),
        "responsibilities": [
            "Conocer marca, modelo y placa.",
            "Mantener un registro consultable y editable.",
            "Validar que la placa esté presente y sea única.",
            "Servir como catálogo para futuras asignaciones de transporte.",
        ],
        "collaborators": [
            ("RepositorioDatos", "persiste la tabla vehicles."),
            ("VehiclesView", "lo lista y administra."),
            ("_VehicleDialog", "captura y valida sus datos."),
        ],
        "attributes": "id, brand, model, plate, created_at",
        "trace": (
            "Tabla vehicles · CRUD en repository.py · ui/views/vehicles.py · "
            "catálogo independiente de movements"
        ),
    },
    {
        "name": "AutenticacionService",
        "stereotype": "Servicio",
        "layer": "Servicios",
        "purpose": "Validar la identidad de los usuarios y gestionar sus contraseñas.",
        "responsibilities": [
            "Verificar la combinación de nombre de usuario y contraseña.",
            "Generar y comprobar hashes PBKDF2 con sal.",
            "Migrar hashes legacy SHA-256 en el siguiente inicio de sesión.",
            "Cambiar la contraseña y limpiar must_change_password.",
            "Devolver el usuario autenticado o un error comprensible.",
        ],
        "collaborators": [
            ("Usuario", "aporta credenciales y rol."),
            ("RepositorioDatos", "consulta y actualiza la tabla users."),
            ("LoginFrame", "captura las credenciales y muestra el error."),
            ("_ForceChangePasswordDialog", "solicita la nueva contraseña."),
            ("App", "recibe el usuario autenticado e inicia la sesión."),
        ],
        "attributes": "hash_password · verify_password · login · change_password",
        "trace": "core/auth.py · tabla users · ui/login_frame.py",
    },
    {
        "name": "RepositorioDatos",
        "stereotype": "Repositorio",
        "layer": "Servicios",
        "purpose": (
            "Centralizar el acceso a SQLite y encapsular consultas, "
            "transacciones y caché."
        ),
        "responsibilities": [
            "Abrir y cerrar conexiones de forma segura.",
            "Ejecutar el CRUD de usuarios, productos, movimientos y catálogos.",
            "Aplicar filtros, búsquedas, paginación y ordenamientos.",
            "Calcular estadísticas, rankings y resúmenes del dashboard.",
            "Mantener la integridad transaccional y invalidar la caché.",
        ],
        "collaborators": [
            ("ConexionBD", "proporciona la conexión y el esquema."),
            ("Todas las entidades", "persisten y recuperan sus datos."),
            ("ServicioMovimientos", "realiza operaciones atómicas de stock."),
            ("ServicioReportes", "obtiene consultas planas para los PDF."),
            ("Vistas de la UI", "solicitan listados y resúmenes."),
        ],
        "attributes": (
            "get_all_* · create_* · update_* · delete_* · get_dashboard_stats · "
            "get_movements_flat · clear_cache"
        ),
        "trace": (
            "database/repository.py · database/connection.py · "
            "módulo de funciones que actúa como fachada de persistencia"
        ),
    },
    {
        "name": "ServicioMovimientos",
        "stereotype": "Control",
        "layer": "Servicios",
        "purpose": (
            "Coordinar las reglas de negocio de movimientos, stock y transacciones."
        ),
        "responsibilities": [
            "Crear movimientos simples y compuestos.",
            "Validar stock y aplicar o revertir cantidades.",
            "Editar y eliminar movimientos con rollback ante errores.",
            "Registrar movimientos de modificación y eliminación.",
            "Agrupar varios ítems en una sola operación atómica.",
        ],
        "collaborators": [
            ("Movimiento / DetalleMovimiento", "son el objeto de la operación."),
            ("Producto", "recibe el ajuste de cantidad y estado."),
            ("RepositorioDatos", "ejecuta SQL y confirma la transacción."),
            ("MovementsView", "inicia el registro, edición o borrado."),
            ("_MovementDialog / _MovementEditDialog", "capturan los datos."),
        ],
        "attributes": (
            "create_movement · create_compound_movement · apply_movement_stock · "
            "revert_movement_stock · update_movement · delete_movement"
        ),
        "trace": (
            "database/repository.py · ui/views/movements.py · "
            "parte de la lógica vive en el repositorio para asegurar atomicidad"
        ),
    },
    {
        "name": "ServicioReportes",
        "stereotype": "Control",
        "layer": "Servicios",
        "purpose": "Generar reportes PDF y coordinar su entrega por correo o WhatsApp.",
        "responsibilities": [
            "Calcular rangos diario, semanal, mensual y personalizado.",
            "Filtrar por tipo, fecha, almacén y selección de movimientos.",
            "Construir PDF de movimientos, inventario, ranking y cierre crítico.",
            "Generar el comprobante individual de un movimiento.",
            "Delegar el envío al notificador y reportar errores al usuario.",
        ],
        "collaborators": [
            ("MovementsView / _ReportsDialog", "solicitan y configuran el reporte."),
            ("RepositorioDatos", "entrega los datos planos."),
            ("PDFExporter", "renderiza el documento PDF."),
            ("NotificadorReportes", "envía por correo o WhatsApp."),
            ("ConfiguracionReportes", "resuelve los destinos."),
            ("DashboardView / _MovementInfoDialog", "usan reportes puntuales."),
        ],
        "attributes": (
            "report_date_range · split_ranking · export_movements · "
            "export_inventory · export_product_ranking · export_critical_closing"
        ),
        "trace": (
            "ui/views/movements.py · core/export.py · core/pdf_export.py · "
            "ui/dashboard_widgets.py"
        ),
    },
    {
        "name": "RespaldoService",
        "stereotype": "Servicio",
        "layer": "Servicios",
        "purpose": "Crear y restaurar copias de seguridad consistentes de la base de datos.",
        "responsibilities": [
            "Crear un respaldo usando la API de backup de SQLite.",
            "Validar que el archivo sea SQLite y contenga las tablas esperadas.",
            "Crear un respaldo de seguridad antes de restaurar.",
            "Restaurar la base y limpiar los archivos sidecar -wal y -shm.",
            "Recargar el esquema y la caché después de la restauración.",
        ],
        "collaborators": [
            ("SystemDataView", "ofrece las acciones de respaldo y carga."),
            ("RepositorioDatos", "invalida la caché y vuelve a consultar."),
            ("ConexionBD", "abre la base y ejecuta initialize_db."),
            ("SQLite", "proporciona la copia consistente y la validación."),
        ],
        "attributes": (
            "create_backup · validate_database · create_safety_backup · "
            "restore_database"
        ),
        "trace": "core/database_backup.py · ui/views/system_data.py",
    },
    {
        "name": "EscaneoMovilService",
        "stereotype": "Servicio",
        "layer": "Servicios",
        "purpose": (
            "Recibir códigos escaneados desde un teléfono conectado a la red local."
        ),
        "responsibilities": [
            "Iniciar un servidor HTTP local y generar un token de sesión.",
            "Servir la página de escaneo y el código QR de acceso.",
            "Validar el token de cada código recibido.",
            "Encolar los códigos para que la interfaz los procese.",
            "Exponer la URL local que debe abrir el teléfono.",
        ],
        "collaborators": [
            ("App", "consume la cola y despacha los códigos a las vistas."),
            ("ProductsView", "recibe el código y busca el producto."),
            ("_BarcodeScanDialog", "muestra el resultado del escaneo."),
            ("_ScanRowDialog / _PhoneScanHelpDialog", "guían al usuario."),
        ],
        "attributes": ("start_scan_server · generate_token · make_qr_pil · get_lan_ip"),
        "trace": ("core/phone_scan.py · ui/app.py (_poll_scan_queue, _dispatch_scan)"),
    },
    {
        "name": "ConfiguracionReportes",
        "stereotype": "Servicio",
        "layer": "Servicios",
        "purpose": "Persistir y normalizar los destinos de correo y WhatsApp.",
        "responsibilities": [
            "Leer y escribir el archivo config.json del usuario.",
            "Normalizar números de teléfono y códigos de país.",
            "Aplicar las variables de entorno con prioridad sobre el archivo.",
            "Informar si un destino proviene de una variable de entorno.",
            "Validar que exista un destino antes de intentar enviar.",
        ],
        "collaborators": [
            ("NotificadorReportes", "consulta los destinos configurados."),
            ("_DestinationsDialog", "permite editarlos desde la interfaz."),
            ("ServicioReportes", "solicita el destino al enviar."),
        ],
        "attributes": (
            "config_file · load_config · save_config · normalize_phone · "
            "get_email_to · get_whatsapp_to · set_destinations"
        ),
        "trace": (
            "core/report_config.py · %APPDATA%/DigiCable/config.json · "
            "REPORT_EMAIL_TO y WHATSAPP_TO"
        ),
    },
    {
        "name": "NotificadorReportes",
        "stereotype": "Servicio",
        "layer": "Servicios",
        "purpose": (
            "Entregar los reportes PDF por correo electrónico o WhatsApp, "
            "con mecanismos de respaldo."
        ),
        "responsibilities": [
            "Abrir Outlook con el PDF ya adjunto y el correo preparado.",
            "Usar mailto:, portapapeles y Explorador si Outlook falla.",
            "Abrir WhatsApp con el mensaje y dejar el PDF listo para adjuntar.",
            "Copiar el archivo al portapapeles y revelarlo en el Explorador.",
            "Informar claramente si falta un destino o falla el cliente.",
        ],
        "collaborators": [
            ("ServicioReportes", "le entrega la ruta del PDF y el asunto."),
            ("ConfiguracionReportes", "resuelve correo y WhatsApp destino."),
            ("Outlook", "crea el correo con adjunto mediante COM."),
            ("WhatsApp / navegador", "abre el chat mediante wa.me."),
            ("win_utils", "copia archivos y revela rutas en Windows."),
        ],
        "attributes": "send_report_email · send_report_whatsapp",
        "trace": ("core/email_report.py · core/whatsapp_report.py · core/win_utils.py"),
    },
    {
        "name": "App",
        "stereotype": "Coordinador",
        "layer": "Interfaz",
        "purpose": (
            "Ventana principal y coordinador de sesión, navegación, almacén "
            "activo y escaneo móvil."
        ),
        "responsibilities": [
            "Mostrar el login y conservar el usuario autenticado.",
            "Mantener el almacén activo y notificar cambios a las vistas.",
            "Construir el sidebar y crear o reutilizar las vistas.",
            "Invalidar vistas cuando cambia el almacén o la sesión.",
            "Consumir la cola de escaneo y despachar los códigos.",
            "Cerrar la sesión y volver al login.",
        ],
        "collaborators": [
            ("LoginFrame", "le entrega el usuario autenticado."),
            ("Sidebar", "solicita navegación y cierre de sesión."),
            ("Vistas de la app", "las instancia y les inyecta current_user/app."),
            ("RepositorioDatos", "consulta almacenes y datos de sesión."),
            ("EscaneoMovilService", "inicia el servidor y llena la cola."),
        ],
        "attributes": (
            "current_user, current_warehouse_id, _views, _warehouses, "
            "scan_url, _scan_queue"
        ),
        "trace": (
            "ui/app.py · _on_login · _navigate · _on_warehouse_change_by_name · "
            "_poll_scan_queue · _dispatch_scan · _logout"
        ),
    },
    {
        "name": "Sidebar",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": "Menú lateral de navegación y control de la sesión.",
        "responsibilities": [
            "Construir las opciones de navegación de la aplicación.",
            "Mostrar Usuarios y Datos del sistema solo al administrador.",
            "Resaltar la opción activa y animar el indicador.",
            "Mostrar el nombre y el rol del usuario conectado.",
            "Solicitar el cierre de sesión.",
        ],
        "collaborators": [
            ("App", "recibe la orden de navegar o cerrar sesión."),
            ("Usuario", "aporta nombre y rol para filtrar opciones."),
            ("Vistas", "son el destino de cada opción del menú."),
        ],
        "attributes": "_buttons, _active, on_navigate, on_logout",
        "trace": "ui/sidebar.py · _nav · _slide_indicator · _on_button_enter",
    },
    {
        "name": "LoginFrame",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": "Capturar las credenciales y iniciar la sesión del usuario.",
        "responsibilities": [
            "Validar que usuario y contraseña no estén vacíos.",
            "Solicitar la autenticación al servicio correspondiente.",
            "Mostrar un error claro si las credenciales fallan.",
            "Forzar el cambio de contraseña cuando must_change_password está activo.",
            "Notificar el éxito a App con el usuario autenticado.",
        ],
        "collaborators": [
            ("AutenticacionService", "valida las credenciales."),
            ("_ForceChangePasswordDialog", "gestiona el cambio obligatorio."),
            ("App", "recibe el usuario y abre la ventana principal."),
            ("Usuario", "es el resultado de un login exitoso."),
        ],
        "attributes": "on_login_success · _do_login · campos de usuario y clave",
        "trace": "ui/login_frame.py · core/auth.py · _ForceChangePasswordDialog",
    },
    {
        "name": "DashboardView",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": (
            "Mostrar un resumen visual del inventario y accesos rápidos a las "
            "operaciones principales."
        ),
        "responsibilities": [
            "Mostrar métricas de disponibles, entradas, salidas y devoluciones.",
            "Cargar estadísticas en segundo plano sin bloquear la interfaz.",
            "Listar los movimientos recientes y abrir su detalle.",
            "Navegar a productos o movimientos con filtros predefinidos.",
            "Imprimir el detalle de un movimiento cuando se solicite.",
        ],
        "collaborators": [
            ("App", "recibe las solicitudes de navegación."),
            ("RepositorioDatos", "entrega estadísticas y movimientos recientes."),
            ("ServicioReportes", "genera el PDF del detalle."),
            ("_MovementInfoDialog", "muestra el detalle del movimiento."),
            ("ProductsView / MovementsView", "son los destinos de navegación."),
        ],
        "attributes": "_load_gen, _load_queue, refresh, _apply_stats, _go",
        "trace": "ui/views/dashboard.py · ui/dashboard_widgets.py",
    },
    {
        "name": "ProductsView",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": "Gestionar el inventario de productos y sus unidades.",
        "responsibilities": [
            "Listar productos agrupados por nombre y marca.",
            "Buscar y filtrar por estado, almacén o texto.",
            "Expandir un grupo para ver y operar sus unidades.",
            "Crear, editar, eliminar y reactivar productos.",
            "Escanear códigos y localizar el producto o unidad.",
            "Exportar el inventario a PDF y mostrar la ayuda de escaneo móvil.",
        ],
        "collaborators": [
            ("Producto / UnidadInventario", "son los datos que muestra y edita."),
            ("Proveedor", "se selecciona al registrar un producto."),
            ("RepositorioDatos", "ejecuta consultas y cambios."),
            ("_GroupRow / _ChildRow", "renderizan grupos y unidades."),
            (
                "_RegistrarProductoDialog / _ProductDialog",
                "capturan altas y ediciones.",
            ),
            ("_GroupEditDialog / _ScanResultDialog", "gestionan grupos y escaneos."),
            ("_BarcodeScanDialog / _PhoneScanHelpDialog", "apoyan el escaneo."),
            ("App / EscaneoMovilService", "entregan los códigos escaneados."),
        ],
        "attributes": (
            "_selected_id, _expanded, _render_gen, refresh, _add_dialog, "
            "_edit_dialog, _delete, _export_pdf, _scan_barcode"
        ),
        "trace": "ui/views/products.py · database/repository.py · core/phone_scan.py",
    },
    {
        "name": "MovementsView",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": "Gestionar y consultar los movimientos de inventario.",
        "responsibilities": [
            "Listar, paginar y filtrar movimientos por tipo, fecha y texto.",
            "Mostrar chips, conteos y el detalle de cada movimiento.",
            "Registrar, editar y eliminar movimientos.",
            "Seleccionar productos y empleados en los diálogos de alta.",
            "Abrir reportes y actualizar los totales después de cada cambio.",
        ],
        "collaborators": [
            ("Movimiento / DetalleMovimiento", "son los datos que lista y edita."),
            ("Producto / Empleado", "se seleccionan al registrar un movimiento."),
            ("ServicioMovimientos", "ejecuta las reglas de stock."),
            ("ServicioReportes", "genera los reportes y comprobantes."),
            ("RepositorioDatos", "consulta y persiste los movimientos."),
            ("_MovementDialog / _MovementEditDialog", "capturan los datos."),
            ("_MovementInfoDialog / _ReportsDialog", "muestran detalle y reportes."),
            ("_SearchableMultiSelect", "permite seleccionar varios productos."),
        ],
        "attributes": (
            "PER_PAGE, COLS, refresh, _reload, _refresh_table, _register_dialog, "
            "_edit_movement, _delete_movement, _open_reports, _open_info"
        ),
        "trace": "ui/views/movements.py · database/repository.py · core/export.py",
    },
    {
        "name": "UsersView",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": "Administrar los usuarios y sus roles.",
        "responsibilities": [
            "Listar los usuarios registrados y su rol.",
            "Crear, editar y eliminar usuarios.",
            "Validar la contraseña mínima y los campos obligatorios.",
            "Evitar que se elimine el último administrador.",
            "Refrescar la tabla después de cada cambio.",
        ],
        "collaborators": [
            ("Usuario", "es la entidad que se administra."),
            ("RepositorioDatos", "persiste la tabla users."),
            ("AutenticacionService", "genera el hash de la contraseña."),
            ("_UserDialog", "captura los datos del usuario."),
            ("App", "inyecta el usuario actual y controla el acceso."),
        ],
        "attributes": "refresh, _add_dialog, _edit_dialog, _delete",
        "trace": "ui/views/users.py · database/repository.py · core/auth.py",
    },
    {
        "name": "SystemDataView",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": "Ofrecer el respaldo y la restauración de la base de datos.",
        "responsibilities": [
            "Mostrar la ruta y el tamaño de la base actual.",
            "Guardar un respaldo en la ubicación elegida.",
            "Seleccionar y validar un archivo de respaldo.",
            "Confirmar la restauración y crear un respaldo de seguridad.",
            "Cerrar la sesión después de restaurar.",
            "Restringir la vista al rol administrador.",
        ],
        "collaborators": [
            ("RespaldoService", "crea, valida y restaura la base."),
            ("App", "recibe la orden de cerrar sesión."),
            ("Usuario", "aporta el rol que autoriza la vista."),
            ("RepositorioDatos", "invalida la caché después de restaurar."),
            ("ConfirmDialog / MessageDialog", "confirman y comunican resultados."),
        ],
        "attributes": "refresh, _backup, _restore, _ensure_admin",
        "trace": "ui/views/system_data.py · core/database_backup.py",
    },
    {
        "name": "CatalogosView",
        "stereotype": "Frontera",
        "layer": "Interfaz",
        "purpose": (
            "Gestionar los catálogos maestros de proveedores, empleados y vehículos."
        ),
        "responsibilities": [
            "Listar los registros del catálogo correspondiente.",
            "Crear, editar y eliminar registros.",
            "Validar campos obligatorios y valores duplicados.",
            "Abrir el diálogo específico de cada catálogo.",
            "Refrescar la tabla después de guardar o eliminar.",
        ],
        "collaborators": [
            ("Proveedor / Empleado / Vehiculo", "son las entidades del catálogo."),
            ("RepositorioDatos", "persiste cada tabla."),
            ("_SupplierDialog / _EmpDialog / _VehicleDialog", "capturan los datos."),
            ("App", "inyecta el usuario y controla el acceso."),
        ],
        "attributes": "refresh, _add_dialog, _edit_dialog, _delete, _save_new",
        "trace": (
            "ui/views/suppliers.py · ui/views/employees.py · "
            "ui/views/vehicles.py · patrón compartido de vista de catálogo"
        ),
    },
]


def on_page(canvas, doc):
    """Dibuja la portada, el encabezado y el pie de cada página."""
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(NAVY_DARK)
        canvas.rect(0, PAGE_H - 390, PAGE_W, 390, stroke=0, fill=1)
        canvas.setFillColor(ORANGE)
        canvas.rect(0, PAGE_H - 390, PAGE_W, 5, stroke=0, fill=1)
        canvas.setFillColor(HexColor("#BFD3E6"))
        canvas.setFont(FONT_B, 8)
        canvas.drawString(MARGIN_X, PAGE_H - 44, "DIGICABLE")
        canvas.setFont(FONT, 8)
        canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 44, "2026")
        canvas.restoreState()
        return

    canvas.setFillColor(NAVY_DARK)
    canvas.setFont(FONT_B, 8)
    canvas.drawString(MARGIN_X, PAGE_H - 34, "DigiCable · Tarjetas CRC")
    canvas.setFont(FONT, 8)
    canvas.setFillColor(MUTED)
    canvas.drawRightString(PAGE_W - MARGIN_X, PAGE_H - 34, "v1.0 · 08/11/2026")
    canvas.setStrokeColor(GRID)
    canvas.setLineWidth(0.5)
    canvas.line(MARGIN_X, PAGE_H - 42, PAGE_W - MARGIN_X, PAGE_H - 42)

    canvas.line(MARGIN_X, 42, PAGE_W - MARGIN_X, 42)
    canvas.setFont(FONT, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(
        MARGIN_X,
        30,
        "Diseño de Software Orientado a Objetos · Sistema DigiCable",
    )
    canvas.drawRightString(PAGE_W - MARGIN_X, 30, f"Página {doc.page}")
    canvas.restoreState()


class CRCDoc(BaseDocTemplate):
    """Documento con índice, marcadores y plantillas de una o dos tarjetas."""

    def __init__(self, filename, **kwargs):
        super().__init__(filename, **kwargs)
        self.toc = TableOfContents()
        self.toc.levelStyles = [TOC0, TOC1]
        self.toc.dotsMinLevel = 0

    def afterFlowable(self, flowable):
        if not isinstance(flowable, Paragraph):
            return
        style = flowable.style.name
        if style not in ("H1", "H2"):
            return
        text = flowable.getPlainText()
        level = 0 if style == "H1" else 1
        key = f"h{level}-{hashlib.md5(text.encode('utf-8')).hexdigest()}"
        self.canv.bookmarkPage(key)
        self.canv.addOutlineEntry(text, key, level=level, closed=False)
        self.notify("TOCEntry", (level, text, self.page, key))


def make_doc(path: str) -> CRCDoc:
    """Crea el documento con una plantilla normal y otra de dos tarjetas."""
    doc = CRCDoc(
        path,
        pagesize=A4,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=70,
        bottomMargin=60,
        title="Tarjetas CRC - DigiCable",
        author="Equipo de desarrollo DigiCable",
        subject="Diseño de Software Orientado a Objetos",
    )
    normal_frame = Frame(
        MARGIN_X,
        60,
        CONTENT_W,
        FRAME_H,
        id="normal",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    card_top = Frame(
        MARGIN_X,
        CARD_TOP_Y,
        CONTENT_W,
        CARD_FRAME_H,
        id="card_top",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    card_bottom = Frame(
        MARGIN_X,
        CARD_BOTTOM_Y,
        CONTENT_W,
        CARD_FRAME_H,
        id="card_bottom",
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
    )
    doc.addPageTemplates(
        [
            PageTemplate(id="normal", frames=[normal_frame], onPage=on_page),
            PageTemplate(
                id="cards",
                frames=[card_top, card_bottom],
                onPage=on_page,
            ),
        ]
    )
    return doc


def _section_block(title, subtitle, items, width, collaborator=False):
    """Construye el bloque de responsabilidades o de colaboradores."""
    rows = [
        [Paragraph(title, CARD_SECTION)],
        [Paragraph(subtitle, CARD_SECTION_SUB)],
    ]
    for item in items:
        if collaborator:
            name, role = item
            text = f"<b>{esc(name)}</b> — {esc(role)}"
        else:
            text = esc(item)
        rows.append([Paragraph(text, CARD_BULLET, bulletText="•")])
    block = Table(rows, colWidths=[width])
    block.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return block


def build_card(card: dict, number: int, extra_pad: float = 0):
    """Devuelve una tarjeta CRC como tabla de ReportLab.

    ``extra_pad`` agrega espacio en blanco dentro del cuerpo para que las
    tarjetas tengan una altura uniforme y se vean como fichas del mismo tamaño.
    """
    color = layer_color(card["layer"])
    resp_w = CONTENT_W * 0.58
    collab_w = CONTENT_W - resp_w
    header = Table(
        [
            [
                Paragraph(
                    f'<font size="7.2" color="#BFD3E6">CRC-{number:02d}</font>'
                    f'<font color="#BFD3E6"> · </font>{esc(card["name"])}',
                    CARD_NAME,
                ),
                Paragraph(esc(card["stereotype"].upper()), CARD_BADGE),
            ]
        ],
        colWidths=[CONTENT_W - 96, 96],
    )
    header.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), NAVY),
                ("BACKGROUND", (1, 0), (1, 0), color),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (0, 0), 10),
                ("RIGHTPADDING", (0, 0), (0, 0), 6),
                ("LEFTPADDING", (1, 0), (1, 0), 4),
                ("RIGHTPADDING", (1, 0), (1, 0), 4),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    purpose = Table(
        [[Paragraph(esc(card["purpose"]), CARD_PURPOSE)]],
        colWidths=[CONTENT_W],
    )
    purpose.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
            ]
        )
    )

    resp = _section_block(
        "RESPONSABILIDADES",
        "Sabe / hace",
        card["responsibilities"],
        resp_w - 18,
    )
    collab = _section_block(
        "COLABORADORES",
        "Con quién trabaja",
        card["collaborators"],
        collab_w - 18,
        collaborator=True,
    )
    body_rows = [[resp, collab]]
    if extra_pad > 0:
        notes_spacer = max(2, extra_pad - 17)
        notes = Table(
            [
                [Paragraph("NOTAS", CARD_SECTION)],
                [Spacer(1, notes_spacer)],
            ],
            colWidths=[CONTENT_W],
        )
        notes.setStyle(
            TableStyle(
                [
                    ("LINEABOVE", (0, 0), (-1, 0), 0.4, GRID),
                    ("LEFTPADDING", (0, 0), (-1, -1), 10),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                    ("TOPPADDING", (0, 0), (-1, 0), 4),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 1),
                    ("TOPPADDING", (0, 1), (-1, 1), 0),
                    ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
                ]
            )
        )
        body_rows.append([notes, ""])
    body = Table(body_rows, colWidths=[resp_w, collab_w])
    body.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (0, 0), 10),
                ("RIGHTPADDING", (0, 0), (0, 0), 8),
                ("LEFTPADDING", (1, 0), (1, 0), 8),
                ("RIGHTPADDING", (1, 0), (1, 0), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                ("LINEAFTER", (0, 0), (0, 0), 0.4, GRID),
                ("SPAN", (0, 1), (1, 1)),
                ("LEFTPADDING", (0, 1), (-1, 1), 0),
                ("RIGHTPADDING", (0, 1), (-1, 1), 0),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 0),
            ]
        )
    )

    foot_left_w = CONTENT_W * 0.58
    foot_right_w = CONTENT_W - foot_left_w
    foot_left = Table(
        [
            [Paragraph("ATRIBUTOS / OPERACIONES", CARD_FOOT_LABEL)],
            [Paragraph(esc(card["attributes"]), CARD_FOOT)],
        ],
        colWidths=[foot_left_w - 18],
    )
    foot_left.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    foot_right = Table(
        [
            [Paragraph("TRAZABILIDAD EN CÓDIGO", CARD_FOOT_LABEL)],
            [Paragraph(esc(card["trace"]), CARD_CODE)],
        ],
        colWidths=[foot_right_w - 18],
    )
    foot_right.setStyle(
        TableStyle(
            [
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    footer = Table(
        [[foot_left, foot_right]],
        colWidths=[foot_left_w, foot_right_w],
    )
    footer.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("LEFTPADDING", (0, 0), (0, 0), 10),
                ("RIGHTPADDING", (0, 0), (0, 0), 8),
                ("LEFTPADDING", (1, 0), (1, 0), 8),
                ("RIGHTPADDING", (1, 0), (1, 0), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEAFTER", (0, 0), (0, 0), 0.4, GRID),
            ]
        )
    )

    outer = Table(
        [[header], [purpose], [body], [footer]],
        colWidths=[CONTENT_W],
    )
    outer.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), white),
                ("BOX", (0, 0), (-1, -1), 0.8, GRID),
                ("LINEBEFORE", (0, 0), (0, -1), 4, color),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.4, GRID),
            ]
        )
    )
    outer.splitByRow = 0
    return outer


def _rule(color=ORANGE, thickness=1.2, before=2, after=6):
    return HRFlowable(
        width="100%",
        thickness=thickness,
        color=color,
        spaceBefore=before,
        spaceAfter=after,
    )


def section(title: str):
    return [
        CondPageBreak(90),
        Paragraph(esc(title), H1),
        _rule(ORANGE, 1.2, 0, 7),
    ]


def subsection(title: str):
    return [
        Paragraph(esc(title), H2),
        _rule(NAVY, 0.6, 0, 5),
    ]


def make_cover():
    story = [Spacer(1, 58)]
    story.append(Paragraph("DISEÑO DE SOFTWARE ORIENTADO A OBJETOS", COVER_KICKER))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Tarjetas CRC", COVER_TITLE))
    story.append(Spacer(1, 4))
    story.append(
        Paragraph(
            "Sistema de Control de Inventarios DigiCable",
            COVER_SUB,
        )
    )
    story.append(Spacer(1, 14))
    story.append(
        Paragraph(
            "Documento de diseño que describe las clases del sistema, sus "
            "responsabilidades y sus colaboraciones, tomando como base la "
            "implementación real en Python, CustomTkinter y SQLite.",
            COVER_BODY,
        )
    )
    story.append(Spacer(1, 30))

    stats = Table(
        [
            [
                Paragraph("26", COVER_STAT_NUM),
                Paragraph("9", COVER_STAT_NUM),
                Paragraph("8", COVER_STAT_NUM),
                Paragraph("9", COVER_STAT_NUM),
            ],
            [
                Paragraph("tarjetas CRC", COVER_STAT_LABEL),
                Paragraph("entidades", COVER_STAT_LABEL),
                Paragraph("servicios / control", COVER_STAT_LABEL),
                Paragraph("fronteras de UI", COVER_STAT_LABEL),
            ],
        ],
        colWidths=[CONTENT_W / 4] * 4,
    )
    stats.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), white),
                ("BOX", (0, 0), (-1, -1), 0.8, GRID),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, GRID),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 0),
                ("TOPPADDING", (0, 1), (-1, 1), 0),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
            ]
        )
    )
    story.append(stats)
    story.append(Spacer(1, 64))

    meta = Table(
        [
            [
                Paragraph("Sistema", COVER_LABEL),
                Paragraph("DigiCable · Control de inventarios", COVER_VALUE),
            ],
            [
                Paragraph("Alcance", COVER_LABEL),
                Paragraph(
                    "Clases de dominio, servicios, repositorio y fronteras de UI",
                    COVER_VALUE,
                ),
            ],
            [
                Paragraph("Audiencia", COVER_LABEL),
                Paragraph(
                    "Equipo de desarrollo, docentes y evaluadores de diseño",
                    COVER_VALUE,
                ),
            ],
            [
                Paragraph("Versión", COVER_LABEL),
                Paragraph("1.0 · 08/11/2026", COVER_VALUE),
            ],
        ],
        colWidths=[70, CONTENT_W - 70],
    )
    meta.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LINEBELOW", (0, 0), (-1, -2), 0.35, GRID),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(meta)
    story.append(Spacer(1, 18))
    note = Table(
        [
            [
                Paragraph(
                    "Las tarjetas de entidad son clases de análisis: en el "
                    "código actual sus datos viven en tablas SQLite y sus "
                    "operaciones se implementan como funciones del "
                    "repositorio. Las tarjetas de servicio y frontera "
                    "corresponden a módulos y clases reales del proyecto.",
                    COVER_NOTE,
                )
            ]
        ],
        colWidths=[CONTENT_W],
    )
    note.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(note)
    story.append(PageBreak())
    return story


def make_toc(doc):
    return [
        Paragraph("Contenido", TOCTitle),
        _rule(ORANGE, 1.2, 0, 8),
        Spacer(1, 4),
        doc.toc,
        PageBreak(),
    ]


def make_intro():
    story = section("1. Introducción")
    story.append(
        Paragraph(
            "Este documento presenta las tarjetas CRC (Class-Responsibility-"
            "Collaboration) del sistema DigiCable. Cada tarjeta describe una "
            "clase, las responsabilidades que asume y las clases con las que "
            "colabora para cumplirlas. El objetivo es documentar el diseño "
            "orientado a objetos del sistema y facilitar la revisión, el "
            "mantenimiento y la evolución del código.",
            BODY,
        )
    )
    story.append(
        Paragraph(
            "El contenido se elaboró a partir de la implementación real: "
            "módulos de interfaz en CustomTkinter, servicios en core, "
            "repositorio de datos y esquema SQLite. Por eso cada tarjeta "
            "incluye una sección de trazabilidad que indica dónde se "
            "materializa en el proyecto.",
            BODY,
        )
    )

    story += subsection("1.1 ¿Qué es una tarjeta CRC?")
    story.append(
        Paragraph(
            "Una tarjeta CRC es una ficha de diseño que se usa para pensar en "
            "objetos antes o durante la implementación. Se escribe en una "
            "tarjeta física o digital y contiene tres bloques: el nombre de la "
            "clase, sus responsabilidades y sus colaboradores.",
            BODY,
        )
    )
    anatomy = [
        [
            Paragraph("Elemento", TABLE_HEAD),
            Paragraph("Qué describe", TABLE_HEAD),
        ],
        [
            Paragraph("Nombre", TABLE_CELL_B),
            Paragraph(
                "Identifica la clase o el concepto que se está modelando.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Responsabilidades", TABLE_CELL_B),
            Paragraph(
                "Lo que la clase sabe y lo que hace. Deben ser cohesivas y "
                "expresarse en lenguaje del dominio.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Colaboradores", TABLE_CELL_B),
            Paragraph(
                "Otras clases con las que trabaja para cumplir sus responsabilidades.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Trazabilidad", TABLE_CELL_B),
            Paragraph(
                "Archivo, tabla o función del proyecto donde se implementa la tarjeta.",
                TABLE_CELL,
            ),
        ],
    ]
    table = LongTable(anatomy, colWidths=[110, CONTENT_W - 110], repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)

    story += subsection("1.2 Cómo leer las tarjetas")
    story.append(
        Paragraph(
            "Cada tarjeta se identifica con un código CRC-01, CRC-02, etc. El "
            "color del encabezado indica la capa: azul para dominio, naranja "
            "para servicios y control, y violeta para fronteras de interfaz. "
            "El bloque de responsabilidades responde a “¿qué sabe y qué hace?” "
            "y el de colaboradores a “¿con quién trabaja?”.",
            BODY,
        )
    )
    story.append(
        Paragraph(
            "La sección de atributos y operaciones es representativa, no un "
            "contrato exhaustivo de la API. En las entidades de dominio se "
            "incluyen los campos de la tabla y las operaciones que las "
            "afectan; en los servicios y vistas se incluyen los métodos o "
            "funciones más relevantes.",
            BODY,
        )
    )

    story += subsection("1.3 Criterios de modelado")
    for text in [
        (
            "Las entidades de dominio representan conceptos del negocio y se "
            "corresponden con las tablas principales de SQLite."
        ),
        (
            "Los servicios y controles agrupan reglas que no pertenecen a una "
            "sola entidad: autenticación, movimientos, reportes, respaldo y "
            "escaneo."
        ),
        (
            "El repositorio se documenta como una fachada de persistencia; en el "
            "código es un módulo de funciones, no una jerarquía de clases."
        ),
        (
            "Las vistas se modelan como fronteras: capturan la intención del "
            "usuario, presentan datos y delegan la lógica en servicios o en el "
            "repositorio."
        ),
        (
            "La tarjeta CatalogosView agrupa SuppliersView, EmployeesView y "
            "VehiclesView porque comparten el mismo patrón de diseño; cada una "
            "conserva su entidad y su diálogo específico."
        ),
    ]:
        story.append(Paragraph(esc(text), BULLET, bulletText="•"))

    story.append(Spacer(1, 8))
    callout = Table(
        [
            [
                Paragraph(
                    "<b>Nota de alcance.</b> El documento prioriza las clases "
                    "con responsabilidades claras dentro del sistema. Los "
                    "widgets auxiliares y las funciones de formato se "
                    "mencionan como colaboradores, pero no reciben tarjeta "
                    "propia para evitar duplicar responsabilidades.",
                    SMALL,
                )
            ]
        ],
        colWidths=[CONTENT_W],
    )
    callout.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), SOFT),
                ("LINEBEFORE", (0, 0), (0, -1), 3, ORANGE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.append(callout)
    story.append(PageBreak())
    return story


def make_architecture():
    story = section("2. Arquitectura y capas")
    story.append(
        Paragraph(
            "El sistema sigue una separación práctica por capas. La interfaz "
            "no ejecuta SQL directamente: las vistas delegan en servicios o "
            "en el repositorio. Los servicios concentran reglas de negocio y "
            "los módulos de infraestructura resuelven la comunicación con "
            "SQLite, Outlook, WhatsApp y el teléfono.",
            BODY,
        )
    )
    layers = [
        [
            Paragraph("Capa", TABLE_HEAD),
            Paragraph("Responsabilidad", TABLE_HEAD),
            Paragraph("Componentes principales", TABLE_HEAD),
        ],
        [
            Paragraph("Frontera / UI", TABLE_CELL_B),
            Paragraph(
                "Capturar la intención del usuario, presentar datos y validar "
                "entradas de formulario.",
                TABLE_CELL,
            ),
            Paragraph(
                "App, Sidebar, LoginFrame, DashboardView, ProductsView, "
                "MovementsView, UsersView, SystemDataView, CatalogosView",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Servicios / Control", TABLE_CELL_B),
            Paragraph(
                "Coordinar reglas de negocio, transacciones, reportes, "
                "respaldo, configuración y escaneo.",
                TABLE_CELL,
            ),
            Paragraph(
                "AutenticacionService, ServicioMovimientos, ServicioReportes, "
                "RespaldoService, EscaneoMovilService, ConfiguracionReportes, "
                "NotificadorReportes",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Persistencia", TABLE_CELL_B),
            Paragraph(
                "Concentrar el acceso a SQLite, las consultas, la caché y la "
                "integridad transaccional.",
                TABLE_CELL,
            ),
            Paragraph("RepositorioDatos, ConexionBD", TABLE_CELL),
        ],
        [
            Paragraph("Infraestructura", TABLE_CELL_B),
            Paragraph(
                "Resolver la interacción con sistemas externos y utilidades "
                "del sistema operativo.",
                TABLE_CELL,
            ),
            Paragraph(
                "SQLite, Outlook, WhatsApp, navegador del teléfono, win_utils",
                TABLE_CELL,
            ),
        ],
    ]
    table = LongTable(
        layers,
        colWidths=[92, 185, CONTENT_W - 277],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(table)

    story += subsection("2.1 Flujo típico de una operación")
    flows = [
        [
            Paragraph("Paso", TABLE_HEAD),
            Paragraph("Origen", TABLE_HEAD),
            Paragraph("Secuencia", TABLE_HEAD),
        ],
        [
            Paragraph("1", TABLE_CELL_B),
            Paragraph("Login", TABLE_CELL_B),
            Paragraph(
                "LoginFrame → AutenticacionService → RepositorioDatos → App",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("2", TABLE_CELL_B),
            Paragraph("Navegación", TABLE_CELL_B),
            Paragraph("Sidebar → App → Vista solicitada", TABLE_CELL),
        ],
        [
            Paragraph("3", TABLE_CELL_B),
            Paragraph("Consulta", TABLE_CELL_B),
            Paragraph(
                "Vista → RepositorioDatos → SQLite → Vista",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("4", TABLE_CELL_B),
            Paragraph("Movimiento", TABLE_CELL_B),
            Paragraph(
                "MovementsView → ServicioMovimientos → RepositorioDatos",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("5", TABLE_CELL_B),
            Paragraph("Reporte", TABLE_CELL_B),
            Paragraph(
                "ServicioReportes → PDFExporter → NotificadorReportes",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("6", TABLE_CELL_B),
            Paragraph("Respaldo", TABLE_CELL_B),
            Paragraph("SystemDataView → RespaldoService → SQLite", TABLE_CELL),
        ],
    ]
    flow_table = LongTable(
        flows,
        colWidths=[40, 90, CONTENT_W - 130],
        repeatRows=1,
    )
    flow_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("GRID", (0, 0), (-1, -1), 0.35, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(flow_table)

    story += subsection("2.2 Principios aplicados")
    for text in [
        (
            "Separación de capas: la UI presenta y captura; los servicios "
            "deciden; el repositorio persiste."
        ),
        (
            "Repositorio como fachada: todas las consultas SQL viven en "
            "database/repository.py y la conexión se centraliza en connection.py."
        ),
        (
            "Atomicidad en movimientos: las operaciones de stock se ejecutan en "
            "una transacción para evitar inventarios inconsistentes."
        ),
        (
            "Vistas como fronteras: reciben current_user y app, y delegan la "
            "lógica en servicios o funciones del repositorio."
        ),
        (
            "Configuración externalizada: los destinos de reportes se guardan en "
            "%APPDATA%/DigiCable/config.json y las variables de entorno tienen "
            "prioridad."
        ),
        (
            "Bajo acoplamiento en escaneo: el servidor móvil deja los códigos en "
            "una cola y App los despacha a la vista interesada."
        ),
    ]:
        story.append(Paragraph(esc(text), BULLET, bulletText="•"))
    story.append(PageBreak())
    return story


def make_summary():
    story = section("3. Resumen y trazabilidad")
    story.append(
        Paragraph(
            "La siguiente tabla resume las 26 tarjetas y su correspondencia "
            "con el código. El orden coincide con el del documento: primero "
            "las entidades de dominio, luego los servicios y controles, y al "
            "final las fronteras de interfaz.",
            BODY,
        )
    )
    story.append(
        Paragraph(
            "<b>Distribución:</b> 9 entidades de dominio, 8 servicios o "
            "controles y 9 fronteras de interfaz.",
            SMALL,
        )
    )
    rows = [
        [
            Paragraph("N°", TABLE_HEAD),
            Paragraph("Tarjeta", TABLE_HEAD),
            Paragraph("Tipo", TABLE_HEAD),
            Paragraph("Capa", TABLE_HEAD),
            Paragraph("Implementación principal", TABLE_HEAD),
        ]
    ]
    for index, card in enumerate(CARDS, 1):
        rows.append(
            [
                Paragraph(f"{index:02d}", TABLE_CELL_B),
                Paragraph(esc(card["name"]), TABLE_CELL_B),
                Paragraph(esc(card["stereotype"]), TABLE_CELL),
                Paragraph(esc(card["layer"]), TABLE_CELL),
                Paragraph(esc(card["trace"]), TABLE_CELL),
            ]
        )
    table = LongTable(
        rows,
        colWidths=[28, 94, 58, 58, CONTENT_W - 238],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("GRID", (0, 0), (-1, -1), 0.3, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 4),
                ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(PageBreak())
    return story


def fit_card(card: dict, number: int, max_height: float):
    """Ajusta la tarjeta a una altura uniforme si su contenido es más corto."""
    table = build_card(card, number)
    _, height = table.wrap(CONTENT_W, max_height)
    if height < CARD_TARGET_H:
        table = build_card(card, number, extra_pad=CARD_TARGET_H - height)
        _, height = table.wrap(CONTENT_W, max_height)
    return table, height


def make_cards():
    story = section("4. Tarjetas CRC")
    story.append(
        Paragraph(
            "Las tarjetas se presentan en el mismo orden del resumen. Cada "
            "una cabe en una mitad de página; el encabezado identifica la "
            "tarjeta y su estereotipo, y el color indica la capa a la que "
            "pertenece. Las tarjetas se agrupan visualmente por capa, aunque "
            "el documento las numera de forma continua.",
            BODY,
        )
    )
    legend = Table(
        [
            [
                Paragraph("Dominio", TABLE_CELL_B),
                Paragraph("Servicios / control", TABLE_CELL_B),
                Paragraph("Fronteras de UI", TABLE_CELL_B),
            ],
            [
                Paragraph(
                    "Entidades del negocio y reglas de datos.",
                    TABLE_CELL,
                ),
                Paragraph(
                    "Coordinación, reglas de negocio y fachadas.",
                    TABLE_CELL,
                ),
                Paragraph(
                    "Pantallas, diálogos y coordinación de sesión.",
                    TABLE_CELL,
                ),
            ],
        ],
        colWidths=[CONTENT_W / 3] * 3,
    )
    legend.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), SOFT),
                ("LINEABOVE", (0, 0), (-1, 0), 3, CYAN),
                ("LINEABOVE", (1, 0), (1, 0), 3, ORANGE),
                ("LINEABOVE", (2, 0), (2, 0), 3, PURPLE),
                ("GRID", (0, 0), (-1, -1), 0.3, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(legend)
    story.append(Spacer(1, 10))

    # La primera tarjeta comparte la página con la introducción de la sección.
    first_card, first_height = fit_card(CARDS[0], 1, FRAME_H)
    if first_height > FRAME_H:
        print(
            f"ADVERTENCIA: la tarjeta 01 mide {first_height:.1f} pt "
            f"y no cabe en {FRAME_H} pt."
        )
    story.append(KeepTogether([first_card]))
    story.append(NextPageTemplate("cards"))
    story.append(PageBreak())

    for index, card in enumerate(CARDS[1:], 2):
        card_table, height = fit_card(card, index, CARD_FRAME_H)
        if height > CARD_FRAME_H:
            print(
                f"ADVERTENCIA: la tarjeta {index:02d} mide {height:.1f} pt "
                f"y no cabe en {CARD_FRAME_H} pt."
            )
        story.append(KeepTogether([card_table]))
        if index < len(CARDS):
            story.append(FrameBreak())

    story.append(NextPageTemplate("normal"))
    story.append(PageBreak())
    return story


def make_matrix():
    story = section("5. Matriz de colaboración")
    story.append(
        Paragraph(
            "La matriz resume las colaboraciones directas de cada tarjeta. "
            "Es una vista de consulta rápida: el detalle de cada relación "
            "está en la tarjeta correspondiente. Las relaciones no son "
            "necesariamente bidireccionales; indican quién solicita o recibe "
            "un servicio.",
            BODY,
        )
    )
    rows = [
        [
            Paragraph("N°", TABLE_HEAD),
            Paragraph("Tarjeta", TABLE_HEAD),
            Paragraph("Colaboradores principales", TABLE_HEAD),
        ]
    ]
    for index, card in enumerate(CARDS, 1):
        names = ", ".join(name for name, _ in card["collaborators"])
        rows.append(
            [
                Paragraph(f"{index:02d}", TABLE_CELL_B),
                Paragraph(esc(card["name"]), TABLE_CELL_B),
                Paragraph(esc(names), TABLE_CELL),
            ]
        )
    table = LongTable(
        rows,
        colWidths=[28, 112, CONTENT_W - 140],
        repeatRows=1,
    )
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("GRID", (0, 0), (-1, -1), 0.3, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(table)
    story.append(PageBreak())
    return story


def make_design_notes():
    story = section("6. Decisiones de diseño y observaciones")
    story.append(
        Paragraph(
            "Las tarjetas permiten leer el diseño desde las responsabilidades. "
            "Esta sección complementa esa lectura con las decisiones "
            "transversales, las fortalezas del diseño actual y los puntos que "
            "conviene mejorar si el sistema sigue creciendo.",
            BODY,
        )
    )

    story += subsection("6.1 Fortalezas")
    for text in [
        (
            "La separación entre UI, servicios y repositorio evita que las "
            "pantallas concentren SQL y facilita las pruebas de las reglas de "
            "negocio."
        ),
        (
            "Los movimientos se ejecutan en transacciones: el stock y el "
            "historial se actualizan juntos o no se actualiza ninguno."
        ),
        (
            "El detalle de movimiento conserva un snapshot de nombre, marca y "
            "seriales, lo que protege el historial ante cambios posteriores."
        ),
        (
            "La configuración de destinos de reportes está externalizada y las "
            "variables de entorno mantienen compatibilidad con despliegues."
        ),
        (
            "El respaldo usa la API de SQLite y crea una copia de seguridad antes "
            "de restaurar, reduciendo el riesgo de pérdida de datos."
        ),
        (
            "El escaneo móvil usa una cola y un token, lo que desacopla el "
            "navegador del teléfono de la ventana principal."
        ),
    ]:
        story.append(Paragraph(esc(text), BULLET, bulletText="•"))

    story += subsection("6.2 Riesgos y mejoras")
    for text in [
        (
            "database/repository.py concentra muchas responsabilidades. Conviene "
            "dividirlo por agregados (productos, movimientos, catálogos, "
            "usuarios) cuando el equipo crezca."
        ),
        (
            "ProductsView y MovementsView son vistas grandes. Extraer "
            "subcomponentes para filtros, tablas y diálogos reduciría su tamaño "
            "y aumentaría la reutilización."
        ),
        (
            "Las entidades se transportan como dicts o sqlite3.Row. Si se "
            "requiere una lógica de dominio más rica, los dataclasses serían un "
            "siguiente paso natural."
        ),
        (
            "La restricción de acceso a Usuarios y Datos del sistema se aplica "
            "en la UI. Conviene reforzarla también en los servicios para que no "
            "dependa solo de la pantalla."
        ),
        (
            "La integración con WhatsApp todavía usa wa.me y deja el PDF listo "
            "para adjuntar; la automatización completa de la app de escritorio "
            "sigue pendiente."
        ),
        (
            "La caché del repositorio es global. Al crecer el sistema conviene "
            "revisar su invalidación y considerar claves por usuario o por "
            "almacén."
        ),
    ]:
        story.append(Paragraph(esc(text), BULLET, bulletText="•"))

    story += subsection("6.3 Patrones y su aplicación")
    patterns = [
        [
            Paragraph("Patrón", TABLE_HEAD),
            Paragraph("Dónde se aplica", TABLE_HEAD),
            Paragraph("Beneficio", TABLE_HEAD),
        ],
        [
            Paragraph("Repository", TABLE_CELL_B),
            Paragraph("database/repository.py", TABLE_CELL),
            Paragraph(
                "Centraliza SQL y desacopla la UI de la persistencia.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Service Layer", TABLE_CELL_B),
            Paragraph(
                "AutenticacionService, ServicioMovimientos, ServicioReportes, "
                "RespaldoService",
                TABLE_CELL,
            ),
            Paragraph(
                "Agrupa reglas de negocio y coordina varios colaboradores.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("MVC-like", TABLE_CELL_B),
            Paragraph("App + vistas + repositorio/servicios", TABLE_CELL),
            Paragraph(
                "Separa presentación, coordinación y modelo de datos.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Producer / Consumer", TABLE_CELL_B),
            Paragraph("queue.Queue del escaneo móvil", TABLE_CELL),
            Paragraph(
                "Desacopla la recepción HTTP del procesamiento en la UI.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Strategy / Fallback", TABLE_CELL_B),
            Paragraph("email_report.py y whatsapp_report.py", TABLE_CELL),
            Paragraph(
                "Permite intentar Outlook y caer a mailto: o al portapapeles.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Snapshot", TABLE_CELL_B),
            Paragraph("movement_items", TABLE_CELL),
            Paragraph(
                "Conserva el estado del producto al momento del movimiento.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Facade", TABLE_CELL_B),
            Paragraph("App y RepositorioDatos", TABLE_CELL),
            Paragraph(
                "Simplifica el acceso a subsistemas y vistas.",
                TABLE_CELL,
            ),
        ],
    ]
    pattern_table = LongTable(
        patterns,
        colWidths=[112, 185, CONTENT_W - 297],
        repeatRows=1,
    )
    pattern_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("GRID", (0, 0), (-1, -1), 0.3, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(pattern_table)

    story += subsection("6.4 Conclusión")
    story.append(
        Paragraph(
            "El diseño de DigiCable combina un núcleo de persistencia estable "
            "con servicios que concentran las reglas críticas y una interfaz "
            "que actúa como frontera. Las tarjetas CRC muestran que las "
            "responsabilidades están razonablemente distribuidas y que las "
            "colaboraciones siguen un flujo comprensible. Las mejoras "
            "señaladas no cuestionan la arquitectura actual: preparan el "
            "sistema para crecer sin perder claridad.",
            BODY,
        )
    )
    return story


def make_glossary():
    story = section("7. Glosario y referencias")
    terms = [
        [
            Paragraph("Término", TABLE_HEAD),
            Paragraph("Definición", TABLE_HEAD),
        ],
        [
            Paragraph("CRC", TABLE_CELL_B),
            Paragraph(
                "Class-Responsibility-Collaboration: ficha de diseño con "
                "nombre, responsabilidades y colaboradores de una clase.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Entidad", TABLE_CELL_B),
            Paragraph(
                "Concepto del dominio con identidad y datos propios; suele "
                "corresponder a una tabla.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Frontera", TABLE_CELL_B),
            Paragraph(
                "Clase que interactúa con el usuario o con un sistema externo "
                "y traduce datos de entrada/salida.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Control", TABLE_CELL_B),
            Paragraph(
                "Clase que coordina el flujo de una operación y aplica reglas "
                "de negocio.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Servicio", TABLE_CELL_B),
            Paragraph(
                "Módulo o clase que ofrece una capacidad reutilizable, como "
                "autenticación, reportes o respaldo.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Repositorio", TABLE_CELL_B),
            Paragraph(
                "Fachada de acceso a datos que oculta el SQL y las "
                "particularidades de la base.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("DTO", TABLE_CELL_B),
            Paragraph(
                "Objeto de transferencia de datos; en este proyecto se usan "
                "dicts y sqlite3.Row.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Snapshot", TABLE_CELL_B),
            Paragraph(
                "Copia del estado de un dato en un momento determinado; por "
                "ejemplo, los ítems de un movimiento.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("WAL", TABLE_CELL_B),
            Paragraph(
                "Write-Ahead Logging: modo de SQLite que usa archivos -wal y "
                "-shm y debe consolidarse antes de copiar la base.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Fallback", TABLE_CELL_B),
            Paragraph(
                "Mecanismo alternativo cuando falla el principal; por "
                "ejemplo, mailto: si Outlook no está disponible.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Transacción", TABLE_CELL_B),
            Paragraph(
                "Unidad de trabajo atómica: se confirma completa o se "
                "revierte completa.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Caché", TABLE_CELL_B),
            Paragraph(
                "Copia temporal de consultas frecuentes para evitar volver a "
                "la base en cada lectura.",
                TABLE_CELL,
            ),
        ],
        [
            Paragraph("Rol", TABLE_CELL_B),
            Paragraph(
                "Perfil de permisos del usuario; en el sistema diferencia "
                "administrador y supervisor.",
                TABLE_CELL,
            ),
        ],
    ]
    new_glossary_table = LongTable(
        terms,
        colWidths=[92, CONTENT_W - 92],
        repeatRows=1,
    )
    new_glossary_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), white),
                ("GRID", (0, 0), (-1, -1), 0.3, GRID),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, SOFT]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    story.append(new_glossary_table)

    story += subsection("7.1 Referencias del código")
    for text in [
        "Interfaz y navegación: ui/app.py, ui/sidebar.py, ui/login_frame.py.",
        (
            "Vistas: ui/views/dashboard.py, products.py, movements.py, users.py, "
            "system_data.py, suppliers.py, employees.py y vehicles.py."
        ),
        (
            "Servicios: core/auth.py, core/database_backup.py, "
            "core/report_config.py, core/email_report.py, "
            "core/whatsapp_report.py y core/phone_scan.py."
        ),
        "Persistencia: database/connection.py y database/repository.py.",
        "Exportación: core/export.py y core/pdf_export.py.",
        "Esquema: inventory.db (SQLite).",
    ]:
        story.append(Paragraph(esc(text), BULLET, bulletText="•"))

    story.append(Spacer(1, 12))
    story.append(
        Paragraph(
            "Documento generado el 08/11/2026 para el Sistema de Control de "
            "Inventarios DigiCable. Las tarjetas se basan en la implementación "
            "del repositorio y pueden actualizarse con el script "
            "scripts/generate_crc_pdf.py.",
            SMALL,
        )
    )
    return story


def _md_cell(text: object) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def render_markdown() -> str:
    """Genera una fuente Markdown editable a partir de las mismas tarjetas."""
    lines = [
        "# Tarjetas CRC — Sistema DigiCable",
        "",
        "**Diseño de Software Orientado a Objetos**",
        "",
        "Versión 1.0 · 08/11/2026",
        "",
        (
            "Documento con 26 tarjetas CRC: 9 entidades de dominio, 8 servicios "
            "o controles y 9 fronteras de interfaz. La versión PDF incluye "
            "portada, índice, arquitectura por capas, matriz de colaboración, "
            "decisiones de diseño y glosario."
        ),
        "",
        "## Resumen y trazabilidad",
        "",
        "| N° | Tarjeta | Tipo | Capa | Implementación principal |",
        "|---|---|---|---|---|",
    ]
    for index, card in enumerate(CARDS, 1):
        lines.append(
            f"| {index:02d} | {_md_cell(card['name'])} | "
            f"{_md_cell(card['stereotype'])} | {_md_cell(card['layer'])} | "
            f"{_md_cell(card['trace'])} |"
        )

    lines += ["", "## Tarjetas CRC", ""]
    for index, card in enumerate(CARDS, 1):
        lines += [
            f"### CRC-{index:02d} · {card['name']}",
            "",
            f"**Tipo:** {card['stereotype']} · **Capa:** {card['layer']}",
            "",
            f"**Propósito:** {card['purpose']}",
            "",
            "**Responsabilidades (sabe / hace)**",
            "",
        ]
        for item in card["responsibilities"]:
            lines.append(f"- {item}")
        lines += ["", "**Colaboradores (con quién trabaja)**", ""]
        for name, role in card["collaborators"]:
            lines.append(f"- **{name}** — {role}")
        lines += [
            "",
            f"**Atributos / operaciones:** {card['attributes']}",
            "",
            f"**Trazabilidad:** {card['trace']}",
            "",
        ]

    lines += [
        "## Matriz de colaboración",
        "",
        "| N° | Tarjeta | Colaboradores principales |",
        "|---|---|---|",
    ]
    for index, card in enumerate(CARDS, 1):
        names = ", ".join(name for name, _ in card["collaborators"])
        lines.append(f"| {index:02d} | {_md_cell(card['name'])} | {_md_cell(names)} |")
    lines += [
        "",
        "## Notas de diseño",
        "",
        (
            "- La separación UI / servicios / repositorio mantiene la lógica de "
            "negocio fuera de las pantallas."
        ),
        (
            "- Los movimientos usan transacciones para actualizar stock e "
            "historial de forma atómica."
        ),
        "- El detalle de movimiento conserva un snapshot de los productos.",
        (
            "- La configuración de reportes se externaliza en "
            "`%APPDATA%/DigiCable/config.json`."
        ),
        (
            "- El respaldo usa la API de SQLite y crea una copia de seguridad "
            "antes de restaurar."
        ),
        (
            "- La automatización completa de WhatsApp Desktop sigue pendiente; "
            "el flujo actual abre `wa.me` y deja el PDF listo para adjuntar."
        ),
        "",
        "## Referencias",
        "",
        "- `ui/app.py`, `ui/sidebar.py`, `ui/login_frame.py`",
        "- `ui/views/*.py`",
        (
            "- `core/auth.py`, `core/database_backup.py`, "
            "`core/report_config.py`, `core/email_report.py`, "
            "`core/whatsapp_report.py`, `core/phone_scan.py`"
        ),
        "- `database/connection.py`, `database/repository.py`",
        "- `core/export.py`, `core/pdf_export.py`",
        "",
    ]
    return "\n".join(lines)


def build(out_path: str) -> None:
    doc = make_doc(out_path)
    story = []
    story.extend(make_cover())
    story.extend(make_toc(doc))
    story.extend(make_intro())
    story.extend(make_architecture())
    story.extend(make_summary())
    story.extend(make_cards())
    story.extend(make_matrix())
    story.extend(make_design_notes())
    story.extend(make_glossary())
    doc.multiBuild(story)


def main() -> None:
    out_path = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    build(out_path)

    os.makedirs(os.path.dirname(DEFAULT_MD), exist_ok=True)
    with open(DEFAULT_MD, "w", encoding="utf-8") as handle:
        handle.write(render_markdown())

    if os.path.abspath(out_path) == os.path.abspath(DEFAULT_OUT):
        os.makedirs(os.path.dirname(DESKTOP), exist_ok=True)
        shutil.copyfile(out_path, DESKTOP)
        print(f"Copia en Escritorio: {DESKTOP}")

    print(f"PDF: {out_path}")
    print(f"Markdown: {DEFAULT_MD}")


if __name__ == "__main__":
    main()

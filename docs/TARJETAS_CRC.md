# Tarjetas CRC — Sistema DigiCable

**Diseño de Software Orientado a Objetos**

Versión 1.0 · 08/11/2026

Documento con 26 tarjetas CRC: 9 entidades de dominio, 8 servicios o controles y 9 fronteras de interfaz. La versión PDF incluye portada, índice, arquitectura por capas, matriz de colaboración, decisiones de diseño y glosario.

## Resumen y trazabilidad

| N° | Tarjeta | Tipo | Capa | Implementación principal |
|---|---|---|---|---|
| 01 | Usuario | Entidad | Dominio | Tabla users · core/auth.py · ui/views/users.py · ui/sidebar.py |
| 02 | Almacen | Entidad | Dominio | Tabla warehouses · get_all_warehouses · App.current_warehouse_id |
| 03 | Producto | Entidad | Dominio | Tabla products · get_products_grouped · create_product · update_product · ui/views/products.py |
| 04 | UnidadInventario | Entidad | Dominio | Filas de products con serial/MAC · get_units_by_model · lookup_product_by_code · _ChildRow |
| 05 | Movimiento | Entidad | Dominio | Tabla movements · create_movement · create_compound_movement · update_movement · delete_movement |
| 06 | DetalleMovimiento | Entidad | Dominio | Tabla movement_items · _attach_item_summaries · get_movement_detail · export_single_movement |
| 07 | Proveedor | Entidad | Dominio | Tabla suppliers · CRUD en repository.py · ui/views/suppliers.py |
| 08 | Empleado | Entidad | Dominio | Tabla employees · CRUD en repository.py · ui/views/employees.py |
| 09 | Vehiculo | Entidad | Dominio | Tabla vehicles · CRUD en repository.py · ui/views/vehicles.py · catálogo independiente de movements |
| 10 | AutenticacionService | Servicio | Servicios | core/auth.py · tabla users · ui/login_frame.py |
| 11 | RepositorioDatos | Repositorio | Servicios | database/repository.py · database/connection.py · módulo de funciones que actúa como fachada de persistencia |
| 12 | ServicioMovimientos | Control | Servicios | database/repository.py · ui/views/movements.py · parte de la lógica vive en el repositorio para asegurar atomicidad |
| 13 | ServicioReportes | Control | Servicios | ui/views/movements.py · core/export.py · core/pdf_export.py · ui/dashboard_widgets.py |
| 14 | RespaldoService | Servicio | Servicios | core/database_backup.py · ui/views/system_data.py |
| 15 | EscaneoMovilService | Servicio | Servicios | core/phone_scan.py · ui/app.py (_poll_scan_queue, _dispatch_scan) |
| 16 | ConfiguracionReportes | Servicio | Servicios | core/report_config.py · %APPDATA%/DigiCable/config.json · REPORT_EMAIL_TO y WHATSAPP_TO |
| 17 | NotificadorReportes | Servicio | Servicios | core/email_report.py · core/whatsapp_report.py · core/win_utils.py |
| 18 | App | Coordinador | Interfaz | ui/app.py · _on_login · _navigate · _on_warehouse_change_by_name · _poll_scan_queue · _dispatch_scan · _logout |
| 19 | Sidebar | Frontera | Interfaz | ui/sidebar.py · _nav · _slide_indicator · _on_button_enter |
| 20 | LoginFrame | Frontera | Interfaz | ui/login_frame.py · core/auth.py · _ForceChangePasswordDialog |
| 21 | DashboardView | Frontera | Interfaz | ui/views/dashboard.py · ui/dashboard_widgets.py |
| 22 | ProductsView | Frontera | Interfaz | ui/views/products.py · database/repository.py · core/phone_scan.py |
| 23 | MovementsView | Frontera | Interfaz | ui/views/movements.py · database/repository.py · core/export.py |
| 24 | UsersView | Frontera | Interfaz | ui/views/users.py · database/repository.py · core/auth.py |
| 25 | SystemDataView | Frontera | Interfaz | ui/views/system_data.py · core/database_backup.py |
| 26 | CatalogosView | Frontera | Interfaz | ui/views/suppliers.py · ui/views/employees.py · ui/views/vehicles.py · patrón compartido de vista de catálogo |

## Tarjetas CRC

### CRC-01 · Usuario

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Representar a la persona que inicia sesión y determinar sus permisos dentro del sistema.

**Responsabilidades (sabe / hace)**

- Conocer su identificador, nombre de usuario, rol y estado de cambio de contraseña.
- Diferenciar el rol administrador del rol supervisor para habilitar acciones.
- Solicitar la validación de credenciales y el cambio de contraseña.
- Servir como contexto de seguridad para las vistas y operaciones.

**Colaboradores (con quién trabaja)**

- **AutenticacionService** — valida credenciales y actualiza la contraseña.
- **App** — conserva current_user y controla el ciclo de sesión.
- **Sidebar** — muestra el usuario, su rol y las opciones permitidas.
- **UsersView / _UserDialog** — administra altas, edición y baja de usuarios.
- **RepositorioDatos** — persiste la tabla users.

**Atributos / operaciones:** id, username, role, password_hash, must_change_password

**Trazabilidad:** Tabla users · core/auth.py · ui/views/users.py · ui/sidebar.py

### CRC-02 · Almacen

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Representar una ubicación física u organizacional que agrupa inventario y movimientos.

**Responsabilidades (sabe / hace)**

- Conocer su identificador, nombre y ubicación.
- Delimitar las consultas de productos, movimientos y estadísticas.
- Ser seleccionado como almacén activo de la sesión.
- Separar el inventario entre almacén Central y Secundario.

**Colaboradores (con quién trabaja)**

- **App** — lo selecciona y conserva como almacén activo.
- **Producto** — clasifica cada unidad o modelo por almacén.
- **Movimiento** — registra el almacén donde ocurrió el cambio.
- **RepositorioDatos** — consulta y filtra por warehouse_id.
- **DashboardView / ProductsView / MovementsView** — aplican el filtro.

**Atributos / operaciones:** id, name, location

**Trazabilidad:** Tabla warehouses · get_all_warehouses · App.current_warehouse_id

### CRC-03 · Producto

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Representar un ítem o modelo inventariable, controlado por cantidad o por unidades serializadas.

**Responsabilidades (sabe / hace)**

- Conocer nombre, marca, modelo, código, serial/MAC, cantidad, unidad, estado, proveedor y almacén.
- Determinar si está disponible, no disponible o inactivo.
- Agrupar sus unidades por nombre y marca para la vista de inventario.
- Validar la disponibilidad de stock antes de una salida o asignación.
- Conservar la trazabilidad de sus cambios y de su proveedor.

**Colaboradores (con quién trabaja)**

- **UnidadInventario** — representa cada unidad física del modelo.
- **Movimiento / DetalleMovimiento** — registran entradas y salidas.
- **Proveedor** — identifica el origen del producto.
- **Almacen** — ubica el stock en una sede.
- **RepositorioDatos** — persiste y consulta la tabla products.
- **ProductsView / _RegistrarProductoDialog** — lo muestran y editan.

**Atributos / operaciones:** id, name, brand, modelo, barcode, serial, mac, quantity, unit, status, supplier_id, warehouse_id

**Trazabilidad:** Tabla products · get_products_grouped · create_product · update_product · ui/views/products.py

### CRC-04 · UnidadInventario

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Representar una unidad física individual, especialmente cuando el producto se controla por serial o MAC.

**Responsabilidades (sabe / hace)**

- Conocer serial, MAC, código de barras, estado y fecha de registro.
- Permitir la rastreabilidad de una unidad dentro de un modelo.
- Reflejar si la unidad está disponible, no disponible o inactiva.
- Colaborar con el escaneo para localizar y seleccionar la unidad.

**Colaboradores (con quién trabaja)**

- **Producto** — define el modelo al que pertenece la unidad.
- **DetalleMovimiento** — conserva el serial afectado por el movimiento.
- **ProductsView / _ChildRow** — la muestran dentro del grupo expandido.
- **_ScanResultDialog** — la localiza a partir de un código escaneado.
- **RepositorioDatos** — consulta por serial, MAC o código de barras.

**Atributos / operaciones:** id, serial, mac, barcode, status, created_at

**Trazabilidad:** Filas de products con serial/MAC · get_units_by_model · lookup_product_by_code · _ChildRow

### CRC-05 · Movimiento

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Registrar un cambio de inventario: entrada, salida, devolución, asignación, modificación o eliminación.

**Responsabilidades (sabe / hace)**

- Conocer tipo, fecha, cantidad, notas, almacén, usuario y empleado.
- Aplicar o revertir el efecto del movimiento sobre el stock.
- Validar que exista stock suficiente en salidas y asignaciones.
- Agrupar varios productos o unidades en un movimiento compuesto.
- Mantener el historial y la auditoría de cada cambio.

**Colaboradores (con quién trabaja)**

- **DetalleMovimiento** — guarda el desglose por producto o unidad.
- **Producto** — recibe el ajuste de cantidad y estado.
- **Empleado** — recibe o devuelve los equipos.
- **Usuario** — identifica quién autorizó el movimiento.
- **Almacen** — indica la sede del cambio.
- **ServicioMovimientos** — coordina reglas y transacciones.
- **MovementsView** — lo lista, filtra y muestra en detalle.

**Atributos / operaciones:** id, type, product_id, employee_id, user_id, quantity, notes, timestamp, warehouse_id

**Trazabilidad:** Tabla movements · create_movement · create_compound_movement · update_movement · delete_movement

### CRC-06 · DetalleMovimiento

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Guardar el desglose por producto o unidad de un movimiento compuesto y preservar el snapshot histórico.

**Responsabilidades (sabe / hace)**

- Conocer movement_id, product_id, nombre, marca, cantidad, unidad y seriales.
- Permitir que un movimiento incluya varios productos o unidades.
- Conservar los datos aunque el producto cambie o se elimine.
- Alimentar los reportes y comprobantes de movimiento.

**Colaboradores (con quién trabaja)**

- **Movimiento** — es su cabecera y le da contexto.
- **Producto** — referencia el ítem original del detalle.
- **ServicioMovimientos** — lo crea y lo adjunta a la transacción.
- **RepositorioDatos** — persiste la tabla movement_items.
- **ServicioReportes / PDFExporter** — lo incluyen en los PDF.

**Atributos / operaciones:** id, movement_id, product_id, name, brand, qty, unit, seriales

**Trazabilidad:** Tabla movement_items · _attach_item_summaries · get_movement_detail · export_single_movement

### CRC-07 · Proveedor

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Representar la empresa o persona que suministra productos.

**Responsabilidades (sabe / hace)**

- Conocer nombre, contacto y RIF.
- Asociarse a uno o varios productos del inventario.
- Mantener un catálogo consultable y editable.
- Validar los datos obligatorios antes de guardar.

**Colaboradores (con quién trabaja)**

- **Producto** — referencia al proveedor que lo suministra.
- **RepositorioDatos** — persiste la tabla suppliers.
- **SuppliersView** — lo lista y administra.
- **_SupplierDialog** — captura y valida sus datos.
- **ProductsView** — lo muestra y permite seleccionarlo.

**Atributos / operaciones:** id, name, contact, rif, created_at

**Trazabilidad:** Tabla suppliers · CRUD en repository.py · ui/views/suppliers.py

### CRC-08 · Empleado

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Representar al colaborador que recibe, devuelve o tiene asignado un equipo.

**Responsabilidades (sabe / hace)**

- Conocer nombre, cédula y cargo.
- Asociarse a movimientos de salida, asignación y devolución.
- Mantener un catálogo de empleados actualizado.
- Validar que la cédula sea única.

**Colaboradores (con quién trabaja)**

- **Movimiento** — lo referencia como receptor o responsable.
- **RepositorioDatos** — persiste la tabla employees.
- **EmployeesView** — lo lista y administra.
- **_EmpDialog** — captura y valida sus datos.
- **MovementsView** — lo muestra en el detalle del movimiento.

**Atributos / operaciones:** id, name, cedula, cargo, created_at

**Trazabilidad:** Tabla employees · CRUD en repository.py · ui/views/employees.py

### CRC-09 · Vehiculo

**Tipo:** Entidad · **Capa:** Dominio

**Propósito:** Representar un vehículo de la empresa dentro del catálogo de apoyo logístico.

**Responsabilidades (sabe / hace)**

- Conocer marca, modelo y placa.
- Mantener un registro consultable y editable.
- Validar que la placa esté presente y sea única.
- Servir como catálogo para futuras asignaciones de transporte.

**Colaboradores (con quién trabaja)**

- **RepositorioDatos** — persiste la tabla vehicles.
- **VehiclesView** — lo lista y administra.
- **_VehicleDialog** — captura y valida sus datos.

**Atributos / operaciones:** id, brand, model, plate, created_at

**Trazabilidad:** Tabla vehicles · CRUD en repository.py · ui/views/vehicles.py · catálogo independiente de movements

### CRC-10 · AutenticacionService

**Tipo:** Servicio · **Capa:** Servicios

**Propósito:** Validar la identidad de los usuarios y gestionar sus contraseñas.

**Responsabilidades (sabe / hace)**

- Verificar la combinación de nombre de usuario y contraseña.
- Generar y comprobar hashes PBKDF2 con sal.
- Migrar hashes legacy SHA-256 en el siguiente inicio de sesión.
- Cambiar la contraseña y limpiar must_change_password.
- Devolver el usuario autenticado o un error comprensible.

**Colaboradores (con quién trabaja)**

- **Usuario** — aporta credenciales y rol.
- **RepositorioDatos** — consulta y actualiza la tabla users.
- **LoginFrame** — captura las credenciales y muestra el error.
- **_ForceChangePasswordDialog** — solicita la nueva contraseña.
- **App** — recibe el usuario autenticado e inicia la sesión.

**Atributos / operaciones:** hash_password · verify_password · login · change_password

**Trazabilidad:** core/auth.py · tabla users · ui/login_frame.py

### CRC-11 · RepositorioDatos

**Tipo:** Repositorio · **Capa:** Servicios

**Propósito:** Centralizar el acceso a SQLite y encapsular consultas, transacciones y caché.

**Responsabilidades (sabe / hace)**

- Abrir y cerrar conexiones de forma segura.
- Ejecutar el CRUD de usuarios, productos, movimientos y catálogos.
- Aplicar filtros, búsquedas, paginación y ordenamientos.
- Calcular estadísticas, rankings y resúmenes del dashboard.
- Mantener la integridad transaccional y invalidar la caché.

**Colaboradores (con quién trabaja)**

- **ConexionBD** — proporciona la conexión y el esquema.
- **Todas las entidades** — persisten y recuperan sus datos.
- **ServicioMovimientos** — realiza operaciones atómicas de stock.
- **ServicioReportes** — obtiene consultas planas para los PDF.
- **Vistas de la UI** — solicitan listados y resúmenes.

**Atributos / operaciones:** get_all_* · create_* · update_* · delete_* · get_dashboard_stats · get_movements_flat · clear_cache

**Trazabilidad:** database/repository.py · database/connection.py · módulo de funciones que actúa como fachada de persistencia

### CRC-12 · ServicioMovimientos

**Tipo:** Control · **Capa:** Servicios

**Propósito:** Coordinar las reglas de negocio de movimientos, stock y transacciones.

**Responsabilidades (sabe / hace)**

- Crear movimientos simples y compuestos.
- Validar stock y aplicar o revertir cantidades.
- Editar y eliminar movimientos con rollback ante errores.
- Registrar movimientos de modificación y eliminación.
- Agrupar varios ítems en una sola operación atómica.

**Colaboradores (con quién trabaja)**

- **Movimiento / DetalleMovimiento** — son el objeto de la operación.
- **Producto** — recibe el ajuste de cantidad y estado.
- **RepositorioDatos** — ejecuta SQL y confirma la transacción.
- **MovementsView** — inicia el registro, edición o borrado.
- **_MovementDialog / _MovementEditDialog** — capturan los datos.

**Atributos / operaciones:** create_movement · create_compound_movement · apply_movement_stock · revert_movement_stock · update_movement · delete_movement

**Trazabilidad:** database/repository.py · ui/views/movements.py · parte de la lógica vive en el repositorio para asegurar atomicidad

### CRC-13 · ServicioReportes

**Tipo:** Control · **Capa:** Servicios

**Propósito:** Generar reportes PDF y coordinar su entrega por correo o WhatsApp.

**Responsabilidades (sabe / hace)**

- Calcular rangos diario, semanal, mensual y personalizado.
- Filtrar por tipo, fecha, almacén y selección de movimientos.
- Construir PDF de movimientos, inventario, ranking y cierre crítico.
- Generar el comprobante individual de un movimiento.
- Delegar el envío al notificador y reportar errores al usuario.

**Colaboradores (con quién trabaja)**

- **MovementsView / _ReportsDialog** — solicitan y configuran el reporte.
- **RepositorioDatos** — entrega los datos planos.
- **PDFExporter** — renderiza el documento PDF.
- **NotificadorReportes** — envía por correo o WhatsApp.
- **ConfiguracionReportes** — resuelve los destinos.
- **DashboardView / _MovementInfoDialog** — usan reportes puntuales.

**Atributos / operaciones:** report_date_range · split_ranking · export_movements · export_inventory · export_product_ranking · export_critical_closing

**Trazabilidad:** ui/views/movements.py · core/export.py · core/pdf_export.py · ui/dashboard_widgets.py

### CRC-14 · RespaldoService

**Tipo:** Servicio · **Capa:** Servicios

**Propósito:** Crear y restaurar copias de seguridad consistentes de la base de datos.

**Responsabilidades (sabe / hace)**

- Crear un respaldo usando la API de backup de SQLite.
- Validar que el archivo sea SQLite y contenga las tablas esperadas.
- Crear un respaldo de seguridad antes de restaurar.
- Restaurar la base y limpiar los archivos sidecar -wal y -shm.
- Recargar el esquema y la caché después de la restauración.

**Colaboradores (con quién trabaja)**

- **SystemDataView** — ofrece las acciones de respaldo y carga.
- **RepositorioDatos** — invalida la caché y vuelve a consultar.
- **ConexionBD** — abre la base y ejecuta initialize_db.
- **SQLite** — proporciona la copia consistente y la validación.

**Atributos / operaciones:** create_backup · validate_database · create_safety_backup · restore_database

**Trazabilidad:** core/database_backup.py · ui/views/system_data.py

### CRC-15 · EscaneoMovilService

**Tipo:** Servicio · **Capa:** Servicios

**Propósito:** Recibir códigos escaneados desde un teléfono conectado a la red local.

**Responsabilidades (sabe / hace)**

- Iniciar un servidor HTTP local y generar un token de sesión.
- Servir la página de escaneo y el código QR de acceso.
- Validar el token de cada código recibido.
- Encolar los códigos para que la interfaz los procese.
- Exponer la URL local que debe abrir el teléfono.

**Colaboradores (con quién trabaja)**

- **App** — consume la cola y despacha los códigos a las vistas.
- **ProductsView** — recibe el código y busca el producto.
- **_BarcodeScanDialog** — muestra el resultado del escaneo.
- **_ScanRowDialog / _PhoneScanHelpDialog** — guían al usuario.

**Atributos / operaciones:** start_scan_server · generate_token · make_qr_pil · get_lan_ip

**Trazabilidad:** core/phone_scan.py · ui/app.py (_poll_scan_queue, _dispatch_scan)

### CRC-16 · ConfiguracionReportes

**Tipo:** Servicio · **Capa:** Servicios

**Propósito:** Persistir y normalizar los destinos de correo y WhatsApp.

**Responsabilidades (sabe / hace)**

- Leer y escribir el archivo config.json del usuario.
- Normalizar números de teléfono y códigos de país.
- Aplicar las variables de entorno con prioridad sobre el archivo.
- Informar si un destino proviene de una variable de entorno.
- Validar que exista un destino antes de intentar enviar.

**Colaboradores (con quién trabaja)**

- **NotificadorReportes** — consulta los destinos configurados.
- **_DestinationsDialog** — permite editarlos desde la interfaz.
- **ServicioReportes** — solicita el destino al enviar.

**Atributos / operaciones:** config_file · load_config · save_config · normalize_phone · get_email_to · get_whatsapp_to · set_destinations

**Trazabilidad:** core/report_config.py · %APPDATA%/DigiCable/config.json · REPORT_EMAIL_TO y WHATSAPP_TO

### CRC-17 · NotificadorReportes

**Tipo:** Servicio · **Capa:** Servicios

**Propósito:** Entregar los reportes PDF por correo electrónico o WhatsApp, con mecanismos de respaldo.

**Responsabilidades (sabe / hace)**

- Abrir Outlook con el PDF ya adjunto y el correo preparado.
- Usar mailto:, portapapeles y Explorador si Outlook falla.
- Abrir WhatsApp con el mensaje y dejar el PDF listo para adjuntar.
- Copiar el archivo al portapapeles y revelarlo en el Explorador.
- Informar claramente si falta un destino o falla el cliente.

**Colaboradores (con quién trabaja)**

- **ServicioReportes** — le entrega la ruta del PDF y el asunto.
- **ConfiguracionReportes** — resuelve correo y WhatsApp destino.
- **Outlook** — crea el correo con adjunto mediante COM.
- **WhatsApp / navegador** — abre el chat mediante wa.me.
- **win_utils** — copia archivos y revela rutas en Windows.

**Atributos / operaciones:** send_report_email · send_report_whatsapp

**Trazabilidad:** core/email_report.py · core/whatsapp_report.py · core/win_utils.py

### CRC-18 · App

**Tipo:** Coordinador · **Capa:** Interfaz

**Propósito:** Ventana principal y coordinador de sesión, navegación, almacén activo y escaneo móvil.

**Responsabilidades (sabe / hace)**

- Mostrar el login y conservar el usuario autenticado.
- Mantener el almacén activo y notificar cambios a las vistas.
- Construir el sidebar y crear o reutilizar las vistas.
- Invalidar vistas cuando cambia el almacén o la sesión.
- Consumir la cola de escaneo y despachar los códigos.
- Cerrar la sesión y volver al login.

**Colaboradores (con quién trabaja)**

- **LoginFrame** — le entrega el usuario autenticado.
- **Sidebar** — solicita navegación y cierre de sesión.
- **Vistas de la app** — las instancia y les inyecta current_user/app.
- **RepositorioDatos** — consulta almacenes y datos de sesión.
- **EscaneoMovilService** — inicia el servidor y llena la cola.

**Atributos / operaciones:** current_user, current_warehouse_id, _views, _warehouses, scan_url, _scan_queue

**Trazabilidad:** ui/app.py · _on_login · _navigate · _on_warehouse_change_by_name · _poll_scan_queue · _dispatch_scan · _logout

### CRC-19 · Sidebar

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Menú lateral de navegación y control de la sesión.

**Responsabilidades (sabe / hace)**

- Construir las opciones de navegación de la aplicación.
- Mostrar Usuarios y Datos del sistema solo al administrador.
- Resaltar la opción activa y animar el indicador.
- Mostrar el nombre y el rol del usuario conectado.
- Solicitar el cierre de sesión.

**Colaboradores (con quién trabaja)**

- **App** — recibe la orden de navegar o cerrar sesión.
- **Usuario** — aporta nombre y rol para filtrar opciones.
- **Vistas** — son el destino de cada opción del menú.

**Atributos / operaciones:** _buttons, _active, on_navigate, on_logout

**Trazabilidad:** ui/sidebar.py · _nav · _slide_indicator · _on_button_enter

### CRC-20 · LoginFrame

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Capturar las credenciales y iniciar la sesión del usuario.

**Responsabilidades (sabe / hace)**

- Validar que usuario y contraseña no estén vacíos.
- Solicitar la autenticación al servicio correspondiente.
- Mostrar un error claro si las credenciales fallan.
- Forzar el cambio de contraseña cuando must_change_password está activo.
- Notificar el éxito a App con el usuario autenticado.

**Colaboradores (con quién trabaja)**

- **AutenticacionService** — valida las credenciales.
- **_ForceChangePasswordDialog** — gestiona el cambio obligatorio.
- **App** — recibe el usuario y abre la ventana principal.
- **Usuario** — es el resultado de un login exitoso.

**Atributos / operaciones:** on_login_success · _do_login · campos de usuario y clave

**Trazabilidad:** ui/login_frame.py · core/auth.py · _ForceChangePasswordDialog

### CRC-21 · DashboardView

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Mostrar un resumen visual del inventario y accesos rápidos a las operaciones principales.

**Responsabilidades (sabe / hace)**

- Mostrar métricas de disponibles, entradas, salidas y devoluciones.
- Cargar estadísticas en segundo plano sin bloquear la interfaz.
- Listar los movimientos recientes y abrir su detalle.
- Navegar a productos o movimientos con filtros predefinidos.
- Imprimir el detalle de un movimiento cuando se solicite.

**Colaboradores (con quién trabaja)**

- **App** — recibe las solicitudes de navegación.
- **RepositorioDatos** — entrega estadísticas y movimientos recientes.
- **ServicioReportes** — genera el PDF del detalle.
- **_MovementInfoDialog** — muestra el detalle del movimiento.
- **ProductsView / MovementsView** — son los destinos de navegación.

**Atributos / operaciones:** _load_gen, _load_queue, refresh, _apply_stats, _go

**Trazabilidad:** ui/views/dashboard.py · ui/dashboard_widgets.py

### CRC-22 · ProductsView

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Gestionar el inventario de productos y sus unidades.

**Responsabilidades (sabe / hace)**

- Listar productos agrupados por nombre y marca.
- Buscar y filtrar por estado, almacén o texto.
- Expandir un grupo para ver y operar sus unidades.
- Crear, editar, eliminar y reactivar productos.
- Escanear códigos y localizar el producto o unidad.
- Exportar el inventario a PDF y mostrar la ayuda de escaneo móvil.

**Colaboradores (con quién trabaja)**

- **Producto / UnidadInventario** — son los datos que muestra y edita.
- **Proveedor** — se selecciona al registrar un producto.
- **RepositorioDatos** — ejecuta consultas y cambios.
- **_GroupRow / _ChildRow** — renderizan grupos y unidades.
- **_RegistrarProductoDialog / _ProductDialog** — capturan altas y ediciones.
- **_GroupEditDialog / _ScanResultDialog** — gestionan grupos y escaneos.
- **_BarcodeScanDialog / _PhoneScanHelpDialog** — apoyan el escaneo.
- **App / EscaneoMovilService** — entregan los códigos escaneados.

**Atributos / operaciones:** _selected_id, _expanded, _render_gen, refresh, _add_dialog, _edit_dialog, _delete, _export_pdf, _scan_barcode

**Trazabilidad:** ui/views/products.py · database/repository.py · core/phone_scan.py

### CRC-23 · MovementsView

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Gestionar y consultar los movimientos de inventario.

**Responsabilidades (sabe / hace)**

- Listar, paginar y filtrar movimientos por tipo, fecha y texto.
- Mostrar chips, conteos y el detalle de cada movimiento.
- Registrar, editar y eliminar movimientos.
- Seleccionar productos y empleados en los diálogos de alta.
- Abrir reportes y actualizar los totales después de cada cambio.

**Colaboradores (con quién trabaja)**

- **Movimiento / DetalleMovimiento** — son los datos que lista y edita.
- **Producto / Empleado** — se seleccionan al registrar un movimiento.
- **ServicioMovimientos** — ejecuta las reglas de stock.
- **ServicioReportes** — genera los reportes y comprobantes.
- **RepositorioDatos** — consulta y persiste los movimientos.
- **_MovementDialog / _MovementEditDialog** — capturan los datos.
- **_MovementInfoDialog / _ReportsDialog** — muestran detalle y reportes.
- **_SearchableMultiSelect** — permite seleccionar varios productos.

**Atributos / operaciones:** PER_PAGE, COLS, refresh, _reload, _refresh_table, _register_dialog, _edit_movement, _delete_movement, _open_reports, _open_info

**Trazabilidad:** ui/views/movements.py · database/repository.py · core/export.py

### CRC-24 · UsersView

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Administrar los usuarios y sus roles.

**Responsabilidades (sabe / hace)**

- Listar los usuarios registrados y su rol.
- Crear, editar y eliminar usuarios.
- Validar la contraseña mínima y los campos obligatorios.
- Evitar que se elimine el último administrador.
- Refrescar la tabla después de cada cambio.

**Colaboradores (con quién trabaja)**

- **Usuario** — es la entidad que se administra.
- **RepositorioDatos** — persiste la tabla users.
- **AutenticacionService** — genera el hash de la contraseña.
- **_UserDialog** — captura los datos del usuario.
- **App** — inyecta el usuario actual y controla el acceso.

**Atributos / operaciones:** refresh, _add_dialog, _edit_dialog, _delete

**Trazabilidad:** ui/views/users.py · database/repository.py · core/auth.py

### CRC-25 · SystemDataView

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Ofrecer el respaldo y la restauración de la base de datos.

**Responsabilidades (sabe / hace)**

- Mostrar la ruta y el tamaño de la base actual.
- Guardar un respaldo en la ubicación elegida.
- Seleccionar y validar un archivo de respaldo.
- Confirmar la restauración y crear un respaldo de seguridad.
- Cerrar la sesión después de restaurar.
- Restringir la vista al rol administrador.

**Colaboradores (con quién trabaja)**

- **RespaldoService** — crea, valida y restaura la base.
- **App** — recibe la orden de cerrar sesión.
- **Usuario** — aporta el rol que autoriza la vista.
- **RepositorioDatos** — invalida la caché después de restaurar.
- **ConfirmDialog / MessageDialog** — confirman y comunican resultados.

**Atributos / operaciones:** refresh, _backup, _restore, _ensure_admin

**Trazabilidad:** ui/views/system_data.py · core/database_backup.py

### CRC-26 · CatalogosView

**Tipo:** Frontera · **Capa:** Interfaz

**Propósito:** Gestionar los catálogos maestros de proveedores, empleados y vehículos.

**Responsabilidades (sabe / hace)**

- Listar los registros del catálogo correspondiente.
- Crear, editar y eliminar registros.
- Validar campos obligatorios y valores duplicados.
- Abrir el diálogo específico de cada catálogo.
- Refrescar la tabla después de guardar o eliminar.

**Colaboradores (con quién trabaja)**

- **Proveedor / Empleado / Vehiculo** — son las entidades del catálogo.
- **RepositorioDatos** — persiste cada tabla.
- **_SupplierDialog / _EmpDialog / _VehicleDialog** — capturan los datos.
- **App** — inyecta el usuario y controla el acceso.

**Atributos / operaciones:** refresh, _add_dialog, _edit_dialog, _delete, _save_new

**Trazabilidad:** ui/views/suppliers.py · ui/views/employees.py · ui/views/vehicles.py · patrón compartido de vista de catálogo

## Matriz de colaboración

| N° | Tarjeta | Colaboradores principales |
|---|---|---|
| 01 | Usuario | AutenticacionService, App, Sidebar, UsersView / _UserDialog, RepositorioDatos |
| 02 | Almacen | App, Producto, Movimiento, RepositorioDatos, DashboardView / ProductsView / MovementsView |
| 03 | Producto | UnidadInventario, Movimiento / DetalleMovimiento, Proveedor, Almacen, RepositorioDatos, ProductsView / _RegistrarProductoDialog |
| 04 | UnidadInventario | Producto, DetalleMovimiento, ProductsView / _ChildRow, _ScanResultDialog, RepositorioDatos |
| 05 | Movimiento | DetalleMovimiento, Producto, Empleado, Usuario, Almacen, ServicioMovimientos, MovementsView |
| 06 | DetalleMovimiento | Movimiento, Producto, ServicioMovimientos, RepositorioDatos, ServicioReportes / PDFExporter |
| 07 | Proveedor | Producto, RepositorioDatos, SuppliersView, _SupplierDialog, ProductsView |
| 08 | Empleado | Movimiento, RepositorioDatos, EmployeesView, _EmpDialog, MovementsView |
| 09 | Vehiculo | RepositorioDatos, VehiclesView, _VehicleDialog |
| 10 | AutenticacionService | Usuario, RepositorioDatos, LoginFrame, _ForceChangePasswordDialog, App |
| 11 | RepositorioDatos | ConexionBD, Todas las entidades, ServicioMovimientos, ServicioReportes, Vistas de la UI |
| 12 | ServicioMovimientos | Movimiento / DetalleMovimiento, Producto, RepositorioDatos, MovementsView, _MovementDialog / _MovementEditDialog |
| 13 | ServicioReportes | MovementsView / _ReportsDialog, RepositorioDatos, PDFExporter, NotificadorReportes, ConfiguracionReportes, DashboardView / _MovementInfoDialog |
| 14 | RespaldoService | SystemDataView, RepositorioDatos, ConexionBD, SQLite |
| 15 | EscaneoMovilService | App, ProductsView, _BarcodeScanDialog, _ScanRowDialog / _PhoneScanHelpDialog |
| 16 | ConfiguracionReportes | NotificadorReportes, _DestinationsDialog, ServicioReportes |
| 17 | NotificadorReportes | ServicioReportes, ConfiguracionReportes, Outlook, WhatsApp / navegador, win_utils |
| 18 | App | LoginFrame, Sidebar, Vistas de la app, RepositorioDatos, EscaneoMovilService |
| 19 | Sidebar | App, Usuario, Vistas |
| 20 | LoginFrame | AutenticacionService, _ForceChangePasswordDialog, App, Usuario |
| 21 | DashboardView | App, RepositorioDatos, ServicioReportes, _MovementInfoDialog, ProductsView / MovementsView |
| 22 | ProductsView | Producto / UnidadInventario, Proveedor, RepositorioDatos, _GroupRow / _ChildRow, _RegistrarProductoDialog / _ProductDialog, _GroupEditDialog / _ScanResultDialog, _BarcodeScanDialog / _PhoneScanHelpDialog, App / EscaneoMovilService |
| 23 | MovementsView | Movimiento / DetalleMovimiento, Producto / Empleado, ServicioMovimientos, ServicioReportes, RepositorioDatos, _MovementDialog / _MovementEditDialog, _MovementInfoDialog / _ReportsDialog, _SearchableMultiSelect |
| 24 | UsersView | Usuario, RepositorioDatos, AutenticacionService, _UserDialog, App |
| 25 | SystemDataView | RespaldoService, App, Usuario, RepositorioDatos, ConfirmDialog / MessageDialog |
| 26 | CatalogosView | Proveedor / Empleado / Vehiculo, RepositorioDatos, _SupplierDialog / _EmpDialog / _VehicleDialog, App |

## Notas de diseño

- La separación UI / servicios / repositorio mantiene la lógica de negocio fuera de las pantallas.
- Los movimientos usan transacciones para actualizar stock e historial de forma atómica.
- El detalle de movimiento conserva un snapshot de los productos.
- La configuración de reportes se externaliza en `%APPDATA%/DigiCable/config.json`.
- El respaldo usa la API de SQLite y crea una copia de seguridad antes de restaurar.
- La automatización completa de WhatsApp Desktop sigue pendiente; el flujo actual abre `wa.me` y deja el PDF listo para adjuntar.

## Referencias

- `ui/app.py`, `ui/sidebar.py`, `ui/login_frame.py`
- `ui/views/*.py`
- `core/auth.py`, `core/database_backup.py`, `core/report_config.py`, `core/email_report.py`, `core/whatsapp_report.py`, `core/phone_scan.py`
- `database/connection.py`, `database/repository.py`
- `core/export.py`, `core/pdf_export.py`

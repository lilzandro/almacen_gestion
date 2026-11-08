# Ficha del documento

| Campo | Valor |
|---|---|
| Producto | DigiCable — Sistema de Control de Inventarios |
| Tipo de documento | Manual de usuario |
| Versión | 2.0 |
| Fecha | Noviembre de 2026 |
| Audiencia | Administradores y supervisores |
| Plataforma | Windows 10 u 11 |
| Base de datos | SQLite local (`inventory.db`) |
| Documentos relacionados | `GUIA_WINDOWS.md`, `GUIA_WINDOWS.pdf`, `HISTORIAS_DE_USUARIO.pdf` |

> **Alcance.** Este manual explica la operación diaria de DigiCable: ingreso, panel, productos, movimientos, reportes, datos maestros, usuarios y respaldo/restauración de la base de datos. Para instalar Python y preparar el proyecto, consultá la guía de Windows.

## Cómo usar este manual

- Los nombres de botones, menús y campos aparecen en **negrita**.
- Los valores, rutas, archivos y nombres técnicos aparecen en `formato de código`.
- Los bloques con fondo claro son **notas**, **avisos** o **recomendaciones**.
- Las instrucciones están pensadas para el **almacén activo** que se muestra en la barra superior. Si cambiás de almacén, los productos, movimientos y el panel cambian también.

## Roles de usuario

| Rol | Alcance |
|---|---|
| `admin` | Acceso completo. Gestiona usuarios, datos del sistema, datos maestros, productos, movimientos y reportes. Puede editar y eliminar movimientos, eliminar productos y restaurar la base de datos. |
| `supervisor` | Opera el inventario y registra movimientos. Puede consultar y editar productos, pero no elimina productos ni grupos. No puede editar ni eliminar movimientos, gestionar usuarios, datos del sistema ni datos maestros (proveedores, empleados y vehículos son de solo lectura). |

# 1. Introducción

DigiCable es una aplicación de escritorio para controlar el inventario de un almacén. Trabaja con una base de datos SQLite local y permite registrar productos, entradas, salidas, devoluciones, reportes en PDF y el envío de esos reportes por correo o WhatsApp.

El sistema está organizado en módulos:

| Módulo | Función principal |
|---|---|
| Panel | Resume el inventario y muestra los últimos movimientos. |
| Productos | Agrupa modelos, administra unidades, seriales, MAC, códigos de barras y stock. |
| Proveedores | Registra los proveedores que se asignan a los productos. |
| Empleados | Registra a las personas que reciben material en una salida. |
| Vehículos | Registra los vehículos asociados a una salida. |
| Movimientos | Consulta, registra, edita y elimina salidas, devoluciones y el historial. |
| Usuarios | Solo administrador: crea y administra las cuentas de acceso. |
| Datos del sistema | Solo administrador: respalda y restaura la base de datos. |

## Novedades de esta versión

- **Reportes por correo con PDF adjunto.** En Windows, el sistema abre Outlook con el destino, el asunto y el PDF ya adjunto; solo hay que revisar y pulsar Enviar.
- **Destinos configurables desde la interfaz.** El correo y el WhatsApp se guardan en `%APPDATA%\DigiCable\config.json` y se administran desde **Reportes > Configurar destinos**. Las variables de entorno siguen teniendo prioridad.
- **Botones de envío en el detalle del movimiento.** El detalle de un movimiento incluye **Correo** y **WhatsApp**, además de **Copiar** e **Imprimir**.
- **Datos del sistema.** Nueva pantalla, debajo de **Usuarios**, para guardar un respaldo completo y restaurar la base de datos con validación y respaldo automático de seguridad.
- **Escaneo con el teléfono.** El sistema muestra un código QR y una dirección local para escanear códigos de barras desde la cámara del teléfono, en la misma red Wi-Fi.
- **Inventario agrupado.** Los productos se agrupan por modelo y marca; cada grupo puede contener unidades individuales con serial, MAC y código.

# 2. Requisitos e instalación

## 2.1 Requisitos

- Windows 10 u 11.
- Python 3.10 o superior (se recomienda 3.11).
- La carpeta del proyecto copiada en el equipo.
- Conexión a internet solo para instalar las dependencias la primera vez.

> **Importante.** No copies la carpeta `.venv` de otro equipo. El entorno virtual se crea de nuevo en el equipo donde se va a ejecutar la aplicación.

## 2.2 Instalación rápida

1. Abrí **PowerShell** dentro de la carpeta del proyecto.
2. Creá el entorno virtual:

   ```powershell
   python -m venv .venv
   ```

3. Activá el entorno:

   ```powershell
   .venv\Scripts\Activate.ps1
   ```

4. Instalá las dependencias:

   ```powershell
   python -m pip install -r requirements.txt
   ```

5. Ejecutá la aplicación:

   ```powershell
   python main.py
   ```

Si PowerShell bloquea la activación del entorno, ejecutá una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repetí el paso 3. En Símbolo del sistema, la activación es `.venv\Scripts\activate.bat`.

> **Ejecutá siempre desde la carpeta del proyecto.** El sistema carga el logo desde `img/` y la base de datos local desde esa carpeta. Si abrís `main.py` desde otra ubicación, pueden faltar recursos o datos.

## 2.3 Primer ingreso

- Usuario inicial: `admin`.
- Contraseña inicial: `admin123`.
- En el primer ingreso, el sistema exige cambiar la contraseña. La nueva contraseña debe tener **mínimo 8 caracteres** y coincidir con la confirmación.

> **Seguridad.** Cambiá `admin123` antes de cargar datos reales. No compartas la cuenta de administrador y creá una cuenta `supervisor` para el trabajo diario cuando no se necesiten tareas administrativas.

# 3. Ingreso y entorno de trabajo

## 3.1 Iniciar sesión

1. Abrí la aplicación.
2. Escribí el **Usuario** y la **Contraseña**.
3. Presioná **Iniciar Sesión** o la tecla **Enter**.

Si los datos son incorrectos, aparece el mensaje **Usuario o contraseña incorrectos**. Si falta un campo, aparece **Completa todos los campos**. El nombre de usuario debe escribirse exactamente como fue creado.

## 3.2 Cambio obligatorio de contraseña

Cuando la cuenta tiene la marca de primer ingreso, se abre la ventana **Debes cambiar tu contraseña**:

1. Escribí la **Nueva contraseña**.
2. Confirmala en el segundo campo.
3. Presioná **Guardar y continuar**.

La ventana no se puede cerrar sin completar el cambio. Si la contraseña tiene menos de 8 caracteres o no coincide, el sistema muestra el error y no continúa.

## 3.3 Ventana principal

La ventana tiene tres zonas:

- **Barra lateral izquierda:** logo, nombre del sistema, módulos y datos del usuario conectado. Al final está **Cerrar Sesión**.
- **Barra superior:** selector **Almacén activo**. Todo lo que se muestra pertenece al almacén seleccionado.
- **Área de contenido:** cambia según el módulo elegido.

El usuario conectado se muestra con su rol: **Admin** o **Supervisor**. Los módulos **Usuarios** y **Datos del sistema** solo aparecen para el administrador.

## 3.4 Cambiar de almacén

1. En la barra superior, elegí el almacén en **Almacén activo**.
2. El sistema vuelve a cargar el panel y las vistas que dependen del almacén.

> **Aviso.** Si cambiás de almacén mientras trabajás, los productos y movimientos visibles cambian. Verificá el almacén activo antes de registrar una salida o una devolución.

## 3.5 Navegación y actualización

- Hacé clic en un módulo de la barra lateral para abrirlo.
- El módulo activo se resalta en naranja.
- Las tablas y contadores se actualizan al entrar al módulo, al registrar una operación o al usar los botones de actualización disponibles en cada pantalla.
- **Cerrar Sesión** vuelve a la pantalla de ingreso y descarta la sesión actual.

# 4. Panel

El **Panel** o **Dashboard** es la primera pantalla después del ingreso. Resume el almacén activo.

## 4.1 Tarjetas de resumen

| Tarjeta | Qué muestra | Al hacer clic |
|---|---|---|
| Productos Disponibles | Cantidad de productos disponibles en el almacén activo. | Abre **Productos** filtrado por **Disponible**. |
| Entradas | Cantidad de movimientos de entrada. | Abre **Movimientos** filtrado por **Entrada**. |
| Salidas | Cantidad de movimientos de salida. | Abre **Movimientos** filtrado por **Salida**. |
| Devoluciones | Cantidad de movimientos de devolución. | Abre **Movimientos** filtrado por **Devolución**. |

## 4.2 Movimientos recientes

La parte inferior muestra los últimos movimientos del almacén activo, con color e ícono según el tipo. Cada tarjeta indica fecha y hora, producto, empleado (si corresponde) y usuario que registró.

- Hacé clic en una tarjeta para abrir el **Detalle del Movimiento**.
- Desde el detalle podés imprimir el comprobante en PDF.
- Para ver el historial completo, abrí **Movimientos** en la barra lateral.

> **Nota.** El panel es informativo. Las operaciones que modifican stock se hacen desde **Productos** o **Movimientos**.

# 5. Productos

## 5.1 Cómo se organiza el inventario

Los productos se agrupan por **nombre del producto** y **marca**. Cada grupo muestra cuántas unidades tiene y el estado del stock. Al expandir el grupo se ven las unidades individuales.

La **categoría** define el tipo de control y la unidad de medida sugerida:

| Categoría | Control | Unidad sugerida |
|---|---|---|
| Equipos de Red | Por número de serie / MAC | Unidades (pieza) |
| Cableado | Por cantidad / volumen | Metros |
| Conectores / Pasivos | Por cantidad / volumen | Bolsas / Cajas |
| Herramientas | Por número de serie / MAC | Unidades (pieza) |
| Accesorios de Instalación | Por cantidad / volumen | Bolsas / Cajas |

El **control por serie** crea una fila por equipo, con serial, MAC y código. El **control por cantidad** usa un stock y un serial opcional para el lote.

## 5.2 Estados del stock

| Estado | Cuándo aparece |
|---|---|
| Disponible | Hay más de 10 unidades disponibles. |
| Stock Bajo | Hay entre 1 y 10 unidades disponibles. |
| Agotado | No hay unidades disponibles. |

En los productos controlados por serie, la cantidad disponible se calcula con las unidades en estado disponible. En los productos por cantidad, se usa el stock total.

## 5.3 Consultar y filtrar

1. Abrí **Productos**.
2. Escribí en **Buscar por nombre o código de barras** y presioná **Enter**.
3. Usá los filtros **Todos**, **Disponible** y **No Disponible** para acotar la lista.
4. Hacé clic en el chevron **▸** de un grupo para ver sus unidades.

La tabla muestra **Modelo / Equipo**, **Marca**, **Unidades**, **Stock**, **Proveedor** y **Acciones**. El botón **Editar grupo** abre la configuración del grupo.

> **Nota.** El buscador de Productos se aplica al presionar **Enter**. Los botones de estado se aplican inmediatamente.

## 5.4 Registrar un producto

1. En **Productos**, presioná **Nuevo Producto**.
2. Completá la sección **Identificación e información básica**:
   - **Nombre del producto** (obligatorio).
   - **Código de barras** (opcional; no puede repetirse).
   - **Categoría** (obligatoria).
   - **Marca / Fabricante**.
   - **Modelo** (se muestra para Equipos de Red y Herramientas).
   - **Proveedor**. Podés crear uno nuevo con el botón **+** sin salir del formulario.
3. En **Control de existencias y trazabilidad**, elegí la **Unidad de medida** y el **Tipo de control de inventario**.
4. Si el control es **Por número de serie / MAC**:
   - Indicá cuántas filas generar con **Cantidad de equipos** o **Cantidad de herramientas** y presioná **Generar filas**.
   - También podés usar **Agregar equipo** para sumar una fila.
   - Completá **Serial** y **MAC** (la MAC no se pide para Herramientas).
   - Usá **Sin** si una unidad no tiene serial.
   - El campo **Código** permite asociar un código de barras a la unidad.
   - El botón de quitar elimina la fila.
5. Si el control es **Por cantidad / volumen**:
   - Completá el **Serial** del lote si lo tenés.
   - Indicá la **Cantidad** en la unidad elegida.
6. Revisá el contador de la cabecera y presioná **Guardar producto**.

Si el código de barras ya existe, el sistema muestra **El código de barras ya existe en otro producto** y no guarda. En un alta masiva, las filas duplicadas se omiten y el mensaje final indica cuántas se registraron y cuáles se omitieron.

> **Entrada automática.** Al registrar un producto con stock mayor que cero, el sistema crea automáticamente un movimiento de **Entrada**. En el control por serie, se registra una entrada por unidad. No hace falta registrar la entrada a mano.

## 5.5 Escanear un código

1. Presioná **Escanear** en la barra superior de Productos.
2. Escaneá con un lector físico o ingresá el código en el campo **Código de barras**.
3. Presioná **Aceptar**.

El sistema busca el código:

- Si existe y está disponible, muestra **Producto encontrado** y el botón **Buscar en Productos**.
- Si existe pero está inactivo, muestra **Producto dado de baja** y, si el usuario es administrador, ofrece **Reactivar producto**.
- Si no existe, muestra **Este código no está registrado** y ofrece registrarlo.

Si abrís el escáner desde un formulario de producto, el código se agrega a la fila de serial/código correspondiente.

## 5.6 Editar un grupo o una unidad

### Editar grupo

1. En la fila del grupo, presioná **Editar grupo**.
2. Podés cambiar el **Nombre**, la **Marca** y el **Proveedor**.
3. Usá **Agregar Productos a este Modelo** para sumar unidades al mismo grupo.
4. Presioná **Guardar** para aplicar los cambios.

El botón **Eliminar grupo completo** solo aparece para el administrador. Elimina las unidades activas del grupo y conserva el historial de movimientos. Si el grupo tiene unidades con movimientos, el historial queda registrado con los datos del producto.

### Editar o eliminar una unidad

1. Expandí el grupo con el chevron.
2. Seleccioná una unidad individual.
3. Usá **Editar** para cambiar serial, MAC, código, estado o cantidad, según el tipo de control.
4. Usá **Eliminar** para borrar la unidad. Esta acción solo está disponible para el administrador y pide confirmación.

> **Historial.** Al eliminar un producto o un grupo, el sistema conserva el historial de movimientos. El producto deja de aparecer en el inventario activo, pero sus movimientos siguen consultables en **Movimientos**.

## 5.7 Reactivar un producto inactivo

Si un código escaneado pertenece a un producto inactivo:

1. Escaneá el código.
2. En la ventana **Producto dado de baja**, presioná **Reactivar producto**.
3. Confirmá. El producto vuelve al inventario activo y el sistema lo ubica en la lista.

Solo el administrador puede reactivar productos.

## 5.8 Exportar el inventario a PDF

1. Aplicá el buscador y el filtro de estado que quieras exportar.
2. Presioná **Exportar PDF**.
3. Elegí la carpeta y el nombre del archivo.
4. El sistema genera un PDF con los grupos visibles y el nombre del almacén activo.

Si no hay modelos con el filtro actual, aparece **No hay modelos para exportar con el filtro actual**.

## 5.9 Escanear con el teléfono

El escaneo móvil permite usar la cámara del teléfono como lector de códigos de barras. La PC y el teléfono deben estar en la **misma red Wi-Fi**.

1. En **Productos**, presioná **¿Escaneas con tu teléfono?**.
2. Aparece un código QR y la dirección local del servidor de escaneo.
3. Abrí la cámara del teléfono y apuntá al QR.
4. Si el navegador advierte que la conexión no es segura, tocá **Avanzado > Continuar**. El certificado es autofirmado.
5. Permití el acceso a la cámara y escaneá los códigos.

También podés usar **Copiar enlace** para abrir la dirección en el teléfono. La dirección suele tener el formato `https://IP:8765/...`.

> **Firewall.** La primera vez, Windows puede pedir permiso para la red privada. Aceptá y permití el puerto **8765 TCP** para redes privadas. Si el escaneo móvil no está disponible, revisá que `openssl` esté instalado y que el puerto no esté bloqueado. El resto de la aplicación funciona aunque el escaneo móvil no esté disponible.

# 6. Movimientos

## 6.1 Consultar el historial

1. Abrí **Movimientos**.
2. Usá el buscador **Buscar producto, empleado o nota** para filtrar.
3. Usá los chips **Todos**, **Entrada**, **Salida**, **Devolución**, **Modificación** y **Eliminación** para filtrar por tipo.
4. Usá **Filtros** para mostrar u ocultar el panel de búsqueda y **Limpiar** para quitar todos los filtros.
5. Navegá con los controles de página del pie. La lista muestra 25 movimientos por página.

La tabla muestra **ID**, **Tipo**, **Fecha / hora**, **Cant.**, **Producto** y **Registrado**. El color lateral identifica el tipo de movimiento.

El historial puede incluir **Entrada**, **Salida**, **Devolución**, **Asignación**, **Modificación** y **Eliminación**. Las entradas se generan al dar de alta productos; las modificaciones y eliminaciones se registran automáticamente al operar sobre productos o movimientos. Los tipos que se registran manualmente desde **Registrar movimiento** son **Salida** y **Devolución**.

## 6.2 Registrar una salida

1. Presioná **Registrar movimiento**.
2. Elegí **Salida**.
3. En **Productos**, buscá y seleccioná uno o varios productos. Indicá la cantidad de cada uno.
4. En **Asignación a empleado**, seleccioná el **Empleado** que recibe el material.
5. Opcionalmente, elegí un **Vehículo**.
6. Escribí **Notas** si necesitás dejar una observación.
7. Presioná **Registrar movimiento**.

La salida reduce el stock disponible. Si el producto se controla por serie, se descuentan unidades disponibles; si se controla por cantidad, se descuenta la cantidad indicada.

> **Validaciones.** La salida exige al menos un empleado y al menos un producto con cantidad mayor que cero. Si falta algo, el sistema muestra un aviso y no registra el movimiento.

## 6.3 Registrar una devolución

1. Presioná **Registrar movimiento**.
2. Elegí **Devolución**.
3. Podés devolver de dos formas:
   - **Por cantidad:** seleccioná el producto y escribí la cantidad.
   - **Por serial:** marcá los seriales pendientes de devolución en la lista **Seriales pendientes de devolución**. Podés buscar por nombre o serial.
4. Escribí **Notas** si corresponde.
5. Presioná **Registrar movimiento**.

La devolución aumenta el stock. Si marcaste seriales, el sistema devuelve esas unidades específicas; si usaste cantidades, devuelve la cantidad indicada.

## 6.4 Comprobantes

Después de registrar una salida o una devolución, el sistema pregunta **¿Imprimir el comprobante ahora?**:

- **Salida:** genera un **Comprobante de Entrega** con espacio para la firma de quien recibe.
- **Devolución:** genera un **Comprobante de Devolución — Verificar lo recibido**, sin firma.

Elegí **Imprimir** para guardar el PDF o **No imprimir** para continuar. También podés imprimir el comprobante después desde el detalle del movimiento con **Imprimir**.

## 6.5 Ver el detalle de un movimiento

Hacé doble clic sobre una fila o seleccioná una fila y abrí el detalle. La ventana muestra:

- Tipo, efecto sobre el inventario y descripción.
- Fecha y hora, cantidad, empleado, usuario que registró y almacén.
- Productos incluidos, con cantidades y seriales cuando corresponde.
- Notas.
- Acciones: **Editar**, **Eliminar**, **Copiar**, **Imprimir**, **Correo**, **WhatsApp** y **Cerrar**.

El botón **Copiar** copia un resumen de texto al portapapeles. **Imprimir** genera un PDF del movimiento.

## 6.6 Editar o eliminar un movimiento

Estas acciones son exclusivas del administrador.

- **Editar:** permite cambiar el tipo (Entrada, Salida o Devolución), el empleado, las cantidades y las notas. El stock se recalcula al guardar. Las unidades con seriales no permiten editar la cantidad desde esta ventana.
- **Eliminar:** pide confirmación y reajusta el stock automáticamente. También podés usar la tecla **Supr** con una fila seleccionada.

> **Cuidado.** Editar o eliminar un movimiento cambia el stock. Verificá el movimiento correcto antes de confirmar.

## 6.7 Generar reportes

1. Abrí **Movimientos** y presioná **Reportes**.
2. Elegí el **Tipo de reporte**:

| Tipo | Período | Filtro por tipo | Contenido |
|---|---|---|---|
| Diario | Hoy | Sí | Movimientos del día. |
| Semanal | Últimos 7 días | Sí | Movimientos de la semana. |
| Mensual | Mes calendario en curso | Sí | Movimientos del mes. |
| Crítico de cierre | Rango de fechas | No | Resumen por tipo, ranking de productos más y menos movidos. |
| Por producto (ranking) | Rango de fechas | No | Top 10 y bottom 10 de productos por movimientos. |
| Selección actual | No aplica | No | Solo las filas seleccionadas en la lista. |

3. Para **Semanal**, **Mensual**, **Crítico de cierre** y **Por producto (ranking)**, ajustá **Desde** y **Hasta** si es necesario. Los botones **Hoy**, **Esta semana** y **Este mes** cargan el rango correspondiente. El formato de fecha es `AAAA-MM-DD`.
4. Para **Diario**, el sistema usa la fecha actual y oculta los campos de fecha.
5. Presioná **Generar PDF**.
6. Elegí la carpeta y el nombre del archivo.

Para **Selección actual**, seleccioná una o más filas con **Ctrl + clic** antes de abrir Reportes. Este reporte se guarda en el equipo y no utiliza las casillas de envío.

> **Nota.** El reporte se genera para el **almacén activo**. Si cambiás de almacén, cambiá también el contexto del reporte.

## 6.8 Configurar destinos de envío

En la ventana **Reportes**, dentro de **Envío (opcional)**, presioná **Configurar destinos…**.

| Campo | Qué ingresar |
|---|---|
| Correo destino | Una dirección de correo, por ejemplo `reportes@empresa.com`. |
| WhatsApp destino | Número en formato internacional, por ejemplo `584121234567`. También se acepta un número local venezolano con `0` inicial; el sistema lo convierte a `58`. |

Presioná **Guardar**. Los destinos se guardan en `%APPDATA%\DigiCable\config.json`.

Las variables de entorno `REPORT_EMAIL_TO` y `WHATSAPP_TO` tienen prioridad sobre la configuración guardada. Si una variable está definida, la interfaz muestra la leyenda **(variable de entorno)** y no se puede cambiar ese destino desde la ventana hasta que se modifique o elimine la variable.

## 6.9 Enviar por correo

1. Configurá el **Correo destino**.
2. Marcá **Enviar por correo (con el PDF adjunto)**.
3. Generá el reporte.

En Windows, si Outlook está instalado, el sistema abre un correo nuevo con el destino, el asunto, el cuerpo y el PDF adjunto. **El correo no se envía automáticamente:** revisalo y pulsá **Enviar** en Outlook.

Si Outlook no está disponible o falla, el sistema:

- Copia el PDF al portapapeles.
- Abre la carpeta con el PDF seleccionado.
- Abre el cliente de correo predeterminado con el enlace `mailto:`.

En ese caso, adjuntá el PDF con **Ctrl + V** o arrastrándolo desde la carpeta que se abrió.

## 6.10 Enviar por WhatsApp

1. Configurá el **WhatsApp destino**.
2. Marcá **Abrir WhatsApp (PDF copiado; Ctrl+V)**.
3. Generá el reporte.

El sistema copia el PDF al portapapeles, abre la carpeta con el archivo seleccionado y abre el chat del número configurado. Para completar el envío:

- En el chat, presioná **Ctrl + V** para adjuntar el PDF copiado, o
- Arrastrá el archivo desde la carpeta que se abrió hasta el chat.

El envío final siempre lo confirmás vos. WhatsApp no permite adjuntar un archivo automáticamente solo con un enlace, por eso el sistema deja el PDF preparado.

## 6.11 Enviar desde el detalle de un movimiento

El detalle de un movimiento incluye **Correo** y **WhatsApp**. Al usarlos:

1. El sistema genera un PDF temporal del movimiento en `%TEMP%\DigiCable\movimiento_<id>.pdf`.
2. Abre Outlook con el PDF adjunto o el chat de WhatsApp con el PDF copiado.
3. Revisá el mensaje y completá el envío.

Estos botones usan los mismos destinos configurados en **Reportes > Configurar destinos**.

# 7. Datos maestros

## 7.1 Proveedores

1. Abrí **Proveedores**.
2. Usá **Buscar por nombre, contacto o RIF** para encontrar un registro.
3. El administrador puede **Agregar Proveedor**, **Editar** y **Eliminar**.

Campos del proveedor:

- **Nombre**.
- **Contacto**.
- **RIF**.

Los proveedores se asignan a los productos desde el formulario de producto o desde **Editar grupo**.

## 7.2 Empleados

1. Abrí **Empleados**.
2. Usá **Buscar por nombre o cédula**.
3. El administrador puede **Agregar Empleado**, **Editar** y **Eliminar**.

Campos del empleado:

- **Nombre** (obligatorio).
- **Cédula** (obligatoria y única).
- **Cargo**.

Los empleados se usan en las salidas. Sin un empleado seleccionado no se puede registrar una salida.

## 7.3 Vehículos

1. Abrí **Vehículos**.
2. Usá **Buscar por marca o placa**.
3. El administrador puede **Agregar Vehículo**, **Editar** y **Eliminar**.

Campos del vehículo:

- **Marca** (obligatoria).
- **Modelo**.
- **Placa** (obligatoria y única).

El vehículo es opcional en una salida, pero ayuda a identificar cómo se transportó el material.

# 8. Usuarios

La sección **Usuarios** solo está disponible para el administrador. Se encuentra debajo de **Movimientos** en la barra lateral.

## 8.1 Crear un usuario

1. Presioná **Agregar Usuario**.
2. Completá **Usuario** y **Contraseña**.
3. Elegí el **Rol**: `admin` o `supervisor`.
4. Presioná **Guardar**.

La contraseña debe tener **mínimo 8 caracteres**. El nombre de usuario debe ser único.

## 8.2 Editar un usuario

1. Seleccioná un usuario en la tabla.
2. Presioná **Editar**.
3. Podés cambiar el **Usuario** y el **Rol**.
4. Para cambiar la contraseña, escribí una nueva; si dejás el campo vacío, la contraseña actual se conserva.
5. Presioná **Guardar**.

## 8.3 Eliminar un usuario

1. Seleccioná un usuario.
2. Presioná **Eliminar** y confirmá.

No podés eliminar tu propio usuario. Si necesitás retirar el acceso de un administrador, primero ingresá con otra cuenta administrativa.

> **Importante.** Los usuarios forman parte de la base de datos. Si restaurás un respaldo, los usuarios y contraseñas vuelven a ser los de ese respaldo.

# 9. Datos del sistema

La sección **Datos del sistema** solo está disponible para el administrador y aparece debajo de **Usuarios**.

## 9.1 Información de la base de datos

La pantalla muestra:

- **Base de datos:** ruta absoluta del archivo `inventory.db` activo.
- **Tamaño y actualización:** tamaño del archivo y última modificación.
- **Respaldos automáticos:** carpeta donde se guardan los respaldos de seguridad.
- **Estado:** resultado de la última operación.

## 9.2 Crear un respaldo

1. Presioná **Guardar respaldo…**.
2. Elegí la carpeta y el nombre. El nombre sugerido es `DigiCable_respaldo_AAAAMMDD_HHMMSS.db`.
3. Presioná **Guardar**.

El sistema crea una copia consistente con la API de SQLite, la valida y la guarda como un único archivo `.db`. No es necesario copiar archivos `-wal` o `-shm`: el respaldo consolida la información.

Al finalizar, muestra la ruta y el tamaño del archivo. Guardá el respaldo en un lugar seguro, preferentemente fuera del equipo (USB, disco externo o carpeta de red).

## 9.3 Restaurar un respaldo

1. Presioná **Seleccionar respaldo…**.
2. Elegí un archivo `.db` válido.
3. Leé la advertencia y presioná **Sí, restaurar**.

Antes de reemplazar la base actual, el sistema:

1. Valida que el archivo sea SQLite y que tenga las tablas requeridas.
2. Crea un **respaldo de seguridad** de la base actual en `%APPDATA%\DigiCable\backups` con el nombre `DigiCable_seguridad_AAAAMMDD_HHMMSS.db`.
3. Copia el contenido del respaldo a la base activa con la API de SQLite.
4. Ejecuta las migraciones necesarias y vuelve a validar.
5. Limpia la caché de datos y cierra la sesión.

Después de restaurar, ingresá con los usuarios de la base restaurada. Si la restauración falla, la base actual no se reemplaza y el mensaje muestra la ruta del respaldo de seguridad.

> **No selecciones el archivo de la base activa.** El sistema no permite restaurar el mismo archivo que está en uso. Elegí una copia de respaldo.

## 9.4 Recomendaciones de respaldo

- Hacé un respaldo antes de actualizar la aplicación, cambiar de equipo o restaurar otro archivo.
- Mantené al menos dos copias: una local y otra fuera del equipo.
- Probá la restauración en un equipo de prueba antes de depender del respaldo.
- No edites `inventory.db` con otras herramientas mientras la aplicación está abierta.
- Si ves archivos `inventory.db-wal` o `inventory.db-shm`, no los borres manualmente: el respaldo desde **Datos del sistema** los consolida.

## 9.5 Copia manual de la base

Como alternativa avanzada, con la aplicación cerrada podés copiar `inventory.db` a otra carpeta. Si existen `inventory.db-wal` o `inventory.db-shm`, copialos junto con el archivo principal. Para restaurar manualmente, reemplazá los tres archivos con la aplicación cerrada.

> **Recomendación.** Para la operación normal, usá **Datos del sistema**. La copia manual requiere cerrar la aplicación y puede dejar una copia inconsistente si se hace en el momento equivocado.

# 10. Seguridad y buenas prácticas

- Cambiá la contraseña inicial `admin123` en el primer ingreso.
- Usá una cuenta `supervisor` para las tareas diarias y reservá `admin` para usuarios, datos del sistema y correcciones.
- Cerrá sesión al alejarte del equipo.
- No compartas contraseñas ni las guardes en archivos de texto.
- Protegé los respaldos: contienen toda la información del inventario, usuarios y movimientos.
- Revisá el correo y el mensaje de WhatsApp antes de enviarlos.
- Verificá el **almacén activo** antes de registrar movimientos.
- No muevas ni renombres `inventory.db` mientras la aplicación está abierta.
- Mantené actualizados Windows, Python y Outlook.
- Si detectás datos extraños, no borres la base: creá un respaldo y consultá a soporte.

# 11. Solución de problemas

| Problema | Qué hacer |
|---|---|
| `python` no se reconoce | Reinstalá Python marcando **Add python.exe to PATH**. |
| `No module named 'customtkinter'` | Activá el entorno con `.venv\Scripts\Activate.ps1` y ejecutá de nuevo. |
| La ventana no abre o se cierra sola | Abrí PowerShell en la carpeta del proyecto y ejecutá `python main.py` para ver el error. |
| No puedo iniciar sesión | Verificá mayúsculas y minúsculas del usuario, la contraseña y que la base sea la correcta. Si olvidaste la contraseña de `admin`, necesitás soporte técnico. |
| El sistema pide cambiar la contraseña | Es el primer ingreso o la cuenta tiene la marca de cambio obligatorio. Usá mínimo 8 caracteres. |
| El código de barras ya existe | El campo es único. Editá el producto existente o usá otro código. |
| No aparecen productos | Revisá el **almacén activo**, el buscador y el filtro de estado. Presioná **Enter** después de buscar. |
| No puedo registrar una salida | Verificá que haya un empleado seleccionado, al menos un producto y cantidades mayores que cero. |
| No aparecen seriales para devolver | Solo se muestran seriales pendientes de devolución del almacén activo. |
| El reporte no se envía por correo | Configurá el destino. Si Outlook no está disponible, el sistema abre `mailto:` y deja el PDF para adjuntar con Ctrl+V. |
| El reporte no se envía por WhatsApp | Configurá el número. El sistema deja el PDF copiado; pegá con Ctrl+V o arrastrá el archivo al chat. |
| El PDF no se genera | Verificá que `reportlab` esté instalado con `python -m pip install -r requirements.txt`. |
| El escaneo con el teléfono no conecta | PC y teléfono en la misma Wi-Fi, firewall con el puerto 8765 TCP permitido y certificado aceptado. |
| `No se pudo generar el certificado` | Falta `openssl` en PATH. El escaneo móvil queda deshabilitado; el resto funciona. |
| No puedo restaurar un respaldo | Elegí un `.db` de DigiCable, distinto de la base activa. Si está dañado, usá otra copia. |
| La base está bloqueada | Cerrá otras instancias de la aplicación y esperá unos segundos. No borres `inventory.db`. |
| La app no encuentra el logo | Ejecutá desde la carpeta del proyecto y verificá que exista `img/`. |

# 12. Glosario

| Término | Significado |
|---|---|
| Almacén activo | Almacén seleccionado en la barra superior. Filtra productos, movimientos y panel. |
| Grupo | Conjunto de productos con el mismo nombre y marca. |
| Unidad | Producto individual dentro de un grupo, generalmente con serial y MAC. |
| Serial | Número de serie del equipo. |
| MAC | Dirección física de red del equipo. |
| Código de barras | Código único que identifica un producto o una unidad. |
| Stock | Cantidad disponible de un producto o grupo. |
| Entrada | Ingreso de material al inventario. Se genera al registrar productos o al editar un movimiento. |
| Salida | Entrega de material a un empleado. Reduce el stock. |
| Devolución | Retorno de material entregado. Aumenta el stock. |
| Asignación | Tipo de movimiento que puede aparecer en el historial cuando el material queda asignado a personal. |
| Modificación | Registro automático de un cambio sobre datos existentes. |
| Eliminación | Registro de baja de un producto, unidad o grupo. |
| Comprobante | PDF de entrega o devolución que se puede imprimir y firmar. |
| Reporte crítico de cierre | Resumen por tipo de movimiento y ranking de productos para un período. |
| Respaldo | Copia completa y validada de la base de datos. |
| Restauración | Reemplazo de la base actual por el contenido de un respaldo. |
| Destino | Correo o número de WhatsApp configurado para recibir reportes. |

# Anexo A. Flujos recomendados

## A.1 Alta de producto con entrada

1. Ingresá como administrador o supervisor.
2. Abrí **Productos** y presioná **Nuevo Producto**.
3. Completá nombre, categoría, marca, proveedor y control de inventario.
4. Cargá seriales/MAC o la cantidad inicial.
5. Guardá el producto.
6. Verificá en **Movimientos** que se haya creado la entrada automática.

## A.2 Salida con comprobante

1. Abrí **Movimientos** y presioná **Registrar movimiento**.
2. Elegí **Salida**, el empleado y los productos.
3. Indicá cantidades y, si corresponde, el vehículo y las notas.
4. Registrá el movimiento.
5. Elegí **Imprimir** para generar el comprobante de entrega.
6. Entregá el comprobante a quien recibe y archivá la firma.

## A.3 Devolución

1. Abrí **Movimientos** y presioná **Registrar movimiento**.
2. Elegí **Devolución**.
3. Marcá los seriales pendientes o indicá las cantidades.
4. Registrá la devolución.
5. Imprimí el comprobante de devolución y verificá lo recibido.

## A.4 Cierre mensual

1. Abrí **Movimientos > Reportes**.
2. Elegí **Mensual** o **Crítico de cierre**.
3. Ajustá el rango de fechas.
4. Generá el PDF.
5. Marcá **Enviar por correo** o **Abrir WhatsApp** si corresponde.
6. Revisá el mensaje y completá el envío.
7. Creá un respaldo desde **Datos del sistema**.

## A.5 Restauración de un respaldo

1. Ingresá como administrador.
2. Abrí **Datos del sistema**.
3. Creá un respaldo de la base actual si es posible.
4. Presioná **Seleccionar respaldo…** y elegí el archivo.
5. Confirmá la restauración.
6. Esperá el mensaje de éxito y el cierre de sesión.
7. Ingresá con los usuarios de la base restaurada.

# Anexo B. Atajos y convenciones

| Acción | Cómo se hace |
|---|---|
| Iniciar sesión | **Enter** en el campo de contraseña. |
| Buscar productos | Escribir el criterio y presionar **Enter**. |
| Seleccionar varios movimientos | **Ctrl + clic** sobre las filas. |
| Eliminar un movimiento seleccionado | Tecla **Supr** (solo administrador). |
| Cerrar un diálogo | **Esc** o el botón **Cancelar** / **Cerrar**. |
| Pegar el PDF en WhatsApp o correo alternativo | **Ctrl + V**. |
| Abrir el detalle de un movimiento | Doble clic sobre la fila. |
| Cambiar de almacén | Selector **Almacén activo** en la barra superior. |

> **Convención de fechas.** Las fechas de los reportes se escriben en formato `AAAA-MM-DD`. Las fechas que muestra la aplicación se presentan como `DD/MM/AAAA`.

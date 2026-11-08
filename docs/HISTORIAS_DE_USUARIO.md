# Historias de Usuario — DigiCable

**Sistema de Control de Inventarios**

| Versión | Fecha | Alcance |
|---|---|---|
| 1.0 | 07/11/2026 | Sistema de escritorio DigiCable (`almacen_gestion`) |

---

## 1. Propósito

Este documento describe las historias de usuario del sistema DigiCable desde la perspectiva de quienes lo operan. Cada historia incluye:

- El rol que la ejecuta.
- El objetivo funcional.
- Los criterios de aceptación verificables.
- La prioridad y el estado actual.

Las historias marcadas como **Implementado** reflejan funcionalidad existente en el sistema. Las marcadas como **Propuesto** forman parte del backlog y no deben considerarse entregadas.

---

## 2. Actores

| Actor | Descripción | Permisos principales |
|---|---|---|
| **Administrador** | Responsable de la configuración y el control total del sistema. | Todo: usuarios, catálogos, productos, movimientos, reportes y almacenes. Puede eliminar/reactivar productos, editar/eliminar movimientos y gestionar usuarios. |
| **Supervisor** | Operador de almacén encargado del día a día. | Dashboard, consulta de catálogos, alta/edición de productos, registro de salidas y devoluciones, generación y envío de reportes. No gestiona usuarios ni elimina registros. |
| **Sistema** | Actor de apoyo que ejecuta reglas automáticas. | Registra entradas al dar de alta productos, genera movimientos de modificación/eliminación y calcula stock, pendientes y reportes. |

### Matriz de permisos

| Funcionalidad | Administrador | Supervisor |
|---|:---:|:---:|
| Ver dashboard y movimientos recientes | ✅ | ✅ |
| Ver, buscar y filtrar productos | ✅ | ✅ |
| Registrar y editar productos/unidades | ✅ | ✅ |
| Eliminar productos o grupos | ✅ | ❌ |
| Reactivar productos inactivos | ✅ | ❌ |
| Registrar salidas y devoluciones | ✅ | ✅ |
| Editar o eliminar movimientos | ✅ | ❌ |
| Ver y buscar proveedores, empleados y vehículos | ✅ | ✅ |
| Crear, editar o eliminar proveedores, empleados y vehículos | ✅ | ❌ |
| Generar, guardar y enviar reportes | ✅ | ✅ |
| Gestionar usuarios | ✅ | ❌ |
| Cambiar el almacén activo | ✅ | ✅ |

---

## 3. Convenciones

- **Formato de historia:** «Como [rol], quiero [acción] para [beneficio]».
- **Prioridad:** Alta (operación diaria), Media (gestión y reportes), Baja (mejora de experiencia).
- **Estado:** Implementado / Propuesto.
- **Criterios de aceptación:** se redactan como situaciones verificables (Dado / Cuando / Entonces).
- **Alcance:** aplicación de escritorio con base de datos local SQLite. Los envíos por correo y WhatsApp dependen de servicios externos.

---

## 4. Resumen de épicas

| Épica | Historias | Enfoque |
|---|---|---|
| E1. Acceso y seguridad | HU-01 a HU-05 | Login, cambio obligatorio de contraseña, roles y protección de credenciales. |
| E2. Dashboard y monitoreo | HU-06 a HU-09 | Resumen de inventario, movimientos recientes y navegación filtrada. |
| E3. Inventario y productos | HU-10 a HU-20 | Altas, equipos serializados, stock, búsqueda, edición, bajas y escaneo. |
| E4. Movimientos y trazabilidad | HU-21 a HU-31 | Salidas, devoluciones, auditoría, comprobantes y envío del detalle. |
| E5. Catálogos maestros | HU-32 a HU-34 | Proveedores, empleados y vehículos. |
| E6. Reportes y distribución | HU-35 a HU-41 | Reportes por período, ranking, cierre, correo y WhatsApp. |
| E7. Administración de usuarios | HU-42 a HU-45 | Alta, edición, baja y validaciones de usuarios. |
| E8. Operación multi-almacén | HU-46 a HU-47 | Selección del almacén activo y aislamiento de datos. |
| E9. Calidad y operación | HU-48 a HU-51 | Operación sin internet, persistencia, rendimiento y errores claros. |

---

## 5. Historias de usuario

### E1. Acceso y seguridad

#### HU-01 · Iniciar sesión
**Historia:** Como usuario registrado, quiero iniciar sesión con mi usuario y contraseña para acceder al sistema según mi rol.

**Criterios de aceptación:**
- Dado un usuario y una contraseña válidos, cuando presiono «Iniciar sesión», entonces accedo al dashboard.
- Dado un usuario o una contraseña incorrectos, entonces veo «Usuario o contraseña incorrectos» y la contraseña se limpia.
- Dado que dejo un campo vacío, entonces veo «Completa todos los campos» y no se intenta autenticar.
- Dado que presiono Enter en el campo de contraseña, entonces se ejecuta el inicio de sesión.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-02 · Cambio obligatorio de contraseña temporal
**Historia:** Como administrador, quiero que los usuarios con contraseña temporal cambien su contraseña al iniciar sesión para evitar credenciales por defecto.

**Criterios de aceptación:**
- Dado un usuario con cambio de contraseña pendiente, cuando inicia sesión, entonces se abre un diálogo obligatorio antes de entrar al sistema.
- Dado que la nueva contraseña tiene menos de 8 caracteres, entonces veo un error y no se guarda.
- Dado que la confirmación no coincide, entonces veo «Las contraseñas no coinciden».
- Dado que el cambio es exitoso, entonces se actualiza la contraseña y el usuario continúa al dashboard.
- Dado que el diálogo está abierto, entonces no se puede cerrar sin completar el cambio.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-03 · Cerrar sesión
**Historia:** Como usuario, quiero cerrar sesión para dejar el sistema protegido cuando me retiro del equipo.

**Criterios de aceptación:**
- Dado que presiono «Cerrar sesión», entonces se destruyen las vistas y vuelvo a la pantalla de login.
- Dado que cierro sesión, entonces no queda ningún usuario autenticado en memoria.
- Dado que vuelvo a iniciar sesión, entonces se reconstruye la interfaz con el rol y el almacén correspondientes.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-04 · Control de acceso por roles
**Historia:** Como administrador, quiero que el sistema restrinja las acciones sensibles según el rol para proteger la integridad del inventario.

**Criterios de aceptación:**
- Dado un usuario supervisor, entonces no ve la opción «Usuarios» en el menú lateral.
- Dado un usuario supervisor, entonces no ve las acciones de eliminar/reactivar productos ni de eliminar movimientos; si intenta editar un movimiento, se muestra un aviso de permiso y no se aplica el cambio.
- Dado un usuario supervisor, entonces no ve los botones de crear/editar/eliminar proveedores, empleados ni vehículos.
- Dado un usuario administrador, entonces ve y puede ejecutar todas las acciones.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-05 · Protección de credenciales
**Historia:** Como administrador, quiero que las contraseñas se almacenen de forma segura para que no puedan leerse directamente desde la base de datos.

**Criterios de aceptación:**
- Las contraseñas se guardan con PBKDF2-SHA256, sal aleatoria y 260 000 iteraciones; nunca en texto plano.
- Al iniciar sesión, la contraseña ingresada se verifica contra el hash almacenado.
- Si existe un hash legado SHA-256, el sistema lo migra automáticamente a PBKDF2 en el siguiente inicio de sesión exitoso.
- La base de datos no expone la contraseña original en ninguna vista ni reporte.

**Prioridad:** Alta · **Estado:** Implementado

---

### E2. Dashboard y monitoreo

#### HU-06 · Ver el resumen del inventario
**Historia:** Como usuario, quiero ver un resumen del inventario y de los movimientos para conocer el estado del almacén de un vistazo.

**Criterios de aceptación:**
- El dashboard muestra cuatro tarjetas: productos disponibles, entradas, salidas y devoluciones.
- Los valores se calculan para el almacén activo.
- Mientras cargan los datos, se muestra un indicador de carga y no se bloquea la ventana.
- Si ocurre un error, se muestra un mensaje claro y la aplicación sigue funcionando.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-07 · Ver los movimientos recientes y su detalle
**Historia:** Como usuario, quiero ver los últimos movimientos y abrir su detalle para revisar qué se movió, quién lo registró y cuándo.

**Criterios de aceptación:**
- El dashboard lista los movimientos más recientes (hasta 10) con tipo, producto, fecha y usuario.
- Al hacer clic en un movimiento, se abre una ventana con productos, cantidades, empleado, vehículo, notas, almacén, usuario y fecha.
- Desde el detalle puedo generar un PDF del movimiento.
- El detalle se cierra con Escape o con el botón «Cerrar».

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-08 · Navegar desde las tarjetas a la lista filtrada
**Historia:** Como usuario, quiero hacer clic en una tarjeta del dashboard para llegar a la lista correspondiente ya filtrada.

**Criterios de aceptación:**
- Al hacer clic en «Productos disponibles», se abre Productos con el filtro «Disponible».
- Al hacer clic en «Entradas», «Salidas» o «Devoluciones», se abre Movimientos con el tipo correspondiente seleccionado.
- El filtro aplicado se refleja visualmente en la vista de destino.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-09 · Filtrar el dashboard por almacén activo
**Historia:** Como usuario, quiero que el dashboard respete el almacén seleccionado para analizar cada ubicación por separado.

**Criterios de aceptación:**
- Al cambiar el almacén activo, las tarjetas y los movimientos recientes se recalculan.
- Las vistas de Productos, Movimientos y Reportes también usan el almacén activo.
- El cambio de almacén no requiere reiniciar la aplicación.

**Prioridad:** Alta · **Estado:** Implementado

---

### E3. Inventario y productos

#### HU-10 · Registrar un producto controlado por cantidad
**Historia:** Como usuario, quiero registrar productos por cantidad para llevar el stock de insumos que no se identifican unitariamente.

**Criterios de aceptación:**
- Puedo indicar nombre, código de barras, categoría, marca, modelo, proveedor, unidad de medida y cantidad inicial.
- El código de barras y la cantidad son obligatorios para este tipo de control.
- La cantidad debe ser un entero mayor que cero.
- Al guardar, el producto queda disponible en el inventario y se registra una entrada inicial.
- Si el código de barras ya existe, veo un error y no se duplica el producto.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-11 · Registrar equipos serializados
**Historia:** Como usuario, quiero registrar equipos uno por uno con serial, MAC y código para saber exactamente qué unidad física tengo en el almacén.

**Criterios de aceptación:**
- Puedo agregar una fila por equipo con serial, MAC y código de barras.
- Puedo escanear cada código y se agrega una fila automáticamente.
- El contador de la cabecera refleja la cantidad de equipos a registrar.
- Al guardar, cada equipo queda como una unidad disponible e identificable.
- Las filas marcadas como «Sin» se omiten deliberadamente.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-12 · Validar los datos de los equipos
**Historia:** Como usuario, quiero que el sistema valide seriales, MAC y códigos para evitar duplicados y datos mal formados.

**Criterios de aceptación:**
- La MAC debe tener formato `AA-BB-CC-DD-EE-FF` (o con `:`), y se guarda en mayúsculas.
- No se permiten seriales duplicados dentro del mismo alta.
- No se permiten códigos de barras duplicados dentro del mismo alta.
- Los equipos de red requieren serial, MAC y código.
- Una fila con solo código de barras, sin serial ni MAC, se rechaza con un mensaje claro.
- Los campos con error se resaltan visualmente.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-13 · Asociar categoría y proveedor, con alta rápida de proveedor
**Historia:** Como usuario, quiero clasificar el producto por categoría y proveedor, pudiendo crear un proveedor sin salir del formulario.

**Criterios de aceptación:**
- La categoría es obligatoria y determina la unidad de medida y el tipo de control sugerido.
- Puedo seleccionar «Sin proveedor» o un proveedor existente.
- Puedo crear un proveedor desde el mismo formulario y queda seleccionado al terminar.
- El modelo se muestra solo para las categorías que lo requieren.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-14 · Registrar automáticamente la entrada inicial
**Historia:** Como usuario, quiero que al dar de alta un producto se registre automáticamente su entrada para que el historial y el stock coincidan desde el primer momento.

**Criterios de aceptación:**
- Al guardar un producto por cantidad con stock inicial, se crea un movimiento de tipo «entrada» con la cantidad indicada.
- El movimiento queda asociado al usuario que registró el producto, al almacén activo y a la nota «Registro inicial».
- Si el movimiento de entrada falla, se muestra un mensaje de error con la causa.
- El dashboard y la lista de movimientos reflejan la entrada.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-15 · Buscar y filtrar productos
**Historia:** Como usuario, quiero buscar productos por nombre o código y filtrarlos por estado para encontrar rápidamente lo que necesito.

**Criterios de aceptación:**
- La búsqueda se puede ejecutar con Enter y no distingue mayúsculas de minúsculas.
- Puedo filtrar por «Todos», «Disponible» y «No disponible».
- Los resultados se agrupan por modelo/marca y muestran el stock correspondiente.
- Si no hay resultados, veo un mensaje que sugiere cambiar el criterio.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-16 · Ver el inventario agrupado y el detalle de unidades
**Historia:** Como usuario, quiero ver el inventario agrupado por modelo/marca y expandir cada grupo para revisar sus unidades.

**Criterios de aceptación:**
- Cada grupo muestra modelo/equipo, marca, cantidad de unidades, stock, proveedor y estado.
- Al expandir un grupo, veo las unidades con serial, MAC o código, según corresponda.
- El stock se muestra como «Disponible», «Stock bajo» o «Agotado» cuando aplica.
- Las unidades inactivas se identifican visualmente.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-17 · Editar una unidad o un grupo completo
**Historia:** Como usuario, quiero corregir los datos de una unidad o de un grupo para mantener el inventario actualizado.

**Criterios de aceptación:**
- Puedo editar los campos permitidos de una unidad sin alterar su historial de movimientos.
- Puedo editar marca, modelo y proveedor de un grupo completo.
- Puedo agregar nuevas unidades a un grupo existente.
- Al guardar cambios, el sistema registra un movimiento de tipo «modificación».
- Los cambios quedan asociados al usuario y a la fecha/hora.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-18 · Dar de baja, eliminar y reactivar productos
**Historia:** Como administrador, quiero dar de baja o eliminar productos y poder reactivarlos para mantener limpio el inventario sin perder el historial.

**Criterios de aceptación:**
- Solo el administrador ve las acciones de eliminar y reactivar.
- Al eliminar un producto o grupo, se pide confirmación y se registra un movimiento de eliminación con el usuario que lo hizo.
- El historial de movimientos se conserva aunque el producto se elimine.
- Un producto inactivo puede reactivarse desde la vista de productos o al escanear su código.
- Un supervisor que intenta reactivar ve un aviso de permiso.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-19 · Exportar el inventario a PDF
**Historia:** Como usuario, quiero exportar el inventario filtrado a PDF para compartirlo o imprimirlo.

**Criterios de aceptación:**
- El PDF respeta la búsqueda y el filtro de estado aplicados.
- Incluye el almacén activo y la fecha de generación.
- Muestra modelo/equipo, marca, unidades, stock y proveedor.
- Si no hay resultados, se avisa y no se genera un PDF vacío.
- Si falta la dependencia de PDF, se muestra un mensaje claro con la instrucción de instalación.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-20 · Escanear códigos con lector USB o con el teléfono
**Historia:** Como usuario, quiero escanear códigos de barras con un lector USB o con la cámara del teléfono para agilizar las altas y las búsquedas.

**Criterios de aceptación:**
- El escaneo con lector USB se puede hacer desde el diálogo de escaneo o desde el alta de producto.
- La opción «¿Escaneas con tu teléfono?» muestra un QR y la URL local del servidor de escaneo.
- La página del teléfono usa HTTPS con certificado autofirmado y un token de acceso.
- Cada código escaneado se envía a la ventana activa y se procesa automáticamente.
- Si el código existe, se localiza el producto; si no existe, se ofrece registrarlo con el código precargado.
- Si el código pertenece a un producto inactivo, se ofrece reactivarlo (solo administrador).

**Prioridad:** Media · **Estado:** Implementado

---

### E4. Movimientos y trazabilidad

#### HU-21 · Registrar una salida de productos
**Historia:** Como usuario, quiero registrar la salida de uno o varios productos hacia un empleado para dejar constancia de quién los retira.

**Criterios de aceptación:**
- Debo seleccionar al menos un empleado y al menos un producto.
- Puedo indicar cantidades por producto, vehículo y notas.
- La salida admite productos por cantidad y equipos serializados.
- Al registrar, el stock se descuenta y se crea un movimiento compuesto con todos los ítems.
- El movimiento queda asociado al usuario, empleado, almacén y fecha/hora.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-22 · Validar stock antes de una salida
**Historia:** Como usuario, quiero que el sistema impida sacar más cantidad de la disponible para no dejar el inventario en negativo.

**Criterios de aceptación:**
- Antes de confirmar una salida, el sistema valida que haya stock suficiente por producto.
- Si no hay stock suficiente, se muestra un error y no se registra el movimiento.
- Para equipos serializados, solo se pueden seleccionar unidades disponibles.
- El stock se actualiza de forma atómica con el movimiento.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-23 · Registrar una devolución por cantidad
**Historia:** Como usuario, quiero registrar la devolución de productos por cantidad para reponer el stock.

**Criterios de aceptación:**
- Puedo seleccionar productos y cantidades devueltas.
- La devolución suma stock y queda registrada como movimiento de tipo «devolución».
- Puedo agregar notas y el sistema guarda usuario, almacén y fecha/hora.
- Si no hay nada para devolver, se muestra un aviso y no se registra el movimiento.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-24 · Devolver equipos serializados y consultar pendientes
**Historia:** Como usuario, quiero devolver equipos por serial y ver qué unidades están pendientes de devolución para controlar el material que está fuera.

**Criterios de aceptación:**
- La ventana de devolución muestra los seriales que están en estado «no disponible» (fuera del almacén).
- Puedo marcar uno o varios seriales para devolverlos.
- Al confirmar, cada unidad vuelve a estado «disponible» y se registra la devolución.
- También puedo consultar productos por cantidad con pendiente de devolución.
- El sistema no permite devolver un serial que no está en estado de salida.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-25 · Consultar y filtrar el historial de movimientos
**Historia:** Como usuario, quiero consultar el historial de movimientos con filtros y paginación para encontrar rápidamente una operación.

**Criterios de aceptación:**
- Puedo filtrar por tipo: todos, entrada, salida, devolución, modificación y eliminación.
- Puedo buscar por producto, código de barras, empleado o notas.
- Puedo filtrar por rango de fechas.
- La lista se pagina de 25 en 25 y muestra el total de resultados.
- Los tipos se identifican con colores y etiquetas.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-26 · Ver el detalle completo de un movimiento
**Historia:** Como usuario, quiero abrir un movimiento para revisar todos sus datos antes de imprimirlo o enviarlo.

**Criterios de aceptación:**
- El detalle muestra el desglose de productos, cantidades, unidades y seriales.
- Muestra empleado, cargo, vehículo, notas, almacén, usuario que registró y fecha/hora.
- Permite generar el PDF del movimiento.
- Permite enviar el detalle por correo o WhatsApp si hay destinos configurados.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-27 · Editar un movimiento
**Historia:** Como administrador, quiero editar un movimiento para corregir errores sin perder la trazabilidad.

**Criterios de aceptación:**
- Solo el administrador puede editar movimientos.
- Se pueden editar los tipos permitidos y sus datos asociados.
- Al guardar, el stock se reajusta según el cambio.
- La edición se aplica sobre el mismo movimiento, sin duplicar el registro.
- Si el ajuste deja stock inválido, se muestra un error y no se guarda.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-28 · Eliminar un movimiento
**Historia:** Como administrador, quiero eliminar un movimiento para revertir una operación registrada por error.

**Criterios de aceptación:**
- Solo el administrador puede eliminar movimientos.
- Antes de eliminar se pide confirmación y se advierte que el stock se reajustará.
- Al eliminar, el stock se revierte automáticamente.
- El movimiento eliminado deja de aparecer en la lista y en los reportes.
- La operación es atómica: si falla el reajuste, no se elimina el movimiento.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-29 · Auditoría automática de cambios
**Historia:** Como administrador, quiero que las altas, modificaciones y eliminaciones queden registradas como movimientos para poder reconstruir la historia del inventario.

**Criterios de aceptación:**
- El alta de un producto genera un movimiento de «entrada».
- La edición de un producto o grupo genera un movimiento de «modificación».
- La eliminación de un producto o grupo genera un movimiento de «eliminación» o «eliminación de grupo».
- Cada movimiento de auditoría guarda usuario, fecha/hora, notas y datos del producto.
- El historial se conserva aunque el producto se elimine.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-30 · Generar el comprobante PDF de salida o devolución
**Historia:** Como usuario, quiero generar un comprobante en PDF de la salida o devolución para entregarlo o imprimirlo.

**Criterios de aceptación:**
- Al registrar una salida, se ofrece generar el «Comprobante de Entrega» con líneas de firma.
- Al registrar una devolución, se ofrece generar el «Comprobante de Devolución — Verificar lo recibido».
- El comprobante incluye movimiento, tipo, fecha, cantidades, empleado, usuario, almacén, productos y notas.
- Puedo elegir la ubicación del PDF.
- Si el PDF falla, se muestra un error y el movimiento ya registrado no se pierde.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-31 · Enviar el comprobante por correo o WhatsApp
**Historia:** Como usuario, quiero enviar el comprobante desde el detalle del movimiento para compartirlo sin pasos adicionales.

**Criterios de aceptación:**
- El detalle ofrece botones «Correo» y «WhatsApp».
- Si no hay destino configurado, se muestra un aviso con la ruta para configurarlo.
- El correo abre Outlook con el PDF adjunto y un asunto con el número y tipo de movimiento.
- WhatsApp abre la conversación con el mensaje preparado y deja el PDF disponible para adjuntar.
- El PDF se genera en una carpeta temporal para no pedir ubicación en cada envío.

**Prioridad:** Media · **Estado:** Implementado (el envío por WhatsApp requiere confirmar el adjunto en la aplicación)

---

### E5. Catálogos maestros

#### HU-32 · Gestionar proveedores
**Historia:** Como administrador, quiero gestionar proveedores para asociarlos a los productos y mantener sus datos de contacto.

**Criterios de aceptación:**
- Puedo crear, editar y eliminar proveedores.
- Los campos son nombre (obligatorio), contacto y RIF.
- Puedo buscar por nombre o RIF.
- Al eliminar un proveedor, los productos asociados quedan como «Sin proveedor» sin eliminarse.
- Un supervisor puede consultar y buscar, pero no modificar.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-33 · Gestionar empleados
**Historia:** Como administrador, quiero gestionar empleados para asociar las salidas de inventario a la persona que recibe.

**Criterios de aceptación:**
- Puedo crear, editar y eliminar empleados.
- Los campos son nombre (obligatorio), cédula (obligatoria y única) y cargo.
- Puedo buscar por nombre o cédula.
- La cédula duplicada se rechaza con un mensaje claro.
- Un supervisor puede consultar y buscar, pero no modificar.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-34 · Gestionar vehículos
**Historia:** Como administrador, quiero gestionar vehículos para registrar cuál se usó en una salida de materiales.

**Criterios de aceptación:**
- Puedo crear, editar y eliminar vehículos.
- Los campos son marca (obligatoria), modelo y placa (obligatoria y única).
- Puedo buscar por marca o placa.
- La placa duplicada se rechaza con un mensaje claro.
- Un supervisor puede consultar y buscar, pero no modificar.

**Prioridad:** Media · **Estado:** Implementado

---

### E6. Reportes y distribución

#### HU-35 · Configurar los destinos de envío
**Historia:** Como usuario, quiero configurar el correo y el WhatsApp de destino para enviar los reportes sin escribirlos cada vez.

**Criterios de aceptación:**
- El diálogo permite guardar un correo y un número de WhatsApp.
- El correo se valida con formato básico.
- El número se normaliza a formato internacional sin «+» (por ejemplo, `04126483715` → `584126483715`).
- Los destinos se guardan en la configuración local del usuario.
- Las variables de entorno `REPORT_EMAIL_TO` y `WHATSAPP_TO` tienen prioridad y se indican en la interfaz.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-36 · Generar reportes por período
**Historia:** Como usuario, quiero generar reportes diarios, semanales o mensuales de movimientos para analizar la operación.

**Criterios de aceptación:**
- Puedo elegir «Diario», «Semanal» o «Mensual».
- Puedo filtrar por tipo de movimiento.
- El PDF incluye período, almacén, usuario que genera, filtros y total de movimientos.
- Los movimientos compuestos se muestran en una sola fila con el resumen de productos.
- Puedo guardar el PDF en la ubicación que elija.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-37 · Generar el reporte por producto (ranking)
**Historia:** Como usuario, quiero ver los productos más y menos movidos en un período para tomar decisiones de reposición.

**Criterios de aceptación:**
- El reporte muestra hasta 10 productos más movidos y hasta 10 menos movidos, sin repetirlos.
- Incluye período, almacén y fecha de generación.
- Si no hay movimientos, muestra «Sin movimientos en el período».
- El PDF se puede guardar y enviar por correo o WhatsApp.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-38 · Generar el reporte crítico de cierre
**Historia:** Como usuario, quiero un reporte de cierre con el resumen del período y el ranking de productos para revisar la operación antes de cerrar.

**Criterios de aceptación:**
- El reporte incluye conteos de entradas, salidas, devoluciones, asignaciones, eliminaciones y modificaciones.
- Incluye las secciones de productos más y menos movidos.
- Incluye período, almacén y fecha de generación.
- Se puede guardar y enviar por correo o WhatsApp.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-39 · Generar un reporte de la selección actual
**Historia:** Como usuario, quiero generar un PDF con los movimientos que tengo seleccionados para compartir exactamente esa selección.

**Criterios de aceptación:**
- Si no hay movimientos seleccionados, se muestra un aviso.
- El PDF incluye solo los movimientos seleccionados.
- Se indica «Selección manual: N movimiento(s)» como filtro.
- El archivo se guarda con un nombre descriptivo.

**Prioridad:** Baja · **Estado:** Implementado

---

#### HU-40 · Enviar reportes por correo con el PDF adjunto
**Historia:** Como usuario, quiero enviar el reporte por correo con el PDF ya adjunto para ahorrar pasos.

**Criterios de aceptación:**
- Si Outlook está disponible, se abre un correo nuevo con el PDF adjunto y el asunto del reporte.
- Si Outlook no está disponible, se abre el cliente de correo predeterminado y se deja el PDF copiado y visible en el Explorador.
- Si no hay correo configurado, se muestra un aviso.
- El envío no bloquea la generación del reporte: si falla, el PDF queda guardado.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-41 · Enviar reportes por WhatsApp
**Historia:** Como usuario, quiero enviar el reporte por WhatsApp para compartirlo con el equipo o conmigo mismo.

**Criterios de aceptación:**
- Si hay número configurado, se abre WhatsApp con el mensaje del reporte preparado.
- El PDF se copia al portapapeles y se muestra en el Explorador para adjuntarlo.
- Si no hay número configurado, se muestra un aviso con la ruta de configuración.
- El usuario confirma el adjunto y el envío en WhatsApp.

**Prioridad:** Media · **Estado:** Implementado (envío asistido; WhatsApp no permite adjuntar archivos por enlace)

---

### E7. Administración de usuarios

#### HU-42 · Crear usuarios
**Historia:** Como administrador, quiero crear usuarios con rol para dar acceso al sistema según las responsabilidades de cada persona.

**Criterios de aceptación:**
- Puedo indicar usuario, contraseña y rol (`admin` o `supervisor`).
- El usuario debe tener entre 3 y 20 caracteres, solo letras, números y guion bajo.
- La contraseña debe tener al menos 8 caracteres.
- El administrador define la contraseña inicial y puede cambiarla luego desde la edición del usuario.
- No se permiten nombres de usuario duplicados.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-43 · Editar usuarios y roles
**Historia:** Como administrador, quiero editar el nombre, el rol o la contraseña de un usuario para mantener sus permisos al día.

**Criterios de aceptación:**
- Puedo cambiar el nombre de usuario y el rol.
- Puedo dejar la contraseña vacía para conservarla o escribir una nueva.
- Si escribo una contraseña nueva, debe cumplir el mínimo de 8 caracteres.
- Los cambios se reflejan en el listado y en el siguiente inicio de sesión del usuario.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-44 · Eliminar usuarios
**Historia:** Como administrador, quiero eliminar usuarios que ya no deben tener acceso.

**Criterios de aceptación:**
- Puedo eliminar un usuario con confirmación previa.
- No puedo eliminarme a mí mismo; el sistema muestra un aviso.
- Si el usuario tiene movimientos asociados, la base de datos impide la eliminación y se muestra el error.
- No se puede eliminar el último usuario con rol administrador.
- El listado se actualiza después de eliminar.

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-45 · Distinguir el rol en la interfaz
**Historia:** Como usuario, quiero ver mi nombre y mi rol en la barra lateral para saber con qué permisos estoy trabajando.

**Criterios de aceptación:**
- La barra lateral muestra el nombre del usuario y «Admin» o «Supervisor».
- El menú «Usuarios» solo aparece para administradores.
- Al cerrar sesión y entrar con otro rol, la interfaz se reconstruye correctamente.

**Prioridad:** Baja · **Estado:** Implementado

---

### E8. Operación multi-almacén

#### HU-46 · Seleccionar el almacén activo
**Historia:** Como usuario, quiero seleccionar el almacén en el que estoy trabajando para que todas las operaciones se registren en la ubicación correcta.

**Criterios de aceptación:**
- La barra superior muestra los almacenes disponibles.
- Al seleccionar un almacén, las vistas dependientes se recargan con los datos de esa ubicación.
- El almacén activo se usa al registrar productos, movimientos y reportes.
- El cambio no requiere reiniciar la aplicación.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-47 · Aislar los datos por almacén
**Historia:** Como usuario, quiero que el dashboard, los productos, los movimientos y los reportes muestren solo los datos del almacén activo para evitar mezclar ubicaciones.

**Criterios de aceptación:**
- El dashboard cuenta productos y movimientos del almacén activo.
- La lista de productos y movimientos se filtra por almacén.
- Los reportes incluyen el nombre del almacén y solo sus datos.
- Al cambiar de almacén, no se muestran datos del almacén anterior.

**Prioridad:** Alta · **Estado:** Implementado

---

### E9. Calidad y operación

#### HU-48 · Operar sin conexión a internet
**Historia:** Como usuario, quiero que el sistema funcione sin internet para poder trabajar en el almacén aunque la red falle.

**Criterios de aceptación:**
- El inicio de sesión, el inventario, los movimientos y los reportes funcionan con la base de datos local.
- El escaneo con lector USB funciona sin red.
- El escaneo con teléfono requiere que el teléfono y la computadora estén en la misma red local.
- Solo los envíos por correo/WhatsApp requieren servicios externos.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-49 · Persistencia e integridad de los datos
**Historia:** Como administrador, quiero que los datos se guarden de forma consistente para evitar pérdidas o registros huérfanos.

**Criterios de aceptación:**
- La base de datos SQLite usa WAL, claves foráneas activas y tiempos de espera para concurrencia.
- Las operaciones que afectan stock y movimientos se ejecutan de forma atómica.
- Al eliminar un movimiento, el stock se revierte en la misma transacción.
- Al eliminar un producto, su historial en movimientos se conserva.
- Los campos únicos (código de barras, cédula, placa, usuario) no permiten duplicados.

**Prioridad:** Alta · **Estado:** Implementado

---

#### HU-50 · Mantener la interfaz fluida
**Historia:** Como usuario, quiero que las vistas carguen sin congelar la aplicación para poder seguir trabajando mientras se consultan los datos.

**Criterios de aceptación:**
- El dashboard carga las estadísticas en un hilo separado y muestra un indicador mientras espera.
- La lista de movimientos se pagina para no renderizar todos los registros a la vez.
- Las altas y los diálogos pesados se construyen de forma diferida para abrir rápido.
- Mientras se genera un reporte, el botón se deshabilita y muestra «Generando…».

**Prioridad:** Media · **Estado:** Implementado

---

#### HU-51 · Recibir mensajes de error claros
**Historia:** Como usuario, quiero entender qué salió mal y cómo corregirlo cuando una operación falla.

**Criterios de aceptación:**
- Los errores de validación indican el campo y la corrección esperada.
- Si falta `reportlab`, se indica el comando de instalación y la aplicación sigue abierta.
- Si falla un envío, el PDF generado no se pierde y se muestra la ruta.
- Si falla una consulta, se muestra un mensaje comprensible y la ventana permanece abierta.

**Prioridad:** Media · **Estado:** Implementado

---

## 6. Backlog propuesto (no implementado)

Las siguientes historias son mejoras recomendadas. No forman parte del alcance actual y deben priorizarse antes de desarrollarse.

| ID | Historia | Valor esperado | Prioridad sugerida |
|---|---|---|---|
| HU-52 | Como usuario, quiero enviar el PDF por WhatsApp sin pasos manuales usando la API oficial de WhatsApp Cloud. | Envío verdaderamente automático y trazable. | Alta |
| HU-53 | Como administrador, quiero crear, editar y desactivar almacenes desde la aplicación. | Operación multi-almacén autónoma. | Media |
| HU-54 | Como usuario, quiero recuperar mi contraseña mediante un código o correo. | Menos dependencia del administrador. | Media |
| HU-55 | Como administrador, quiero bloquear la cuenta tras varios intentos fallidos. | Mayor seguridad. | Media |
| HU-56 | Como usuario, quiero alertas de stock mínimo y productos agotados. | Reposición proactiva. | Media |
| HU-57 | Como usuario, quiero exportar inventario y movimientos a Excel/CSV. | Análisis externo y compatibilidad. | Media |
| HU-58 | Como administrador, quiero un botón para respaldar y restaurar la base de datos. | Continuidad operativa. | Alta |
| HU-59 | Como administrador, quiero una bitácora de auditoría consultable con filtros por usuario y acción. | Control y cumplimiento. | Media |
| HU-60 | Como usuario, quiero adjuntar una foto o firma digital al comprobante. | Evidencia de entrega. | Baja |

---

## 7. Trazabilidad con el código

| Épica | Módulos principales |
|---|---|
| E1. Acceso y seguridad | `core/auth.py`, `ui/login_frame.py`, `ui/sidebar.py` |
| E2. Dashboard | `ui/views/dashboard.py`, `database/repository.py` (`get_dashboard_stats`) |
| E3. Inventario y productos | `ui/views/products.py`, `core/phone_scan.py`, `core/export.py` |
| E4. Movimientos | `ui/views/movements.py`, `database/repository.py` (`create_compound_movement`, `get_movements_flat`) |
| E5. Catálogos | `ui/views/suppliers.py`, `ui/views/employees.py`, `ui/views/vehicles.py` |
| E6. Reportes y distribución | `ui/views/movements.py` (`_ReportsDialog`), `core/export.py`, `core/pdf_export.py`, `core/email_report.py`, `core/whatsapp_report.py`, `core/report_config.py` |
| E7. Usuarios | `ui/views/users.py`, `core/auth.py` |
| E8. Multi-almacén | `ui/app.py`, `database/connection.py`, `database/repository.py` |
| E9. Calidad | `database/connection.py`, `core/export.py`, `ui/views/dashboard.py` |

---

## 8. Criterios generales de aceptación del sistema

1. La aplicación inicia en Windows sin requerir servidor de base de datos.
2. Un usuario autenticado solo accede a las funciones permitidas por su rol.
3. Todo cambio de stock queda respaldado por un movimiento con usuario y fecha.
4. Los reportes reflejan el almacén activo y los filtros aplicados.
5. Los datos persisten entre reinicios y no se pierden ante un cierre inesperado de la interfaz.
6. Los errores se comunican en español y no dejan la aplicación en un estado inconsistente.

---

*Documento generado para el proyecto DigiCable. Las historias marcadas como implementadas se verificaron contra el código actual; las propuestas requieren análisis y priorización.*

# Guía de uso para el Cliente — DigiCable Inventario

Esta guía explica cómo **abrir el sistema** y **usar sus funciones** para que
puedas probar el producto. No necesitás conocimientos técnicos; si algo no
funciona, al final está qué información pasar a soporte.

---

## 1. Qué es

Sistema de control de inventario de almacén: gestiona productos, proveedores,
empleados, vehículos y movimientos (entradas, salidas, devoluciones), y genera
**reportes en PDF**.

La aplicación se ejecuta con Docker y muestra una ventana de escritorio.

---

## 2. Qué necesitás

- Una computadora con **Docker** instalado (Docker Desktop en Windows/macOS).
- El **proyecto** (carpeta del sistema) en tu equipo.
- En Windows: el programa **VcXsrv** abierto. En macOS: **XQuartz**. En Linux no
  hace falta nada extra.

---

## 3. Cómo iniciar el sistema

Abrí una terminal (o PowerShell) **dentro de la carpeta del proyecto** y ejecutá
según tu sistema:

### Linux
```bash
xhost +local:docker
docker compose up
```
La primera vez puede tardar unos minutos (construye la imagen). Cuando termine,
aparecerá la ventana del sistema.

### Windows
1. Abrí **XLaunch** (VcXsrv) → *Multiple windows* → *Start no client* →
   ✅ *Disable access control* → *Finish*.
2. En PowerShell:
```powershell
docker compose -f docker-compose.windows.yml up --build
```

### macOS
1. Abrí **XQuartz**.
2. En la terminal:
```bash
xhost +localhost
docker compose -f docker-compose.macos.yml up --build
```

### Cómo detenerlo
- En la ventana del sistema: iniciá **Cerrar Sesión** y cerrá la ventana.
- O en la terminal: `Ctrl + C`, y luego `docker compose down`.

---

## 4. Primer ingreso

- **Usuario:** `admin`
- **Contraseña:** `admin123`

> Por seguridad, el sistema te pedirá **cambiar la contraseña** la primera vez.
> Elegí una de al menos 8 caracteres.

---

## 5. Uso del sistema

### 5.1 Panel (Dashboard)
Resumen general: productos disponibles, entradas, salidas y devoluciones, y los
movimientos recientes. Podés tocar las tarjetas para ir al detalle.

### 5.2 Productos
- **Nuevo Producto:** botón `⊕ Nuevo Producto`. Completá nombre, categoría, marca,
  modelo y proveedor.
  - Control **por cantidad**: indicá el stock inicial (unidades, metros, etc.).
  - Control **por serie**: agregá los equipos con su **serial** y **MAC**.
- **Editar / Eliminar:** botones en cada unidad o en la fila del grupo.
- **Exportar PDF:** botón `↓ Exportar PDF` en la parte superior. Genera el
  reporte del inventario con lo que esté filtrado en pantalla.
- **Buscar / Filtrar:** por nombre/código y por estado (Disponible / No disponible).
- **Escaneo rápido:** usá el escáner de código de barras si tenés uno conectado.

### 5.3 Movimientos
- **Registrar movimiento:** botón `+ Registrar movimiento`.
  - **Salida:** elegí el **empleado** y los **productos** con sus cantidades.
    La salida descuenta stock. Para equipos por serie, se marca la unidad
    entregada.
  - **Devolución:** elegí productos por cantidad o marcá los **seriales** que
    vuelven. La devolución repone stock.
- **Filtros y búsqueda:** por tipo (Entrada, Salida, Devolución, Modificación,
  Eliminación) y texto.
- **Ver detalle:** doble clic sobre un movimiento.
- **Editar / Eliminar:** solo el rol **admin** (los movimientos de varios
  productos no se pueden editar; se eliminan y se registran de nuevo).
  Al eliminar, el stock se reajusta automáticamente.
- **Exportar PDF:** botón `↓ Exportar PDF`. Respeta los filtros activos
  (tipo, búsqueda y almacén).

### 5.4 Proveedores, Empleados y Vehículos
- **Proveedores:** nombre, contacto y RIF.
- **Empleados:** nombre, cédula y cargo.
- **Vehículos:** marca, modelo y placa.

(La carga y edición de estos datos la realiza el rol **admin**.)

### 5.5 Usuarios (solo admin)
- Crear usuarios y asignar rol **admin** o **supervisor**.
- Cambiar contraseñas y eliminar usuarios.
- No se puede eliminar el **último administrador** ni tu propio usuario.

### 5.6 Escaneo con el teléfono
1. Entrá a **Productos → ¿Escaneás con tu teléfono?**.
2. Escaneá el **código QR** con la cámara del teléfono (misma red Wi‑Fi que la
   computadora).
3. El navegador mostrará una **advertencia de seguridad** (certificado
   autofirmado): aceptala para continuar.
4. Apuntá al código de barras; se cargará automáticamente en el sistema.

### 5.7 Reportes PDF
- **Movimientos:** historial completo con encabezado, fecha, almacén, filtros y
  numeración de páginas.
- **Inventario:** listado agrupado por modelo/marca con unidades y stock.

En ambos casos, elegí dónde guardar el archivo `.pdf` cuando se abra el diálogo.

---

## 6. Roles

| Acción | Admin | Supervisor |
|--------|:-----:|:----------:|
| Ver y registrar productos / movimientos | ✅ | ✅ |
| Exportar reportes PDF | ✅ | ✅ |
| Editar / eliminar movimientos | ✅ | ❌ |
| Eliminar productos o grupos | ✅ | ❌ |
| Gestionar Usuarios | ✅ | ❌ |

---

## 7. Respaldos (recomendado)

Tus datos viven en la carpeta **`data/`** del proyecto. Para respaldar:

1. Cerrá el sistema (`docker compose down`).
2. Copiá la carpeta `data/` a un lugar seguro (con fecha).
3. Volvé a iniciar con `docker compose up`.

---

## 8. Problemas frecuentes

| Problema | Qué hacer |
|----------|-----------|
| No aparece la ventana | Verificá que Docker esté abierto y que VcXsrv/XQuartz esté iniciado. Reiniciá con `docker compose up`. |
| “No se puede conectar a la pantalla” | Linux: `xhost +local:docker`. Windows: VcXsrv con *Disable access control*. macOS: XQuartz + `xhost +localhost`. |
| El teléfono no conecta | Misma red Wi‑Fi, aceptar el certificado, y permitir el puerto 8765 en el firewall. |
| Un producto con movimientos no se puede eliminar | Es correcto: se conserva el historial. Podés darlo de baja (inactivo). |
| Error al exportar PDF | Avisá a soporte con el mensaje exacto que aparece en pantalla. |

**Al reportar un problema, enviá a soporte:**
- Qué estabas haciendo (paso a paso).
- El mensaje de error (texto o captura).
- El sistema operativo y si usás Docker.
- Si es posible, los últimos registros: en la terminal donde corre el sistema,
  copiá las últimas líneas.

---

## 9. Notas importantes

- La contraseña inicial `admin/admin123` **debe cambiarse** en el primer ingreso.
- Cerrá la sesión con **Cerrar Sesión** antes de apagar el equipo.
- No borres la carpeta `data/`: ahí está toda la información del inventario.

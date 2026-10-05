# Guía de instalación en Windows con Docker — DigiCable Inventario

Esta guía explica cómo ejecutar el sistema en **Windows 10 u 11** usando
**Docker Desktop**. No necesitas instalar Python ni las dependencias: todo corre
dentro de un contenedor. La ventana del sistema se muestra en tu escritorio
gracias a **VcXsrv**.

Si preferís instalar Python directamente, usá la guía `GUIA_WINDOWS.md`.

---

## 1. Qué necesitas

- Windows 10 (64 bits, versión 2004 o superior) u Windows 11.
- **Docker Desktop** para Windows: https://www.docker.com/products/docker-desktop/
- **VcXsrv** (servidor de pantalla X): https://sourceforge.net/projects/vcxsrv/
- La **carpeta del proyecto** (`scanner_inventory`) copiada en tu equipo.

---

## 2. Instalar los programas (una sola vez)

### Docker Desktop

1. Instalá Docker Desktop con las opciones por defecto.
2. Reiniciá el equipo si el instalador lo pide.
3. Abrí Docker Desktop y esperá a que diga **Engine running** (ícono de la
   ballena en la barra de tareas, en verde).

Para verificar, abrí **PowerShell** y ejecutá:

```powershell
docker --version
docker compose version
```

Ambos deben mostrar una versión. Si no, Docker Desktop todavía no terminó de
iniciar.

### VcXsrv

1. Instalá VcXsrv con las opciones por defecto.
2. Abrí **XLaunch** desde el menú Inicio. Configurá:
   - **Multiple windows** → Next
   - **Start no client** → Next
   - ✅ **Disable access control** (es obligatorio)
   - Finish

VcXsrv debe estar abierto (aparece un ícono de X en la bandeja del sistema)
cada vez que uses el sistema. Con **Disable access control** no pide contraseña.

---

## 3. Iniciar el sistema

1. Verificá que **Docker Desktop** esté en ejecución y que **VcXsrv** esté abierto.
2. Abrí **PowerShell** dentro de la carpeta del proyecto. La forma más fácil:
   abrí la carpeta en el Explorador de archivos, hacé clic en la barra de
   dirección, escribí `powershell` y presioná Enter.
3. Ejecutá:

```powershell
docker compose -f docker-compose.windows.yml up --build
```

La primera vez tarda varios minutos (descarga la imagen y las dependencias).
Cuando termine, aparece la ventana de inicio de sesión del sistema.

Las siguientes veces basta con:

```powershell
docker compose -f docker-compose.windows.yml up
```

> Dejá la ventana de PowerShell abierta mientras uses el sistema. Es la que
> muestra los mensajes de la aplicación.

**Credenciales iniciales:** usuario `admin` · contraseña `admin123`.
La primera vez te pedirá cambiar la contraseña. Hacelo.

---

## 4. Uso del sistema

| Módulo | Qué hace |
|--------|----------|
| Panel (Dashboard) | Resumen de productos disponibles, entradas, salidas y devoluciones, y últimos movimientos. |
| Productos | Alta, edición y baja de productos. Agrupados por modelo, con unidades individuales. |
| Movimientos | Entradas, salidas, devoluciones y asignaciones. Exportable a PDF. |
| Proveedores / Empleados / Vehículos | Registro de datos maestros. |
| Usuarios | Solo para `admin`. |

**Roles:**
- `admin`: acceso total, incluida la gestión de usuarios.
- `supervisor`: no gestiona usuarios ni elimina registros.

**Almacén activo:** la barra superior permite cambiar entre almacenes. Todo lo
que veas corresponde al almacén seleccionado.

**Productos con movimientos:** no se borran definitivamente en uso normal; el
sistema conserva el historial y el producto queda **inactivo** (baja lógica).

---

## 5. Cerrar el sistema

- En la ventana del sistema: **Cerrar Sesión** y cerrá la ventana.
- En PowerShell: presioná `Ctrl + C`, y luego ejecutá:

```powershell
docker compose -f docker-compose.windows.yml down
```

Podés cerrar VcXsrv y Docker Desktop cuando ya no los necesites.

---

## 6. Dónde están los datos

Toda la información está en la carpeta **`data`** dentro del proyecto. Ahí vive
el archivo `data\inventory.db`. Esa carpeta se conserva aunque reinicies o
reconstruyas el contenedor.

> No borres la carpeta `data`: ahí está todo el inventario y los usuarios.

---

## 7. Respaldos (recomendado)

1. Cerrá el sistema (sección 5).
2. Copiá la carpeta **`data`** completa a un USB o a otra carpeta.

**Para restaurar:** con el sistema cerrado, reemplazá la carpeta `data` del
proyecto por la copia.

---

## 8. Escaneo con el teléfono (opcional)

El sistema puede recibir códigos de barras desde la cámara de un teléfono de la
misma red Wi-Fi. El puerto **8765** del contenedor queda publicado en la PC.

1. Al iniciar, la consola muestra la dirección para el teléfono
   (`https://IP:8765/...`). La IP es la de tu PC en la red Wi-Fi
   (en PowerShell: `ipconfig`, buscá *Dirección IPv4*).
2. En el teléfono, abrí esa dirección y aceptá el certificado. Es autofirmado,
   por eso el navegador advierte; es normal.
3. **Firewall de Windows:** la primera vez puede aparecer un aviso de Windows
   Defender. Marcá **Redes privadas** y permití el acceso. Si el teléfono no
   conecta, permití el puerto **8765 TCP** para redes privadas.

El teléfono y la PC deben estar en la **misma red Wi-Fi**.

---

## 9. Problemas frecuentes

| Problema | Qué hacer |
|----------|-----------|
| `docker` no se reconoce / no conecta al motor | Abrí Docker Desktop y esperá a que diga *Engine running*. |
| No aparece la ventana del sistema | Verificá que VcXsrv esté abierto con **Disable access control**. Reiniciá con `docker compose -f docker-compose.windows.yml up`. |
| `couldn't connect to display` | VcXsrv no está corriendo o no tiene **Disable access control**. Volvé a abrir XLaunch con esa opción. |
| Los cambios de código no aparecen | Reconstruí la imagen: `docker compose -f docker-compose.windows.yml up --build`. |
| `unable to open database file` | La carpeta `data` no existe o no es escribible. Crearla dentro del proyecto y reintentar. |
| El teléfono no conecta | Misma red Wi-Fi, firewall permitiendo el puerto 8765 y aceptar el certificado en el teléfono. |
| Error al exportar PDF | Anotá el mensaje exacto que aparece en pantalla y avisá a soporte. |
| El puerto 8765 está ocupado | Cerrá el programa que lo usa, o reiniciá Docker Desktop. |

**Al reportar un problema, enviá:**
- Qué estabas haciendo, paso a paso.
- El mensaje de error exacto (texto de la consola o captura).
- La versión de Windows y de Docker Desktop (`docker --version`).
- Las últimas líneas de la consola de PowerShell donde corre el sistema.

---

## 10. Notas importantes

- Cambiá la contraseña inicial `admin123` en el primer ingreso.
- Cerrá la sesión con **Cerrar Sesión** antes de apagar el equipo.
- Hacé respaldos periódicos de la carpeta `data` (sección 7).

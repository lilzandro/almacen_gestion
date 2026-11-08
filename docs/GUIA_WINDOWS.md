# Guía de instalación y uso en Windows — DigiCable Inventario

Esta guía explica cómo instalar y abrir el sistema en **Windows 10 u 11**, sin
Docker. Todo se ejecuta directamente con Python.

Para el detalle de cada pantalla y de las funciones nuevas, consultá el
**Manual de usuario**: `MANUAL_DE_USUARIO.md` o `MANUAL_DE_USUARIO.pdf`.

---

## 1. Qué necesitas

- Windows 10 u 11.
- **Python 3.11** (3.10 o superior también sirve).
- La **carpeta del proyecto** (`scanner_inventory`) copiada en tu equipo.
- Conexión a internet solo para instalar las dependencias (una vez).

> No copies la carpeta `.venv` de otro equipo. Se crea una nueva en el paso 3.

---

## 2. Instalar Python (una sola vez)

1. Descargá Python 3.11 desde https://www.python.org/downloads/windows/.
2. Ejecutá el instalador y **marcá la casilla "Add python.exe to PATH"** antes de
   hacer clic en *Install Now*.
3. Dejá marcada la opción **tcl/tk and IDLE** (viene marcada por defecto; el
   sistema la necesita para su ventana).

Para verificar, abrí **PowerShell** y ejecutá:

```powershell
python --version
```

Debe mostrar `Python 3.11.x`. Si dice que `python` no se reconoce, reinstalá
Python marcando la casilla de PATH.

---

## 3. Preparar el proyecto (una sola vez)

Abrí **PowerShell** dentro de la carpeta del proyecto. La forma más fácil:
abrí la carpeta en el Explorador de archivos, hacé clic en la barra de dirección,
escribí `powershell` y presioná Enter.

```powershell
# Crear el entorno virtual
python -m venv .venv

# Activarlo
.venv\Scripts\Activate.ps1

# Instalar las dependencias
python -m pip install -r requirements.txt
```

Si PowerShell muestra un error de "scripts deshabilitados" al activar el entorno,
ejecutá una sola vez:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

y repetí `.venv\Scripts\Activate.ps1`.

En Símbolo del sistema (cmd) el comando de activación es
`.venv\Scripts\activate.bat`.

Dependencias instaladas: `customtkinter`, `reportlab` (reportes PDF), `Pillow`
(logo) y `qrcode`.

---

## 4. Abrir el sistema

Desde la carpeta del proyecto, con el entorno activado (verás `(.venv)` al
inicio de la línea):

```powershell
python main.py
```

Aparece la ventana de inicio de sesión.

> Ejecutalo siempre **desde la carpeta del proyecto**. El sistema carga el logo
> desde `img\`, y eso solo funciona si la carpeta de trabajo es esa.

**Credenciales iniciales:** usuario `admin` · contraseña `admin123`.
La primera vez que ingreses te pedirá cambiar la contraseña. Hacelo.

Para cerrar: usá **Cerrar Sesión** o cerrá la ventana.

---

## 5. Uso del sistema

| Módulo | Qué hace |
|--------|----------|
| Panel (Dashboard) | Resumen de productos disponibles, entradas, salidas, devoluciones y últimos movimientos. |
| Productos | Alta, edición, escaneo y exportación PDF. Agrupados por modelo, con unidades individuales, seriales, MAC y stock. |
| Movimientos | Salidas y devoluciones, historial completo y reportes PDF. Editar y eliminar es solo para `admin`. |
| Proveedores / Empleados / Vehículos | Datos maestros. El `admin` puede crear, editar y eliminar; el `supervisor` solo consulta. |
| Usuarios | Solo para `admin`. |
| Datos del sistema | Solo para `admin`: respaldo y restauración de la base de datos. |

**Roles:**
- `admin`: acceso total, incluida la gestión de usuarios, datos del sistema, datos maestros y eliminación de productos/movimientos.
- `supervisor`: opera el inventario y registra movimientos; puede consultar y editar productos y generar reportes. No gestiona usuarios, datos del sistema ni datos maestros, y no edita ni elimina movimientos ni elimina productos/grupos.

**Almacén activo:** la barra superior permite cambiar entre almacenes. Todo lo
que veas (productos, movimientos, panel) corresponde al almacén seleccionado.

**Productos con movimientos:** al eliminar un producto o un grupo, el sistema
conserva el historial de movimientos y los datos del producto en ese historial.
El producto deja de aparecer en el inventario activo. Si un código pertenece a
un producto inactivo, el escaneo permite reactivarlo (solo `admin`).

---

## 6. Escaneo con el teléfono (opcional)

El sistema puede recibir códigos de barras desde la cámara de un teléfono de la
misma red Wi-Fi.

1. El certificado de seguridad se crea solo la primera vez y necesita el comando
   `openssl` disponible en PATH. Si no lo tenés, el sistema funciona igual, pero el
   escaneo por teléfono queda deshabilitado (la consola lo indica).
2. Al iniciar, la consola muestra la dirección para el teléfono (`https://IP:8765/...`).
3. En el teléfono, abrí esa dirección y aceptá el certificado (es autofirmado,
   por eso el navegador advierte; es normal).
4. **Firewall de Windows:** la primera vez puede aparecer un aviso de Windows
   Defender. Marcá **Redes privadas** y permitir el acceso. Si no aparece y el
   teléfono no conecta, revisá el firewall manualmente y permití el puerto
   **8765 TCP** para redes privadas.

El teléfono y la PC deben estar en la **misma red Wi-Fi**.

---

## 7. Respaldos y restauración (recomendado)

Toda la información está en un solo archivo: **`inventory.db`**, en la carpeta del
proyecto.

### 7.1 Respaldo desde el sistema

1. Ingresá como `admin`.
2. Abrí **Datos del sistema** (está debajo de **Usuarios** en la barra lateral).
3. Presioná **Guardar respaldo…**.
4. Elegí la carpeta y el nombre. El nombre sugerido es
   `DigiCable_respaldo_AAAAMMDD_HHMMSS.db`.
5. Guardá el archivo en un lugar seguro, preferentemente fuera del equipo.

El respaldo usa la API de SQLite, consolida la información y queda como un único
archivo `.db`. No hace falta copiar `inventory.db-wal` ni `inventory.db-shm`.

### 7.2 Restaurar desde el sistema

1. Ingresá como `admin`.
2. Abrí **Datos del sistema**.
3. Presioná **Seleccionar respaldo…** y elegí un archivo `.db` válido.
4. Confirmá la restauración.

Antes de reemplazar la base actual, el sistema valida el archivo, crea un
**respaldo de seguridad** en `%APPDATA%\DigiCable\backups` y recién después
copia los datos. Al terminar, cierra la sesión: ingresá con los usuarios de la
base restaurada.

> No selecciones el archivo de la base activa. Si la restauración falla, la base
> actual no se reemplaza y el mensaje muestra la ruta del respaldo de seguridad.

### 7.3 Copia manual

Como alternativa avanzada, con la aplicación cerrada podés copiar
`inventory.db` a otra carpeta. Si existen `inventory.db-wal` o
`inventory.db-shm`, copialos junto con el archivo principal. Para restaurar
manualmente, reemplazá los tres archivos con la aplicación cerrada.

> Para la operación normal, usá **Datos del sistema**. La copia manual requiere
> cerrar la aplicación y puede dejar una copia inconsistente si se hace en el
> momento equivocado.

---

## 8. Problemas frecuentes

| Problema | Qué hacer |
|----------|-----------|
| `python` no se reconoce como comando | Reinstalá Python marcando **Add python.exe to PATH**. |
| `No module named 'customtkinter'` (o similar) | El entorno no está activado. Ejecutá `.venv\Scripts\Activate.ps1` y luego `python main.py`. |
| Error al activar el entorno en PowerShell | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` y repetí. |
| La ventana no abre o se cierra sola | Abrí PowerShell desde la carpeta del proyecto y ejecutá `python main.py` para ver el error en pantalla. |
| El logo no aparece | Verificá que la carpeta `img` esté dentro del proyecto y que ejecutes desde la carpeta del proyecto. |
| No se puede exportar PDF / aviso de `reportlab` | Ejecutá `python -m pip install -r requirements.txt` con el entorno activado. |
| El teléfono no conecta | Misma red Wi-Fi, firewall permitiendo el puerto 8765 y aceptar el certificado en el teléfono. |
| `[phone_scan] No se pudo generar el certificado` en consola | Falta `openssl` en PATH. Instalalo (o agregá su carpeta `bin` al PATH). El resto del sistema funciona igual. |
| `unable to open database file` o error de base de datos | La carpeta del proyecto no permite escribir. Movela a una carpeta de tu usuario (por ejemplo `Documentos`) y ejecutá de nuevo. |
| Olvidé la contraseña de `admin` | Requiere soporte técnico: hay que restablecerla en la base de datos. No borres `inventory.db`. |

**Al reportar un problema, enviá:**
- Qué estabas haciendo, paso a paso.
- El mensaje de error exacto (copiá el texto de la consola de PowerShell).
- La versión de Windows y de Python (`python --version`).

---

## 9. Envío de reportes por correo y WhatsApp

Los reportes se generan desde **Movimientos → Reportes**. Los destinos se
configuran una vez y quedan guardados en
`%APPDATA%\DigiCable\config.json`.

### 9.1 Configurar los destinos

1. Abrí **Movimientos → Reportes**.
2. En **Envío (opcional)**, presioná **Configurar destinos…**.
3. Completá:
   - **Correo destino**: por ejemplo `reportes@empresa.com`.
   - **WhatsApp destino**: número internacional sin `+`, por ejemplo
     `584121234567`. También se acepta un número local con `0` inicial; el
     sistema lo convierte a `58`.
4. Presioná **Guardar**.

### 9.2 Correo

1. Marcá **Enviar por correo (con el PDF adjunto)**.
2. Generá el reporte.

Si Outlook está instalado, el sistema abre un correo nuevo con el destino, el
asunto, el cuerpo y el PDF ya adjunto. Revisalo y pulsá **Enviar** en Outlook:
el correo no se envía automáticamente.

Si Outlook no está disponible, el sistema abre el cliente de correo
predeterminado con `mailto:` y deja el PDF copiado y seleccionado en el
Explorador para adjuntarlo con **Ctrl + V**.

### 9.3 WhatsApp

1. Marcá **Abrir WhatsApp (PDF copiado; Ctrl+V)**.
2. Generá el reporte.

El sistema copia el PDF al portapapeles, abre la carpeta con el archivo
seleccionado y abre el chat del número configurado. Para completar el envío,
pegá el PDF con **Ctrl + V** o arrastrá el archivo desde la carpeta hasta el
chat. El envío final siempre lo confirmás vos.

### 9.4 Variables de entorno (opcional)

Las variables `REPORT_EMAIL_TO` y `WHATSAPP_TO` tienen prioridad sobre la
configuración guardada. Si una variable está definida, la interfaz muestra la
leyenda **(variable de entorno)** y no se puede cambiar ese destino desde la
ventana hasta modificarla o eliminarla.

**Forma más simple: crear `run.bat`** en la carpeta del proyecto (clic
derecho → Nuevo → Documento de texto, escribir el contenido de abajo,
guardar como `run.bat`, no como `.txt`):
```bat
@echo off
set REPORT_EMAIL_TO=tu_correo_destino@ejemplo.com
set WHATSAPP_TO=584121234567
python main.py
```
Reemplazá los 2 valores por los reales. A partir de ahí, abrí el sistema
siempre con doble clic en `run.bat`, en vez de `python main.py` directo.

**Alternativa en PowerShell**, sin crear un archivo, en la misma sesión que
después abre `python main.py`:
```powershell
$env:REPORT_EMAIL_TO = "tu_correo_destino@ejemplo.com"
$env:WHATSAPP_TO = "584121234567"
python main.py
```
Esto solo dura mientras esa ventana de PowerShell esté abierta — para que
quede siempre disponible, usá `run.bat` en su lugar.

---

## 10. Notas importantes

- Cambiá la contraseña inicial `admin123` en el primer ingreso.
- Hacé respaldos periódicos desde **Datos del sistema** (sección 7).
- Revisá el correo y el mensaje de WhatsApp antes de enviarlos.
- No muevas ni renombres archivos dentro de la carpeta del proyecto.
- Para el detalle de cada pantalla, usá el **Manual de usuario**.

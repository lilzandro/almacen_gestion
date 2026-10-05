# Guía de instalación y uso en Windows — DigiCable Inventario

Esta guía explica cómo instalar y abrir el sistema en **Windows 10 u 11**, sin
Docker. Todo se ejecuta directamente con Python.

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
| Panel (Dashboard) | Resumen de productos disponibles, entradas, salidas y devoluciones, y últimos movimientos. |
| Productos | Alta, edición y baja de productos. Agrupados por modelo, con unidades individuales. |
| Movimientos | Entradas, salidas, devoluciones y asignaciones. Exportable a PDF. |
| Proveedores / Empleados / Vehículos | Registro de datos maestros. |
| Usuarios | Solo para `admin`. |

**Roles:**
- `admin`: acceso total, incluida la gestión de usuarios.
- `supervisor`: no gestiona usuarios ni elimina registros.

**Almacén activo:** la barra superior permite cambiar entre almacenes. Todo lo
que veas (productos, movimientos, panel) corresponde al almacén seleccionado.

**Productos con movimientos:** no se borran definitivamente en uso normal; el
sistema conserva el historial y el producto queda **inactivo** (baja lógica).

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

## 7. Respaldos (recomendado)

Toda la información está en un solo archivo: **`inventory.db`**, en la carpeta del
proyecto.

**Para respaldar:**
1. Cerrá el sistema (Cerrar Sesión y cerrar la ventana).
2. Copiá `inventory.db` a un USB o a otra carpeta. Si ves también archivos
   `inventory.db-wal` o `inventory.db-shm`, copialos junto con él.

**Para restaurar:** con el sistema cerrado, reemplazá `inventory.db` por la copia.

> No borres `inventory.db` salvo que quieras empezar de cero: se pierde todo el
> inventario y los usuarios.

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

## 9. Notas importantes

- Cambiá la contraseña inicial `admin123` en el primer ingreso.
- Hacé respaldos periódicos de `inventory.db` (sección 7).
- No muevas ni renombres archivos dentro de la carpeta del proyecto.

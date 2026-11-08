# 📦 DigiCable — Sistema de Control de Inventarios

Aplicación de escritorio para gestionar inventario de almacén. Desarrollada con Python y CustomTkinter, con base de datos SQLite local y exportación de reportes a PDF.

---

## Características

- Gestión de productos agrupados por modelo, con código de barras, serial, MAC y stock
- Escaneo de códigos con lector físico o con la cámara del teléfono (misma red Wi-Fi)
- Control de proveedores, empleados y vehículos
- Registro de salidas y devoluciones, con comprobantes de entrega y devolución
- Historial de movimientos con reportes diarios, semanales, mensuales, ranking y cierre crítico
- Envío de reportes por correo con PDF adjunto (Outlook) y por WhatsApp
- Respaldo y restauración de la base de datos desde **Datos del sistema**
- Control de acceso por roles (`admin` / `supervisor`)
- Exportación de inventario y movimientos a PDF

---

## Stack

| Tecnología | Uso |
|---|---|
| Python 3.11 | Lenguaje principal |
| CustomTkinter | Interfaz gráfica |
| SQLite | Base de datos local |
| reportlab | Generación de reportes PDF |
| Pillow | Logo y recursos gráficos |

---

## Instalación y ejecución local

### Requisitos

- Python 3.10 o superior
- pip

### Pasos

```bash
# Clonar repositorio
git clone <url-del-repo>
cd scanner_inventory

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar
python main.py
```

**Credenciales por defecto:** usuario `admin` · contraseña `admin123`

---

## Ejecución con Docker

Docker permite correr la app sin instalar Python ni dependencias en el host. La ventana gráfica se muestra en el escritorio del sistema operativo.

**Guías completas:**
- 📘 [Manual de usuario](docs/MANUAL_DE_USUARIO.md) — operación diaria, productos, movimientos, reportes, respaldos y roles.
- 🪟 [Guía de instalación en Windows (sin Docker)](docs/GUIA_WINDOWS.md) — instalación, uso, respaldos y problemas frecuentes.
- 🐳 [Guía de instalación en Windows con Docker](docs/GUIA_WINDOWS_DOCKER.md) — Docker Desktop + VcXsrv, uso, respaldos y problemas frecuentes.

### Linux

**Requisitos:** Docker, Docker Compose

```bash
# Permitir acceso al display (una vez por sesión)
xhost +local:docker

# Build y ejecutar
docker compose up --build
```

### Windows

**Requisitos:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) + [VcXsrv](https://sourceforge.net/projects/vcxsrv/)

**Configurar VcXsrv (una sola vez):**

1. Abrir **XLaunch**
2. Seleccionar **Multiple windows**
3. Seleccionar **Start no client**
4. ✅ Marcar **Disable access control**
5. Clic en **Finish**

```cmd
docker compose -f docker-compose.windows.yml up --build
```

### macOS

**Requisitos:** Docker Desktop + [XQuartz](https://www.xquartz.org/)

```bash
# Instalar XQuartz, luego reiniciar sesión
# En XQuartz: Preferencias → Seguridad → ✅ Permitir conexiones de clientes de red

xhost +localhost
docker compose -f docker-compose.macos.yml up --build
```

### Detener el contenedor

```bash
docker compose down
```

> La base de datos vive en `./data/inventory.db` (carpeta del proyecto) y sobrevive reinicios del contenedor. Respaldá copiando la carpeta `data/`.

---

## Estructura del proyecto

```
scanner_inventory/
├── main.py                 # Punto de entrada
├── requirements.txt
├── Dockerfile
├── docker-compose.yml            # Linux
├── docker-compose.windows.yml    # Windows (VcXsrv)
├── docker-compose.macos.yml      # macOS (XQuartz)
├── database/
│   ├── connection.py       # Conexión SQLite (WAL, FK ON, ruta por env)
│   └── repository.py       # CRUD por entidad
├── core/
│   ├── auth.py             # Login y hash de contraseña
│   ├── database_backup.py  # Respaldo y restauración SQLite
│   ├── email_report.py     # Correo con PDF adjunto (Outlook)
│   ├── export.py           # Reportes PDF (datos)
│   ├── pdf_export.py       # Render PDF (reportlab)
│   ├── phone_scan.py       # Servidor de escaneo móvil
│   ├── report_config.py    # Destinos de correo y WhatsApp
│   └── whatsapp_report.py  # Apertura de WhatsApp y PDF listo
├── ui/
│   ├── app.py              # Router de vistas
│   ├── login_frame.py
│   ├── sidebar.py
│   ├── widgets.py          # Componentes reutilizables
│   └── views/              # Una vista por módulo
├── docs/
│   ├── MANUAL_DE_USUARIO.md      # Manual de usuario completo
│   └── GUIA_WINDOWS.md           # Guía de instalación y uso en Windows
├── tests/                  # Pruebas (pytest)
├── data/                   # Base de datos persistida (Docker)
├── img/                    # Logo y recursos
└── md/                     # Documentación interna
```

---

## Consideraciones

- **Roles:** `admin` tiene acceso total, incluidos usuarios, datos del sistema y datos maestros. `supervisor` opera inventario y movimientos, pero no gestiona usuarios/datos del sistema/datos maestros ni edita o elimina movimientos.
- **Productos con movimientos:** al eliminar un producto o grupo se conserva el historial en `movement_items`; los productos inactivos se pueden reactivar desde el escaneo (solo `admin`).
- **Campos únicos:** `barcode`, `cedula` (empleados) y `placa` (vehículos) no permiten duplicados.
- **Reportes PDF:** requieren `reportlab` (incluido en `requirements.txt`). Si falta, la app abre igual y al exportar muestra un aviso para instalarlo.
- **Reportes por correo/WhatsApp:** los destinos se configuran en **Reportes → Configurar destinos** y se guardan en `%APPDATA%\DigiCable\config.json`. `REPORT_EMAIL_TO` y `WHATSAPP_TO` tienen prioridad.
- **Respaldos:** **Datos del sistema** crea un `.db` consistente y, al restaurar, un respaldo de seguridad en `%APPDATA%\DigiCable\backups`.
- **Base de datos:** SQLite en modo WAL. No requiere servidor de base de datos.
- **Primera ejecución:** la base de datos se crea automáticamente con el usuario `admin` al iniciar.

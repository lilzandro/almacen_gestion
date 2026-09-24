# 📦 DigiCable — Sistema de Control de Inventarios

Aplicación de escritorio para gestionar inventario de almacén. Desarrollada con Python y CustomTkinter, con base de datos SQLite local y exportación de reportes a PDF.

---

## Características

- Gestión de productos con código de barras, serial y MAC
- Control de proveedores, empleados y vehículos
- Registro de movimientos de stock (entrada, salida, devolución, asignación)
- Exportación de reportes a PDF
- Control de acceso por roles (`admin` / `supervisor`)
- Baja lógica de productos

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
- 👤 [Guía para el cliente](docs/GUIA_DOCKER_CLIENTE.md) — cómo abrir y usar el sistema paso a paso.
- 🛠️ [Guía de soporte técnico](docs/GUIA_DOCKER_SOPORTE.md) — instalación, operación y resolución de problemas.

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
│   ├── export.py           # Reportes PDF (datos)
│   └── pdf_export.py       # Render PDF (reportlab)
├── ui/
│   ├── app.py              # Router de vistas
│   ├── login_frame.py
│   ├── sidebar.py
│   ├── widgets.py          # Componentes reutilizables
│   └── views/              # Una vista por módulo
├── docs/
│   ├── GUIA_DOCKER_CLIENTE.md    # Guía de uso (cliente)
│   └── GUIA_DOCKER_SOPORTE.md    # Guía técnica (soporte)
├── tests/                  # Pruebas (pytest)
├── data/                   # Base de datos persistida (Docker)
├── img/                    # Logo y recursos
└── md/                     # Documentación interna
```

---

## Consideraciones

- **Roles:** `admin` tiene acceso total incluyendo gestión de usuarios. `supervisor` no puede gestionar usuarios ni eliminar registros.
- **Productos con movimientos:** `delete_product()` borra físicamente conservando el historial en `movement_items`; `deactivate_product()` los deja en estado `inactivo`.
- **Campos únicos:** `barcode`, `cedula` (empleados) y `placa` (vehículos) no permiten duplicados.
- **Reportes PDF:** requieren `reportlab` (incluido en `requirements.txt`). Si falta, la app abre igual y al exportar muestra un aviso para instalarlo.
- **Base de datos:** SQLite en modo WAL. No requiere servidor de base de datos.
- **Primera ejecución:** la base de datos se crea automáticamente con el usuario `admin` al iniciar.

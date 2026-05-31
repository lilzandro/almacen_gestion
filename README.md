# 📦 DigiCable — Sistema de Control de Inventarios

Aplicación de escritorio para gestionar inventario de almacén. Desarrollada con Python y CustomTkinter, con base de datos SQLite local y exportación a Excel.

---

## Características

- Gestión de productos con código de barras, serial y MAC
- Control de proveedores, empleados y vehículos
- Registro de movimientos de stock (entrada, salida, devolución, asignación)
- Exportación de reportes a Excel
- Control de acceso por roles (`admin` / `supervisor`)
- Baja lógica de productos

---

## Stack

| Tecnología | Uso |
|---|---|
| Python 3.11 | Lenguaje principal |
| CustomTkinter | Interfaz gráfica |
| SQLite | Base de datos local |
| openpyxl | Exportación Excel |
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
DISPLAY=host.docker.internal:0 docker compose up --build
```

### Detener el contenedor

```bash
docker compose down
```

> La base de datos (`inventory.db`) se persiste en el directorio del proyecto y sobrevive reinicios del contenedor.

---

## Estructura del proyecto

```
scanner_inventory/
├── main.py                 # Punto de entrada
├── requirements.txt
├── database/
│   ├── connection.py       # Conexión SQLite (WAL mode, FK ON)
│   └── repository.py       # CRUD por entidad
├── core/
│   ├── auth.py             # Login y hash de contraseña
│   └── export.py           # Exportación Excel
├── ui/
│   ├── app.py              # Router de vistas
│   ├── login_frame.py
│   ├── sidebar.py
│   ├── widgets.py          # Componentes reutilizables
│   └── views/              # Una vista por módulo
├── img/                    # Logo y recursos
└── md/                     # Documentación interna
```

---

## Consideraciones

- **Roles:** `admin` tiene acceso total incluyendo gestión de usuarios. `supervisor` no puede gestionar usuarios ni eliminar registros.
- **Productos con movimientos:** no se pueden eliminar físicamente. Se da de baja con estado `inactivo`.
- **Campos únicos:** `barcode`, `cedula` (empleados) y `placa` (vehículos) no permiten duplicados.
- **Base de datos:** SQLite en modo WAL. No requiere servidor de base de datos.
- **Primera ejecución:** la base de datos se crea automáticamente con el usuario `admin` al iniciar.

# DigiCable — Sistema de Control de Inventarios

Aplicación de escritorio para gestionar inventario de almacén. Permite registrar productos, proveedores, empleados, vehículos, movimientos de stock y exportar reportes Excel.

**Stack:** Python 3.11, CustomTkinter, SQLite, openpyxl, Pillow

**Credenciales por defecto:** usuario `admin`, contraseña `admin123`

---

## Instalación y ejecución local

```bash
pip install -r requirements.txt
python main.py
```

---

## Ejecución con Docker

### Linux

**Requisito:** Docker y Docker Compose instalados.

```bash
# Permitir que Docker acceda al display (una sola vez por sesión)
xhost +local:docker

# Build y ejecutar
docker compose up --build
```

### Windows

**Requisito:** Docker Desktop + [VcXsrv](https://sourceforge.net/projects/vcxsrv/) instalado.

**Configurar VcXsrv (una sola vez):**
1. Abrir **XLaunch**
2. Seleccionar **Multiple windows**
3. Seleccionar **Start no client**
4. Marcar la casilla **Disable access control**
5. Hacer clic en **Finish**

**Ejecutar la app:**
```cmd
docker compose -f docker-compose.windows.yml up --build
```

La ventana de la aplicación aparece en el escritorio del host en ambos sistemas operativos.

---

## Detener el contenedor

```bash
docker compose down
```

> La base de datos (`inventory.db`) se persiste en el directorio del proyecto y sobrevive reinicios del contenedor.

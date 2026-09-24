# Guía de Soporte Técnico — DigiCable Inventario (Docker)

Documento técnico para instalar, operar y resolver problemas del sistema
empaquetado en Docker. Para la guía de uso del usuario final ver
[`GUIA_DOCKER_CLIENTE.md`](GUIA_DOCKER_CLIENTE.md).

---

## 1. Arquitectura

- **Imagen**: `python:3.11-slim` + `python3-tk` (interfaz gráfica), `openssl`
  (certificado del escaneo por teléfono) y librerías X11.
- **App**: CustomTkinter (GUI), SQLite (datos), reportlab (reportes PDF).
- **Pantalla**: el contenedor se conecta al servidor X del host
  (Xorg/XWayland en Linux, VcXsrv en Windows, XQuartz en macOS).
- **Datos**: SQLite en `/app/data/inventory.db`, persistido en la carpeta
  `./data/` del proyecto (bind mount).
- **Escaneo por teléfono**: servidor HTTPS en el puerto **8765** con token por
  sesión y certificado autofirmado (se genera en runtime).
- **Red**:
  - Linux: `network_mode: host` (el escaneo queda expuesto con la IP del host).
  - Windows/macOS: se publica `8765:8765` (Docker Desktop no soporta host network).

---

## 2. Requisitos

| SO | Motor | Servidor X |
|----|-------|-----------|
| Linux | Docker Engine + Compose plugin | Xorg o XWayland (escritorio) |
| Windows 10/11 | Docker Desktop | [VcXsrv (XLaunch)](https://sourceforge.net/projects/vcxsrv/) |
| macOS | Docker Desktop | [XQuartz](https://www.xquartz.org/) |

Verificación rápida:

```bash
docker --version
docker compose version
```

---

## 3. Puesta en marcha

Siempre desde la raíz del proyecto.

### Linux

```bash
# Permitir que el contenedor use la pantalla (una vez por sesión o tras reiniciar)
xhost +local:docker

# Construir y ejecutar
docker compose up --build
```

Si tu sesión usa Wayland, el `docker-compose.yml` monta la cookie `XAUTHORITY`
del host. Si `XAUTHORITY` no está definido, definilo antes de levantar
(p. ej. `export XAUTHORITY=$HOME/.Xauthority`) o usá el override de abajo.

### Windows (Docker Desktop + VcXsrv)

1. Abrir **XLaunch** y configurar:
   - Multiple windows → Start no client → **Disable access control** → Finish.
2. En PowerShell, desde el proyecto:

```powershell
docker compose -f docker-compose.windows.yml up --build
```

### macOS (Docker Desktop + XQuartz)

1. Instalar XQuartz y reiniciar sesión.
2. En XQuartz: *Preferencias → Seguridad →* ✅ *Permitir conexiones de clientes de red*.
3. En una terminal:

```bash
xhost +localhost
docker compose -f docker-compose.macos.yml up --build
```

### Detener

```bash
docker compose down          # Linux
docker compose -f docker-compose.windows.yml down   # Windows
docker compose -f docker-compose.macos.yml down     # macOS
```

---

## 4. Persistencia y respaldo

- La base de datos vive en **`./data/inventory.db`** (más `inventory.db-wal`
  e `inventory.db-shm` en modo WAL).
- Se crea automáticamente en el primer arranque.

**Respaldar** (app detenida, para copia consistente):

```bash
docker compose down
cp -a data data_backup_$(date +%Y%m%d)
docker compose up
```

**Restaurar**:

```bash
docker compose down
rm -rf data && cp -a data_backup_YYYYMMDD data
docker compose up
```

> En Linux, como el contenedor corre como **root**, los archivos de `./data`
> pertenecen a `root`. Para copiarlos usá `sudo` o ejecutá `sudo chown -R
> $USER:$USER data`.

---

## 5. Variables y volúmenes

| Variable | Valor por defecto | Descripción |
|----------|-------------------|-------------|
| `INVENTORY_DB` | `/app/data/inventory.db` | Ruta de la base SQLite dentro del contenedor |
| `DISPLAY` | `:0` (Linux) / `host.docker.internal:0` | Pantalla X |
| `XAUTHORITY` | cookie del host | Autenticación X (solo Linux) |

| Volumen | Destino | Uso |
|---------|---------|-----|
| `./data` | `/app/data` | Base de datos |
| `/tmp/.X11-unix` | `/tmp/.X11-unix` | Socket X (Linux) |

Para usar otra ruta de BD (p. ej. volumen nombrado), editá `INVENTORY_DB` y el
volumen en el compose.

---

## 6. Escaneo por teléfono (puerto 8765)

- La app muestra un QR/URL (`https://<IP>:8765`) en *Productos → ¿Escaneás con
  tu teléfono?*.
- El teléfono debe estar en la **misma red** que el equipo.
- El certificado es **autofirmado**: el navegador mostrará una advertencia;
  hay que aceptarla para continuar.
- **Linux (host network)**: la URL usa la IP de la LAN del equipo. Correcto.
- **Windows/macOS (puertos)**: el contenedor no conoce la IP del host; si la URL
  del QR no coincide, abrí manualmente `https://<IP-de-la-PC>:8765` en el teléfono.
- Firewall: permitir el puerto **8765** entrante.

---

## 7. Operación y mantenimiento

```bash
# Ver logs
docker compose logs -f

# Shell dentro del contenedor
docker compose exec app bash

# Reconstruir tras cambios de código/dependencias
docker compose down
docker compose up --build

# Rebuild sin caché (si algo quedó raro)
docker compose build --no-cache
docker compose up
```

Actualizar la app: `git pull` y repetir `docker compose up --build`.

---

## 8. Solución de problemas

| Síntoma | Causa probable | Solución |
|---------|----------------|----------|
| `couldn't connect to display ":0"` / no abre la ventana | Sin acceso al servidor X | Linux: `xhost +local:docker`; Windows: VcXsrv con *Disable access control*; macOS: XQuartz + `xhost +localhost` |
| `Authorization required, but no authorization protocol specified` | Cookie X incorrecta | Definir `XAUTHORITY` o montar la cookie correcta; alternativa: `xhost +local:docker` |
| La app no arranca y `data` tiene un **directorio** `inventory.db` | Se montó el archivo en vez de la carpeta | Borrar ese directorio y usar `./data:/app/data` (este repo ya lo hace) |
| `unable to open database file` | Ruta/carpeta de BD inexistente | Verificar `INVENTORY_DB` y que `./data` exista/ser escribible |
| Los cambios de código no aparecen | Imagen vieja | `docker compose up --build` |
| El teléfono no conecta | Red distinta, firewall o URL con IP incorrecta | Misma red, abrir 8765, usar la IP de la PC; aceptar el certificado |
| `Permission denied` al copiar `./data` | Archivos propiedad de root | `sudo cp` o `sudo chown -R $USER:$USER data` |
| `reportlab` / reportes PDF fallan | Dependencia no instalada en la imagen | Reconstruir la imagen (`--build`); verificar `requirements.txt` |

---

## 9. Checklist de despliegue

- [ ] Docker y Compose instalados.
- [ ] Servidor X operativo (Xorg/XWayland, VcXsrv o XQuartz).
- [ ] `xhost` (Linux/macOS) o VcXsrv con control de acceso deshabilitado (Windows).
- [ ] Carpeta `./data` creada/escribible (se crea sola al primer arranque).
- [ ] `docker compose up --build` levanta la ventana.
- [ ] Login inicial `admin` / `admin123` y **cambio de contraseña** realizado.
- [ ] Generar un reporte PDF de prueba (Movimientos e Inventario).
- [ ] Escaneo por teléfono probado y puerto 8765 accesible.
- [ ] Respaldo de `./data` configurado.

---

## 10. Notas de seguridad

- Cambiar la contraseña por defecto `admin` en el primer ingreso (es obligatorio).
- La base SQLite se crea con permisos `600` (solo el dueño). En Docker el dueño
  es `root`.
- El certificado del escáner es autofirmado (uso en LAN); el acceso se protege
  con un token por sesión.
- `network_mode: host` (Linux) expone el puerto 8765 en la red local; usar solo
  en redes de confianza.

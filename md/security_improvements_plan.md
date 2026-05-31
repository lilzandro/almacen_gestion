# Plan de Mejoras de Seguridad para ScanStock

## Tabla de Contenidos
1. [Arquitectura General](#arquitectura-general)
2. [Mejoras de Autenticación](#mejoras-de-autenticación)
3. [Protección de la Base de Datos](#protección-de-la-base-de-datos)
4. [Seguridad en la Interfaz de Usuario (UI)](#seguridad-en-la-interfaz-de-usuario-ui)
5. [Pruebas y Validación](#pruebas-y-validación)
6. [Implementación Paso a Paso](#implementación-paso-a-paso)
7. [Recursos y Referencias](#recursos-y-referencias)

---

## Arquitectura General
- Separar claramente las responsabilidades: UI, lógica de negocio y acceso a datos.
- Utilizar patrones de diseño seguros (por ejemplo, "defense in depth").
- Mantener todas las dependencias actualizadas.

---

## Mejoras de Autenticación
1. **Hashing con Sal y Pepper**
   - Reemplazar el hash SHA-256 simple por `pbkdf2_hmac` con sal aleatoria.
   - Almacenar sal y hash en la base de datos separados por `:`.

2. **Contraseñas Fuera de Hardcoding**
   - Generar contraseñas de forma aleatoria y forzar complejidad.
   - Almacenar hashes en columnas dedicadas de la tabla `users`.

3. **MFA (Autenticación de Dos Factores) (opcional)**
   - Implementar códigos de verificación por correo o aplicación OTP.

---

## Protección de la Base de Datos
1. **Ubicación Segura del Archivo SQLite**
   - Usar un directorio del sistema con permisos restringidos (`/var/lib/scans/`).
   - Encriptar la base de datos si es posible.

2. **Cifrado de Campos Sensibles**
   - Cifrar datos como números de serie de escáneres antes de guardarlos.

3. **Acceso Solo Lectura para Operaciones Específicas**
   - Conceder permisos mínimos a usuarios de la base de datos.

---

## Seguridad en la Interfaz de Usuario (UI)
1. **Validación de Entrada**
   - Validar todos los campos de texto antes de enviarlos al backend.
   - Usar expresiones regulares para evitar inyecciones de scripts.

2. **Escape de Datos en Salidas**
   - Cuando se muestren datos en la UI, escaparlos para prevenir XSS.

3. **Mensajes de Error Seguros**
   - No revelar detalles internos del sistema en los mensajes de error.
   - Mostrar mensajes genéricos al usuario.

4. **Control de Acceso Basado en Roles**
   - Deshabilitar botones y menús según el rol del usuario.
   - Añadir verificación de permisos antes de ejecutar acciones críticas.

5. **Protección contra Clickjacking**
   - Añadir encabezados HTTP `X-Frame-Options: DENY`.

---

## Pruebas y Validación
- **Escaneo de Seguridad Automatizado**
  - Utilizar herramientas como `OWASP ZAP` o `Burp Suite`.
- **Pruebas de Penetración Manual**
  - Intentar SQL injection, XSS y otros vectores comunes.
- **Revisión de Código**
  - Realizar revisiones de seguridad entre pares.

---

## Implementación Paso a Paso
| Paso | Acción | Archivo/Modulo Afectado | Prioridad |
|------|--------|--------------------------|-----------|
| 1 | Migrar hash de contraseñas a pbkdf2 | `database/repository.py` | Alta |
| 2 | Añadir validación de usuarios | `core/auth.py` | Alta |
| 3 | Implementar escape de datos en UI | `ui/widgets.py` | Media |
| 4 | Añadir encabezados de seguridad en respuestas | `app.py` | Media |
| 5 | Configurar permisos de archivo para DB | `database/connection.py` | Baja |
| 6 | Revisar y probar todas las funcionalidades | Toda la base de código | Continua |

---

## Recursos y Referencias
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Password Hashing Competition](https://password-hashing.com/)
- [CustomTkinter Security Best Practices](https://github.com/TomSchimansky/CustomTkinter)
- [SQLite Security Recommendations](https://www.sqlite.org/security.html)

---

*Este documento está pensado como una guía para la implementación gradual de mejoras de seguridad en ScanStock, empezando por las áreas de mayor riesgo y procediendo a fortalecer la UI.*
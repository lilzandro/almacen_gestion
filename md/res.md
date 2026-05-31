ScanStock — Sistema de Inventario de Escáneres
Sistema de escritorio ligero para gestionar el inventario de escáneres del almacén: registros de entradas, asignaciones a empleados, devoluciones y genera informes Excel.

🛠 Requisitos
Python 3.10+
Las siguientes librerías (solo 2 externas):
pip install -r requirements.txt
🚀 Ejecución
python main.py
La base de datos inventory.dbse crea automáticamente en la carpeta del proyecto al primer inicio.

Credenciales por defecto
Usuario	Contraseña	Rol
administración	administrador123	Administración
📂 Estructura del Proyecto
scanner_inventory/
├── main.py                    # Punto de entrada
├── requirements.txt           # customtkinter, openpyxl
├── inventory.db               # Base de datos (generada automáticamente)
│
├── database/
│   ├── connection.py          # Conexión SQLite, inicialización de tablas
│   └── repository.py          # Todas las funciones CRUD
│
├── core/
│   ├── auth.py                # Login y hash SHA-256
│   └── export.py              # Exportación a Excel
│
├── ui/
│   ├── app.py                 # Ventana principal, router de vistas
│   ├── login_frame.py         # Pantalla de Login
│   ├── sidebar.py             # Menú lateral de navegación
│   ├── widgets.py             # Helpers (Treeview, estilos)
│   └── views/
│       ├── dashboard.py       # Resumen estadístico
│       ├── scanners.py        # CRUD Escáneres
│       ├── suppliers.py       # CRUD Proveedores
│       ├── employees.py       # CRUD Empleados
│       ├── movements.py       # Entradas / Salidas / Devoluciones
│       └── users.py           # Gestión de Usuarios (solo Admin)
│
└── docs/
    └── README.md              # Este documento
🗄 Base de Datos
La base de datos es SQLite con 5 tablas:

Unable to render rich display

Parse error on line 2:
... USERS { int id PK; string username; s
-----------------------^
Expecting 'BLOCK_STOP', 'ATTRIBUTE_WORD', ',', 'COMMENT', got ';'

For more information, see https://docs.github.com/get-started/writing-on-github/working-with-advanced-formatting/creating-diagrams#creating-mermaid-diagrams

Diagrama
    USUARIOS { int id PK; string nombre_de_usuario; string hash_de_contraseña; string rol }
    PROVEEDORES { int id PK; string nombre; string contacto; string dirección }
    EMPLEADOS { int id PK; string nombre; string departamento; string código_empleado }
    ESCÁNERES { int id PK; string model; string serial_number; string status; int supplier_id FK }
    MOVIMIENTOS { int id PK; string type; string timestamp; int scanner_id FK; int employee_id FK; int user_id FK }
    PROVEEDORES ||--o{ ESCÁNERES : "provee"
    ESCÁNERES ||--o{ MOVIMIENTOS : ""
    EMPLEADOS ||--o{ MOVIMIENTOS : "recibe"
    USUARIOS ||--o{ MOVIMIENTOS : "registra"
👥 Roles
Módulo	Administración	Usuario
Panel	✅	✅
Escáneres (ver/editar)	✅	✅
Escáneres (eliminar)	✅	❌
proveedores	✅	✅
Empalados	✅	✅
Movimientos	✅	✅
Gestión de Usuarios	✅	❌
📊 Reporteros
Desde el módulo Movimientos , el botón "📥 Exportar Excel" genera un archivo .xlsxcon todo el historial de movimientos con formato coloreado.

El módulo Escáneres incluye exportación del inventario completo con estado visual por colores (verde=disponible, naranja=asignado, rojo=mantenimiento).

⚡ Stack Tecnológico
Capa	Tecnología	Motivo
Interfaz de usuario	CustomTkinter	Ligero, moderno, modo oscuro nativo
Base Datos	sqlite3 (integrado)	Sin dependencias, extremadamente rápido
Informes	openpyxl	Genera .xlsx sin cargar pandas
Seguridad	hashlib (integrado)	SHA-256, sin dependencias externas

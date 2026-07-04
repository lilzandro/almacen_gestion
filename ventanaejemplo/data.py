# -*- coding: utf-8 -*-
"""
data.py — Configuración de catálogos y especificaciones dinámicas.

Es el equivalente Python del objeto CATEGORIAS del prototipo. Al cambiar la
categoría, la sección "Ficha técnica" se reconstruye con estas specs y se
sugiere el tipo de control de inventario + la unidad de medida.

Tipos de spec soportados:
  "select" → menú desplegable (opción única)
  "text"   → campo de texto (mono=True para códigos)
  "chips"  → selección múltiple (botones tipo etiqueta)
  "seg"    → selección única segmentada (CTkSegmentedButton)
"""

# (codigo, etiqueta visible)
UNIDADES = [
    ("und",  "Unidades (pieza)"),
    ("m",    "Metros"),
    ("caja", "Bolsas / Cajas"),
]
UNIDAD_LABEL = dict(UNIDADES)

# Tipos de control de inventario
CTRL_SERIE    = "serie"      # por N.º de serie / MAC (tabla de equipos)
CTRL_CANTIDAD = "cantidad"   # por cantidad / volumen (stock + mínimo)

# Categoría → {control por defecto, unidad por defecto, specs dinámicas}
CATEGORIAS = {
    "Equipos de Red": {
        "control": CTRL_SERIE, "unidad": "und",
        "specs": [
            {"id": "puerto_tipo", "label": "Tipo de puerto", "type": "select",
             "options": ["Gigabit (10/100/1000)", "Fast Ethernet (10/100)"]},
            {"id": "puerto_n", "label": "N.º de puertos", "type": "text",
             "placeholder": "Ej: 4", "mono": True},
            {"id": "bandas", "label": "Bandas Wi-Fi", "type": "chips",
             "options": ["2.4 GHz", "5 GHz", "6 GHz"]},
            {"id": "optico", "label": "Conector óptico", "type": "select",
             "options": ["Ninguno", "SC/APC", "SC/UPC", "LC/UPC"]},
        ],
    },
    "Cableado": {
        "control": CTRL_CANTIDAD, "unidad": "m",
        "specs": [
            {"id": "cable_tipo", "label": "Tipo", "type": "select",
             "options": ["Fibra Monomodo", "Fibra Multimodo", "Cobre UTP"]},
            {"id": "hilos", "label": "N.º de hilos", "type": "select",
             "options": ["1 hilo", "2 hilos", "4 hilos", "6 hilos", "12 hilos", "N/A"]},
            {"id": "cat", "label": "Categoría", "type": "select",
             "options": ["Cat5e", "Cat6", "Cat6A", "N/A"]},
            {"id": "resistencia", "label": "Resistencia", "type": "seg",
             "options": ["Interior", "Exterior", "Int/Ext"]},
        ],
    },
    "Conectores / Pasivos": {
        "control": CTRL_CANTIDAD, "unidad": "caja",
        "specs": [
            {"id": "con_tipo", "label": "Tipo de conector", "type": "select",
             "options": ["SC/APC", "SC/UPC", "LC", "RJ45", "Otro"]},
            {"id": "presentacion", "label": "Presentación", "type": "text",
             "placeholder": "Ej: Bolsa x 100"},
        ],
    },
    "Herramientas": {
        "control": CTRL_SERIE, "unidad": "und",
        "specs": [
            {"id": "herr_tipo", "label": "Tipo de herramienta", "type": "text",
             "placeholder": "Ej: Fusionadora, Pelacable"},
        ],
    },
    "Accesorios de Instalación": {
        "control": CTRL_CANTIDAD, "unidad": "caja",
        "specs": [
            {"id": "acc_tipo", "label": "Tipo de accesorio", "type": "text",
             "placeholder": "Ej: Grapas, Bridas, Rosetas"},
        ],
    },
}

CATEGORIA_NOMBRES = list(CATEGORIAS.keys())
PROVEEDORES = ["Sin proveedor", "Furukawa Electric", "TP-Link Andina",
               "Cisco Systems", "Distribuidora Telecom S.A."]

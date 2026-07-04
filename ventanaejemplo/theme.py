# -*- coding: utf-8 -*-
"""
theme.py — Sistema visual de "Registrar Producto" (opción C) portado a
CustomTkinter. Mapea 1:1 los tokens de color del diseño HTML y resuelve
las fuentes (IBM Plex con fallback automático).

Los colores son las mismas variables CSS del prototipo:
  --navy, --blue, --orange, --ink, --line, --bg, --ok, etc.
"""

# ── Paleta (idéntica al CSS del prototipo) ───────────────────────────────────
NAVY        = "#0c2f54"   # cabecera (azul marino de marca)
NAVY_2      = "#0a2542"   # degradado inferior de cabecera
NAVY_LINE   = "#173b63"   # borde bajo cabecera
BLUE        = "#1763a6"   # acción primaria / estados activos
BLUE_D      = "#125488"   # hover de la acción primaria
BLUE_SOFT   = "#eaf1f8"   # relleno suave (badges, chips activos suaves)
ORANGE      = "#e07d23"   # acento secundario (* requerido, foco naranja)
ORANGE_D    = "#c96a16"   # texto/hover naranja
ORANGE_SOFT = "#fdf4ea"   # fondo de alerta de stock
INK         = "#16212e"   # texto principal
INK_2       = "#5b6b7b"   # texto secundario / etiquetas
INK_3       = "#8a98a6"   # texto terciario / hints / placeholders
LINE        = "#d8e0e8"   # borde de campos
LINE_2      = "#e7ecf1"   # divisores suaves
BG          = "#f4f6f8"   # fondo del cuerpo
BG_2        = "#eef2f6"   # fondo de barras/cajas (genbar)
WHITE       = "#ffffff"
OK          = "#1f8a5b"   # verde "en stock / completado"
TITLEBAR    = "#2c3138"   # barra de título del SO
TITLEBAR_TX = "#c5ccd5"

# ── Métricas ─────────────────────────────────────────────────────────────────
RADIUS_FIELD  = 8
RADIUS_BTN    = 9
RADIUS_CARD   = 11
FIELD_H       = 38
BTN_H         = 42

# Familias preferidas → fallback. Si no tienes IBM Plex instalada, usa la
# primera disponible del sistema. (Ver guía: cómo instalar IBM Plex.)
SANS_STACK = ["IBM Plex Sans", "Segoe UI", "Helvetica Neue", "Helvetica", "Arial"]
MONO_STACK = ["IBM Plex Mono", "Cascadia Mono", "Consolas", "Menlo", "Courier New"]


def _pick(stack):
    """Devuelve la primera familia instalada del stack (requiere root Tk)."""
    import tkinter.font as tkfont
    available = set(tkfont.families())
    for fam in stack:
        if fam in available:
            return fam
    return stack[-1]


def make_fonts():
    """
    Construye el set de fuentes. DEBE llamarse DESPUÉS de crear la ventana
    raíz (CTk()), porque tkinter.font necesita un intérprete Tk activo.
    Devuelve un dict listo para pasar a los widgets.
    """
    import customtkinter as ctk
    sans = _pick(SANS_STACK)
    mono = _pick(MONO_STACK)
    return {
        "title":     ctk.CTkFont(family=sans, size=21, weight="bold"),
        "eyebrow":   ctk.CTkFont(family=sans, size=11, weight="bold"),
        "section":   ctk.CTkFont(family=sans, size=13, weight="bold"),
        "label":     ctk.CTkFont(family=sans, size=12, weight="bold"),
        "input":     ctk.CTkFont(family=sans, size=13),
        "input_mono":ctk.CTkFont(family=mono, size=13),
        "hint":      ctk.CTkFont(family=sans, size=11),
        "btn":       ctk.CTkFont(family=sans, size=14, weight="bold"),
        "counter":   ctk.CTkFont(family=mono, size=16, weight="bold"),
        "seg_title": ctk.CTkFont(family=sans, size=13, weight="bold"),
        "seg_desc":  ctk.CTkFont(family=sans, size=11),
        "chip":      ctk.CTkFont(family=sans, size=12),
        "_sans": sans, "_mono": mono,
    }

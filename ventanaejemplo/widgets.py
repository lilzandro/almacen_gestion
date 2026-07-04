# -*- coding: utf-8 -*-
"""
widgets.py — Componentes reutilizables que reproducen el lenguaje visual del
prototipo (opción C) con CustomTkinter:

  LabeledEntry      campo de texto con etiqueta + hint (+ modo mono / numérico)
  LabeledSelect     desplegable con borde claro (look de "select" del HTML)
  ChipGroup         selección múltiple tipo etiqueta (Bandas Wi-Fi)
  SegSingle         selección única segmentada (Resistencia)
  InventoryToggle   las dos tarjetas "Serie/MAC" vs "Cantidad/Volumen"
  SerialTable       tabla de equipos (serial + MAC) con generar/agregar/quitar
  section_header    cabecera numerada de sección
"""
import customtkinter as ctk
from ventanaejemplo.theme import (WHITE, INK, INK_2, INK_3, LINE, LINE_2, BG_2, BLUE, BLUE_D,
                   BLUE_SOFT, NAVY, ORANGE, ORANGE_D, ORANGE_SOFT, OK,
                   RADIUS_FIELD, RADIUS_BTN, RADIUS_CARD, FIELD_H)
from ventanaejemplo.data import CTRL_SERIE, CTRL_CANTIDAD


# ── helpers ──────────────────────────────────────────────────────────────────
def _focus_ring(entry):
    """Resalta el borde en azul al enfocar (equivalente al :focus del CSS)."""
    entry.bind("<FocusIn>",  lambda e: entry.configure(border_color=BLUE))
    entry.bind("<FocusOut>", lambda e: entry.configure(border_color=LINE))


def _label_row(master, fonts, text, required):
    row = ctk.CTkFrame(master, fg_color="transparent")
    ctk.CTkLabel(row, text=text, font=fonts["label"], text_color=INK_2).pack(side="left")
    if required:
        ctk.CTkLabel(row, text=" *", font=fonts["label"], text_color=ORANGE).pack(side="left")
    return row


def section_header(master, fonts, num, title):
    bar = ctk.CTkFrame(master, fg_color="transparent")
    badge = ctk.CTkFrame(bar, fg_color=BLUE_SOFT, corner_radius=6, width=24, height=24)
    badge.pack(side="left"); badge.pack_propagate(False)
    ctk.CTkLabel(badge, text=str(num), font=fonts["section"], text_color=BLUE).pack(expand=True)
    ctk.CTkLabel(bar, text="  " + title.upper(), font=fonts["section"],
                 text_color=NAVY).pack(side="left")
    return bar


# ── campo de texto ───────────────────────────────────────────────────────────
class LabeledEntry(ctk.CTkFrame):
    def __init__(self, master, fonts, label, placeholder="", required=False,
                 hint=None, mono=False, numeric=False, on_change=None):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self._numeric = numeric
        _label_row(self, fonts, label, required).grid(row=0, column=0, sticky="w", pady=(0, 6))
        self.entry = ctk.CTkEntry(
            self, placeholder_text=placeholder,
            font=fonts["input_mono"] if mono else fonts["input"],
            height=FIELD_H, corner_radius=RADIUS_FIELD, fg_color=WHITE,
            border_color=LINE, border_width=1, text_color=INK,
            placeholder_text_color=INK_3)
        self.entry.grid(row=1, column=0, sticky="ew")
        _focus_ring(self.entry)
        if numeric:
            self.entry.bind("<KeyRelease>", self._filter_numeric)
        if on_change:
            self.entry.bind("<KeyRelease>", lambda e: on_change(), add="+")
        if hint:
            ctk.CTkLabel(self, text=hint, font=fonts["hint"], text_color=INK_3,
                         anchor="w", justify="left").grid(row=2, column=0, sticky="w", pady=(5, 0))

    def _filter_numeric(self, _e):
        v = self.entry.get()
        clean = "".join(c for c in v if c.isdigit() or c == ".")
        if clean != v:
            self.entry.delete(0, "end"); self.entry.insert(0, clean)

    def get(self): return self.entry.get()
    def set(self, v):
        self.entry.delete(0, "end"); self.entry.insert(0, v)


# ── desplegable (look "select" claro con borde) ──────────────────────────────
class LabeledSelect(ctk.CTkFrame):
    def __init__(self, master, fonts, label, values, required=False, hint=None,
                 placeholder="Seleccionar…", command=None):
        super().__init__(master, fg_color="transparent")
        self.columnconfigure(0, weight=1)
        self._cmd = command
        _label_row(self, fonts, label, required).grid(row=0, column=0, sticky="w", pady=(0, 6))
        wrap = ctk.CTkFrame(self, fg_color=WHITE, border_color=LINE, border_width=1,
                            corner_radius=RADIUS_FIELD, height=FIELD_H)
        wrap.grid(row=1, column=0, sticky="ew"); wrap.grid_propagate(False)
        self.var = ctk.StringVar(value=placeholder)
        self.menu = ctk.CTkOptionMenu(
            wrap, values=values, variable=self.var, command=self._on,
            font=fonts["input"], height=FIELD_H - 6, corner_radius=6,
            fg_color=WHITE, button_color=WHITE, button_hover_color=BG_2,
            text_color=INK, dropdown_fg_color=WHITE, dropdown_text_color=INK,
            dropdown_hover_color=BLUE_SOFT, dropdown_font=fonts["input"], anchor="w")
        self.menu.pack(fill="both", expand=True, padx=2, pady=2)
        if hint:
            ctk.CTkLabel(self, text=hint, font=fonts["hint"], text_color=INK_3,
                         anchor="w").grid(row=2, column=0, sticky="w", pady=(5, 0))

    def _on(self, value):
        if self._cmd:
            self._cmd(value)

    def get(self): return self.var.get()
    def set(self, v): self.var.set(v)
    def set_values(self, values): self.menu.configure(values=values)


# ── chips (selección múltiple) ───────────────────────────────────────────────
class ChipGroup(ctk.CTkFrame):
    def __init__(self, master, fonts, options):
        super().__init__(master, fg_color="transparent")
        self._sel = set()
        self._btns = {}
        for o in options:
            b = ctk.CTkButton(self, text=o, font=fonts["chip"], height=32,
                              corner_radius=999, fg_color=WHITE, text_color=INK_2,
                              border_color=LINE, border_width=1, hover_color=BG_2,
                              command=lambda v=o: self._toggle(v))
            b.pack(side="left", padx=(0, 8))
            self._btns[o] = b

    def _toggle(self, o):
        if o in self._sel:
            self._sel.discard(o)
            self._btns[o].configure(fg_color=WHITE, text_color=INK_2, border_color=LINE, hover_color=BG_2)
        else:
            self._sel.add(o)
            self._btns[o].configure(fg_color=BLUE, text_color=WHITE, border_color=BLUE, hover_color=BLUE_D)

    def get(self): return sorted(self._sel)


# ── selección única segmentada ───────────────────────────────────────────────
class SegSingle(ctk.CTkFrame):
    def __init__(self, master, fonts, options):
        super().__init__(master, fg_color="transparent")
        self.seg = ctk.CTkSegmentedButton(
            self, values=options, font=fonts["chip"], corner_radius=RADIUS_FIELD,
            fg_color=BG_2, selected_color=BLUE, selected_hover_color=BLUE_D,
            unselected_color=BG_2, unselected_hover_color=LINE,
            text_color=INK_2, text_color_disabled=INK_3)
        self.seg.pack(anchor="w")

    def get(self): return self.seg.get()


# ── toggle de control de inventario (dos tarjetas) ───────────────────────────
class InventoryToggle(ctk.CTkFrame):
    def __init__(self, master, fonts, command):
        super().__init__(master, fg_color="transparent")
        self._cmd = command
        self.var = ctk.StringVar(value=CTRL_SERIE)
        self.columnconfigure((0, 1), weight=1, uniform="seg")
        self._cards = {}
        self._make(0, CTRL_SERIE, "Por N.º de Serie / MAC",
                   "Equipos asignados individualmente a un cliente (routers, módems, ONT).", fonts)
        self._make(1, CTRL_CANTIDAD, "Por Cantidad / Volumen",
                   "Material que se consume por partes (rollos de cable, conectores).", fonts)
        self._refresh()

    def _make(self, col, value, title, desc, fonts):
        card = ctk.CTkFrame(self, fg_color=WHITE, border_width=2, border_color=LINE,
                            corner_radius=RADIUS_CARD)
        card.grid(row=0, column=col, sticky="ew",
                  padx=(0, 5) if col == 0 else (5, 0))
        card.columnconfigure(1, weight=1)
        rb = ctk.CTkRadioButton(card, text="", value=value, variable=self.var,
                                width=22, radiobutton_width=18, radiobutton_height=18,
                                fg_color=BLUE, border_color=LINE, hover_color=BLUE,
                                command=lambda: self._select(value))
        rb.grid(row=0, column=0, rowspan=2, padx=(14, 10), pady=14, sticky="n")
        t = ctk.CTkLabel(card, text=title, font=fonts["seg_title"], text_color=INK,
                         anchor="w", justify="left")
        t.grid(row=0, column=1, sticky="w", pady=(13, 1), padx=(0, 14))
        d = ctk.CTkLabel(card, text=desc, font=fonts["seg_desc"], text_color=INK_2,
                         anchor="w", justify="left", wraplength=300)
        d.grid(row=1, column=1, sticky="w", pady=(0, 13), padx=(0, 14))
        for w in (card, t, d):
            w.bind("<Button-1>", lambda e, v=value: self._select(v))
        self._cards[value] = card

    def _select(self, value):
        self.var.set(value)
        self._refresh()
        if self._cmd:
            self._cmd(value)

    def _refresh(self):
        for v, card in self._cards.items():
            on = (v == self.var.get())
            card.configure(border_color=BLUE if on else LINE,
                           fg_color=BLUE_SOFT if on else WHITE)

    def get(self): return self.var.get()
    def set(self, mode):
        self.var.set(mode); self._refresh()


# ── tabla de seriales / MAC ──────────────────────────────────────────────────
# Columnas: [sin] [#] [serial] [mac (?)] [quitar]


class SerialTable(ctk.CTkFrame):
    def __init__(self, master, fonts, on_count_change=None, show_mac=True):
        super().__init__(master, fg_color="transparent")
        self.fonts = fonts
        self.on_count_change = on_count_change
        self.show_mac = show_mac
        self.rows = []

        # Columnas dinámicas
        self._col_headers = ["Sin", "#", "Serial"]
        self._col_widths = [(40,), (34,), (None,)]
        if show_mac:
            self._col_headers.append("MAC  (AA-BB-CC-DD-EE-FF)")
            self._col_widths.append((None,))
        self._col_headers.append("")
        self._col_widths.append((44,))

        self._col_keys = ["chk", "num", "serial"]
        if show_mac:
            self._col_keys.append("mac")
        self._col_keys.append("xbtn")

        # Barra "Generar filas"
        gen = ctk.CTkFrame(self, fg_color=BG_2, corner_radius=RADIUS_FIELD)
        gen.pack(fill="x", pady=(0, 12))
        gen_label = "Cantidad de equipos" if show_mac else "Cantidad de herramientas"
        ctk.CTkLabel(gen, text=gen_label, font=fonts["label"],
                     text_color=NAVY).pack(side="left", padx=(14, 10), pady=12)
        self.gen_n = ctk.CTkEntry(gen, width=78, height=34, placeholder_text="Ej: 5",
                                  font=fonts["input_mono"], fg_color=WHITE,
                                  border_color=LINE, border_width=1, corner_radius=RADIUS_FIELD,
                                  text_color=INK, placeholder_text_color=INK_3)
        self.gen_n.pack(side="left", pady=12)
        _focus_ring(self.gen_n)
        ctk.CTkButton(gen, text="▸ Generar filas", font=fonts["chip"], height=34,
                      corner_radius=RADIUS_FIELD, fg_color=WHITE, text_color=BLUE,
                      border_color=LINE, border_width=1, hover_color=BLUE_SOFT,
                      command=self.generar).pack(side="left", padx=10, pady=12)

        # Tabla
        table = ctk.CTkFrame(self, fg_color=WHITE, border_color=LINE, border_width=1,
                             corner_radius=RADIUS_FIELD)
        table.pack(fill="x")
        head = ctk.CTkFrame(table, fg_color=NAVY, corner_radius=0)
        head.pack(fill="x")
        self._config_cols(head)
        for c, txt in enumerate(self._col_headers):
            ctk.CTkLabel(head, text=txt, font=fonts["hint"], text_color="#cfe0f0",
                         anchor="w").grid(row=0, column=c, sticky="w", padx=10, pady=8)
        self.holder = ctk.CTkFrame(table, fg_color="transparent")
        self.holder.pack(fill="x")
        self._config_cols(self.holder)
        foot = ctk.CTkFrame(table, fg_color="#fafbfc", corner_radius=0)
        foot.pack(fill="x")
        ctk.CTkButton(foot, text="+ Agregar equipo", font=fonts["chip"], height=34,
                      corner_radius=RADIUS_FIELD, fg_color=WHITE, text_color=BLUE,
                      border_color=LINE, border_width=1, hover_color=BLUE_SOFT,
                      command=self.add_row).pack(side="left", padx=12, pady=10)

        self.add_row()

    def _col_index(self, name):
        return self._col_keys.index(name)

    def _config_cols(self, frame):
        for c, w in enumerate(self._col_widths):
            if w[0] is None:
                frame.columnconfigure(c, weight=1, uniform="serial")
            else:
                frame.columnconfigure(c, minsize=w[0])

    def add_row(self):
        row = {}
        idx = len(self.rows)
        chk_var = ctk.StringVar(value="off")
        chk = ctk.CTkCheckBox(self.holder, text="", variable=chk_var, onvalue="on",
                              offvalue="off", checkbox_width=18, checkbox_height=18,
                              corner_radius=5, fg_color=NAVY, border_color=LINE,
                              hover_color=NAVY, width=18,
                              command=lambda: self._toggle_sin(row))
        num = ctk.CTkLabel(self.holder, text=str(idx + 1), font=self.fonts["input_mono"],
                           text_color=INK_3)
        serial = ctk.CTkEntry(self.holder, height=32, font=self.fonts["input_mono"],
                              placeholder_text="SN-…", fg_color=WHITE, border_color=LINE,
                              border_width=1, corner_radius=RADIUS_FIELD, text_color=INK,
                              placeholder_text_color=INK_3)
        rr = idx
        chk.grid(row=rr, column=self._col_index("chk"), padx=10, pady=5)
        num.grid(row=rr, column=self._col_index("num"), padx=10, pady=5)
        serial.grid(row=rr, column=self._col_index("serial"), padx=6, pady=5, sticky="ew")
        row["chk"] = chk
        row["chk_var"] = chk_var
        row["num"] = num
        row["serial"] = serial

        if self.show_mac:
            mac = ctk.CTkEntry(self.holder, height=32, font=self.fonts["input_mono"],
                               placeholder_text="AA-BB-CC-DD-EE-FF", fg_color=WHITE,
                               border_color=LINE, border_width=1, corner_radius=RADIUS_FIELD,
                               text_color=INK, placeholder_text_color=INK_3)
            _focus_ring(mac)
            mac.grid(row=rr, column=self._col_index("mac"), padx=6, pady=5, sticky="ew")
            row["mac"] = mac

        _focus_ring(serial)
        xbtn = ctk.CTkButton(self.holder, text="✕", width=28, height=28,
                             corner_radius=6, fg_color=WHITE, text_color=ORANGE_D,
                             border_color="#f0d3b5", border_width=1, hover_color=ORANGE_SOFT,
                             command=lambda: self.remove_row(row))
        xbtn.grid(row=rr, column=self._col_index("xbtn"), padx=8, pady=5)
        row["xbtn"] = xbtn

        self.rows.append(row)
        self._renumber()
        self._notify()

    def _toggle_sin(self, row):
        sin = row["chk_var"].get() == "on"
        state = "disabled" if sin else "normal"
        for key in ("serial", "mac") if self.show_mac else ("serial",):
            e = row[key]
            e.delete(0, "end")
            e.configure(state=state)

    def remove_row(self, row):
        for key in self._col_keys:
            row[key].destroy()
        self.rows.remove(row)
        self._renumber()
        self._notify()

    def generar(self):
        try:
            n = max(0, min(200, int(self.gen_n.get() or 0)))
        except ValueError:
            n = 0
        for row in list(self.rows):
            self.remove_row(row)
        for _ in range(n):
            self.add_row()

    def _renumber(self):
        for i, row in enumerate(self.rows):
            row["num"].configure(text=str(i + 1))
            for key in self._col_keys:
                row[key].grid_configure(row=i)

    def _notify(self):
        if self.on_count_change:
            self.on_count_change(len(self.rows))

    def count(self): return len(self.rows)

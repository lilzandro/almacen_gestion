# -*- coding: utf-8 -*-
"""
registrar_producto.py — Implementación de referencia de la OPCIÓN C
(formulario en una sola columna con scroll) usando CustomTkinter.

Ejecuta:  python registrar_producto.py
Requiere: pip install customtkinter

Lógica dinámica incluida:
  • Al cambiar la CATEGORÍA se reconstruyen las specs técnicas y se sugiere
    el control de inventario + la unidad de medida.
  • El TIPO DE CONTROL alterna entre la tabla de seriales/MAC y los campos
    de cantidad/mínimo (con alerta de stock bajo).
  • El contador de la cabecera se actualiza solo.
"""
import customtkinter as ctk

from ventanaejemplo.theme import (make_fonts, BG, BG_2, WHITE, NAVY, NAVY_2, NAVY_LINE, BLUE,
                   BLUE_D, INK, INK_2, INK_3, LINE, LINE_2, ORANGE, ORANGE_D,
                   ORANGE_SOFT, OK, RADIUS_BTN, RADIUS_FIELD, BTN_H)
from ventanaejemplo.data import (CATEGORIAS, CATEGORIA_NOMBRES, UNIDADES, UNIDAD_LABEL,
                  PROVEEDORES, CTRL_SERIE, CTRL_CANTIDAD)
from ventanaejemplo.widgets import (LabeledEntry, LabeledSelect, ChipGroup, SegSingle,
                     InventoryToggle, SerialTable, section_header)


class RegistrarProducto(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        self.title("Registrar Producto")
        self.geometry("1040x720")
        self.minsize(860, 600)
        self.configure(fg_color=BG)

        self.fonts = make_fonts()
        self.control_mode = CTRL_SERIE
        self.spec_widgets = {}        # id -> widget (para leer valores)
        self.serial_table = None

        self._build_header()
        self._build_footer()    # reservar el footer ANTES del cuerpo expansible
        self._build_body()      # (si no, el body con expand=True lo recortaría)

        # Estado inicial = primera categoría
        self.on_categoria_change(CATEGORIA_NOMBRES[0])

    # ── Cabecera azul marino con contador ────────────────────────────────────
    def _build_header(self):
        h = ctk.CTkFrame(self, fg_color=NAVY, corner_radius=0, height=72)
        h.pack(fill="x", side="top"); h.pack_propagate(False)
        left = ctk.CTkFrame(h, fg_color="transparent")
        left.pack(side="left", padx=24, pady=14)
        ctk.CTkLabel(left, text="INVENTARIO · NUEVO ÍTEM", font=self.fonts["eyebrow"],
                     text_color="#86a7c9").pack(anchor="w")
        ctk.CTkLabel(left, text="REGISTRAR PRODUCTO", font=self.fonts["title"],
                     text_color=WHITE).pack(anchor="w")

        pill = ctk.CTkFrame(h, fg_color=NAVY_2, corner_radius=999)
        pill.pack(side="right", padx=24)
        self.counter_num = ctk.CTkLabel(pill, text="1", font=self.fonts["counter"],
                                        text_color=WHITE)
        self.counter_num.pack(side="left", padx=(14, 6), pady=7)
        self.counter_unit = ctk.CTkLabel(pill, text="EQUIPO", font=self.fonts["eyebrow"],
                                         text_color="#9fbcd8")
        self.counter_unit.pack(side="left", padx=(0, 14))

    # ── Cuerpo con scroll (3 secciones) ──────────────────────────────────────
    def _build_body(self):
        self.body = ctk.CTkScrollableFrame(self, fg_color=BG)
        self.body.pack(fill="both", expand=True)
        self.body.columnconfigure(0, weight=1)

        self._build_seccion_basica()
        self._divider()
        self._build_seccion_existencias()
        self._divider()
        self._build_seccion_tecnica()

    def _divider(self):
        ctk.CTkFrame(self.body, fg_color=LINE_2, height=1).pack(fill="x", padx=24)

    def _section(self, num, title):
        sec = ctk.CTkFrame(self.body, fg_color="transparent")
        sec.pack(fill="x", padx=24, pady=22)
        sec.columnconfigure((0, 1), weight=1, uniform="col")
        section_header(sec, self.fonts, num, title).grid(
            row=0, column=0, columnspan=2, sticky="w", pady=(0, 16))
        return sec

    @staticmethod
    def _place(widget, row, col, span=1, pady=(0, 14)):
        padx = 0 if span == 2 else ((0, 9) if col == 0 else (9, 0))
        widget.grid(row=row, column=col, columnspan=span, sticky="ew", padx=padx, pady=pady)

    # ── Sección 1 — Identificación e información básica ──────────────────────
    def _build_seccion_basica(self):
        sec = self._section(1, "Identificación e información básica")
        f = self.fonts
        self.in_nombre = LabeledEntry(sec, f, "Nombre del producto", required=True,
                                      placeholder="Router ONT Huawei…",
                                      hint="Ej: Router ONT Huawei HG8245H")
        self.in_sku = LabeledEntry(sec, f, "Código interno / SKU", mono=True,
                                   placeholder="RED-ONT-0042",
                                   hint="Identificador único de almacén")
        self.in_categoria = LabeledSelect(sec, f, "Categoría", CATEGORIA_NOMBRES,
                                          required=True, placeholder="Seleccionar categoría…",
                                          command=self.on_categoria_change)
        self.in_marca = LabeledEntry(sec, f, "Marca / Fabricante",
                                     placeholder="Huawei, Cisco, Furukawa…")
        self.in_modelo = LabeledEntry(sec, f, "Modelo", mono=True, placeholder="HG8245H")
        self.in_proveedor = LabeledSelect(sec, f, "Proveedor", PROVEEDORES,
                                          placeholder="Sin proveedor")

        self._place(self.in_nombre, 1, 0)
        self._place(self.in_sku, 1, 1)
        self._place(self.in_categoria, 2, 0, span=2)
        self._place(self.in_marca, 3, 0)
        self._place(self.in_modelo, 3, 1)
        self._place(self.in_proveedor, 4, 0, span=2, pady=(0, 0))

    # ── Sección 2 — Control de existencias y trazabilidad ────────────────────
    def _build_seccion_existencias(self):
        sec = self._section(2, "Control de existencias y trazabilidad")
        f = self.fonts
        self.in_unidad = LabeledSelect(sec, f, "Unidad de medida",
                                       [u[1] for u in UNIDADES],
                                       command=lambda _v: self.update_counter())
        self.in_ubicacion = LabeledEntry(sec, f, "Ubicación física",
                                         placeholder="Bodega Norte · Pasillo A · Estante 2",
                                         hint="Bodega · Pasillo · Estante")
        self._place(self.in_unidad, 1, 0)
        self._place(self.in_ubicacion, 1, 1)

        ctk.CTkLabel(sec, text="Tipo de control de inventario", font=f["label"],
                     text_color=INK_2).grid(row=2, column=0, columnspan=2, sticky="w", pady=(2, 6))
        self.inv_toggle = InventoryToggle(sec, f, command=self.set_control)
        self.inv_toggle.grid(row=3, column=0, columnspan=2, sticky="ew", pady=(0, 14))

        # Área dinámica (tabla de seriales  ó  campos de cantidad)
        self.exist_dyn = ctk.CTkFrame(sec, fg_color="transparent")
        self.exist_dyn.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.exist_dyn.columnconfigure((0, 1), weight=1, uniform="col")

    def set_control(self, mode):
        """Reconstruye el área dinámica según el tipo de control elegido."""
        self.control_mode = mode
        for w in self.exist_dyn.winfo_children():
            w.destroy()
        self.serial_table = None
        f = self.fonts

        if mode == CTRL_SERIE:
            lbl = ctk.CTkLabel(self.exist_dyn, text="Equipos / unidades a registrar",
                               font=f["label"], text_color=INK_2)
            lbl.grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
            self.serial_table = SerialTable(self.exist_dyn, f,
                                            on_count_change=lambda _n: self.update_counter())
            self.serial_table.grid(row=1, column=0, columnspan=2, sticky="ew")
        else:
            self.in_stock = LabeledEntry(self.exist_dyn, f, "Cantidad actual en stock",
                                         numeric=True, mono=True, placeholder="Ej: 1500",
                                         on_change=self._on_stock_change)
            self.in_minimo = LabeledEntry(self.exist_dyn, f, "Punto de pedido (stock mínimo)",
                                          numeric=True, mono=True, placeholder="Ej: 300",
                                          on_change=self._on_stock_change,
                                          hint="Dispara la alerta de reposición para los técnicos.")
            self._place(self.in_stock, 0, 0)
            self._place(self.in_minimo, 0, 1)
            self.alert = ctk.CTkFrame(self.exist_dyn, fg_color=ORANGE_SOFT,
                                      border_color="#f3dcc1", border_width=1,
                                      corner_radius=RADIUS_FIELD)
            self.alert_lbl = ctk.CTkLabel(self.alert, text="", font=f["hint"],
                                          text_color="#8a5212", justify="left", wraplength=560)
            self.alert_lbl.pack(anchor="w", padx=13, pady=10)
        self.update_counter()

    def _on_stock_change(self):
        self.update_counter()
        self._check_alert()

    def _check_alert(self):
        if self.control_mode != CTRL_CANTIDAD:
            return
        s, m = self.in_stock.get(), self.in_minimo.get()
        try:
            bajo = s != "" and m != "" and float(s) <= float(m)
        except ValueError:
            bajo = False
        if bajo:
            unidad = self._unidad_code()
            self.alert_lbl.configure(
                text=f"⚠  Por debajo del punto de pedido. El stock ({s} {unidad}) es igual o "
                     f"menor al mínimo definido. Se recomienda solicitar reposición.")
            self.alert.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 0))
        else:
            self.alert.grid_forget()

    # ── Sección 3 — Ficha técnica y especificaciones ─────────────────────────
    def _build_seccion_tecnica(self):
        sec = self._section(3, "Ficha técnica y especificaciones")
        f = self.fonts
        ctk.CTkLabel(sec, text="Descripción funcional", font=f["label"],
                     text_color=INK_2).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 6))
        self.in_desc = ctk.CTkTextbox(sec, height=70, font=f["input"], fg_color=WHITE,
                                      border_color=LINE, border_width=1, corner_radius=RADIUS_FIELD,
                                      text_color=INK, wrap="word")
        self.in_desc.grid(row=2, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        self.cat_badge = ctk.CTkLabel(sec, text="", font=f["hint"], text_color=INK_2)
        self.cat_badge.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 12))

        self.specs_holder = ctk.CTkFrame(sec, fg_color="transparent")
        self.specs_holder.grid(row=4, column=0, columnspan=2, sticky="ew")
        self.specs_holder.columnconfigure((0, 1), weight=1, uniform="col")

    def render_specs(self, specs):
        for w in self.specs_holder.winfo_children():
            w.destroy()
        self.spec_widgets = {}
        f = self.fonts
        if not specs:
            ctk.CTkLabel(self.specs_holder,
                         text="Esta categoría no requiere especificaciones técnicas adicionales.",
                         font=f["hint"], text_color=INK_3).grid(
                row=0, column=0, columnspan=2, sticky="w")
            return
        r = 0
        col = 0
        for sp in specs:
            span = 2 if sp["type"] == "chips" else 1
            if sp["type"] == "select":
                place = val = LabeledSelect(self.specs_holder, f, sp["label"], sp["options"])
            elif sp["type"] in ("chips", "seg"):
                # contenedor con etiqueta encima; el control se crea DENTRO de él
                place = ctk.CTkFrame(self.specs_holder, fg_color="transparent")
                ctk.CTkLabel(place, text=sp["label"], font=f["label"], text_color=INK_2,
                             anchor="w").pack(anchor="w", pady=(0, 6))
                val = (ChipGroup(place, f, sp["options"]) if sp["type"] == "chips"
                       else SegSingle(place, f, sp["options"]))
                val.pack(anchor="w", fill="x")
            else:
                place = val = LabeledEntry(self.specs_holder, f, sp["label"],
                                           placeholder=sp.get("placeholder", ""), mono=sp.get("mono", False))
            if span == 2:
                col = 0
                place.grid(row=r, column=0, columnspan=2, sticky="ew", pady=(0, 14))
                r += 1
            else:
                padx = (0, 9) if col == 0 else (9, 0)
                place.grid(row=r, column=col, sticky="ew", padx=padx, pady=(0, 14))
                col += 1
                if col > 1:
                    col = 0; r += 1
            self.spec_widgets[sp["id"]] = val   # widget que expone .get()

    # ── Lógica de categoría ──────────────────────────────────────────────────
    def on_categoria_change(self, nombre):
        cfg = CATEGORIAS.get(nombre)
        if not cfg:
            return
        self.in_categoria.set(nombre)
        # Sugerir unidad y control por defecto de la categoría
        self.in_unidad.set(UNIDAD_LABEL[cfg["unidad"]])
        self.inv_toggle.set(cfg["control"])
        self.set_control(cfg["control"])
        # Reconstruir specs técnicas
        self.cat_badge.configure(text=f"Especificaciones para  ·  {nombre}")
        self.render_specs(cfg["specs"])

    # ── Contador de cabecera ─────────────────────────────────────────────────
    def _unidad_code(self):
        label = self.in_unidad.get()
        for code, lab in UNIDADES:
            if lab == label:
                return code
        return "und"

    def update_counter(self):
        if self.control_mode == CTRL_SERIE and self.serial_table is not None:
            n = self.serial_table.count()
            self.counter_num.configure(text=str(n))
            self.counter_unit.configure(text=("EQUIPO" if n == 1 else "EQUIPOS"))
        else:
            stock = getattr(self, "in_stock", None)
            val = stock.get() if stock else ""
            self.counter_num.configure(text=val if val != "" else "0")
            self.counter_unit.configure(text=self._unidad_code().upper())

    # ── Footer ───────────────────────────────────────────────────────────────
    def _build_footer(self):
        f = ctk.CTkFrame(self, fg_color=WHITE, corner_radius=0, height=72)
        f.pack(fill="x", side="bottom"); f.pack_propagate(False)
        ctk.CTkFrame(f, fg_color=LINE, height=1).pack(fill="x", side="top")
        inner = ctk.CTkFrame(f, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=24)
        ctk.CTkLabel(inner, text="Desplázate para ver todas las secciones",
                     font=self.fonts["hint"], text_color=INK_3).pack(side="left")
        ctk.CTkButton(inner, text="✓ Guardar producto", font=self.fonts["btn"],
                      height=BTN_H, corner_radius=RADIUS_BTN, fg_color=BLUE,
                      hover_color=BLUE_D, text_color=WHITE,
                      command=self.guardar).pack(side="right", padx=(12, 0), pady=14)
        ctk.CTkButton(inner, text="✕ Cancelar", font=self.fonts["btn"], height=BTN_H,
                      corner_radius=RADIUS_BTN, fg_color=WHITE, text_color=ORANGE_D,
                      border_color="#f0d3b5", border_width=1, hover_color=ORANGE_SOFT,
                      command=self.cancelar).pack(side="right", pady=14)

    # ── Acciones ─────────────────────────────────────────────────────────────
    def recolectar(self):
        """Devuelve un dict con todos los datos del formulario."""
        data = {
            "nombre": self.in_nombre.get(),
            "sku": self.in_sku.get(),
            "categoria": self.in_categoria.get(),
            "marca": self.in_marca.get(),
            "modelo": self.in_modelo.get(),
            "proveedor": self.in_proveedor.get(),
            "unidad": self._unidad_code(),
            "ubicacion": self.in_ubicacion.get(),
            "control": self.control_mode,
            "descripcion": self.in_desc.get("1.0", "end").strip(),
            "specs": {sid: w.get() for sid, w in self.spec_widgets.items()},
        }
        if self.control_mode == CTRL_SERIE and self.serial_table:
            data["equipos"] = [
                {"serial": r["serial"].get(), "mac": r["mac"].get(),
                 "sin": r["chk_var"].get() == "on"}
                for r in self.serial_table.rows]
        else:
            data["stock"] = getattr(self, "in_stock", None) and self.in_stock.get()
            data["minimo"] = getattr(self, "in_minimo", None) and self.in_minimo.get()
        return data

    def guardar(self):
        data = self.recolectar()
        # Validación mínima: nombre + categoría
        faltan = []
        if not data["nombre"]:
            faltan.append("Nombre")
            self.in_nombre.entry.configure(border_color=ORANGE)
        if not data["categoria"] or data["categoria"].startswith("Seleccionar"):
            faltan.append("Categoría")
        if faltan:
            print("⚠ Faltan campos obligatorios:", ", ".join(faltan))
            return
        print("✓ Producto a guardar:")
        for k, v in data.items():
            print(f"   {k}: {v}")

    def cancelar(self):
        self.destroy()


if __name__ == "__main__":
    RegistrarProducto().mainloop()

# Auditoría de ventanas emergentes (popups)

**Fecha:** 2026-11-01
**Plan:** `docs/superpowers/plans/2026-11-01-auditoria-ventanas-emergentes.md`
**Técnica:** root mapeado fuera de pantalla (`1400x900+3000+3000`, nunca `withdraw`),
bombeo del loop ~600ms, comparación de `geometry()` declarado vs
`winfo_reqwidth()/winfo_reqheight()` del contenido real, y verificación de
que ningún botón quede por debajo del borde inferior del diálogo.

**Datos:** instanciados con datos reales de `inventory.db` (4 empleados,
4 proveedores, 2 vehículos, 18 productos, 24 movimientos). Para los diálogos
de contenido variable (`_EmpDialog`, `_UserDialog`, `_SupplierDialog`,
`_VehicleDialog`, `_GroupEditDialog`) se usó el caso de nombre más largo
disponible en la BD.

---

## Resultado: tabla de auditoría

| Diálogo | Declarado (WxH) | Real (WxH) | Contenido pide (WxH) | ¿Entra? | Botones fuera | Notas |
|---------|-----------------|------------|----------------------|---------|---------------|-------|
| `_EmpDialog` | 550x420 | 550x420 | 412x350 | Sí | — | resizable(T,T). Nombre más largo: "José Luis Rondón" |
| `_UserDialog` | 500x420 | 500x420 | 400x350 | Sí | — | resizable(T,T). Username largo de prueba |
| `_VehicleDialog` | 550x400 | 550x400 | 421x350 | Sí | — | resizable(T,T). Datos de vehículo real |
| `_SupplierDialog` | 550x400 | 550x400 | 436x350 | Sí | — | resizable(T,T). Nombre más largo: "Distribuidora Telecom S.A." |
| `_GroupEditDialog` | 450x560 | 450x560 | 318x410 | Sí | — | resizable(F,F) — prioridad. Con 12 unidades y proveedor |
| `_BarcodeScanDialog` | 460x240 | 460x240 | 339x188 | Sí | — | resizable(F,F) — prioridad |
| `_ScanRowDialog` | 460x200 | 460x200 | 264x148 | Sí | — | resizable(F,F) — prioridad |
| `_PhoneScanHelpDialog` | 480x620 | 480x620 | 400x538 | Sí | — | resizable(F,F) — prioridad. QR + 4 pasos |
| `_ScanResultDialog` | 480x560 | 480x560 | 412x238 | Sí | — | resizable(F,F) — prioridad. Probado sin row (`_build_notfound`) |
| `_ProductDialog` | 500x550 | 500x550 | 584x565 | **No** | — | **HALLAZGO**. resizable(T,T). Nombre/marca largos |
| `_MovementInfoDialog` | 960x800 | 960x800 | 256x432 | Sí | — | CTkScrollableFrame. Movimiento real de BD (5 ítems) |
| `_MovementDialog` | 900x750 | 900x748 | 661x748 | Sí (justo) | — | resizable(T,T). Alto real 748 == contenido 748 (límite) |
| `_ForceChangePasswordDialog` | 400x380 | 400x380 | 300x320 | Sí | — | resizable(F,F) — prioridad. Primer login |
| `DashboardView._show_movement_detail` | 720x780 | 720x780 | 320x366 | Sí | — | CTkToplevel directo (no hereda de BaseDialog) |

**Resumen:** 14 de 14 diálogos auditados. 13 entran. 1 hallazgo real:
**_ProductDialog** (contenido 584x565 no cabe en 500x550 declarado).

---

## Hallazgo concreto: _ProductDialog

- **Archivo:** `ui/views/products.py:3128` (`_ProductDialog.__init__`)
- **Línea de geometría:** `ui/views/products.py:3147` → `self.geometry("500x550")`
- **Valor declarado:** 500x550
- **Valor real medido (contenido):** 584x565 (ancho y alto exceden el declarado)
- **Impacto:** al abrir el diálogo de editar producto con un nombre/marca
  largos, partes del contenido quedan fuera del área declarada de 500x550.
  El diálogo es `resizable(True, True)` así que el usuario puede agrandar a
  mano, pero el tamaño inicial no acomoda el contenido real.

**Acción requerida:** agregar una Task a este plan (Task 3) con test-primero
que verifique `winfo_reqheight() <= alto_declarado` y `winfo_reqwidth() <= ancho_declarado`,
y corregir la geometría declarada (propuesta: `600x620`) para que el
contenido entre sin que el usuario tenga que redimensionar.

---

## Diálogos ya cubiertos (no repetidos en esta auditoría)

- `_MovementEditDialog` — Task 1 de este plan (fix: 500x480 → 540x800).
- `ConfirmDialog` / `MessageDialog` — corregidos en secciones previas de CLAUDE.md.
- `_ReportsDialog` y `_RegistrarProductoDialog` — verificados sin hallazgos en el diagnóstico de este plan.

---

## Próximos pasos

1. Agregar Task 3 a `docs/superpowers/plans/2026-11-01-auditoria-ventanas-emergentes.md` para corregir `_ProductDialog` (test-primero, fix de geometría, suite, commit).
2. Implementar Task 3.
3. Correr `.venv/bin/python -m pytest tests/ -q` (debe pasar).
4. Commit.

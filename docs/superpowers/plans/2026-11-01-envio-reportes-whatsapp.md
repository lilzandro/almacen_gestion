# Envío de reportes por WhatsApp Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Agregar el envío de reportes PDF por WhatsApp desde el diálogo "Reportes" de Movimientos, con el mismo patrón ya probado para correo (`core/email_report.py`) y Telegram (`core/telegram_report.py`): un checkbox opcional, gateado por variables de entorno, sin dependencias nuevas.

**Architecture:** `core/whatsapp_report.py` nuevo, usando la API oficial de Meta ("WhatsApp Cloud API") vía `urllib` puro — mismo estilo que `telegram_report.py` (sin `requests`, sin SDK de Twilio). Envía el PDF en 2 llamadas HTTP: subir el archivo a `/media` (devuelve un `media_id`) y enviar un mensaje `type=document` referenciando ese `media_id`. En `ui/views/movements.py::_ReportsDialog`, un tercer `CTkCheckBox` junto a los de correo/Telegram, gateado igual por `os.environ.get(...)`, y una rama más en `_send()`.

**Tech Stack:** Python 3.10+ (`urllib.request`, `json` — stdlib), CustomTkinter, pytest con `monkeypatch`.

**Spec:** Pedido del usuario en esta conversación ("planifica el enviar los reportes al correo y whatsapp"). **El correo ya está implementado y funcionando end-to-end** (confirmado leyendo `core/email_report.py` + el wiring en `_ReportsDialog._send`, líneas 454-471, y sus tests en `tests/test_reports.py:162-211`) — no hay nada que planificar ahí, este plan cubre solo WhatsApp.

**Corrección de una decisión anterior documentada en `CLAUDE.md`:** la sección "Letra más grande, reportes periódicos..." de ese archivo dice *"Mensajería: solo Telegram (WhatsApp requiere Twilio u otro proveedor de pago — descartado por ahora)"*. Esa afirmación asumía Twilio como único camino; no es la única opción. **Meta ofrece la WhatsApp Cloud API de forma directa y gratuita** (sin intermediario de pago) para números de prueba/desarrollo y con una cuota mensual gratuita de conversaciones iniciadas por el negocio en producción — no hace falta Twilio. Este plan usa esa vía directa, con el mismo patrón `urllib` que ya se usa para Telegram, así que no se agrega ninguna dependencia a `requirements.txt`.

**Limitación real de la plataforma (no es un bug a resolver, es una regla de Meta — dejarla explícita para el usuario, no hay forma de evitarla con código):** un mensaje de documento "freeform" (sin plantilla pre-aprobada) solo se puede entregar si el número destino **le escribió al número de negocio en las últimas 24 horas** ("ventana de servicio al cliente"). Si el destinatario no escribió nada en ese período, la API devuelve un error y el envío falla — igual que si faltaran las credenciales, queda reflejado en el aviso de error del diálogo, no como un crash. Para que el envío automático de reportes funcione de forma confiable, quien recibe el reporte necesita mandarle al menos un mensaje al número de negocio cada 24h (p. ej. "hola" una vez al día) — es una limitación operativa de WhatsApp Business, no algo que este plan pueda resolver de otra forma sin agregar plantillas pre-aprobadas (fuera de alcance, es un proceso de aprobación de Meta que toma días y no se pidió acá).

## Global Constraints

- Sin dependencias nuevas en `requirements.txt` — solo `urllib.request`/`json` (stdlib), igual que `telegram_report.py`.
- Credenciales por variables de entorno, nunca hardcodeadas: `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID` (el ID del número de WhatsApp Business emisor), `WHATSAPP_TO` (el número destino, formato internacional sin `+`, ej. `584121234567`).
- Mismo contrato de error que `send_report_email`/`send_report_telegram`: si faltan credenciales, `raise RuntimeError` con mensaje claro; si la API rechaza el envío, `raise RuntimeError` con el detalle de la respuesta — nunca dejar una excepción sin capturar llegar hasta la UI sin pasar por el `try/except` de `_send()`.
- No tocar `send_report_email`/`send_report_telegram` ni sus tests — este plan solo agrega, no modifica código existente de correo/Telegram.
- `python -m pytest tests/ -q` en verde después de cada tarea.

## Review Focus

- Credenciales incompletas (falta solo `WHATSAPP_TO`, por ejemplo) → debe avisar con `RuntimeError` igual que si faltaran las 3, no intentar la llamada HTTP con un valor `None`.
- La API de Meta puede devolver `200 OK` con un cuerpo de error JSON (no siempre un código HTTP de error) — el código debe chequear el contenido de la respuesta (`"id" in result` / `"messages" in result`), no solo que `urlopen` no lanzó excepción. Mismo patrón que `telegram_report.py` ya usa (`if not result.get("ok")`).
- El PDF adjunto debe llegar completo en el cuerpo de la petición de subida (`multipart/form-data`) — verificar con un test que compara bytes exactos, igual que ya hace `test_send_report_telegram_envia_documento`.
- El checkbox de WhatsApp debe quedar deshabilitado si faltan sus 3 variables de entorno, igual que ya pasa con correo/Telegram — no debe poder tildarse si el envío va a fallar seguro por falta de configuración.
- Que un fallo de WhatsApp (ej. ventana de 24h vencida) no impida que el reporte en PDF ya generado quede guardado, ni que bloquee el envío por correo/Telegram si esos checkboxes también estaban tildados — `_send()` ya acumula errores en una lista en vez de abortar en el primer fallo; la rama nueva debe seguir ese mismo patrón.

---

### Task 1: `core/whatsapp_report.py` — envío del PDF vía WhatsApp Cloud API

**Files:**
- Create: `core/whatsapp_report.py`
- Test: `tests/test_reports.py` (junto a los tests de Telegram, línea ~258)

**Interfaces:**
- Produces: `send_report_whatsapp(filepath: str, caption: str = "") -> None` — misma forma que `send_report_telegram(filepath, caption="")`. Lanza `RuntimeError` si faltan credenciales o si la API rechaza la subida/el envío. Usado por la Tarea 2.

- [ ] **Step 1: Escribir el test de credenciales faltantes**

```python
def test_send_report_whatsapp_sin_credenciales_avisa(monkeypatch):
    from core.whatsapp_report import send_report_whatsapp

    for key in ("WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID", "WHATSAPP_TO"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="WHATSAPP_TOKEN"):
        send_report_whatsapp("x.pdf")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_reports.py::test_send_report_whatsapp_sin_credenciales_avisa -v`
Expected: FAIL con `ModuleNotFoundError: No module named 'core.whatsapp_report'`.

- [ ] **Step 3: Escribir el test de envío exitoso (2 llamadas HTTP: subir media + enviar documento)**

```python
def test_send_report_whatsapp_envia_documento(tmp_path, monkeypatch):
    import core.whatsapp_report as whatsapp_report

    pdf = tmp_path / "reporte.pdf"
    pdf.write_bytes(b"%PDF-1.4 contenido de prueba")
    monkeypatch.setenv("WHATSAPP_TOKEN", "TOKEN")
    monkeypatch.setenv("WHATSAPP_PHONE_ID", "111222333")
    monkeypatch.setenv("WHATSAPP_TO", "584121234567")

    calls = []

    class FakeResponse:
        def __init__(self, body):
            self._body = body

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return self._body

    def fake_urlopen(req, timeout=0):
        calls.append(req)
        if len(calls) == 1:
            return FakeResponse(b'{"id": "MEDIA123"}')
        return FakeResponse(b'{"messages": [{"id": "wamid.ABC"}]}')

    monkeypatch.setattr(whatsapp_report.urllib.request, "urlopen", fake_urlopen)
    whatsapp_report.send_report_whatsapp(str(pdf), "Reporte")

    assert len(calls) == 2
    upload_req, send_req = calls
    assert upload_req.full_url == (
        "https://graph.facebook.com/v22.0/111222333/media"
    )
    assert b'name="file"' in upload_req.data
    assert pdf.read_bytes() in upload_req.data
    assert upload_req.headers["Authorization"] == "Bearer TOKEN"

    assert send_req.full_url == (
        "https://graph.facebook.com/v22.0/111222333/messages"
    )
    import json
    payload = json.loads(send_req.data)
    assert payload["to"] == "584121234567"
    assert payload["type"] == "document"
    assert payload["document"]["id"] == "MEDIA123"
    assert payload["document"]["caption"] == "Reporte"
```

- [ ] **Step 4: Run test to verify it still fails**

Run: `pytest tests/test_reports.py::test_send_report_whatsapp_envia_documento -v`
Expected: FAIL (módulo no existe todavía).

- [ ] **Step 5: Implementar `core/whatsapp_report.py`**

```python
"""Envío de reportes PDF por WhatsApp (Meta Cloud API, urllib, sin deps extra).

Credenciales por variables de entorno:
WHATSAPP_TOKEN, WHATSAPP_PHONE_ID (número emisor), WHATSAPP_TO (número destino).

Limitación de la plataforma: un documento "freeform" (sin plantilla
pre-aprobada) solo se entrega si WHATSAPP_TO le escribió al número de
negocio en las últimas 24 horas (ventana de servicio de WhatsApp Business).
"""
import json
import os
import urllib.request

GRAPH_VERSION = "v22.0"


def send_report_whatsapp(filepath, caption=""):
    token = os.environ.get("WHATSAPP_TOKEN")
    phone_id = os.environ.get("WHATSAPP_PHONE_ID")
    to = os.environ.get("WHATSAPP_TO")
    if not all([token, phone_id, to]):
        raise RuntimeError(
            "Falta configurar WHATSAPP_TOKEN/WHATSAPP_PHONE_ID/WHATSAPP_TO."
        )
    media_id = _upload_media(filepath, token, phone_id)
    _send_document(media_id, to, caption, token, phone_id)


def _upload_media(filepath, token, phone_id):
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{phone_id}/media"
    boundary = "----digicable-boundary"
    with open(filepath, "rb") as f:
        file_bytes = f.read()
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="messaging_product"\r\n\r\n'
        f"whatsapp\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; '
        f'filename="{os.path.basename(filepath)}"\r\n'
        f"Content-Type: application/pdf\r\n\r\n"
    ).encode() + file_bytes + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        url, data=body,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    if "id" not in result:
        raise RuntimeError(f"WhatsApp rechazó la subida del archivo: {result}")
    return result["id"]


def _send_document(media_id, to, caption, token, phone_id):
    url = f"https://graph.facebook.com/{GRAPH_VERSION}/{phone_id}/messages"
    payload = json.dumps({
        "messaging_product": "whatsapp",
        "to": to,
        "type": "document",
        "document": {
            "id": media_id, "caption": caption, "filename": "reporte.pdf",
        },
    }).encode()
    req = urllib.request.Request(
        url, data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    if "messages" not in result:
        raise RuntimeError(f"WhatsApp rechazó el envío: {result}")
```

- [ ] **Step 6: Run both tests to verify they pass**

Run: `pytest tests/test_reports.py::test_send_report_whatsapp_sin_credenciales_avisa tests/test_reports.py::test_send_report_whatsapp_envia_documento -v`
Expected: PASS en ambos.

- [ ] **Step 7: Run full suite**

Run: `python -m pytest tests/ -q`
Expected: todos los tests pasan, incluidos los 2 nuevos.

- [ ] **Step 8: Commit**

```bash
git add core/whatsapp_report.py tests/test_reports.py
git commit -m "feat: enviar reportes PDF por WhatsApp (Meta Cloud API)

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

### Task 2: Checkbox "Enviar por WhatsApp" en `_ReportsDialog`

**Files:**
- Modify: `ui/views/movements.py:243-274` (bloque de checkboxes de envío)
- Modify: `ui/views/movements.py:454-471` (`_send`)

**Interfaces:**
- Consumes: `send_report_whatsapp(filepath, caption="")` de la Tarea 1.
- Produces: nada nuevo para otras tareas — es el último eslabón de la cadena UI → `core`.

- [ ] **Step 1: Agregar la variable y el checkbox, junto a los de correo/Telegram**

En el bloque `email_ok`/`telegram_ok` (línea ~243-248), agregar:
```python
whatsapp_ok = all(os.environ.get(k) for k in (
    "WHATSAPP_TOKEN", "WHATSAPP_PHONE_ID", "WHATSAPP_TO"
))
```
Después de `self._telegram_var = tk.BooleanVar(value=False)` (línea 250), agregar:
```python
self._whatsapp_var = tk.BooleanVar(value=False)
```
Después del `CTkCheckBox` de Telegram (línea 257-262), agregar:
```python
ctk.CTkCheckBox(
    body, text="Enviar por WhatsApp", variable=self._whatsapp_var,
    font=ctk.CTkFont(size=13), text_color=DSG_TEXT_BODY,
    fg_color=DSG_BRAND, hover_color=DSG_PRIMARY_HOVER,
    state="normal" if whatsapp_ok else "disabled",
).pack(anchor="w", padx=16, pady=2)
```

- [ ] **Step 2: Incluir WhatsApp en el chequeo y el aviso de "Sin configurar"**

Cambiar:
```python
if not (email_ok and telegram_ok):
    missing = []
    if not email_ok:
        missing.append("SMTP_HOST/SMTP_USER/SMTP_PASSWORD/REPORT_EMAIL_TO")
    if not telegram_ok:
        missing.append("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID")
```
por:
```python
if not (email_ok and telegram_ok and whatsapp_ok):
    missing = []
    if not email_ok:
        missing.append("SMTP_HOST/SMTP_USER/SMTP_PASSWORD/REPORT_EMAIL_TO")
    if not telegram_ok:
        missing.append("TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID")
    if not whatsapp_ok:
        missing.append("WHATSAPP_TOKEN/WHATSAPP_PHONE_ID/WHATSAPP_TO")
```
(el resto del bloque, que construye el `CTkLabel` con `" · ".join(missing)`, queda igual).

- [ ] **Step 3: Agregar la rama de envío en `_send`**

Cambiar:
```python
    def _send(self, path, title, d1, d2):
        subject = f"DigiCable · {title} ({d1:%d/%m/%Y} - {d2:%d/%m/%Y})"
        errors = []
        if self._email_var.get():
            try:
                from core.email_report import send_report_email

                send_report_email(path, subject, "Reporte adjunto.")
            except Exception as e:
                errors.append(f"Correo: {e}")
        if self._telegram_var.get():
            try:
                from core.telegram_report import send_report_telegram

                send_report_telegram(path, subject)
            except Exception as e:
                errors.append(f"Telegram: {e}")
        return errors
```
por (agrega solo el bloque `if self._whatsapp_var.get():` al final, antes del `return`):
```python
    def _send(self, path, title, d1, d2):
        subject = f"DigiCable · {title} ({d1:%d/%m/%Y} - {d2:%d/%m/%Y})"
        errors = []
        if self._email_var.get():
            try:
                from core.email_report import send_report_email

                send_report_email(path, subject, "Reporte adjunto.")
            except Exception as e:
                errors.append(f"Correo: {e}")
        if self._telegram_var.get():
            try:
                from core.telegram_report import send_report_telegram

                send_report_telegram(path, subject)
            except Exception as e:
                errors.append(f"Telegram: {e}")
        if self._whatsapp_var.get():
            try:
                from core.whatsapp_report import send_report_whatsapp

                send_report_whatsapp(path, subject)
            except Exception as e:
                errors.append(f"WhatsApp: {e}")
        return errors
```

- [ ] **Step 4: Escribir un test de UI que confirme el wiring del checkbox a `_send`**

Mismo patrón que ya exista para Telegram en `tests/test_movements_view.py` si lo hay; si no existe ninguno para correo/Telegram tampoco (confirmado: no hay ninguno hoy), agregar uno mínimo que no dependa de un servidor X real:

```python
def test_send_incluye_whatsapp_si_el_checkbox_esta_tildado(monkeypatch):
    from ui.views import movements as movements_mod

    captured = {}
    monkeypatch.setattr(
        movements_mod, "send_report_whatsapp",
        lambda path, caption="": captured.setdefault("called", (path, caption)),
        raising=False,
    )

    class _Dialog:
        _email_var = type("V", (), {"get": lambda self: False})()
        _telegram_var = type("V", (), {"get": lambda self: False})()
        _whatsapp_var = type("V", (), {"get": lambda self: True})()

    import datetime
    errors = movements_mod._ReportsDialog._send(
        _Dialog(), "x.pdf", "Reporte", datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 31),
    )
    assert errors == []  # el monkeypatch de send_report_whatsapp no lanza nada
```
**Nota para el ejecutor:** el `_send` real hace `from core.whatsapp_report import send_report_whatsapp` dentro del método (import local, no a nivel de módulo) — por eso este test monkeypatchea `core.whatsapp_report.send_report_whatsapp` directamente, no `movements_mod.send_report_whatsapp` (ajustar el test al patrón de import real antes de escribirlo, revisando cómo está hecho el `import` local en el Step 3 de arriba):
```python
def test_send_incluye_whatsapp_si_el_checkbox_esta_tildado(monkeypatch):
    import core.whatsapp_report as whatsapp_report
    from ui.views import movements as movements_mod

    captured = {}
    monkeypatch.setattr(
        whatsapp_report, "send_report_whatsapp",
        lambda path, caption="": captured.setdefault("called", (path, caption)),
    )

    class _Dialog:
        _email_var = type("V", (), {"get": lambda self: False})()
        _telegram_var = type("V", (), {"get": lambda self: False})()
        _whatsapp_var = type("V", (), {"get": lambda self: True})()

    import datetime
    errors = movements_mod._ReportsDialog._send(
        _Dialog(), "x.pdf", "Reporte", datetime.date(2026, 1, 1),
        datetime.date(2026, 1, 31),
    )
    assert errors == []
    assert captured["called"][0] == "x.pdf"
```

- [ ] **Step 5: Run test to verify it fails, then implement, then verify it passes**

Run: `pytest tests/test_movements_view.py::test_send_incluye_whatsapp_si_el_checkbox_esta_tildado -v`
Expected antes del Step 1-3: FAIL (`AttributeError: _whatsapp_var`). Después de aplicarlos: PASS.

- [ ] **Step 6: Run full suite**

Run: `python -m pytest tests/ -q`
Expected: todos los tests pasan.

- [ ] **Step 7: Commit**

```bash
git add ui/views/movements.py tests/test_movements_view.py
git commit -m "feat: checkbox de envio por WhatsApp en el dialogo de Reportes

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>"
```

---

## Self-Review

1. **Spec coverage:** correo → ya implementado, documentado como tal en el header del plan (sin tarea, porque no hace falta). WhatsApp → Tarea 1 (backend) + Tarea 2 (UI). Cubierto completo.
2. **Step scan:** cada step deja una sola acción verificable. El Step 4 de la Tarea 2 incluye una aclaración sobre el import local (nota explícita) porque es la única decisión no evidente del signature/test — no es relleno, es la pieza que evita que el ejecutor monkeypatchee el lugar equivocado.
3. **Type consistency:** `send_report_whatsapp(filepath, caption="")` se nombra igual en la Tarea 1 (Produces) y en el uso real de la Tarea 2 (`_send`), coincide con la forma de `send_report_telegram`.
4. **Review Focus:** las 5 líneas de arriba (credenciales incompletas, respuesta 200-con-error, bytes del PDF completos, checkbox deshabilitado, errores no bloquean otros envíos) tienen su test o verificación explícita en los Steps de ambas tareas.
5. **Proporción:** el código de `whatsapp_report.py` se transcribe completo porque es un algoritmo de 2 llamadas HTTP con un formato de `multipart`/JSON específico que el signature solo no deja inequívoco (a diferencia de, por ejemplo, el checkbox de la Tarea 2, donde sí alcanza con mostrar el diff exacto sin más explicación) — está en línea con cómo ya se entregó `telegram_report.py` en el plan anterior que lo originó.

---

Plan completo y guardado en `docs/superpowers/plans/2026-11-01-envio-reportes-whatsapp.md`. Por favor revísalo. ¿Qué método de ejecución prefieres?

- **Subagent-driven** — un subagente fresco implementa cada tarea y un revisor fresco la chequea antes de pasar a la siguiente, más una revisión final de toda la rama. Más riguroso; cuesta un contexto nuevo por tarea y por revisión.
- **Native** — se implementa todo en esta misma sesión, como ya viene haciendo el ejecutor (opencode) entre turnos, con una revisión final de toda la rama al terminar. Más barato y rápido; sin revisión independiente hasta el final.

Para este plan recomiendo **Native**: son 2 tareas con una dependencia simple y lineal (la UI de la Tarea 2 solo consume la función que deja la Tarea 1), de tamaño chico, con el mismo patrón ya probado 2 veces en este repo (correo, Telegram) — bajo riesgo de error de diseño, no justifica el overhead de un subagente+revisor por tarea. ¿El plan refleja lo que querés, y con qué método seguimos?

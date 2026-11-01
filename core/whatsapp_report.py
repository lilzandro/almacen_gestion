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

"""Abre WhatsApp con un mensaje prellenado para mandar el reporte.

No envía el PDF automáticamente — wa.me no permite adjuntar archivos por URL,
solo prellenar texto. Abre el chat con WHATSAPP_TO y un mensaje que recuerda
adjuntar el PDF a mano. Configurar solo WHATSAPP_TO (número destino, formato
internacional sin "+", ej. 584121234567).
"""
import os
import webbrowser
from urllib.parse import quote


def send_report_whatsapp(filepath, caption=""):
    to = os.environ.get("WHATSAPP_TO")
    if not to:
        raise RuntimeError("Falta configurar WHATSAPP_TO.")
    text = f"{caption}\n\nAdjuntar el archivo: {os.path.basename(filepath)}"
    webbrowser.open(f"https://wa.me/{to}?text={quote(text)}")

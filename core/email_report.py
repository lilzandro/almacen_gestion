"""Abre el cliente de correo con un mensaje prellenado para mandar el reporte.

No envía el PDF automáticamente — mailto: no permite adjuntar archivos por
URL, solo prellenar asunto/cuerpo. Abre el cliente de correo predeterminado
con REPORT_EMAIL_TO, el asunto y un cuerpo que recuerda adjuntar el PDF a
mano. Configurar solo REPORT_EMAIL_TO (dirección de destino).
"""
import os
import webbrowser
from urllib.parse import quote


def send_report_email(filepath, subject, body=""):
    to = os.environ.get("REPORT_EMAIL_TO")
    if not to:
        raise RuntimeError("Falta configurar REPORT_EMAIL_TO.")
    full_body = f"{body}\n\nAdjuntar el archivo: {os.path.basename(filepath)}"
    url = f"mailto:{to}?subject={quote(subject)}&body={quote(full_body)}"
    webbrowser.open(url)

"""Envío de reportes PDF por correo (smtplib, sin dependencias extra).

Credenciales por variables de entorno:
SMTP_HOST, SMTP_PORT (default 465), SMTP_USER, SMTP_PASSWORD, REPORT_EMAIL_TO.
"""
import os
import smtplib
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def send_report_email(filepath, subject, body=""):
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    to = os.environ.get("REPORT_EMAIL_TO")
    if not all([host, user, password, to]):
        raise RuntimeError(
            "Falta configurar SMTP_HOST/SMTP_USER/SMTP_PASSWORD/REPORT_EMAIL_TO."
        )
    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"] = user
    msg["To"] = to
    msg.attach(MIMEText(body or "Reporte adjunto."))
    with open(filepath, "rb") as f:
        part = MIMEApplication(f.read(), Name=os.path.basename(filepath))
    part["Content-Disposition"] = (
        f'attachment; filename="{os.path.basename(filepath)}"'
    )
    msg.attach(part)
    port = int(os.environ.get("SMTP_PORT", "465"))
    with smtplib.SMTP_SSL(host, port) as server:
        server.login(user, password)
        server.send_message(msg)

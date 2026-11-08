"""Abre un correo con el reporte PDF adjunto.

En Windows, si Outlook está disponible, crea el correo con el PDF ya adjunto
y lo muestra para que lo revises y pulses Enviar. Si Outlook no está
disponible o falla, abre el enlace `mailto:` y deja el PDF copiado al
portapapeles y seleccionado en el Explorador para adjuntarlo a mano.

El destino se configura en Reportes → Configurar destinos, o con la variable
REPORT_EMAIL_TO (tiene prioridad).
"""
import os
import subprocess
import webbrowser
from urllib.parse import quote

from core.report_config import get_email_to
from core.win_utils import copy_file_to_clipboard as _copy_file_to_clipboard
from core.win_utils import reveal_file as _reveal_file

_CREATE_NO_WINDOW = 0x08000000

_OUTLOOK_SCRIPT = r"""
$ErrorActionPreference = 'Stop'
$ol = New-Object -ComObject Outlook.Application
$mail = $ol.CreateItem(0)
$mail.To = $env:DC_MAIL_TO
$mail.Subject = $env:DC_MAIL_SUBJECT
$mail.Body = $env:DC_MAIL_BODY
[void]$mail.Attachments.Add($env:DC_MAIL_FILE)
$mail.Display()
"""


def _outlook_available():
    """True si Windows tiene instalado el cliente de escritorio de Outlook."""
    if os.name != "nt":
        return False
    try:
        import winreg

        with winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Clients\Mail\Microsoft Outlook"
        ):
            return True
    except OSError:
        return False


def _send_with_outlook(filepath, to, subject, body):
    """Abre Outlook con el PDF adjunto. Devuelve True si lo logró."""
    env = os.environ.copy()
    env["DC_MAIL_TO"] = to
    env["DC_MAIL_SUBJECT"] = subject
    env["DC_MAIL_BODY"] = body
    env["DC_MAIL_FILE"] = os.path.abspath(filepath)
    try:
        proc = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive",
                "-Command", _OUTLOOK_SCRIPT,
            ],
            env=env,
            capture_output=True,
            timeout=30,
            creationflags=_CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def send_report_email(filepath, subject, body=""):
    to = get_email_to()
    if not to:
        raise RuntimeError(
            "Falta configurar el correo destino (Reportes → Configurar destinos)."
        )
    body = body or "Reporte adjunto."
    if _outlook_available() and _send_with_outlook(filepath, to, subject, body):
        return

    copied = _copy_file_to_clipboard(filepath)
    if copied:
        hint = (
            "El PDF quedó copiado al portapapeles. En el correo, presioná "
            "Ctrl+V para adjuntarlo."
        )
    else:
        hint = "Adjuntá el archivo desde la carpeta que se abrió."
    full_body = f"{body}\n\n{hint}\nArchivo: {os.path.basename(filepath)}"
    url = f"mailto:{to}?subject={quote(subject)}&body={quote(full_body)}"
    _reveal_file(filepath)
    webbrowser.open(url)

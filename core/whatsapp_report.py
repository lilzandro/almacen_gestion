"""Abre WhatsApp con el reporte y el PDF listo para adjuntar.

wa.me no permite adjuntar archivos por URL (limitación de WhatsApp). Para que
el PDF quede a mano, se copia al portapapeles como archivo y se abre el
Explorador con el PDF seleccionado: en el chat de WhatsApp Web o Desktop
alcanza con Ctrl+V, o se arrastra desde el Explorador.

El destino se configura en Reportes → Configurar destinos, o con la variable
WHATSAPP_TO (tiene prioridad).
"""
import os
import webbrowser
from urllib.parse import quote

from core.report_config import get_whatsapp_to
from core.win_utils import copy_file_to_clipboard as _copy_file_to_clipboard
from core.win_utils import reveal_file as _reveal_file


def send_report_whatsapp(filepath, caption=""):
    to = get_whatsapp_to()
    if not to:
        raise RuntimeError(
            "Falta configurar el WhatsApp destino (Reportes → Configurar destinos)."
        )
    name = os.path.basename(filepath)
    copied = _copy_file_to_clipboard(filepath)
    if copied:
        hint = (
            "El PDF quedó copiado al portapapeles: en el chat presioná Ctrl+V "
            "para adjuntarlo."
        )
    else:
        hint = f"Adjuntar el archivo: {name}"
    text = f"{caption}\n\n{hint}\nArchivo: {name}"
    _reveal_file(filepath)
    webbrowser.open(f"https://wa.me/{to}?text={quote(text)}")

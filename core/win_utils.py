"""Utilidades de Windows para compartir archivos.

Permiten dejar un PDF copiado al portapapeles como archivo (para pegarlo con
Ctrl+V en un correo o chat) y abrir el Explorador con el archivo seleccionado.
"""
import os
import subprocess

_CREATE_NO_WINDOW = 0x08000000


def copy_file_to_clipboard(filepath):
    """Copia el archivo al portapapeles de Windows (lista de archivos)."""
    if os.name != "nt":
        return False
    env = os.environ.copy()
    env["DC_CLIP_FILE"] = os.path.abspath(filepath)
    try:
        proc = subprocess.run(
            [
                "powershell", "-NoProfile", "-NonInteractive", "-Command",
                "Set-Clipboard -Path $env:DC_CLIP_FILE",
            ],
            env=env,
            capture_output=True,
            timeout=15,
            creationflags=_CREATE_NO_WINDOW,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return proc.returncode == 0


def reveal_file(filepath):
    """Abre el Explorador con el archivo seleccionado (para arrastrarlo)."""
    if os.name != "nt":
        return
    try:
        subprocess.Popen(
            ["explorer", "/select,", os.path.abspath(filepath)],
            creationflags=_CREATE_NO_WINDOW,
        )
    except OSError:
        pass

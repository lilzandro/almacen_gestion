"""Destinos de envío de reportes (correo y WhatsApp).

Se guardan en un JSON local del usuario para no depender de variables de
entorno. Las variables REPORT_EMAIL_TO y WHATSAPP_TO siguen teniendo
prioridad, por compatibilidad con run.sh y despliegues existentes.
"""
import json
import os

_ENV_EMAIL = "REPORT_EMAIL_TO"
_ENV_WHATSAPP = "WHATSAPP_TO"
DEFAULT_COUNTRY_CODE = "58"


def config_file() -> str:
    """Ruta del archivo de configuración (override con DIGICABLE_CONFIG_DIR)."""
    base = os.environ.get("DIGICABLE_CONFIG_DIR")
    if not base:
        base = os.path.join(
            os.environ.get("APPDATA") or os.path.expanduser("~"), "DigiCable"
        )
    return os.path.join(base, "config.json")


def load_config() -> dict:
    try:
        with open(config_file(), encoding="utf-8") as fh:
            data = json.load(fh)
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def save_config(data: dict) -> None:
    path = config_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def normalize_phone(number) -> str:
    """Deja solo dígitos en formato internacional (wa.me).

    Acepta números locales venezolanos con 0 inicial (ej. 04126483715) y los
    convierte a 584126483715. Los que ya traen código de país no se tocan.
    """
    digits = "".join(ch for ch in str(number or "") if ch.isdigit())
    if digits.startswith("00"):
        digits = digits[2:]
    if digits.startswith("0"):
        digits = DEFAULT_COUNTRY_CODE + digits[1:]
    return digits


def get_email_to() -> str:
    value = os.environ.get(_ENV_EMAIL)
    if value:
        return value.strip()
    return str(load_config().get("report_email_to") or "").strip()


def get_whatsapp_to() -> str:
    value = os.environ.get(_ENV_WHATSAPP)
    if value:
        return normalize_phone(value)
    return normalize_phone(load_config().get("whatsapp_to"))


def set_destinations(email, whatsapp) -> None:
    data = load_config()
    data["report_email_to"] = (email or "").strip()
    data["whatsapp_to"] = normalize_phone(whatsapp)
    save_config(data)


def env_override(field: str) -> bool:
    """True si el destino efectivo lo define una variable de entorno."""
    return bool(os.environ.get(_ENV_EMAIL if field == "email" else _ENV_WHATSAPP))

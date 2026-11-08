from core import report_config


def test_normaliza_numero_local_venezolano():
    assert report_config.normalize_phone("0412-6483715") == "584126483715"
    assert report_config.normalize_phone("+58 412 6483715") == "584126483715"
    assert report_config.normalize_phone("00584126483715") == "584126483715"


def test_guarda_destinos_y_normaliza_whatsapp(tmp_path, monkeypatch):
    monkeypatch.delenv("REPORT_EMAIL_TO", raising=False)
    monkeypatch.delenv("WHATSAPP_TO", raising=False)
    monkeypatch.setenv("DIGICABLE_CONFIG_DIR", str(tmp_path))

    report_config.set_destinations("destino@ejemplo.com", "+58 412-123.45.67")

    assert report_config.get_email_to() == "destino@ejemplo.com"
    assert report_config.get_whatsapp_to() == "584121234567"


def test_variables_de_entorno_tienen_prioridad(tmp_path, monkeypatch):
    monkeypatch.setenv("DIGICABLE_CONFIG_DIR", str(tmp_path))
    monkeypatch.setenv("REPORT_EMAIL_TO", "env@ejemplo.com")
    monkeypatch.delenv("WHATSAPP_TO", raising=False)

    report_config.set_destinations("config@ejemplo.com", "584121234567")

    assert report_config.get_email_to() == "env@ejemplo.com"
    assert report_config.get_whatsapp_to() == "584121234567"
    assert report_config.env_override("email") is True
    assert report_config.env_override("whatsapp") is False


def test_sin_configuracion_devuelve_vacio(tmp_path, monkeypatch):
    monkeypatch.delenv("REPORT_EMAIL_TO", raising=False)
    monkeypatch.delenv("WHATSAPP_TO", raising=False)
    monkeypatch.setenv("DIGICABLE_CONFIG_DIR", str(tmp_path))

    assert report_config.get_email_to() == ""
    assert report_config.get_whatsapp_to() == ""

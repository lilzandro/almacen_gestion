"""Pruebas de reportes: filtros por fecha, ranking y exportaciones."""
import pytest


def test_get_movements_flat_filtra_por_rango_de_fechas(db, q):
    repo = db["repo"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "enero")
    enero = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "febrero")
    febrero = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]

    conn = repo.get_connection()
    try:
        conn.execute(
            "UPDATE movements SET timestamp='2026-01-15 10:00:00' WHERE id=?", (enero,)
        )
        conn.execute(
            "UPDATE movements SET timestamp='2026-02-15 10:00:00' WHERE id=?", (febrero,)
        )
        conn.commit()
    finally:
        conn.close()

    rows = repo.get_movements_flat(date_from="2026-01-01", date_to="2026-01-31")
    assert [r["id"] for r in rows] == [enero]

    rows = repo.get_movements_flat(date_from="2026-02-01", date_to="2026-02-28")
    assert [r["id"] for r in rows] == [febrero]

    assert len(repo.get_movements_flat()) == 2


def test_get_product_movement_ranking_agrupa_y_ordena(db, q):
    repo = db["repo"]
    cable = repo.create_product(
        "Cable", "BC-CABLE", "Gen", "", "", 100, None, "und",
        warehouse_id=db["wh_id"],
    )

    entrada = repo.create_compound_movement(
        "entrada", db["user_id"],
        [
            {"name": "Router", "brand": "TPLink", "qty": 5, "unit": "und",
             "kind": "quantity"},
            {"name": "Cable", "brand": "Gen", "qty": 10, "unit": "und",
             "kind": "quantity"},
        ],
        warehouse_id=db["wh_id"],
    )
    salida = repo.create_compound_movement(
        "salida", db["user_id"],
        [
            {"name": "Router", "brand": "TPLink", "qty": 3, "unit": "und",
             "kind": "quantity"},
            {"name": "Cable", "brand": "Gen", "qty": 2, "unit": "und",
             "kind": "quantity"},
        ],
        warehouse_id=db["wh_id"],
    )
    fuera = repo.create_movement(
        "entrada", cable, None, db["user_id"], 100, "abril",
        warehouse_id=db["wh_id"],
    )
    conn = repo.get_connection()
    try:
        conn.execute("UPDATE movements SET timestamp='2026-03-10 09:00:00' WHERE id IN (?,?)",
                     (entrada, salida))
        conn.execute("UPDATE movements SET timestamp='2026-04-10 09:00:00' WHERE id=?",
                     (fuera,))
        conn.commit()
    finally:
        conn.close()

    rows = repo.get_product_movement_ranking(
        "2026-03-01", "2026-03-31", warehouse_id=db["wh_id"]
    )
    assert [(r["name"], r["entradas"], r["salidas"], r["total"]) for r in rows] == [
        ("Cable", 10, 2, 12),
        ("Router", 5, 3, 8),
    ]


def test_get_movement_counts_filtra_por_fecha(db, q):
    repo = db["repo"]
    repo.create_movement("entrada", db["qty_pid"], None, db["user_id"], 1, "uno")
    uno = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]
    repo.create_movement("salida", db["qty_pid"], None, db["user_id"], 1, "dos")
    dos = q("SELECT id FROM movements ORDER BY id DESC LIMIT 1")[0]["id"]
    conn = repo.get_connection()
    try:
        conn.execute("UPDATE movements SET timestamp='2026-05-02 09:00:00' WHERE id=?", (uno,))
        conn.execute("UPDATE movements SET timestamp='2026-06-02 09:00:00' WHERE id=?", (dos,))
        conn.commit()
    finally:
        conn.close()

    counts = repo.get_movement_counts(date_from="2026-05-01", date_to="2026-05-31")
    assert counts["entrada"] == 1
    assert counts["salida"] == 0
    assert repo.get_movement_counts()["entrada"] == 1
    assert repo.get_movement_counts()["salida"] == 1


def test_export_product_ranking_genera_pdf(tmp_path):
    from core.export import export_product_ranking

    path = tmp_path / "ranking.pdf"
    top = [
        {"name": "Router", "brand": "TPLink", "entradas": 10, "salidas": 2, "total": 12},
    ]
    bottom = [
        {"name": "Switch", "brand": "Cisco", "entradas": 1, "salidas": 0, "total": 1},
    ]
    export_product_ranking(
        str(path), top, bottom, "2026-05-01", "2026-05-31",
        warehouse_name="Principal",
    )
    assert path.exists() and path.stat().st_size > 1000


def test_export_critical_closing_genera_pdf(tmp_path):
    from core.export import export_critical_closing

    path = tmp_path / "cierre.pdf"
    summary = [("Entradas", 10), ("Salidas", 4), ("Devoluciones", 1)]
    top = [
        {"name": "Router", "brand": "TPLink", "entradas": 10, "salidas": 2, "total": 12},
    ]
    bottom = [
        {"name": "Switch", "brand": "Cisco", "entradas": 1, "salidas": 0, "total": 1},
    ]
    export_critical_closing(
        str(path), summary, top, bottom, "2026-05-01", "2026-05-31",
        warehouse_name="Principal",
    )
    assert path.exists() and path.stat().st_size > 1000


def test_report_date_range_diario_semanal_mensual():
    from datetime import date

    from ui.views.movements import report_date_range

    hoy = date(2026, 6, 15)
    assert report_date_range("Diario", hoy) == (hoy, hoy)
    assert report_date_range("Semanal", hoy) == (date(2026, 6, 9), hoy)
    assert report_date_range("Mensual", hoy) == (date(2026, 6, 1), hoy)
    assert report_date_range("Crítico de cierre", hoy) == (date(2026, 6, 1), hoy)


def test_split_ranking_separa_mas_y_menos_movidos_sin_repetir():
    from ui.views.movements import split_ranking

    rows = [
        {"name": f"P{i}", "brand": "B", "total": 100 - i} for i in range(15)
    ]
    top, bottom = split_ranking(rows, limit=3)
    assert [r["name"] for r in top] == ["P0", "P1", "P2"]
    assert [r["name"] for r in bottom] == ["P14", "P13", "P12"]


def test_send_report_email_sin_credenciales_avisa(monkeypatch):
    from core.email_report import send_report_email

    for key in ("SMTP_HOST", "SMTP_USER", "SMTP_PASSWORD", "REPORT_EMAIL_TO"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="SMTP_HOST"):
        send_report_email("x.pdf", "asunto")


def test_send_report_email_adjunta_el_pdf(tmp_path, monkeypatch):
    import core.email_report as email_report

    pdf = tmp_path / "reporte.pdf"
    pdf.write_bytes(b"%PDF-1.4 contenido de prueba")
    for key, value in {
        "SMTP_HOST": "smtp.test", "SMTP_PORT": "465", "SMTP_USER": "u@test",
        "SMTP_PASSWORD": "secret", "REPORT_EMAIL_TO": "dest@test",
    }.items():
        monkeypatch.setenv(key, value)

    sent = {}

    class FakeSMTP:
        def __init__(self, host, port):
            sent["server"] = (host, port)

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def login(self, user, password):
            sent["login"] = (user, password)

        def send_message(self, msg):
            sent["msg"] = msg

    monkeypatch.setattr(email_report.smtplib, "SMTP_SSL", FakeSMTP)
    email_report.send_report_email(str(pdf), "Reporte", "cuerpo")

    msg = sent["msg"]
    assert sent["server"] == ("smtp.test", 465)
    assert sent["login"] == ("u@test", "secret")
    assert msg["To"] == "dest@test"
    assert msg["Subject"] == "Reporte"
    attachments = [p for p in msg.walk() if p.get_filename() == "reporte.pdf"]
    assert len(attachments) == 1
    assert attachments[0].get_payload(decode=True) == pdf.read_bytes()


def test_send_report_telegram_sin_credenciales_avisa(monkeypatch):
    from core.telegram_report import send_report_telegram

    for key in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(key, raising=False)
    with pytest.raises(RuntimeError, match="TELEGRAM_BOT_TOKEN"):
        send_report_telegram("x.pdf")


def test_send_report_telegram_envia_documento(tmp_path, monkeypatch):
    import core.telegram_report as telegram_report

    pdf = tmp_path / "reporte.pdf"
    pdf.write_bytes(b"%PDF-1.4 contenido de prueba")
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "TOKEN")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "12345")

    captured = {}

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return b'{"ok": true}'

    def fake_urlopen(req, timeout=0):
        captured["url"] = req.full_url
        captured["data"] = req.data
        captured["timeout"] = timeout
        return FakeResponse()

    monkeypatch.setattr(telegram_report.urllib.request, "urlopen", fake_urlopen)
    telegram_report.send_report_telegram(str(pdf), "Reporte")

    assert captured["url"] == "https://api.telegram.org/botTOKEN/sendDocument"
    assert b'name="chat_id"' in captured["data"]
    assert b"12345" in captured["data"]
    assert b'filename="reporte.pdf"' in captured["data"]
    assert pdf.read_bytes() in captured["data"]
    assert captured["timeout"] == 30


def test_export_single_movement_genera_pdf_simple(tmp_path):
    from core.export import export_single_movement

    detail = {
        "id": 7,
        "type": "salida",
        "timestamp": "2026-05-02 09:00:00",
        "quantity": 3,
        "unit": "und",
        "product": "Router",
        "brand": "TPLink",
        "employee": "Ana",
        "cargo": "Tecnica",
        "registered_by": "admin",
        "warehouse": "Principal",
        "notes": "prueba",
        "items": [],
    }
    path = tmp_path / "movimiento.pdf"
    export_single_movement(str(path), detail)
    assert path.exists() and path.stat().st_size > 1000


def test_export_single_movement_con_items_y_textos_dados(tmp_path):
    from core.export import export_single_movement

    detail = {
        "id": 12,
        "type": "entrada",
        "timestamp": "2026-05-03 11:30:00",
        "employee": "-",
        "registered_by": "admin",
        "notes": "",
        "items": [
            {"name": "Router", "brand": "TPLink", "qty": 5, "unit": "und",
             "seriales": "SN-1, SN-2"},
            {"name": "Cable", "brand": "Gen", "qty": 10, "unit": "m",
             "seriales": ""},
        ],
    }
    path = tmp_path / "movimiento_items.pdf"
    export_single_movement(
        str(path), detail,
        quantity_text="5 und - 10 m",
        employee_text="-",
        warehouse_name="Secundario",
    )
    assert path.exists() and path.stat().st_size > 1000


def test_export_single_movement_sin_textos_deriva_cantidad_y_productos(
    tmp_path, monkeypatch
):
    """Camino del popup del Dashboard: no pasa quantity_text."""
    import core.export as export

    captured = {}
    monkeypatch.setattr(export, "_build_pdf", lambda **kw: captured.update(kw))

    detail = {
        "id": 21,
        "type": "entrada",
        "timestamp": "2026-05-04 08:00:00",
        "items": [
            {"name": "Router", "brand": "TPLink", "qty": 5, "unit": "und",
             "seriales": "SN-1"},
            {"name": "Cable", "brand": "Gen", "qty": 10, "unit": "m",
             "seriales": ""},
        ],
    }
    export.export_single_movement(str(tmp_path / "x.pdf"), detail)

    rows = {row[0]: row[1] for row in captured["rows"]}
    assert rows["Cantidades"] == "5 und · 10 m"
    assert rows["Almacén"] == "—"
    assert "Producto" not in rows  # compuesto: los ítems van en su sección
    section = captured["extra_sections"][0]
    assert section["title"] == "Productos"
    assert [r[0] for r in section["rows"]] == ["Router", "Cable"]
    assert section["rows"][0][4] == "SN-1"

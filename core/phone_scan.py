"""Servidor local de escaneo desde el teléfono.

Sirve una página web con la cámara del teléfono (API BarcodeDetector, sin
dependencias ni internet) y recibe los códigos escaneados vía POST /scan.

- HTTPS con certificado autofirmado (core/certs) para poder usar la cámara
  (getUserMedia exige contexto seguro).
- Token de acceso: la página lo incrusta; POST /scan sin token válido se
  rechaza con 403.
- Los códigos se encolan en una queue.Queue que la GUI consume con after().
"""

import json
import secrets
import socket
import ssl
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import os

_CERT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")
CERT_FILE = os.path.join(_CERT_DIR, "cert.pem")
KEY_FILE = os.path.join(_CERT_DIR, "key.pem")


def _cert_sans():
    """Nombres e IPs que debe cubrir el certificado autofirmado."""
    names = {"localhost"}
    ips = {"127.0.0.1"}
    try:
        ip = get_lan_ip()
        if ip:
            ips.add(ip)
    except Exception:
        pass
    return names, ips


def _ensure_cert_openssl() -> bool:
    """Genera el certificado con el binario `openssl` del sistema."""
    import shutil as _shutil
    import subprocess

    openssl = _shutil.which("openssl")
    if not openssl:
        return False

    names, ips = _cert_sans()
    sans = ",".join([f"DNS:{n}" for n in sorted(names)] + [f"IP:{i}" for i in sorted(ips)])

    os.makedirs(_CERT_DIR, exist_ok=True)
    subprocess.run(
        [
            openssl, "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-keyout", KEY_FILE, "-out", CERT_FILE, "-days", "3650",
            "-subj", "/CN=digicable-inventory",
            "-addext", f"subjectAltName={sans}",
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    return True


def _ensure_cert_python() -> bool:
    """Genera el certificado con la librería `cryptography` (sin openssl externo)."""
    try:
        import datetime
        import ipaddress

        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID
    except ImportError:
        return False

    try:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = x509.Name(
            [
                x509.NameAttribute(NameOID.COMMON_NAME, "digicable-inventory"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, "DigiCable"),
            ]
        )

        names, ips = _cert_sans()
        alt = [x509.DNSName(n) for n in sorted(names)]
        for ip in sorted(ips):
            try:
                alt.append(x509.IPAddress(ipaddress.ip_address(ip)))
            except ValueError:
                pass

        now = datetime.datetime.now(datetime.timezone.utc)
        cert = (
            x509.CertificateBuilder()
            .subject_name(subject)
            .issuer_name(subject)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - datetime.timedelta(days=1))
            .not_valid_after(now + datetime.timedelta(days=3650))
            .add_extension(x509.SubjectAlternativeName(alt), critical=False)
            .sign(key, hashes.SHA256())
        )

        os.makedirs(_CERT_DIR, exist_ok=True)
        with open(KEY_FILE, "wb") as fh:
            fh.write(
                key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.TraditionalOpenSSL,
                    encryption_algorithm=serialization.NoEncryption(),
                )
            )
        with open(CERT_FILE, "wb") as fh:
            fh.write(cert.public_bytes(serialization.Encoding.PEM))
        return True
    except Exception as e:
        print(f"[phone_scan] No se pudo generar el certificado con cryptography: {e}")
        return False


def _ensure_cert() -> bool:
    """Genera un certificado autofirmado si no existe (no se versiona la clave).

    Intenta primero con el binario `openssl` del sistema y, si no está
    disponible, usa la librería Python `cryptography` (ver requirements.txt).
    """
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        return True
    try:
        if _ensure_cert_openssl():
            return True
    except Exception as e:
        print(f"[phone_scan] openssl no disponible o falló: {e}")
    return _ensure_cert_python()

_SCAN_PAGE = """<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Escáner de inventario</title>
<style>
  body { margin:0; font-family:system-ui,sans-serif; background:#031D44; color:#fff; }
  h1 { font-size:20px; margin:14px 14px 6px; }
  p  { font-size:13px; margin:2px 14px; color:#9fbcd8; }
  video { width:100vw; height:56vh; object-fit:cover; background:#000; display:block; }
  .res { font-size:26px; font-weight:700; padding:14px; min-height:70px; word-break:break-all;
         background:#F7F5FB; color:#031D44; }
  .ok { color:#0a7d2f; } .err { color:#b3261e; }
  .count { font-size:14px; padding:6px 14px; color:#9fbcd8; }
</style>
</head>
<body>
  <h1>📷 Escanear código</h1>
  <p>Apunta al código de barras. Cada lectura se envía automáticamente al sistema.</p>
  <video id="cam" autoplay playsinline muted></video>
  <div class="res" id="res">Esperando lectura…</div>
  <div class="count" id="count">0 lecturas enviadas</div>
<script>
const TOKEN = "__TOKEN__";
const res = document.getElementById("res");
const countEl = document.getElementById("count");
let sent = 0;
let last = null;
let lastAt = 0;

function beep() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)();
    const o = ctx.createOscillator();
    const g = ctx.createGain();
    o.connect(g); g.connect(ctx.destination);
    o.frequency.value = 1200; o.type = "square";
    g.gain.setValueAtTime(0.15, ctx.currentTime);
    o.start(); o.stop(ctx.currentTime + 0.12);
  } catch (e) {}
}

async function postCode(code) {
  try {
    await fetch("/scan", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({code: code, token: TOKEN})
    });
    sent += 1;
    countEl.textContent = sent + " lecturas enviadas";
    res.classList.add("ok"); res.classList.remove("err");
    res.textContent = code;
    beep();
  } catch (e) {
    res.classList.add("err"); res.classList.remove("ok");
    res.textContent = "Error al enviar: " + code;
  }
}

async function loop(detector) {
  const cam = document.getElementById("cam");
  try {
    const codes = await detector.detect(cam);
    if (codes && codes.length) {
      const v = codes[0].rawValue;
      const now = Date.now();
      if (v && (v !== last || now - lastAt > 1500)) {
        last = v; lastAt = now;
        await postCode(v);
      }
    }
  } catch (e) {}
  setTimeout(() => loop(detector), 350);
}

(async () => {
  if (!("BarcodeDetector" in window)) {
    res.classList.add("err");
    res.textContent = "Tu navegador no soporta BarcodeDetector. Usa Chrome o Edge (Android).";
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({video: {facingMode: "environment"}});
    document.getElementById("cam").srcObject = stream;
  } catch (e) {
    res.classList.add("err");
    res.textContent = "Sin permiso de cámara. Autoriza la cámara en el navegador.";
    return;
  }
  const preferred = [
    "ean_13","ean_8","upc_a","upc_e",
    "code_128","code_39","code_93","codabar","itf",
    "data_matrix","pdf417","aztec","qr_code"
  ];
  let formats = preferred;
  try {
    if (typeof BarcodeDetector.getSupportedFormats === "function") {
      const supported = await BarcodeDetector.getSupportedFormats();
      if (Array.isArray(supported) && supported.length) {
        formats = preferred.filter((f) => supported.includes(f));
      }
    }
  } catch (e) {}
  let detector;
  try {
    detector = formats.length ? new BarcodeDetector({formats}) : new BarcodeDetector();
  } catch (e) {
    try { detector = new BarcodeDetector(); } catch (e2) {
      res.classList.add("err");
      res.textContent = "No se pudo iniciar el detector de códigos.";
      return;
    }
  }
  loop(detector);
})();
</script>
</body>
</html>
"""


def generate_token() -> str:
    return secrets.token_hex(16)


def make_qr_pil(url, box_size=10, border=2):
    """Genera una imagen PIL con el código QR de la URL.
    Retorna None si la librería qrcode no está instalada."""
    try:
        import qrcode
    except ImportError:
        return None
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white").get_image()


def get_lan_ip() -> str:
    """IP local de la red (la que el teléfono debe usar para abrir la página)."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


def _make_handler(scan_queue, token):
    class ScanHandler(BaseHTTPRequestHandler):
        def _send(self, status, body=None, content_type="application/json"):
            data = json.dumps(body).encode() if body is not None else b""
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            if data:
                self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                page = _SCAN_PAGE.replace("__TOKEN__", token)
                data = page.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            else:
                self._send(204)

        def do_POST(self):
            if self.path != "/scan":
                self._send(404, {"error": "not found"})
                return
            try:
                length = int(self.headers.get("Content-Length", 0))
                payload = json.loads(self.rfile.read(length) or b"{}")
            except Exception:
                self._send(400, {"error": "bad json"})
                return
            if payload.get("token") != token:
                self._send(403, {"error": "invalid token"})
                return
            code = str(payload.get("code") or "").strip()
            if not code:
                self._send(400, {"error": "missing code"})
                return
            scan_queue.put(code)
            self._send(200, {"ok": True})

        def log_message(self, fmt, *args):
            pass

    return ScanHandler


def start_scan_server(scan_queue, host="0.0.0.0", port=8765):
    """Inicia el servidor HTTPS en un hilo daemon.

    Retorna dict con {url, token, server} o None si no se pudo iniciar.
    """
    try:
        if not _ensure_cert():
            print("[phone_scan] Certificado no disponible; escaneo móvil deshabilitado.")
            return None
        token = generate_token()
        handler = _make_handler(scan_queue, token)
        server = ThreadingHTTPServer((host, port), handler)

        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(CERT_FILE, KEY_FILE)
        server.socket = ctx.wrap_socket(server.socket, server_side=True)

        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()

        ip = get_lan_ip()
        return {
            "url": f"https://{ip}:{port}",
            "token": token,
            "server": server,
            "thread": thread,
        }
    except Exception as e:
        print(f"[phone_scan] No se pudo iniciar el servidor de escaneo: {e}")
        return None

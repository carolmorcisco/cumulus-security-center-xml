import json
import os
from html import escape
from wsgiref.simple_server import make_server


INCIDENTS = {
    "fraude": {"menu": "Posible fraude"},
    "caja": {"menu": "Incidente caja"},
    "desembolso": {"menu": "Desembolso >50K"},
    "oficina": {"menu": "Alerta oficina"},
}


def public_base_url(environ: dict) -> str:
    configured = os.getenv("PUBLIC_BASE_URL", "").strip().rstrip("/")
    if configured:
        return configured
    scheme = environ.get("HTTP_X_FORWARDED_PROTO", environ.get("wsgi.url_scheme", "http"))
    host = environ.get("HTTP_X_FORWARDED_HOST", environ.get("HTTP_HOST", "127.0.0.1:8000"))
    return f"{scheme}://{host}".rstrip("/")


def specialist_extension() -> str:
    value = os.getenv("SPECIALIST_EXTENSION", "7001").strip()
    allowed = "0123456789#*ABCD,"
    if not value or any(character not in allowed for character in value):
        return "7001"
    return value


def security_menu(environ: dict) -> str:
    base_url = public_base_url(environ)
    menu_items = "\n".join(
        f"""  <MenuItem>
    <Name>{escape(item['menu'])}</Name>
    <URL>{escape(f'{base_url}/incident/{key}')}</URL>
  </MenuItem>"""
        for key, item in INCIDENTS.items()
    )
    return f"""<?xml version="1.0" encoding="utf-8"?>
<CiscoIPPhoneMenu>
  <Title>Cumulus Emergencias</Title>
  <Prompt>Seleccione la emergencia</Prompt>
{menu_items}
</CiscoIPPhoneMenu>"""


def phone_error(message: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<CiscoIPPhoneText>
  <Title>Cumulus Security</Title>
  <Prompt>Seleccione Volver</Prompt>
  <Text>{escape(message)}</Text>
  <SoftKeyItem>
    <Name>Volver</Name>
    <URL>SoftKey:Back</URL>
    <Position>1</Position>
  </SoftKeyItem>
  <SoftKeyItem>
    <Name>Salir</Name>
    <URL>SoftKey:Exit</URL>
    <Position>3</Position>
  </SoftKeyItem>
</CiscoIPPhoneText>"""


def incident_confirmation(incident_key: str, environ: dict) -> str | None:
    incident = INCIDENTS.get(incident_key)
    if incident is None:
        return None

    extension = specialist_extension()
    base_url = public_base_url(environ)

    # Use the simplest Dial URI for maximum compatibility with Webex Calling.
    # The phone changes to its native call screen after the user presses Conectar.
    dial_uri = f"Dial:{extension}"
    text = f"{incident['menu']}: Conectar con especialista?"

    return f"""<?xml version="1.0" encoding="utf-8"?>
<CiscoIPPhoneText>
  <Title>ALERTA DE EMERGENCIA</Title>
  <Prompt>Asistencia inmediata</Prompt>
  <Text>{escape(text)}</Text>
  <SoftKeyItem>
    <Name>Conectar</Name>
    <URL>{escape(dial_uri)}</URL>
    <Position>1</Position>
  </SoftKeyItem>
  <SoftKeyItem>
    <Name>Volver</Name>
    <URL>{escape(base_url)}</URL>
    <Position>2</Position>
  </SoftKeyItem>
  <SoftKeyItem>
    <Name>Salir</Name>
    <URL>SoftKey:Exit</URL>
    <Position>3</Position>
  </SoftKeyItem>
</CiscoIPPhoneText>"""


def browser_preview() -> str:
    items = "".join(
        f'<div class="menu-item"><span>{number}</span>{escape(item["menu"])}</div>'
        for number, item in enumerate(INCIDENTS.values(), start=1)
    )
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Cumulus Security Center</title>
  <style>
    :root {{ --navy:#07182d; --blue:#1170cf; --mint:#72e0c2; }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; min-height:100vh; display:grid; place-items:center; background:#eef7fb;
      font-family:Arial,sans-serif; color:white; }}
    .phone {{ width:390px; max-width:92vw; padding:18px; border-radius:28px; background:#101820;
      box-shadow:0 24px 60px rgba(7,24,45,.28); }}
    .screen {{ overflow:hidden; border-radius:12px; background:linear-gradient(145deg,var(--navy),#0b4780); }}
    .brand {{ padding:12px 16px 9px; border-bottom:1px solid rgba(255,255,255,.18); }}
    .brand small {{ display:block; color:var(--mint); font-weight:800; letter-spacing:.1em; }}
    .brand h1 {{ margin:3px 0 0; font-size:21px; }}
    .prompt {{ padding:9px 16px 3px; color:#d9f4ff; font-weight:700; }}
    .menu {{ padding:0 9px 10px; }}
    .menu-item {{ display:flex; align-items:center; gap:9px; margin-top:6px; padding:9px 10px;
      border-radius:7px; background:rgba(255,255,255,.1); font-weight:700; }}
    .menu-item:first-child {{ background:linear-gradient(90deg,var(--blue),#0d99c7); }}
    .menu-item span {{ display:grid; place-items:center; width:22px; height:22px; border-radius:50%;
      background:rgba(255,255,255,.18); }}
    .keys {{ display:flex; justify-content:space-between; padding:8px 18px; background:#06111f;
      color:#bcefff; font-size:12px; font-weight:700; }}
    .note {{ margin-top:12px; text-align:center; color:#24435c; font-size:13px; }}
  </style>
</head>
<body>
  <main>
    <section class="phone" aria-label="Vista simulada de la pantalla pequeña del Cisco 9811">
      <div class="screen">
        <div class="brand"><small>CUMULUS FINANCE</small><h1>Emergencias</h1></div>
        <div class="prompt">Seleccione la emergencia</div>
        <div class="menu">{items}</div>
        <div class="keys"><span>Seleccionar</span><span>Salir</span></div>
      </div>
    </section>
    <div class="note">Vista conceptual compacta para Cisco 9811.</div>
  </main>
</body>
</html>"""


def application(environ, start_response):
    method = environ.get("REQUEST_METHOD", "GET").upper()
    path = environ.get("PATH_INFO", "/")
    status = "200 OK"
    content_type = "text/xml; charset=utf-8"

    if method != "GET":
        status = "405 Method Not Allowed"
        body = phone_error("Metodo no permitido.")
    elif path == "/":
        body = security_menu(environ)
    elif path.startswith("/incident/"):
        incident_key = path.removeprefix("/incident/").strip("/")
        body = incident_confirmation(incident_key, environ)
        if body is None:
            status = "404 Not Found"
            body = phone_error("Opcion no disponible.")
    elif path == "/preview":
        content_type = "text/html; charset=utf-8"
        body = browser_preview()
    elif path == "/health":
        content_type = "application/json; charset=utf-8"
        body = json.dumps(
            {
                "status": "ok",
                "service": "cumulus-security-center",
                "specialist_extension": specialist_extension(),
            }
        )
    else:
        status = "404 Not Found"
        body = phone_error("Recurso no disponible.")

    encoded = body.encode("utf-8")
    start_response(
        status,
        [
            ("Content-Type", content_type),
            ("Content-Length", str(len(encoded))),
            ("Cache-Control", "no-store, no-cache, must-revalidate"),
        ],
    )
    return [encoded]


if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    print(f"Cumulus Security Center disponible en http://0.0.0.0:{port}")
    with make_server("0.0.0.0", port, application) as server:
        server.serve_forever()

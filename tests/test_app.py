import json
import os
import unittest
from io import BytesIO
from wsgiref.util import setup_testing_defaults

from app import application


def call_app(path="/", method="GET"):
    environ = {}
    setup_testing_defaults(environ)
    environ.update(
        {
            "REQUEST_METHOD": method,
            "PATH_INFO": path,
            "HTTP_HOST": "testserver",
            "wsgi.input": BytesIO(b""),
        }
    )
    captured = {}

    def start_response(status, headers):
        captured["status"] = status
        captured["headers"] = dict(headers)

    body = b"".join(application(environ, start_response)).decode("utf-8")
    return captured["status"], captured["headers"], body


class CumulusSecurityCenterTests(unittest.TestCase):
    def test_menu_is_compact_phone_xml(self):
        status, headers, body = call_app("/")
        self.assertEqual(status, "200 OK")
        self.assertTrue(headers["Content-Type"].startswith("text/xml"))
        self.assertIn("<CiscoIPPhoneMenu>", body)
        self.assertIn("Cumulus Security", body)
        self.assertEqual(body.count("<MenuItem>"), 4)
        self.assertIn("Posible fraude", body)
        self.assertIn("Incidente caja", body)
        self.assertIn("Desembolso &gt;50K", body)
        self.assertIn("Alerta oficina", body)

    def test_confirmation_contains_9861_dial_uri(self):
        old_value = os.environ.get("SPECIALIST_EXTENSION")
        os.environ["SPECIALIST_EXTENSION"] = "9861"
        try:
            status, _, body = call_app("/incident/fraude")
        finally:
            if old_value is None:
                os.environ.pop("SPECIALIST_EXTENSION", None)
            else:
                os.environ["SPECIALIST_EXTENSION"] = old_value
        self.assertEqual(status, "200 OK")
        self.assertIn("<CiscoIPPhoneText>", body)
        self.assertIn("Dial:9861", body)
        self.assertNotIn("Cumulus/SecurityCenter", body)
        self.assertIn("Llamar", body)

    def test_unknown_incident_returns_phone_error(self):
        status, _, body = call_app("/incident/no-existe")
        self.assertEqual(status, "404 Not Found")
        self.assertIn("<CiscoIPPhoneText>", body)
        self.assertIn("Opcion no disponible", body)

    def test_preview_and_health(self):
        preview_status, _, _ = call_app("/preview")
        health_status, _, health_body = call_app("/health")
        self.assertEqual(preview_status, "200 OK")
        self.assertEqual(health_status, "200 OK")
        self.assertEqual(json.loads(health_body)["status"], "ok")


if __name__ == "__main__":
    unittest.main()

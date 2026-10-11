import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.config import settings
from app.security import TrustedProxyAuthMiddleware


def make_test_app():
    app = FastAPI()
    app.add_middleware(TrustedProxyAuthMiddleware)

    @app.get("/documents/")
    def documents():
        return {"ok": True}

    @app.get("/health")
    def health():
        return {"ok": True}

    return app


class TestTrustedProxyAuth(unittest.TestCase):
    def test_rejects_requests_from_untrusted_network(self):
        with (
            patch.object(settings, "AUTH_MODE", "proxy"),
            patch.object(settings, "TRUSTED_PROXY_CIDRS", ["10.0.0.0/24"]),
        ):
            client = TestClient(
                make_test_app(),
                client=("10.0.1.10", 12345),
            )
            response = client.get(
                "/documents/",
                headers={"X-Auth-Request-Email": "user@example.test"},
            )

        self.assertEqual(response.status_code, 403)

    def test_requires_identity_assertion_from_trusted_proxy(self):
        with (
            patch.object(settings, "AUTH_MODE", "proxy"),
            patch.object(settings, "TRUSTED_PROXY_CIDRS", ["10.0.0.0/24"]),
        ):
            client = TestClient(
                make_test_app(),
                client=("10.0.0.10", 12345),
            )
            response = client.get("/documents/")

        self.assertEqual(response.status_code, 401)

    def test_allows_verified_identity_from_trusted_proxy(self):
        with (
            patch.object(settings, "AUTH_MODE", "proxy"),
            patch.object(settings, "TRUSTED_PROXY_CIDRS", ["10.0.0.0/24"]),
        ):
            client = TestClient(
                make_test_app(),
                client=("10.0.0.10", 12345),
            )
            response = client.get(
                "/documents/",
                headers={"X-Auth-Request-Email": "user@example.test"},
            )

        self.assertEqual(response.status_code, 200)

    def test_keeps_health_endpoint_public(self):
        with (
            patch.object(settings, "AUTH_MODE", "proxy"),
            patch.object(settings, "TRUSTED_PROXY_CIDRS", ["10.0.0.0/24"]),
        ):
            client = TestClient(
                make_test_app(),
                client=("192.168.1.10", 12345),
            )
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)

    def test_disabled_mode_preserves_local_development_access(self):
        with patch.object(settings, "AUTH_MODE", "disabled"):
            client = TestClient(
                make_test_app(),
                client=("127.0.0.1", 12345),
            )
            response = client.get("/documents/")

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()

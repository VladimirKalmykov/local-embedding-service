from __future__ import annotations

import json
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .config import Settings
from .errors import ServiceError
from .service import EmbeddingService


class ServiceHttpServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, service: EmbeddingService) -> None:
        super().__init__(address, ServiceRequestHandler)
        self.service = service


class ServiceRequestHandler(BaseHTTPRequestHandler):
    server: ServiceHttpServer

    def do_GET(self) -> None:
        if not self._authorized():
            return
        if self.path == "/health":
            self._send_json(HTTPStatus.OK, self.server.service.health())
            return
        if self.path == "/v1/models":
            self._send_json(HTTPStatus.OK, self.server.service.models())
            return
        self._send_error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")

    def do_POST(self) -> None:
        if not self._authorized():
            return
        if self.path != "/v1/embeddings":
            self._send_error(HTTPStatus.NOT_FOUND, "NOT_FOUND", "Endpoint not found.")
            return
        content_type = self.headers.get_content_type()
        if content_type != "application/json":
            self._send_error(
                HTTPStatus.UNSUPPORTED_MEDIA_TYPE,
                "INVALID_CONTENT_TYPE",
                "Content-Type must be application/json.",
            )
            return
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            content_length = 0
        limit = self.server.service.settings.max_request_bytes
        if content_length <= 0 or content_length > limit:
            self._send_error(
                HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                "INVALID_CONTENT_LENGTH",
                "Request body is empty or exceeds the size limit.",
            )
            return
        try:
            payload = json.loads(self.rfile.read(content_length))
            if not isinstance(payload, dict):
                raise ValueError("JSON body must be an object")
            result = self.server.service.create_embeddings(payload)
        except ServiceError as error:
            self._send_error(error.status, error.code, error.message)
            return
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
            self._send_error(HTTPStatus.BAD_REQUEST, "INVALID_JSON", str(error))
            return
        self._send_json(HTTPStatus.OK, result)

    def do_OPTIONS(self) -> None:
        self._send_error(
            HTTPStatus.METHOD_NOT_ALLOWED,
            "CORS_DISABLED",
            "Cross-origin browser access is disabled.",
        )

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _authorized(self) -> bool:
        token = self.server.service.settings.bearer_token
        if token is None:
            return True
        if self.headers.get("Authorization") == f"Bearer {token}":
            return True
        self._send_error(
            HTTPStatus.UNAUTHORIZED,
            "UNAUTHORIZED",
            "A valid bearer token is required.",
        )
        return False

    def _send_error(self, status: int, code: str, message: str) -> None:
        self._send_json(status, {"error": {"code": code, "message": message}})

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode(
            "utf-8"
        )
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def create_server(settings: Settings | None = None) -> ServiceHttpServer:
    resolved = settings or Settings.from_environment()
    service = EmbeddingService(resolved)
    return ServiceHttpServer((resolved.host, resolved.port), service)


def main() -> None:
    server = create_server()
    host, port = server.server_address
    print(f"Local Embedding Service listening on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()


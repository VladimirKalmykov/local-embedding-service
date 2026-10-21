from __future__ import annotations


class ServiceError(RuntimeError):
    def __init__(self, code: str, message: str, status: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status = status


class ValidationError(ServiceError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(code, message, 400)


class BackendUnavailableError(ServiceError):
    def __init__(self, message: str) -> None:
        super().__init__("BACKEND_UNAVAILABLE", message, 503)


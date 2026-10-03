class DomainError(Exception):
    """Business-rule failure raised by the service layer and mapped to an HTTP status."""

    status_code = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationFailed(DomainError):
    status_code = 400


class NotAuthenticated(DomainError):
    status_code = 401


class Forbidden(DomainError):
    status_code = 403


class NotFound(DomainError):
    status_code = 404


class Conflict(DomainError):
    status_code = 409

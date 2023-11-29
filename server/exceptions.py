import json

from fastapi import FastAPI, Request, Response


class DomainError(Exception):
    status_code = 400


class NotFoundError(DomainError):
    status_code = 404


class AlreadyExistsError(DomainError):
    status_code = 409


class UnauthorizedError(DomainError):
    status_code = 401


class UnexpectedError(DomainError):
    status_code = 500


def domain_error_handler(_request: Request, exc: DomainError) -> Response:
    return Response(status_code=exc.status_code, content=json.dumps(
        {"message": str(exc)}), media_type="application/json")


def configure(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, domain_error_handler)

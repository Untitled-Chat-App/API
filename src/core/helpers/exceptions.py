""" (module) exception
This module contains exceptions to make development easier
"""

import sys
from typing import Optional

from rich.text import Text
from rich.panel import Panel
from rich.console import Console
from fastapi import HTTPException
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded


class BaseException(Exception):
    """Base class for other exceptions to inherit form"""

    pass


class RichBaseException(BaseException):
    """
    Base rich class for other exceptions to inherit form
    This one prints the error to console with rich
    """

    def __init__(self, title: str, message: str) -> None:
        error_message = Panel(
            Text.from_markup(f"[yellow]{message}"),
            title=title,
            border_style="red",
        )
        Console().print(error_message, justify="left")
        super().__init__()


class InvalidRedisURL(RichBaseException):
    def __init__(self) -> None:
        super().__init__(
            "INVALID REDIS CONNECTION URL!!!",
            "App failed to connect to redis as invalid connection url was passed",
        )
        sys.exit(1)


class InvalidRedisPassword(RichBaseException):
    def __init__(self) -> None:
        super().__init__(
            "INVALID REDIS PASSWORD!!!",
            "App failed to connect to redis as invalid password was passed",
        )
        sys.exit(1)


class InvalidUsernameError(HTTPException):
    def __init__(self, username: str) -> None:
        status_code = 422
        detail = {
            "success": False,
            "detail": "Username failed checks",
            "username_provided": username,
            "tip": "Follow the criteria",
            "criteria": [
                "username must be 3-32 characters long",
                "no _ or . allowed at the beginning",
                "no __ or _. or ._ or .. inside",
                "no _ or . at the end",
                "Allowed Characters: a-z, A-Z, 0-9, '.' and '_'",
            ],
        }

        super().__init__(status_code, detail)


class SignupConflictError(HTTPException):
    def __init__(self, attr: Optional[str] = None, val: Optional[str] = None) -> None:
        status_code = 409
        if attr and val:
            detail = {
                "success": False,
                "detail": f"A user with the {attr}: {val} already exists!",
                "tip": f"Use another {attr}",
            }
        else:
            detail = {
                "success": False,
                "detail": "One of the values failed the unique check",
                "tip": "Change some of the values and retry",
            }

        super().__init__(status_code, detail)


class InputTooLong(HTTPException):
    def __init__(self) -> None:
        status_code = 409
        detail = {
            "success": False,
            "detail": "One of the values given was too long",
            "tip": "Try changing the length of the provided values to meet the length limits",
            "limits": {
                "username": "Max 32 characters",
                "firstname": "Max 64 characters",
                "lastname": "Max 64 characters",
                "email": "Max 256 characters",
            },
        }

        super().__init__(status_code, detail)


class InvalidEmailError(HTTPException):
    def __init__(self, email: str) -> None:
        status_code = 422
        detail = {
            "success": False,
            "detail": "Email failed checks",
            "email_provided": email,
            "tip": "Enter a real email",
        }

        super().__init__(status_code, detail)


class UserIsBanned(HTTPException):
    def __init__(self, email: str) -> None:
        status_code = 403
        detail = {
            "success": False,
            "detail": "You are banned from signing up to the app",
            "tip": "ngl thats a major skill issue, i would recommend you to just 'get good'",
        }

        super().__init__(status_code, detail)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> Response:
    response = JSONResponse(
        {
            "success": False,
            "detail": f"Rate limit exceeded: {exc.detail}",
            "tip": "Slow down buddy its really not that deep",
        },
        status_code=429,
    )
    response = request.app.state.limiter._inject_headers(
        response, request.state.view_rate_limit
    )
    return response

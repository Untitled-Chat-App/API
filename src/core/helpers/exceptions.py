""" (module) exception
This module contains exceptions to make development easier
"""

import sys
from enum import Enum
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


class HTTPStatusCodes(Enum):
    """Custom HTTP status codes to use internally"""

    EXPIRED_TOKEN = 461
    INVALID_TOKEN = 462


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


class InvalidDevmodeValue(RichBaseException):
    def __init__(self, provided: str) -> None:
        super().__init__(
            "INVALID RUN MODE!!!",
            f"DEVMODE can either be 'true' or 'false'. You provided: {provided} which is not valid!",
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


class InvalidKeyType(HTTPException):
    def __init__(self, key_type: str) -> None:
        status_code = 400
        detail = (
            {
                "success": False,
                "detail": "key_type given is not one of the options",
                "options": ["identity_key", "signed_prekey"],
                "given": key_type,
            },
        )

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


class FailedToLogin(HTTPException):
    def __init__(self) -> None:
        status_code = 401
        detail = {
            "success": False,
            "detail": "Failed to login user due to incorrect username or password",
            "tip": "Check username and password for any mistakes",
        }

        super().__init__(status_code, detail)


class ExpiredTokenError(HTTPException):
    def __init__(self) -> None:
        status_code = HTTPStatusCodes.EXPIRED_TOKEN.value

        detail = {
            "success": False,
            "detail": "Token is expired",
            "tip": "Request a new token",
        }

        super().__init__(status_code, detail)


class InvalidTokenError(HTTPException):
    def __init__(self) -> None:
        status_code = HTTPStatusCodes.INVALID_TOKEN.value

        detail = {
            "success": False,
            "detail": "Token is invalid",
            "tip": "Request a new token and stop giving me sussy ones",
        }

        super().__init__(status_code, detail)


class InvalidSignedKey(HTTPException):
    def __init__(self) -> None:
        status_code = 422

        detail = {
            "success": False,
            "detail": "Signed Pre Key provided is not a valid signed prekey",
            "tip": "please use the correct format for signed pre key",
            "format": {
                "key_id": "integer",
                "public_key": "string",
                "signature": "string",
            },
        }

        super().__init__(status_code, detail)


class NoPermission(HTTPException):
    def __init__(self, perms_needed: list[str]) -> None:
        status_code = 401

        detail = {
            "success": False,
            "detail": "You don't have permission to perform this operation",
            "required_perms": perms_needed,
            "tip": "Request ALL the neccecary scopes to be able to use this endpoint",
        }

        super().__init__(status_code, detail)


class KeyNotFound(HTTPException):
    def __init__(
        self,
        provided: int,
        key_type: str = "key",
    ) -> None:
        status_code = 404
        detail = {
            "success": False,
            "detail": f"Could not find {key_type} with the provided id",
            "provided": provided,
            "tip": "double check that you are providing the correct ID",
        }
        super().__init__(status_code, detail)


class PreKeyBundleFetchError(HTTPException):
    def __init__(self) -> None:
        status_code = 404

        detail = {
            "success": False,
            "detail": "Was not able to fetch pre key bundle! Most likely reason is that the user does not exist",
            "tip": "Double check parameters being provided to route such as the user id",
        }

        super().__init__(status_code, detail)


class InvalidSnowflakeID(HTTPException):
    def __init__(self) -> None:
        status_code = 401

        detail = {
            "success": False,
            "detail": "Snowflake provided either from a token or as an id is not valid",
            "tip": "Double check parameters being provided or if you are using a token, use a new one",
        }

        super().__init__(status_code, detail)


class InvalidSnowflakeType(HTTPException):
    def __init__(self, id_type: str) -> None:
        status_code = 401

        detail = {
            "success": False,
            "detail": "Snowflake ID type provided is not a valid type",
            "provided": id_type,
            "allowed_types": [
                "USER_ID",
                "ROOM_ID",
                "DEVICE_ID",
                "MESSAGE_ID",
                "AUTH_TOK_ID",
                "VERIF_TOK_ID",
                "REFRESH_TOK_ID",
            ],
            "tip": "Maybe try a new token if you are using one or double check the ID",
        }

        super().__init__(status_code, detail)


class SnowflakeGenerationFailed(HTTPException):
    def __init__(self) -> None:
        status_code = 500

        detail = {
            "success": False,
            "detail": "Was not able to generate a new snowflake",
            "tip": "This could be a bug if you can report this in the issues section on untitled chat github",
        }

        super().__init__(status_code, detail)


class UCHTTPExceptions:
    INVALID_USERNAME_ERROR = InvalidUsernameError
    SIGNUP_CONFLICT_ERROR = SignupConflictError
    INPUT_TOO_LONG = InputTooLong
    INVALID_EMAIL_ERROR = InvalidEmailError
    FAILED_TO_LOGIN = FailedToLogin
    EXPIRED_TOKEN_ERROR = ExpiredTokenError
    INVALID_TOKEN_ERROR = InvalidTokenError
    INVALID_SIGNED_KEY = InvalidSignedKey
    NO_PERMISSION = NoPermission
    KEY_NOT_FOUND = KeyNotFound
    PRE_KEY_BUNDLE_FETCH_ERROR = PreKeyBundleFetchError
    INVALID_SNOWFLAKE_ID = InvalidSnowflakeID
    INVALID_SNOWFLAKE_TYPE = InvalidSnowflakeType
    SNOWFLAKE_GENERATION_FAILED = SnowflakeGenerationFailed
    INVALID_KEY_TYPE = InvalidKeyType


async def user_is_banned(request: Request):
    response = JSONResponse(
        {
            "success": False,
            "detail": "You are banned from signing up to the app",
            "tip": "ngl thats a major skill issue, i would recommend you to just 'get good'",
        }
    )

    return response


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

""" (module) chatapp
This contains the ChatAPI class (FastAPI subclass)
"""

__all__ = ["ChatAPI"]

import os
from typing import Final
from os.path import join, dirname

import aioredis
from fastapi import FastAPI
from dotenv import load_dotenv
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from fastapi.middleware.cors import CORSMiddleware
from slowapi.extension import Limiter, _rate_limit_exceeded_handler


DEFAULT_RATELIMIT: Final = "30/minute"


def get_description() -> str:
    """
    Get the description for the api that will be displayed in the docs

    Returns:
        str: The api's description
    """

    path = join(dirname(__file__), "../../../", "assets/text/api_desc.md")
    with open(path) as f:
        description = f.read()
    return description


def create_redis_connection() -> aioredis.Redis:
    """
    Creates a connection the the redis database

    Returns:
        aioredis.Redis: the connection to the db
    """

    load_dotenv()

    return aioredis.from_url(
        os.environ["REDIS_URL"],
        decode_responses=True,
        password=os.environ.get("REDIS_PASSWORD"),
        port=6379,
    )


class ChatAPI(FastAPI):
    """
    This is a subclass of fastapi.FastAPI
    """

    def __init__(self, version: str) -> None:
        super().__init__(
            title="Untitled Chat REST API",
            version=version,
            description=get_description(),
            license_info={
                "name": "MIT",
                "url": "https://opensource.org/licenses/MIT",
            },
        )

        self.redis = create_redis_connection()

        # CORS
        cors_options = {
            "allow_origins": ["*"],
            "allow_methods": ["*"],
            "allow_headers": ["*"],
            "allow_credentials": True,
        }
        self.add_middleware(CORSMiddleware, **cors_options)

        # Rate Limiting
        self.state.limiter = Limiter(
            key_func=get_remote_address,
            default_limits=[DEFAULT_RATELIMIT],
        )
        self.add_middleware(SlowAPIMiddleware)
        self.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

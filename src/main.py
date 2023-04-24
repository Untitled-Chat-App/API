""" (script)
python script to start the rest api and load routes
if you are reading my code i'm sorry :moyai:
"""

__version__ = "0.0.1"
__author__ = ["FusionSid"]
__licence__ = "MIT License"

import os
import asyncio
from typing import Final
from threading import Thread
from os.path import dirname, exists, join

import uvicorn
import aioredis.exceptions
from tortoise.contrib.fastapi import register_tortoise

from rmq import rabbitmq_server
from routes import router_list, BannedUserMiddleware
from core import (
    ChatAPI,
    InvalidRedisURL,
    InvalidRedisPassword,
    InvalidDevmodeValue,
    TORTOISE_CONFIG,
)

app = ChatAPI(__version__)


@app.on_event("startup")
async def startup_event():
    try:
        await app.redis.ping()
    except aioredis.exceptions.ConnectionError:
        raise InvalidRedisURL
    except aioredis.exceptions.ResponseError:
        raise InvalidRedisPassword

    Thread(target=lambda: asyncio.run(rabbitmq_server()), daemon=True).start()


# load routes
for route in router_list:
    app.include_router(router=route)

app.add_middleware(BannedUserMiddleware)

# register tortoise orm
register_tortoise(
    app,
    config=TORTOISE_CONFIG,
    generate_schemas=True,
    add_exception_handlers=True,
)
PORT: Final = 8443
SSL_CERTFILE_PATH: Final = join(dirname(__file__), "cert.pem")
SSL_KEYFILE_PATH: Final = join(dirname(__file__), "key.pem")

both_certfiles_exist = all([exists(SSL_CERTFILE_PATH), exists(SSL_KEYFILE_PATH)])

devmode = os.environ.get("DEVMODE", "nothing").lower()
if devmode not in ["true", "false"]:
    raise InvalidDevmodeValue(provided=devmode)

if devmode == "true" or not both_certfiles_exist:
    options = {"app": "main:app", "port": PORT, "reload": True}
else:
    options = {
        "app": "main:app",
        "reload": False,
        "port": PORT,
        "access_log": False,
        "ssl_keyfile": SSL_KEYFILE_PATH,
        "ssl_certfile": SSL_CERTFILE_PATH,
    }

if __name__ == "__main__":
    uvicorn.run(**options)

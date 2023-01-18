""" (script)
python script to start the rest api and load routes
if you are reading my code i'm sorry :moyai:
"""

__version__ = "0.0.1"
__author__ = ["FusionSid"]
__licence__ = "MIT License"

import os
from os.path import dirname, join

import uvicorn
import aioredis.exceptions

from routes import router_list
from core import ChatAPI, InvalidRedisURL, InvalidRedisPassword


def main(app: ChatAPI) -> None:
    for route in router_list:
        app.include_router(route)

    # start uvicorn server
    PORT = 80
    SSL_CERTFILE_PATH = join(dirname(__file__), "cert.pem")
    SSL_KEYFILE_PATH = join(dirname(__file__), "key.pem")

    is_devmode = os.environ.get("DEVMODE", "").lower()
    if is_devmode not in ["true", "false"]:
        return print("INVALID OPTION")

    if is_devmode == "true":
        options = {"app": "main:app", "port": PORT, "reload": True}
    else:
        options = {
            "app": "main:app",
            "reload": False,
            "port": PORT,
            "access_log": False,
            "ssl_keyfile": SSL_CERTFILE_PATH,
            "ssl_certfile": SSL_KEYFILE_PATH,
        }

    uvicorn.run(**options)


# Has to be outside if __name__ block as uvicorn can't find it otherwise
app = ChatAPI(__version__)


@app.on_event("startup")
async def startup_event():
    # Ping the redis server to check if its connected
    # If ping fails raise an exception and kill the app
    try:
        await app.redis.ping()
    except aioredis.exceptions.ConnectionError:
        raise InvalidRedisURL
    except aioredis.exceptions.ResponseError:
        raise InvalidRedisPassword


if __name__ == "__main__":
    main(app)

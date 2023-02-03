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
from core import ChatAPI, InvalidRedisURL, InvalidRedisPassword, Base, engine

app = ChatAPI(__version__)


@app.on_event("startup")
async def startup_event():
    try:
        await app.redis.ping()
    except aioredis.exceptions.ConnectionError:
        raise InvalidRedisURL
    except aioredis.exceptions.ResponseError:
        raise InvalidRedisPassword

    async with engine.begin() as conn:
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


# load routes
for route in router_list:
    app.include_router(router=route)

# start uvicorn server
PORT = 8443
SSL_CERTFILE_PATH = join(dirname(__file__), "cert.pem")
SSL_KEYFILE_PATH = join(dirname(__file__), "key.pem")

is_devmode = os.environ.get("DEVMODE", "").lower()
if is_devmode not in ["true", "false"]:
    print("INVALID OPTION")
    exit(1)  # bad

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

if __name__ == "__main__":
    uvicorn.run(**options)

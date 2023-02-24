import json
import asyncio
from typing import AsyncIterator
from contextlib import asynccontextmanager

from aio_pika import Message, connect
from aio_pika.abc import AbstractChannel

CONN_URL = "amqp://guest:guest@localhost/"


@asynccontextmanager
async def get_channel(queue_name: str) -> AsyncIterator[AbstractChannel]:
    """
    Asynchronous context manager for getting a channel connection

    Parameters:
        queue_name (str): The name of the queue to connect to

    Yeilds:
        channel: AsyncIterator[aio_pika.AbstractChannel]b
    """
    connection = await connect(CONN_URL)
    channel = await connection.channel()
    await channel.declare_queue(queue_name)

    yield channel

    await connection.close()


# test case
async def main() -> None:
    MSG1 = {"email": "e@e.com", "eee": 5}
    MSG2 = {"password": "FusionSid"}
    async with get_channel("send_emails") as channel1:
        await channel1.default_exchange.publish(
            Message(json.dumps(MSG1).encode()),
            routing_key="send_emails",
        )

    async with get_channel("hash_pass") as channel2:
        await channel2.default_exchange.publish(
            Message(json.dumps(MSG2).encode()),
            routing_key="hash_pass",
        )


if __name__ == "__main__":
    asyncio.run(main())

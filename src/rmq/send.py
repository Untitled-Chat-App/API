import json
from typing import AsyncIterator
from contextlib import asynccontextmanager

from aio_pika import Message, connect
from aio_pika.abc import AbstractChannel

from core import RMQ_CONN_URL


@asynccontextmanager
async def get_channel(queue_name: str) -> AsyncIterator[AbstractChannel]:
    """
    Asynchronous context manager for getting a channel connection

    Parameters:
        queue_name (str): The name of the queue to connect to

    Yeilds:
        channel: AsyncIterator[aio_pika.AbstractChannel]
    """
    connection = await connect(RMQ_CONN_URL)
    channel = await connection.channel()
    await channel.declare_queue(queue_name)

    yield channel

    await connection.close()


async def send_to_channel(channel_name: str, data: dict) -> None:
    async with get_channel(channel_name) as channel:
        await channel.default_exchange.publish(
            Message(json.dumps(data).encode()),
            routing_key=channel_name,
        )

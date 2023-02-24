# these 2 are test queue callbacks
# ill change them to actual functions later
import json
import asyncio

from aio_pika import connect
from aio_pika.abc import AbstractIncomingMessage

from core import argon2_hash


async def on_message_email(message: AbstractIncomingMessage) -> None:
    message_data = json.loads(message.body)
    print(f"SENDING EMAIL TO {message_data['email']}")


async def on_message_hash(message: AbstractIncomingMessage) -> None:
    msg = message.body
    msg = json.loads(msg)
    print(await argon2_hash(msg["password"]))


async def rabbitmq_server() -> None:
    CHANNELS = [
        {"name": "send_emails", "callback": on_message_email},
        {"name": "hash_pass", "callback": on_message_hash},
    ]
    connection = await connect("amqp://guest:guest@localhost/")
    async with connection:
        for channel_data in CHANNELS:
            channel = await connection.channel()
            queue = await channel.declare_queue(channel_data["name"])
            await queue.consume(channel_data["callback"], no_ack=True)

        await asyncio.Future()

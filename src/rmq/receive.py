import os
import json
import asyncio

from tortoise import Tortoise
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

import aiosmtplib
from dotenv import load_dotenv
from aio_pika import connect, Message
from aio_pika.abc import AbstractIncomingMessage

from core import RMQ_CONN_URL, User, TORTOISE_CONFIG

load_dotenv()  # just incase ya feel me?
BASE_URL = (
    "http://127.0.0.1:8443/api/v1"
    if os.environ["DEVMODE"] == "false"
    else "https://chatapi.fusionsid.xyz/api/v1"
)


async def sendmail(message: MIMEMultipart):
    smtp_client = aiosmtplib.SMTP(hostname="smtp.gmail.com", port=465, use_tls=True)

    await smtp_client.connect()
    await smtp_client.ehlo()
    await smtp_client.login(os.environ["EMAIL"], os.environ["EMAIL_PASSWORD"])

    try:
        await smtp_client.send_message(message)
    except (aiosmtplib.SMTPRecipientsRefused, aiosmtplib.SMTPResponseException):
        data = {"user_id": message["user_id"]}
        await delete_user_account(Message(json.dumps(data).encode()))

    await smtp_client.quit()


async def send_verification_email(msg: AbstractIncomingMessage) -> None:
    message = json.loads(msg.body)
    # Email data
    email = MIMEMultipart("alternative")
    email["To"] = message["email"]
    email["From"] = "chat@fusionsid.xyz"
    email["Subject"] = "Verify Untitled Chat Email!"
    token = message["token"]
    html = f"<a href='{BASE_URL}/users/verify?token={token}'>LINK</a>\n<p>Token: {token}</p>"
    email.attach(MIMEText(html, "html"))

    await sendmail(email)


async def send_welcome_email(msg: AbstractIncomingMessage) -> None:
    message = json.loads(msg.body)
    # Email data
    email = MIMEMultipart("alternative")
    email["To"] = message["email"]
    email["From"] = "chat@fusionsid.xyz"
    email["Subject"] = "Welcome to Untitled Chat"

    html = "Welcome to untitled chat"
    email.attach(MIMEText(html, "html"))

    await sendmail(email)


async def delete_user_account(msg: AbstractIncomingMessage | Message) -> None:
    message = json.loads(msg.body)
    user_id = message["user_id"]

    await User.filter(id=user_id).delete()


async def rabbitmq_server() -> None:
    # create db connection
    await Tortoise.init(config=TORTOISE_CONFIG)

    CHANNELS = [
        {"name": "verification_email", "callback": send_verification_email},
        {"name": "welcome_email", "callback": send_welcome_email},
        {"name": "delete_account", "callback": delete_user_account},
    ]
    connection = await connect(RMQ_CONN_URL)
    async with connection:
        for channel_data in CHANNELS:
            channel = await connection.channel()
            queue = await channel.declare_queue(channel_data["name"])
            await queue.consume(channel_data["callback"], no_ack=True)

        await asyncio.Future()

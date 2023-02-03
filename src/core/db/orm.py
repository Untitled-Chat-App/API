__all__ = ("Base", "get_session", "engine")

import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

load_dotenv()

engine = create_async_engine(
    os.environ["DATABASE_URL"],
    echo=True if os.environ["DEVMODE"] == "true" else False,
    future=True,
)
Base = declarative_base()


@asynccontextmanager
async def get_session():
    try:
        async_session: AsyncSession = sessionmaker(engine, class_=AsyncSession)  # type: ignore

        async with async_session() as session:  # type: ignore
            yield session
    except Exception:
        await session.rollback()  # type: ignore
        raise

    finally:
        await session.close()

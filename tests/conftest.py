from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db import models  # noqa: F401  registers all tables on Base.metadata
from app.db.base import Base
from app.db.models import User


@pytest_asyncio.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    async with sessionmaker() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def user(db_session: AsyncSession) -> User:
    u = User(id=1, first_name="Test")
    db_session.add(u)
    await db_session.commit()
    return u


@pytest.fixture
def frozen_time():
    from freezegun import freeze_time

    return freeze_time

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


@pytest_asyncio.fixture(autouse=True)
async def _reset_send_limiter():
    """Full tokens + a fresh lock before every test.

    app.scheduler.notify._send_limiter is a module-level singleton shared
    for the whole process lifetime — correct in production (one real 20/sec
    cap across all sends), but across a pytest session it means later tests
    inherit whatever token deficit earlier tests left behind, and its
    asyncio.Lock is bound to whichever event loop first acquired it. Without
    this reset, unrelated tests can block for real wall-clock seconds on
    genuine rate-limit sleeps or a lock tied to an already-closed loop.
    """
    import time

    from app.scheduler.notify import _send_limiter

    _send_limiter._tokens = float(_send_limiter._capacity)
    _send_limiter._last_refill = time.monotonic()
    _send_limiter._lock = None
    yield

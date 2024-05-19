import asyncio
from typing import Any
from urllib.parse import urljoin

import aiohttp
import pytest
from redis.asyncio import Redis

from .settings import test_settings


@pytest.fixture(scope="session")
async def clean_cache():
    """Удаление всех ключей из Redis (из текущей db)"""

    redis = Redis.from_url(
        f"redis://{test_settings.REDIS.REDIS_HOST}:{test_settings.REDIS.REDIS_PORT}",
    )
    await redis.flushdb()
    yield redis
    await redis.close()


@pytest.fixture(scope="session")
async def client_session() -> aiohttp.ClientSession:
    """AIOHTTP - сессия"""

    client_session = aiohttp.ClientSession()
    yield client_session
    await client_session.close()


@pytest.fixture(scope="session")
async def event_loop(request):
    """Event_loop для scope='session'"""

    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def make_get_request(client_session):
    """Отправка GET - запроса c AIOHTTP - сессией"""

    async def inner(endpoint: str, params: dict | None = None) -> tuple[Any, Any]:
        params = params or {}
        url = urljoin(test_settings.MOVIES_API_URL, endpoint)
        async with client_session.get(url, params=params) as raw_response:
            response = await raw_response.json()
            status = raw_response.status

            return status, response

    return inner

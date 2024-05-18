import asyncio
from typing import Any
from urllib.parse import urljoin

import aiohttp
import pytest
from redis.asyncio import Redis

from settings import test_settings


@pytest.fixture(scope="session")
async def clean_cache():
    """Удаление всех ключей из Redis (из текущей db)"""

    redis = Redis.from_url(
        f"redis://{test_settings.redis.host}:{test_settings.redis.port}",
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
        url = urljoin(test_settings.movies_api_url, endpoint)
        async with client_session.get(url, params=params) as raw_response:
            response = await raw_response.json()
            status = raw_response.status

            return status, response

    return inner

# @pytest.fixture
# def es_write_data():
#     async def inner(data: List[dict]):
#         bulk_query = get_es_bulk_query(data, test_settings.es_index, test_settings.es_id_field)
#         str_query = '\n'.join(bulk_query) + '\n'
#
#         es_client = AsyncElasticsearch(hosts=test_settings.es_host,
#                                        validate_cert=False,
#                                        use_ssl=False)
#         response = await es_client.bulk(str_query, refresh=True)
#         await es_client.close()
#         if response['errors']:
#             raise Exception('Ошибка записи данных в Elasticsearch')
#
#     return inner

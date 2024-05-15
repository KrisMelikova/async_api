from typing import Any

from orjson import orjson
from redis.asyncio import Redis

from src.core.config import config
from src.core.logger import a_api_logger
from src.utils.orjson_dumps import orjson_dumps

redis: Redis | None = None


async def get_redis() -> Redis:
    return redis


class CacheService:
    """Имплементация класса для кеширования данных"""

    def __init__(self, cache: Redis, index: str):
        self.cache = cache
        self.index = index

    async def cache_key_generation(self, **kwargs) -> str:
        """Генерация ключа для кеширования"""

        sorted_kwargs = dict(sorted(kwargs.items()))
        key_strings = [self.index]

        for key, value in sorted_kwargs.items():
            key_strings.append(f"{key}::{value}")

        prepared_key = "::".join(key_strings)

        return prepared_key

    async def get(self, key) -> Any:
        """Получение данных из кеша"""

        try:
            data = await self.cache.get(key)
        except Exception as exc:
            a_api_logger.error(
                f"Ошибка при взятии значения по ключу {key} из кеша: {exc}"
            )
            return None

        if not data:
            return None

        if isinstance(data := orjson.loads(data), list):
            return [orjson.loads(item) for item in data]
        return data

    async def set(self, key, value) -> None:
        """Сохранение данных в кеш"""

        try:
            if isinstance(value, list):
                await self.cache.set(
                    key,
                    orjson_dumps([item.json() for item in value], default=list),
                    ex=config.cache_expire_in_seconds,
                )
            else:
                await self.cache.set(
                    key, value.json(), ex=config.cache_expire_in_seconds
                )
        except Exception as exc:
            a_api_logger.error(f"Ошибка при записи по ключу {key} в кеш: {exc}")

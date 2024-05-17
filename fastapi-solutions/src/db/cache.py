from abc import abstractmethod, ABC
from typing import Any

from orjson import orjson
from redis.asyncio import Redis

from src.core.config import config
from src.core.logger import a_api_logger
from src.models.model_config import BaseOrjsonModel
from src.utils.orjson_dumps import orjson_dumps

redis: Redis | None = None


async def get_redis() -> Redis:
    return redis


class BaseAsyncCacheService(ABC):
    @abstractmethod
    async def cache_key_generation(self, **kwargs):
        pass

    @abstractmethod
    async def get_single_record(self, key):
        pass

    @abstractmethod
    async def get_list_of_records(self, key):
        pass

    @abstractmethod
    async def set_single_record(self, key, value):
        pass

    @abstractmethod
    async def set_list_of_records(self, key, value):
        pass


class AsyncCacheService(BaseAsyncCacheService):
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

    async def get_data_from_cache(self, key: str) -> Any:
        """Получение данных из кеша по ключу"""

        try:
            data = await self.cache.get(key)
        except Exception as exc:
            a_api_logger.error(
                f"Ошибка при взятии значения по ключу {key} из кеша: {exc}"
            )
            return None

        if not data:
            return None

        return orjson.loads(data)

    async def get_single_record(self, key: str) -> Any:
        """Получение данных о единичной записи из кеша по ключу"""

        data = await self.get_data_from_cache(key)

        if not data:
            return None

        return data

    async def get_list_of_records(self, key: str) -> Any:
        """Получение данных о списке записей из кеша по ключу"""

        data = await self.get_data_from_cache(key)

        if not data:
            return None

        return [orjson.loads(item) for item in data]

    async def set_single_record(self, key: str, value: BaseOrjsonModel) -> None:
        """Сохранение единичной записи в кеш"""

        try:
            await self.cache.set(
                key, value.json(), ex=config.cache_expire_in_seconds
            )
        except Exception as exc:
            a_api_logger.error(f"Ошибка при записи по ключу {key} в кеш: {exc}")

    async def set_list_of_records(self, key: str, value: list[BaseOrjsonModel]) -> None:
        """Сохранение списка записей в кеш"""

        try:
            await self.cache.set(
                key,
                orjson_dumps([item.json() for item in value], default=list),
                ex=config.cache_expire_in_seconds,
            )
        except Exception as exc:
            a_api_logger.error(f"Ошибка при записи по ключу {key} в кеш: {exc}")

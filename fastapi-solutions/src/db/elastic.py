from abc import ABC, abstractmethod

from elastic_transport import ObjectApiResponse
from elasticsearch import AsyncElasticsearch, NotFoundError

from src.core.logger import a_api_logger

es: AsyncElasticsearch | None = None


async def get_elastic() -> AsyncElasticsearch:
    return es


class AbstractElasticsearchRepository(ABC):
    """Абстрактный репозиторий Elasticsearch"""

    def __init__(self, elastic: AsyncElasticsearch, index: str):
        self.elastic = elastic
        self.index = index

    @abstractmethod
    async def get(self, id_: str) -> dict[str, any] | None:
        """Получение сущности по ID"""

    @abstractmethod
    async def search(self, query: dict) -> ObjectApiResponse | None:
        """Поиск сущностей по запросу"""


class ElasticSearchRepository(AbstractElasticsearchRepository, ABC):
    """Репозиторий для работы с Elasticsearch"""

    async def get(self, id_: str) -> dict[str, any] | None:
        """Получение сущности по ID"""
        try:
            doc = await self.elastic.get(index=self.index, id=id_)
            return doc["_source"]
        except NotFoundError as e:
            a_api_logger.error(f"Сущность не найдена: {e}")
            return None

    async def search(self, query: dict) -> ObjectApiResponse | None:
        """Поиск сущностей по запросу"""
        try:
            result = await self.elastic.search(index=self.index, body=query)
            return result
        except Exception as e:
            a_api_logger.error(f"Ошибка при поиске: {e}")
            return None

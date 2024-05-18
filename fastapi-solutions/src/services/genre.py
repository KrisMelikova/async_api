import uuid
from functools import lru_cache

from elastic_transport import ObjectApiResponse
from elasticsearch import NotFoundError, AsyncElasticsearch
from fastapi import Depends
from redis.asyncio import Redis

from src.core.logger import a_api_logger
from src.db.cache import get_redis, AsyncCacheService
from src.db.elastic import ElasticSearchRepository, get_elastic
from src.models.genre import Genre


class GenreService:
    """Класс, позволяющий вернуть данные о жанрах"""

    def __init__(
        self,
        cache: Redis,
        elastic: AsyncElasticsearch,
        index_name: str = "genres",
    ):
        self.index_name = index_name
        self.cache = AsyncCacheService(cache, self.index_name)
        self.elastic = ElasticSearchRepository(elastic, self.index_name)

    async def get_genre(self, genre_uuid: str) -> Genre | None:
        """Получение информации по конкретному жанру по его uuid"""

        cache_key = await self.cache.cache_key_generation(genre_uuid=genre_uuid)
        genre = await self.cache.get_single_record(cache_key)

        if not genre:
            genre = await self.elastic.get(genre_uuid)

            if not genre:
                a_api_logger.info(f"Жанр (uuid: {genre_uuid}) не найден")
                return None

            genre = Genre(**genre)

            await self.cache.set_single_record(cache_key, genre)

        return genre

    async def get_genres(self, page_number: int, page_size: int) -> list[Genre] | None:
        """Получение списка жанров из поисковой системы или кеша"""

        cache_key = await self.cache.cache_key_generation(
            page_number=page_number,
            page_size=page_size,
        )
        genres = await self.cache.get_list_of_records(cache_key)

        if not genres:
            genres = await self.get_all_genres_from_elastic(
                page_size=page_size, page_number=page_number
            )

            if not genres:
                return None

            await self.cache.set_list_of_records(cache_key, genres)

        return genres

    async def get_genre_name(self, genre_id: uuid.UUID = None) -> str | None:
        """Получение названия жанра по переданному uuid жанра"""
        if genre_id:
            genre_result = await self.elastic.get(str(genre_id))
            return genre_result["name"]
        return None

    async def get_uuid_genre(self, genre_name: str) -> uuid.UUID:
        """Получение uuid жанра по переданному названию жанра"""

        query = {"query": {"match": {"name": genre_name}}}
        response = await self.elastic.search(query)
        if response["hits"]["total"]["value"] > 0:
            genre_data = response["hits"]["hits"][0]["_source"]
            return genre_data["id"]
        else:
            raise NotFoundError(f"Жанр '{genre_name}' не найден")

    async def get_all_genres_from_elastic(
        self, page_size: int, page_number: int
    ) -> list[Genre] | None:
        """Получение списка жанров из поисковой системы"""

        query = await self.construct_query_for_genres_list(page_size, page_number)
        es_response = await self.elastic.search(query)
        genres = await self.parse_result_w_genres_list(es_response)

        return genres

    async def construct_query_for_genres_list(
        self, page_size: int, page_number: int
    ) -> dict:
        """Получение запроса для выборки жанров из поисковой системы"""

        query = {
            "query": {"match_all": {}},
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }

        return query

    async def parse_result_w_genres_list(
        self, es_response: ObjectApiResponse
    ) -> list[Genre] | None:
        """Парсинг результата поиска жанров"""

        hits = es_response.get("hits")
        if not hits:
            a_api_logger.info("Не найдено ни одного жанра")
            return None

        total = es_response["hits"]["total"]["value"]
        a_api_logger.info(f"Найдено {total} жанров")

        genres = [Genre(**doc["_source"]) for doc in hits.get("hits", [])]

        return genres


@lru_cache()
def get_genre_service(
    cache: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(cache, elastic)

import uuid
from functools import lru_cache
from typing import Optional

from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from src.core.logger import a_api_logger
from src.db.cache import get_redis, AsyncCacheService
from src.db.elastic import ElasticSearchRepository, get_elastic
from src.models.person import PersonWithFilms, PersonFilm, PersonFilmWithRating
from src.services.film import FilmService, get_film_service


class PersonService:
    def __init__(
        self,
        cache: Redis,
        elastic: AsyncElasticsearch,
        film_service: FilmService,
        index_name: str = "persons",
    ):
        self.index_name = index_name
        self.cache = AsyncCacheService(cache, self.index_name)
        self.elastic = ElasticSearchRepository(elastic, self.index_name)
        self.film_service = film_service

    async def get_by_id(self, person_id: str) -> Optional[PersonWithFilms]:
        """Получение данных о персоне по ее id"""

        cache_key = await self.cache.cache_key_generation(person_uuid=person_id)
        person = await self.cache.get_single_record(cache_key)

        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                a_api_logger.info(f"Персона с id {person_id} не найдена")
                return None

            await self.cache.set_single_record(cache_key, person)

        return person

    async def search_for_a_person(
        self, query: str, page_number: int = 1, page_size: int = 10
    ):
        """Полнотекcтовый поиск для персон"""
        try:
            query = await self._construct_query(query, page_number, page_size)
            doc = await self.elastic.search(query)

            persons_list = []
            for hit in doc["hits"]["hits"]:
                films = await self.film_service.get_films_for_persons(
                    hit["_source"]["full_name"]
                )
                person_films = [
                    PersonFilm(uuid=film[0], roles=film[1]["roles"])
                    for film in films.items()
                ]
                persons_list.append(
                    PersonWithFilms(
                        uuid=hit["_source"]["id"],
                        full_name=hit["_source"]["full_name"],
                        films=person_films,
                    ).dict()
                )
        except NotFoundError:
            a_api_logger.info(f"Для запроса {query} по персонам ничего не найдено")
            return None
        return persons_list

    async def _construct_query(
        self,
        query: str,
        page_number: int = 1,
        page_size: int = 10,
    ) -> dict:
        """Создание запроса для выполнения к индексу Elasticsearch"""

        query = {
            "query": {"match": {"full_name": {"query": query, "fuzziness": "auto"}}},
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        return query

    async def get_only_person_films(
        self, person_id: uuid
    ) -> list[PersonFilmWithRating] | None:
        """Получение фильмов персоны по ее id"""

        cache_key = await self.cache.cache_key_generation(
            person_uuid=person_id, movie="movie"
        )
        person_films = await self.cache.get_list_of_records(cache_key)

        if not person_films:
            person_films = await self.elastic.get(person_id)
            if person_films:
                films = await self.film_service.get_films_for_persons(
                    person_films["full_name"]
                )
                person_films = [
                    PersonFilmWithRating(
                        uuid=film[0],
                        title=film[1]["title"],
                        imdb_rating=film[1]["imdb_rating"],
                    )
                    for film in films.items()
                ]
                await self.cache.set_list_of_records(cache_key, person_films)
        return person_films

    async def _get_person_from_elastic(self, person_id: uuid) -> PersonWithFilms | None:
        """Получение персоны из поисковой системы"""

        result = await self.elastic.get(person_id)
        if result:
            films = await self.film_service.get_films_for_persons(result["full_name"])
            person_films = [
                PersonFilm(uuid=film[0], roles=film[1]["roles"])
                for film in films.items()
            ]
            return PersonWithFilms(
                uuid=result["id"], full_name=result["full_name"], films=person_films
            )
        return None


@lru_cache()
def get_person_service(
    cache: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
    film_service: FilmService = Depends(get_film_service),
) -> PersonService:
    return PersonService(cache, elastic, film_service)

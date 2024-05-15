import uuid
from functools import lru_cache
from typing import Optional

from fastapi import Depends

from elasticsearch import AsyncElasticsearch, NotFoundError
from redis.asyncio import Redis

from src.core.logger import a_api_logger
from src.db.elastic import get_elastic
from src.db.cache import get_redis, CacheService
from src.models.person import PersonWithFilms, PersonFilm, PersonFilmWithRating


class PersonService:
    def __init__(
        self, cache: Redis, elastic: AsyncElasticsearch, index_name: str = "persons"
    ):
        self.index_name = index_name
        self.cache = CacheService(cache, self.index_name)
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[PersonWithFilms]:
        cache_key = await self.cache.cache_key_generation(person_uuid=person_id)
        person = await self.cache.get(cache_key)

        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                a_api_logger.info("Not found person")
                return None

            await self.cache.set(cache_key, person)

        return person

    async def search_for_a_person(
        self, query: str, page_number: int = 1, page_size: int = 10
    ):
        try:
            query = await self._construct_query(query, page_number, page_size)
            doc = await self.elastic.search(index="persons", body=query)
            persons_list = []
            for hit in doc["hits"]["hits"]:
                films = await self._get_films_for_persons(hit["_source"]["full_name"])
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

    async def get_only_person_films(self, person_id: uuid) -> PersonWithFilms | None:
        cache_key = await self.cache.cache_key_generation(
            person_uuid=person_id, movie="movie"
        )
        person_films = await self.cache.get(cache_key)

        if not person_films:
            try:
                doc = await self.elastic.get(index="persons", id=person_id)
                result = doc["_source"]
                films = await self._get_films_for_persons(result["full_name"])
                person_films = [
                    PersonFilmWithRating(
                        uuid=film[0],
                        title=film[1]["title"],
                        imdb_rating=film[1]["imdb_rating"],
                    )
                    for film in films.items()
                ]
            except NotFoundError:
                a_api_logger.error("Failed to get person films from elastic!")
                return None

            await self.cache.set(cache_key, person_films)

        return person_films

    async def _get_person_from_elastic(self, person_id: uuid) -> PersonWithFilms | None:
        try:
            doc = await self.elastic.get(index="persons", id=person_id)
            result = doc["_source"]
            films = await self._get_films_for_persons(result["full_name"])
            person_films = [
                PersonFilm(uuid=film[0], roles=film[1]["roles"])
                for film in films.items()
            ]
        except NotFoundError:
            a_api_logger.error("Failed to get person from elastic!")
            return None
        return PersonWithFilms(
            uuid=result["id"], full_name=result["full_name"], films=person_films
        )

    async def _get_films_for_persons(self, person_name: str) -> dict | None:
        ROLES = {
            "directors_names": "director",
            "actors_names": "actor",
            "writers_names": "writer",
        }
        try:
            films = {}
            for role in ROLES.keys():
                query = {
                    "query": {
                        "bool": {
                            "should": [{"match": {role: person_name}}],
                            "minimum_should_match": 1,
                        }
                    }
                }
                result = await self.elastic.search(index="movies", body=query)
                if result:
                    for film in result["hits"]["hits"]:
                        film = film["_source"]
                        if film["id"] not in films:
                            films[film["id"]] = {}
                            films[film["id"]]["roles"] = [ROLES[role]]
                            films[film["id"]]["title"] = film["title"]
                            films[film["id"]]["imdb_rating"] = film["imdb_rating"]
                        else:
                            films[film["id"]]["roles"].append(ROLES[role])
            return films
        except NotFoundError:
            return None


@lru_cache()
@lru_cache()
def get_person_service(
    cache: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(cache, elastic)

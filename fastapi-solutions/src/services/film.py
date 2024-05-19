import uuid
from functools import lru_cache

from elasticsearch import AsyncElasticsearch
from pydantic import parse_obj_as
from fastapi import Depends
from redis.asyncio import Redis

from src.db.cache import get_redis, AsyncCacheService

from src.models.film import FullFilm, Genre, FilmBase
from src.models.person import Person
from src.db.elastic import ElasticSearchRepository, get_elastic
from src.services.genre import GenreService, get_genre_service

ROLES = {
    "directors_names": "director",
    "actors_names": "actor",
    "writers_names": "writer",
}


class FilmService:
    """Класс, который позволяет вернуть данные о фильмах"""

    def __init__(
        self,
        cache: Redis,
        elastic: AsyncElasticsearch,
        genre_service: GenreService,
        index_name: str = "movies",
    ):
        self.index_name = index_name
        self.cache = AsyncCacheService(cache, self.index_name)
        self.elastic = ElasticSearchRepository(elastic, self.index_name)
        self.genre_service = genre_service

    async def get_film_details(self, film_id: str) -> FullFilm | None:
        """Получение полной информации по фильму"""

        cache_key = await self.cache.cache_key_generation(film_uuid=film_id)
        film = await self.cache.get_single_record(cache_key)

        if not film:
            film_data = await self.elastic.get(film_id)
            if not film_data:
                return None
            film = await self.get_full_info(film_data)

            await self.cache.set_single_record(cache_key, film)

            return film

        film = FullFilm(**film)

        return film

    async def get_full_info(self, film_data: dict) -> FullFilm:
        """Преобразование исходных данных фильма"""

        genres_list = []
        for genre_name in film_data["genres"]:
            genre_uuid = await self.genre_service.get_uuid_genre(genre_name)
            genre_obj = Genre(id=genre_uuid, name=genre_name)
            genres_list.append(genre_obj)

        film_data.update(
            {
                "genres": genres_list,
                "actors": await self.get_person_list(film_data["actors"]),
                "writers": await self.get_person_list(film_data["writers"]),
                "directors": await self.get_person_list(film_data["directors"]),
            }
        )
        return FullFilm(**film_data)

    @staticmethod
    async def get_person_list(person_data):
        return [
            Person(uuid=person["id"], full_name=person["name"])
            for person in person_data
        ]

    async def get_similar_films(self, film_id: str) -> list[FilmBase] | None:
        """Получение списка фильмов, у которых есть хотя бы один такой же жанр,
        как у переданного фильма (film_id)"""

        cache_key = await self.cache.cache_key_generation(
            film_uuid=film_id, similar="similar"
        )
        cached_film_data = await self.cache.get_list_of_records(cache_key)

        if not cached_film_data:
            film_data = await self.elastic.get(film_id)
            if not film_data:
                return None

            genres = film_data["genres"]
            query = {
                "query": {
                    "bool": {
                        "should": [{"match": {"genres": genre}} for genre in genres],
                        "minimum_should_match": 1,
                    }
                }
            }
            result = await self.elastic.search(query)

            films = [
                parse_obj_as(FilmBase, hit["_source"]) for hit in result["hits"]["hits"]
            ]

            await self.cache.set_list_of_records(cache_key, films)

            return films

        return [FilmBase(**data) for data in cached_film_data]

    async def get_all_films_from_elastic(
        self,
        genre: uuid.UUID = None,
        sort: str = "-imdb_rating",
        page_number: int = 1,
        page_size: int = 10,
    ) -> list[FilmBase]:
        """Получение всех фильмов с возможностью фильтрации по uuid жанра.
        По умолчанию отсортированы по убыванию imdb_rating"""

        cache_key = await self.cache.cache_key_generation(
            genre=genre,
            sort=sort,
            page_number=page_number,
            page_size=page_size,
        )
        films = await self.cache.get_list_of_records(cache_key)

        if not films:
            query = await self.construct_query(genre, sort, page_number, page_size)

            result = await self.elastic.search(query)
            films = [FilmBase(**doc["_source"]) for doc in result["hits"]["hits"]]

            if films:
                await self.cache.set_list_of_records(cache_key, films)
                return films
        return [FilmBase(**data) for data in films]

    async def construct_query(
        self,
        genre: uuid.UUID = None,
        sort: str = "-imdb_rating",
        page_number: int = 1,
        page_size: int = 10,
    ) -> dict:
        """Создание запроса на получение фильмов с фильтрацией по жанру из Elasticsearch"""

        sort_direction, sort_field = self.sort(sort)

        query = {
            "query": {"match_all": {}},
            "sort": [{sort_field: {"order": sort_direction}}],
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        genre_name = await self.genre_service.get_genre_name(genre)
        if genre_name:
            query["query"] = {"terms": {"genres": [str(genre_name)]}}
        return query

    async def search_film(
        self, search: str, page_number: int, page_size: int
    ) -> list[FilmBase] | None:
        """Поиск фильмов"""

        query = await self.construct_query_for_search(search, page_number, page_size)
        result = await self.elastic.search(query)

        film = [
            parse_obj_as(FilmBase, hit["_source"]) for hit in result["hits"]["hits"]
        ]
        return film

    @staticmethod
    async def construct_query_for_search(
        search: str, page_number: int, page_size: int
    ) -> dict:
        """Создание запроса для полнотекстового поиска фильмов в Elasticsearch"""

        query = {
            "query": {
                "multi_match": {
                    "query": search,
                    "fields": ["title", "description"],
                    "fuzziness": "AUTO",
                }
            },
            "from": (page_number - 1) * page_size,
            "size": page_size,
        }
        return query

    async def get_films_for_persons(self, person_name: str) -> dict | None:
        """Получение фильмов по персонам"""

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
            result = await self.elastic.search(query)
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

    @staticmethod
    def sort(sort: str) -> tuple[str, str]:
        sort_direction = "asc" if not sort.startswith("-") else "desc"
        sort_field = sort[1:] if sort_direction == "desc" else sort
        return sort_direction, sort_field


@lru_cache()
def get_film_service(
    cache: Redis = Depends(get_redis),
    elastic: AsyncElasticsearch = Depends(get_elastic),
    genre_service: GenreService = Depends(get_genre_service),
) -> FilmService:
    return FilmService(cache, elastic, genre_service)

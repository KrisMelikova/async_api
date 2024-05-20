from orjson import orjson

from pydantic import BaseModel, Field


def orjson_dumps(v, *, default):
    return orjson.dumps(v, default=default).decode()


class BaseOrjsonModel(BaseModel):
    class Config:
        populate_by_name = True
        json_loads = orjson.loads
        json_dumps = orjson_dumps


class Genre(BaseOrjsonModel):
    uuid: str = Field(alias="id")
    name: str


class Person(BaseOrjsonModel):
    uuid: str
    full_name: str


class FullFilm(BaseOrjsonModel):
    uuid: str = Field(..., alias="id")
    title: str | None
    description: str | None
    imdb_rating: float | None
    genres: list[Genre]
    actors: list[Person]
    writers: list[Person]
    directors: list[Person]

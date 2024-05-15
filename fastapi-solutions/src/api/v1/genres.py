import uuid
from http import HTTPStatus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.services.genre import GenreService, get_genre_service
from src.utils.pagination import Paginator

router = APIRouter()


class Genre(BaseModel):
    uuid: uuid.UUID
    name: str


@router.get(
    "/",
    response_model=list[Genre],
    summary="Получение всех жанров",
    description="Возвращает список всех жанров",
)
async def genres(
    paginated_params: Paginator = Depends(),
    genre_service: GenreService = Depends(get_genre_service),
) -> list[Genre]:
    genres_list = await genre_service.get_genres(
        paginated_params.page_number, paginated_params.page_size
    )
    if not genres_list:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail="Не найдено ни одного жанра"
        )

    return genres_list


@router.get(
    "/{genre_id}",
    response_model=Genre,
    summary="Получение жанра по его uuid",
    description="Возвращает информацию по заданному жанру",
)
async def genre(
    genre_uuid: str, genre_service: GenreService = Depends(get_genre_service)
) -> Genre:
    genre = await genre_service.get_genre(genre_uuid)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Жанр не найден")
    return genre

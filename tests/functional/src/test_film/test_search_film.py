import pytest

from testdata.films.film_search_data import (
    films_search_data,
    films_search_data_for_pagination,
)

pytestmark = pytest.mark.asyncio

FILM_ENDPOINT = "films"


async def test_films_search_success(make_get_request):
    query = "Star%2BWars"

    status, response = await make_get_request(
        endpoint=FILM_ENDPOINT + f"/search/?search={query}",
    )

    assert status == 200
    assert len(response) == 10
    assert response == films_search_data


async def test_films_search_not_found(make_get_request):
    query = "L"

    status, response = await make_get_request(
        endpoint=FILM_ENDPOINT + f"/search/?search={query}",
    )

    assert status == 404
    assert response == {"detail": "Не найдено ни одного фильма"}


async def test_films_search_pagination(make_get_request):
    query = "Star%2BWars"
    params = {
        "page_number": 1,
        "page_size": 5,
    }

    status, response = await make_get_request(
        endpoint=FILM_ENDPOINT + f"/search/?search={query}",
        params=params,
    )

    assert status == 200
    assert len(response) == params["page_size"]
    assert response == films_search_data_for_pagination


async def test_film_search_page_number_error(make_get_request):
    query = "Star%2BWars"
    params = {
        "page_number": -5,
        "page_size": 5,
    }

    status, response = await make_get_request(
        endpoint=FILM_ENDPOINT + f"/search/?search={query}",
        params=params,
    )

    assert status == 422
    assert response["detail"][0]["msg"] == "Input should be greater than or equal to 1"


async def test_film_search_page_size_error(make_get_request):
    query = "Star%2BWars"
    params = {
        "page_number": 1,
        "page_size": 200,
    }

    status, response = await make_get_request(
        endpoint=FILM_ENDPOINT + f"/search/?search={query}",
        params=params,
    )

    assert status == 422
    assert response["detail"][0]["msg"] == "Input should be less than or equal to 100"

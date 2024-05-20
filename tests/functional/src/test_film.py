import json

import pytest

from testdata.films.all_films import all_films
from testdata.films.full_info_film import full_info_film
from testdata.films.similar_films import similar_films
from testdata.mapping import FullFilm

pytestmark = pytest.mark.asyncio

ENDPOINT = "films"
FIlMS_PAGE_SIZE = 10


async def test_get_all_films_success(clean_cache, make_get_request):
    status, response = await make_get_request(endpoint=ENDPOINT)

    assert status == 200
    assert len(response) == FIlMS_PAGE_SIZE
    assert response == all_films


async def test_get_film_by_id_success(clean_cache, make_get_request):
    test_film_id = "00af52ec-9345-4d66-adbe-50eb917f463a"

    status, response_w_film = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_film_id}",
    )

    assert status == 200
    for key, value in full_info_film.items():
        assert response_w_film.get(key) == value


async def test_get_film_not_found(clean_cache, make_get_request):
    test_film_id = "test_film_uuid"

    status, response_w_genre = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_film_id}",
    )

    assert status == 404


async def test_compare_result_from_elastic_and_redis(
    clean_cache,
    make_get_request,
):
    test_film_id = "00af52ec-9345-4d66-adbe-50eb917f463a"

    es_status, response_w_film_from_elastic = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_film_id}",
    )

    r_status, response_w_film_from_redis = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_film_id}",
    )

    assert es_status == r_status
    assert response_w_film_from_elastic == response_w_film_from_redis


async def test_get_film_from_redis(clean_cache, make_get_request):
    test_film_id = "00af52ec-9345-4d66-adbe-50eb917f463a"

    _, response_w_film_from_elastic = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_film_id}",
    )

    film_from_cache = await clean_cache.get(f"movies::film_uuid::{test_film_id}")
    film_from_cache = json.loads(film_from_cache)

    assert FullFilm(**film_from_cache) == FullFilm(**response_w_film_from_elastic)


async def test_film_pagination(clean_cache, make_get_request):
    params = {
        "page_number": 1,
        "page_size": 5,
    }

    status, response = await make_get_request(endpoint=ENDPOINT, params=params)

    assert status == 200
    assert len(response) == params["page_size"]


async def test_film_pagination_page_number_error(make_get_request):
    params = {
        "page_number": -5,
        "page_size": 5,
    }

    status, response = await make_get_request(endpoint=ENDPOINT, params=params)

    assert status == 422
    assert response["detail"][0]["msg"] == "Input should be greater than or equal to 1"


async def test_film_pagination_page_size_error(make_get_request):
    params = {
        "page_number": 1,
        "page_size": 200,
    }

    status, response = await make_get_request(endpoint=ENDPOINT, params=params)

    assert status == 422
    assert response["detail"][0]["msg"] == "Input should be less than or equal to 100"


async def test_get_similar_films_by_id_success(clean_cache, make_get_request):
    test_film_id = "05d7341e-e367-4e2e-acf5-4652a8435f93"

    status, response_w_film = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_film_id}/similar",
    )

    assert status == 200
    assert response_w_film == similar_films

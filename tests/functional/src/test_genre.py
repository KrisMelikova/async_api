import json

import pytest

# весь файл с тестами запустится в асинхронном режиме
pytestmark = pytest.mark.asyncio

ENDPOINT = "genres"
GENRES_PAGE_SIZE = 10


async def test_get_all_genres_success(clean_cache, make_get_request):
    status, response = await make_get_request(endpoint=ENDPOINT)

    assert status == 200
    assert len(response) == GENRES_PAGE_SIZE


async def test_get_genre_by_id_success(clean_cache, make_get_request):
    test_genre_id = "6c162475-c7ed-4461-9184-001ef3d9f26e"

    status, response_w_genre = await make_get_request(
        endpoint=ENDPOINT + "/{genre_id}" + f"?genre_uuid={test_genre_id}",
    )

    assert status == 200
    assert response_w_genre["uuid"] == test_genre_id
    assert response_w_genre["name"] == "Sci-Fi"


async def test_get_genre_not_found(clean_cache, make_get_request):
    test_genre_id = "test_genre_uuid"

    status, response_w_genre = await make_get_request(
        endpoint=ENDPOINT + "/{genre_id}" + f"?genre_uuid={test_genre_id}",
    )

    assert status == 404


async def test_compare_result_from_elastic_and_redis(
        clean_cache, make_get_request,
):
    test_genre_id = "5373d043-3f41-4ea8-9947-4b746c601bbd"

    es_status, response_w_genre_from_elastic = await make_get_request(
        endpoint=ENDPOINT + "/{genre_id}" + f"?genre_uuid={test_genre_id}",
    )

    r_status, response_w_genre_from_redis = await make_get_request(
        endpoint=ENDPOINT + "/{genre_id}" + f"?genre_uuid={test_genre_id}",
    )

    assert es_status == r_status
    assert response_w_genre_from_elastic == response_w_genre_from_redis


async def test_get_genre_from_redis(clean_cache, make_get_request):
    test_genre_id = "ca88141b-a6b4-450d-bbc3-efa940e4953f"

    _, response_w_genre_from_elastic = await make_get_request(
        endpoint=ENDPOINT + "/{genre_id}" + f"?genre_uuid={test_genre_id}",
    )

    genre_from_cache = await clean_cache.get(f"genres::genre_uuid::{test_genre_id}")
    genre_from_cache = json.loads(genre_from_cache)

    assert genre_from_cache == response_w_genre_from_elastic


async def test_genre_pagination(clean_cache, make_get_request):
    params = {
        "page_number": 1,
        "page_size": 5,
    }

    status, response = await make_get_request(endpoint=ENDPOINT, params=params)

    assert status == 200
    assert len(response) == params["page_size"]


async def test_genre_pagination_page_number_error(make_get_request):
    params = {
        "page_number": -5,
        "page_size": 5,
    }

    status, response = await make_get_request(endpoint=ENDPOINT, params=params)

    assert status == 422
    assert response["detail"][0]["msg"] == "Input should be greater than or equal to 1"


async def test_genre_pagination_page_size_error(make_get_request):
    params = {
        "page_number": 1,
        "page_size": 200,
    }

    status, response = await make_get_request(endpoint=ENDPOINT, params=params)

    assert status == 422
    assert response["detail"][0]["msg"] == "Input should be less than or equal to 100"

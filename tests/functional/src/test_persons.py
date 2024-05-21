import json
import pytest
from testdata.mapping import Person

# весь файл с тестами запустится в асинхронном режиме
pytestmark = pytest.mark.asyncio

ENDPOINT = "persons"

async def test_get_persons_by_id_success(clean_cache, make_get_request):
    test_person_id = "46c7d430-c1bf-46df-8632-e49e29ee0033"

    status, response_w_person = await make_get_request(
        endpoint=ENDPOINT + f"/{test_person_id}",
    )

    assert status == 200
    assert response_w_person["uuid"] == test_person_id
    assert response_w_person["full_name"] == "Nate Scholz"

async def test_persons_not_found(make_get_request):
    test_person_id = "Something"

    status, response = await make_get_request(
        endpoint=ENDPOINT + f"/{test_person_id}",
    )

    assert status == 404
    assert response ==  {'detail': 'Персона с id Something не найдена'}


async def test_compare_result_from_elastic_and_redis(
    clean_cache,
    make_get_request,
):
    test_person_id = "46c7d430-c1bf-46df-8632-e49e29ee0033"

    es_status, response_w_person_from_elastic = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_person_id}",
    )

    r_status, response_w_person_from_redis = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_person_id}",
    )

    assert es_status == r_status
    assert response_w_person_from_elastic == response_w_person_from_redis
async def test_get_person_from_redis(clean_cache, make_get_request):
    test_person_id = "46c7d430-c1bf-46df-8632-e49e29ee0033"

    _, response_w_person_from_elastic = await make_get_request(
        endpoint=f"{ENDPOINT}/{test_person_id}",
    )

    person_from_cache = await clean_cache.get(f"persons::person_uuid::{test_person_id}")
    person_from_cache = json.loads(person_from_cache)

    assert Person(**person_from_cache) == Person(**response_w_person_from_elastic)

async def test_get_person_films(clean_cache, make_get_request):
    test_person_id = "46c7d430-c1bf-46df-8632-e49e29ee0033"
    film_id = "f75f574c-1103-4422-8018-07543151fb87"
    status, response_w_film = await make_get_request(
        endpoint=ENDPOINT + f"/{test_person_id}/film/",
    )

    assert status == 200
    assert len(response_w_film) == 1
    assert response_w_film[0]["uuid"] == film_id
    assert response_w_film[0]["title"] == "Star Wars: Episode XXXVIII - 10 Years Later"
    assert response_w_film[0]["imdb_rating"] == 5.1

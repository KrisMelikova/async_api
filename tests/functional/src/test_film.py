from testdata.films.full_data_film import full_data_film
import pytest

pytestmark = pytest.mark.asyncio

ENDPOINT = "films"
FIlMS_PAGE_SIZE = 10


async def test_get_all_films_success(clean_cache, make_get_request):
    status, response = await make_get_request(endpoint=ENDPOINT)

    assert status == 200
    assert len(response) == FIlMS_PAGE_SIZE


async def test_get_film_by_id_success(clean_cache, make_get_request):
    test_film_id = "00af52ec-9345-4d66-adbe-50eb917f463a"

    status, response_w_film = await make_get_request(
        endpoint=f'{ENDPOINT}/{test_film_id}',
    )

    assert status == 200
    for key, value in full_data_film.items():
        assert response_w_film.get(key) == value


async def test_get_film_not_found(clean_cache, make_get_request):
    test_film_id = "test_film_uuid"

    status, response_w_genre = await make_get_request(
        endpoint=f'{ENDPOINT}/{test_film_id}',
    )

    assert status == 404

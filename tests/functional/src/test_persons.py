import json
import pytest

# весь файл с тестами запустится в асинхронном режиме
pytestmark = pytest.mark.asyncio

ENDPOINT = "persons"

async def test_get_persons_by_id_success(clean_cache, make_get_request):
    test_person_id = "00395304-dd52-4c7b-be0d-c2cd7a495684"

    status, response_w_person = await make_get_request(
        endpoint=ENDPOINT + f"/{test_person_id}",
    )

    assert status == 200
    assert response_w_person["uuid"] == test_person_id
    assert response_w_person["full_name"] == "Jennifer Hale"

async def test_persons_not_found(make_get_request):
    test_person_id = "Something"

    status, response = await make_get_request(
        endpoint=ENDPOINT + f"/{test_person_id}",
    )

    assert status == 404
    assert response ==  {'detail': 'Персона с id Something не найдена'}
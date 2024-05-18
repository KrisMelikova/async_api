import pytest

# весь файл с тестами запустится в асинхронном режиме
pytestmark = pytest.mark.asyncio


# временный тест
async def test_test(clean_cache, client_session, make_get_request):
    status, response = await make_get_request(
        endpoint=f"genres/?page_size=10&page_number=1"
    )

    assert status == 200
    assert len(response) == 10

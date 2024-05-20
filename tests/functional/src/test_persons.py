import json
import pytest

# весь файл с тестами запустится в асинхронном режиме
pytestmark = pytest.mark.asyncio

ENDPOINT = "persons"

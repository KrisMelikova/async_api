from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class RedisSettings(BaseSettings):
    """Конфигурация для Redis"""

    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379


class ElasticSettings(BaseSettings):
    """Конфигурация для ElasticSearch"""

    ELASTIC_HOST: str = "127.0.0.1"
    ELASTIC_PORT: int = 9200


class TestSettings(BaseSettings):
    """Конфигурация проекта для тестирования"""

    MOVIES_API_URL: str = "http://127.0.0.1:8000/api/v1/"
    REDIS: RedisSettings = RedisSettings()
    ELASTIC: ElasticSettings = ElasticSettings()


test_settings = TestSettings()
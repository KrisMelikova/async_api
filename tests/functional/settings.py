from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

load_dotenv()


class RedisSettings(BaseSettings):
    """Конфигурация для Redis"""

    host: str = Field("127.0.0.1", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")


class ElasticSettings(BaseSettings):
    """Конфигурация для ElasticSearch"""

    host: str = Field("127.0.0.1", env="ELASTIC_HOST")
    port: int = Field(9200, env="ELASTIC_PORT")


class TestSettings(BaseSettings):
    """Конфигурация проекта для тестирования"""

    movies_api_url: str = "http://127.0.0.1:8000/api/v1/"
    redis: RedisSettings = RedisSettings()
    elastic: ElasticSettings = ElasticSettings()


test_settings = TestSettings()

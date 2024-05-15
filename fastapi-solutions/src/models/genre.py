from pydantic import Field

from src.models.model_config import BaseOrjsonModel


class Genre(BaseOrjsonModel):
    uuid: str = Field(alias="id")
    name: str

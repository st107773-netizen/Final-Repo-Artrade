from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache

class Settings(BaseSettings):
    database_url: str = Field(alias="DATABASE_URL")
    norms_path: str = Field(default="config/norms.yml", alias="NORMS_PATH")
    exclude_lifecycle_incomplete: bool = Field(default=True, alias="EXCLUDE_LIFECYCLE_INCOMPLETE")
    exclude_outcome_unknown: bool = Field(default=True, alias="EXCLUDE_OUTCOME_UNKNOWN")

    class Config:
        env_file = ".env"
        case_sensitive = False

@lru_cache
def get_settings() -> Settings:
    return Settings()

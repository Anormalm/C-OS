from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="COS_", env_file=".env", extra="ignore")

    app_name: str = "C-OS"
    app_env: str = "dev"
    log_level: str = "INFO"

    graph_backend: str = "inmemory"
    vector_backend: str = "inmemory"

    embedding_dim: int = Field(default=256, ge=64)
    chunk_size: int = Field(default=1000, ge=200)
    chunk_overlap: int = Field(default=120, ge=0)
    feedback_log_path: str | None = None
    action_log_path: str | None = None

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "password"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    fairshare_secret_key: str = ""
    jwt_secret: str = ""
    database_url: str = "sqlite:///./fairshare.db"
    port: int = 3000
    seed_demo: bool = False

    model_config = {
        "env_file": ("../.env", "../.env.local"),
        "env_file_encoding": "utf-8",
    }


settings = Settings()

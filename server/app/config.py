"""Application settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    fairshare_secret_key: str = ""
    jwt_secret: str = ""
    database_url: str = "sqlite:///./fairshare.db"
    port: int = 3000
    seed_demo: bool = False
    allowed_origins: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8080,http://127.0.0.1:8080"
    # Invite code required at registration. Empty string = registration disabled.
    registration_invite_code: str = ""
    # Docker/ngrok settings live in .env.local for deployment but are not used by the app directly.
    ngrok_authtoken: str = ""
    ngrok_domain: str = ""

    model_config = {
        "env_file": ("../.env", "../.env.local"),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()

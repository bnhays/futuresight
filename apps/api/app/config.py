from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    mongodb_url: str = "mongodb://localhost:27017"
    mongodb_db: str = "futuresight"
    scryfall_base_url: str = "https://api.scryfall.com"
    cors_origins: list[str] = ["http://localhost:4321"]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

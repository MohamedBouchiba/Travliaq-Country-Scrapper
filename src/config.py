from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    APP_NAME: str = "Travliaq-Country-Scrapper"
    MONGODB_URI: str
    DB_NAME: str = "travliaq_knowledge_base"
    COUNTRY_COLLECTION: str = "countries"
    CITY_COLLECTION: str = "cities"
    LOG_LEVEL: str = "INFO"
    SCRAPER_MODE: str = "frequent"  # Options: "rare", "frequent"

    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()

settings = get_settings()

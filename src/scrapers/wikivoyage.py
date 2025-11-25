import requests
import logging
from typing import List, Optional, Dict, Any
from src.scrapers.base import BaseScraper
from src.models import Country, City
from src.database import Database

logger = logging.getLogger(__name__)

class WikivoyageScraper(BaseScraper):
    # Wikivoyage API endpoint
    BASE_URL = "https://en.wikivoyage.org/w/api.php"

    def __init__(self, db: Database):
        self.db = db

    def fetch_countries(self) -> List[Country]:
        return []

    def fetch_cities(self) -> List[City]:
        logger.info("Starting Wikivoyage enrichment for existing cities...")
        
        # 1. Get cities from DB that need enrichment (or all for frequent update)
        # For efficiency, we should probably iterate over cities in our DB
        # But BaseScraper interface expects returning a list of City objects to be upserted.
        # So we will fetch cities from DB, enrich them, and return them.
        
        # Connect to DB if not already connected (Synchronizer handles connection, but we need access)
        # We passed DB instance in init.
        
        # Fetch a batch of cities (e.g., top 50 by population or random for MVP)
        # In a real frequent job, we might process a specific subset or use a cursor.
        # For this MVP, let's pick 20 major cities to demonstrate.
        
        target_cities = [
            "Paris", "London", "New York", "Tokyo", "Dubai", 
            "Singapore", "Barcelona", "Rome", "Bangkok", "Istanbul"
        ]
        
        enriched_cities = []
        
        for city_name in target_cities:
            try:
                summary = self._get_city_summary(city_name)
                if summary:
                    # Create a partial City object for update
                    # We need country_code to match the unique index (name, country_code)
                    # Ideally we should query the DB to get the correct country_code for "Paris" etc.
                    # But here we are mocking the "selection" logic.
                    # Let's assume we found them. 
                    
                    # REAL IMPLEMENTATION:
                    # db_city = self.db.cities.find_one({"name": city_name})
                    # if db_city: ...
                    
                    # For MVP simplicity without querying DB inside scraper (keeping it pure-ish):
                    # We will just return what we found and let the Upsert handle it IF we have the keys.
                    # Without country_code, we can't upsert correctly into our schema.
                    
                    # So, let's change strategy:
                    # The Synchronizer should probably pass the context or we query DB here.
                    # Since we have self.db, let's use it.
                    
                    db_city = self.db.cities.find_one({"name": city_name})
                    if db_city:
                        city = City(
                            name=db_city['name'],
                            country_code=db_city['country_code'],
                            source="wikivoyage",
                            travel_info={
                                "summary": summary,
                                "source": "Wikivoyage"
                            }
                        )
                        enriched_cities.append(city)
                        logger.info(f"Enriched {city_name}")
            except Exception as e:
                logger.warning(f"Failed to enrich {city_name}: {e}")
                
        return enriched_cities

    def _get_city_summary(self, city_name: str) -> Optional[str]:
        params = {
            "action": "query",
            "format": "json",
            "prop": "extracts",
            "titles": city_name,
            "exintro": 1,
            "explaintext": 1,
            "redirects": 1
        }
        
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=10)
            data = response.json()
            
            pages = data.get("query", {}).get("pages", {})
            for page_id, page_data in pages.items():
                if page_id != "-1":
                    return page_data.get("extract")
        except Exception:
            pass
        return None

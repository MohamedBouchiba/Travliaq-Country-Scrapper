import requests
import logging
import gzip
import json
from typing import List
from src.scrapers.base import BaseScraper
from src.models import Country, City

logger = logging.getLogger(__name__)

class GeoDataScraper(BaseScraper):
    # The cities data is stored as a gzipped JSON file
    BASE_URL = "https://raw.githubusercontent.com/dr5hn/countries-states-cities-database/master/json/cities.json.gz"

    def fetch_countries(self) -> List[Country]:
        # This scraper is focused on Cities
        return []

    def fetch_cities(self) -> List[City]:
        logger.info(f"Fetching cities from {self.BASE_URL}")
        try:
            # Download the gzipped file
            response = requests.get(self.BASE_URL, timeout=120)
            response.raise_for_status()
            
            # Decompress the gzipped content
            decompressed_data = gzip.decompress(response.content)
            data_str = decompressed_data.decode('utf-8')
            
            # Parse JSON
            data = json.loads(data_str)
            
            cities = []
            # Limit to major cities or process all? 
            # Let's process all but maybe filter by population if available to keep DB clean?
            # The dataset has: name, latitude, longitude, country_code, state_code
            
            count = 0
            for item in data:
                try:
                    # Basic validation
                    if not item.get('name') or not item.get('country_code'):
                        continue
                        
                    # Optional: Filter tiny villages if needed. 
                    # For now, we take everything.
                    
                    city = City(
                        name=item.get('name'),
                        country_code=item.get('country_code'),
                        country_name=item.get('country_name'),
                        state_code=item.get('state_code'),
                        state_name=item.get('state_name'),
                        latitude=float(item.get('latitude')) if item.get('latitude') else None,
                        longitude=float(item.get('longitude')) if item.get('longitude') else None,
                        source="dr5hn/countries-states-cities"
                    )
                    cities.append(city)
                    count += 1
                    
                    # Safety break for MVP to avoid 150k cities insertion taking forever during dev
                    # Remove this limit for production!
                    # if count > 5000: break 
                    
                except Exception as e:
                    continue
            
            logger.info(f"Fetched {len(cities)} cities")
            return cities
            
        except Exception as e:
            logger.error(f"Error fetching cities: {e}")
            return []

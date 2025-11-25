import requests
from typing import List
from src.scrapers.base import BaseScraper
from src.models import Country, City
import logging

logger = logging.getLogger(__name__)

class RestCountriesScraper(BaseScraper):
    # Correct v3.1 URL with required fields (max 10 fields)
    BASE_URL = "https://restcountries.com/v3.1/all?fields=name,cca2,cca3,capital,region,subregion,languages,currencies,population,continents"

    def fetch_countries(self) -> List[Country]:
        logger.info(f"Fetching countries from {self.BASE_URL}")
        try:
            headers = {
                "User-Agent": "Travliaq-Country-Scrapper/1.0"
            }
            response = requests.get(self.BASE_URL, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            countries = []
            for item in data:
                try:
                    # Basic validation
                    if not item.get('cca2'):
                        continue
                        
                    country = Country(
                        name=item.get('name', {}).get('common', 'Unknown'),
                        code_iso2=item.get('cca2'),
                        code_iso3=item.get('cca3'),
                        capital=item.get('capital', []),
                        region=item.get('region'),
                        subregion=item.get('subregion'),
                        languages=item.get('languages'),
                        currencies=item.get('currencies'),
                        population=item.get('population'),
                        continents=item.get('continents'),
                        flags=item.get('flags'),
                        source="restcountries.com"
                    )
                    countries.append(country)
                except Exception as e:
                    logger.warning(f"Error parsing country item: {e}")
                    continue
            
            logger.info(f"Fetched {len(countries)} countries")
            return countries
            
        except Exception as e:
            logger.error(f"Error fetching countries: {e}")
            return []

    def fetch_cities(self) -> List[City]:
        # REST Countries API does not provide cities
        return []

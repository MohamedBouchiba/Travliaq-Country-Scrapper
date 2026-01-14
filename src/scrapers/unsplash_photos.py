"""
Unsplash Photo Enrichment Scraper

This scraper enriches country data with high-quality representative photos
from Unsplash API. Uses the official Unsplash API to ensure compliance with
their guidelines and proper attribution.

API Key: Get yours at https://unsplash.com/developers
"""

import requests
import logging
from typing import Optional, Dict
from src.config import settings

logger = logging.getLogger(__name__)


class UnsplashPhotoScraper:
    """
    Fetches high-quality representative photos for countries using Unsplash API.

    Unsplash provides free high-resolution photos with proper attribution.
    Rate limits: 50 requests/hour for demo apps, 5000/hour for production.
    """

    BASE_URL = "https://api.unsplash.com"

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Unsplash scraper.

        Args:
            api_key: Unsplash API access key (gets from settings if not provided)
        """
        self.api_key = api_key or getattr(settings, 'UNSPLASH_API_KEY', None)
        if not self.api_key:
            logger.warning("No Unsplash API key provided. Photo enrichment will be skipped.")

    def get_country_photo(self, country_name: str, fallback_queries: list[str] = None) -> Optional[list[Dict[str, str]]]:
        """
        Fetch representative photos for a country (2 photos for comparison).

        Args:
            country_name: Name of the country (e.g., "France", "Japan")
            fallback_queries: Alternative search terms if main query fails

        Returns:
            List of dictionaries with photo_url, credit, source, and index, or None if not found
        """
        if not self.api_key:
            return None

        # Primary search query: country name + landmark/landscape keywords
        queries = [
            f"{country_name} landmark",
            f"{country_name} landscape",
            f"{country_name} architecture",
            f"{country_name} travel"
        ]

        # Add custom fallback queries if provided
        if fallback_queries:
            queries.extend(fallback_queries)

        for query in queries:
            try:
                photos = self._search_photo(query)
                if photos:
                    logger.info(f"Found {len(photos)} photo(s) for {country_name} using query: {query}")
                    return photos
            except Exception as e:
                logger.debug(f"Query '{query}' failed for {country_name}: {e}")
                continue

        logger.warning(f"No photo found for {country_name} after trying all queries")
        return None

    def _search_photo(self, query: str) -> Optional[Dict[str, str]]:
        """
        Search for a photo using Unsplash API.

        Args:
            query: Search query string

        Returns:
            Dictionary with photo data or None
        """
        headers = {
            "Authorization": f"Client-ID {self.api_key}",
            "Accept-Version": "v1"
        }

        params = {
            "query": query,
            "per_page": 2,  # Get 2 photos for comparison
            "orientation": "landscape",  # Better for country representations
            "content_filter": "high",     # Family-friendly content only
            "order_by": "relevant"
        }

        try:
            response = requests.get(
                f"{self.BASE_URL}/search/photos",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()

            data = response.json()

            if data.get("total") > 0 and data.get("results"):
                results = data["results"]
                photos = []

                # Get up to 2 photos
                for idx, photo in enumerate(results[:2], 1):
                    # Extract high-quality URL (regular size - good balance of quality/size)
                    photo_url = photo["urls"]["regular"]

                    # Build proper attribution per Unsplash guidelines
                    photographer = photo["user"]["name"]
                    photographer_username = photo["user"]["username"]
                    credit = f"Photo by {photographer} on Unsplash"

                    photos.append({
                        "photo_url": photo_url,
                        "photo_credit": credit,
                        "photo_source": f"https://unsplash.com/@{photographer_username}",
                        "index": idx
                    })

                return photos if photos else None

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Unsplash API request failed for query '{query}': {e}")
            # Re-raise 403 errors so they can be caught and handled for rate limiting
            if "403" in str(e) or "Forbidden" in str(e):
                raise
            return None
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse Unsplash response for query '{query}': {e}")
            return None


# Curated fallback queries for countries with specific landmarks
COUNTRY_SPECIFIC_QUERIES = {
    "France": ["Eiffel Tower Paris", "French Riviera"],
    "Japan": ["Mount Fuji", "Tokyo skyline", "Kyoto temple"],
    "Italy": ["Colosseum Rome", "Venice canals"],
    "United States": ["New York skyline", "Grand Canyon"],
    "United Kingdom": ["Big Ben London", "Tower Bridge"],
    "Spain": ["Sagrada Familia Barcelona", "Alhambra Granada"],
    "Germany": ["Neuschwanstein Castle", "Brandenburg Gate"],
    "China": ["Great Wall", "Forbidden City Beijing"],
    "India": ["Taj Mahal", "Jaipur palace"],
    "Brazil": ["Christ the Redeemer Rio", "Copacabana beach"],
    "Australia": ["Sydney Opera House", "Great Barrier Reef"],
    "Canada": ["Banff Lake Louise", "Toronto skyline"],
    "Mexico": ["Chichen Itza", "Guanajuato colorful"],
    "Thailand": ["Grand Palace Bangkok", "Phi Phi Islands"],
    "Greece": ["Santorini", "Acropolis Athens"],
    "Egypt": ["Pyramids Giza", "Luxor temple"],
    "Morocco": ["Marrakech medina", "Chefchaouen blue city"],
    "Turkey": ["Cappadocia balloons", "Hagia Sophia Istanbul"],
    "United Arab Emirates": ["Burj Khalifa Dubai", "Sheikh Zayed Mosque"],
    "South Africa": ["Table Mountain Cape Town", "Safari wildlife"],
    "Argentina": ["Perito Moreno Glacier", "Buenos Aires"],
    "Peru": ["Machu Picchu", "Cusco plaza"],
    "New Zealand": ["Milford Sound", "Mount Cook"],
    "Iceland": ["Northern lights", "Blue Lagoon"],
    "Norway": ["Fjords", "Northern lights Tromso"],
    "Switzerland": ["Matterhorn", "Swiss Alps"],
    "Netherlands": ["Amsterdam canals", "Windmills Kinderdijk"],
    "Portugal": ["Lisbon tram", "Porto Douro river"],
    "Russia": ["Red Square Moscow", "Saint Basil Cathedral"],
    "South Korea": ["Seoul Gyeongbokgung", "Jeju Island"],
    "Indonesia": ["Bali rice terraces", "Borobudur temple"],
    "Vietnam": ["Ha Long Bay", "Hoi An lanterns"],
    "Singapore": ["Marina Bay Sands", "Gardens by the Bay"],
    "Malaysia": ["Petronas Towers", "Batu Caves"],
}


def get_country_photo_with_fallbacks(scraper: UnsplashPhotoScraper, country_name: str) -> Optional[Dict[str, str]]:
    """
    Helper function to get country photo with curated fallback queries.

    Args:
        scraper: UnsplashPhotoScraper instance
        country_name: Name of the country

    Returns:
        Photo data dictionary or None
    """
    fallbacks = COUNTRY_SPECIFIC_QUERIES.get(country_name)
    return scraper.get_country_photo(country_name, fallback_queries=fallbacks)

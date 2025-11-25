import logging
import sys
from src.database import Database
from src.scrapers.restcountries import RestCountriesScraper
from src.services.synchronizer import Synchronizer
from src.config import settings

from src.scrapers.geodata import GeoDataScraper
from src.scrapers.wikivoyage import WikivoyageScraper

# Configure logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info(f"Starting {settings.APP_NAME}")
    
    try:
        db = Database()
        
        # Initialize all scrapers
        # Note: WikivoyageScraper needs DB access
        scrapers = [
            RestCountriesScraper(),
            GeoDataScraper(),
            WikivoyageScraper(db)
        ]
        
        synchronizer = Synchronizer(db, scrapers)
        synchronizer.run(mode=settings.SCRAPER_MODE)
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

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
    
    # --- DIAGNOSTICS START ---
    try:
        import socket
        import ssl
        import requests
        
        logger.info(f"Python: {sys.version}")
        logger.info(f"OpenSSL: {ssl.OPENSSL_VERSION}")
        
        # Check Public IP
        try:
            ip = requests.get('https://api.ipify.org', timeout=5).text
            logger.info(f"Container Public IP: {ip}")
            logger.info("IMPORTANT: Ensure this IP is whitelisted in MongoDB Atlas Network Access (or use 0.0.0.0/0)")
        except Exception as e:
            logger.error(f"Could not fetch public IP: {e}")
            
        # Test basic SSL
        try:
            requests.get('https://www.google.com', timeout=5)
            logger.info("Basic SSL connectivity check (google.com): PASSED")
        except Exception as e:
            logger.error(f"Basic SSL connectivity check failed: {e}")
            
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
    # --- DIAGNOSTICS END ---
    
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

from src.database import Database
from src.scrapers.base import BaseScraper
from src.scrapers.budget_calculator import BudgetCalculatorScraper
from typing import List
import logging

logger = logging.getLogger(__name__)

class Synchronizer:
    def __init__(self, db: Database, scrapers: List[BaseScraper]):
        self.db = db
        self.scrapers = scrapers

    def run(self, mode: str = "frequent"):
        logger.info(f"Starting synchronization in mode: {mode.upper()}")
        self.db.connect()
        
        try:
            active_scrapers = []
            
            # Filter scrapers based on mode
            if mode == "rare":
                # In rare mode, we run base data scrapers
                active_scrapers = [s for s in self.scrapers if s.__class__.__name__ in ["RestCountriesScraper", "GeoDataScraper"]]
            elif mode == "frequent":
                # In frequent mode, we run enrichment scrapers
                active_scrapers = [s for s in self.scrapers if s.__class__.__name__ in ["WikivoyageScraper"]]
            elif mode == "budget":
                # In budget mode, we only run budget calculation
                self._run_budget_calculation()
                return
            else:
                logger.warning(f"Unknown mode {mode}, running all scrapers")
                active_scrapers = self.scrapers

            for scraper in active_scrapers:
                scraper_name = scraper.__class__.__name__
                logger.info(f"Running scraper: {scraper_name}")
                
                # Countries
                try:
                    countries = scraper.fetch_countries()
                    if countries:
                        self.db.upsert_countries(countries)
                except Exception as e:
                    logger.error(f"Error in {scraper_name} (Countries): {e}")
                
                # Cities
                try:
                    cities = scraper.fetch_cities()
                    if cities:
                        self.db.upsert_cities(cities)
                except Exception as e:
                    logger.error(f"Error in {scraper_name} (Cities): {e}")
                    
        finally:
            self.db.close()

        logger.info("Synchronization completed")

    def _run_budget_calculation(self):
        """Run the budget calculator and update countries."""
        logger.info("Running budget calculation...")

        budget_scraper = BudgetCalculatorScraper()
        budgets = budget_scraper.calculate_budgets()

        if budgets:
            self.db.update_country_budgets(budgets)
            logger.info(f"Budget calculation completed: {len(budgets)} countries updated")
        else:
            logger.warning("No budgets calculated")

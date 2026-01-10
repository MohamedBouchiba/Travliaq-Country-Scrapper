"""
Budget Calculator Scraper

Calculates daily travel budget ranges from cost of living CSV data
and updates the countries collection in MongoDB.

Budget range includes min and max values for mid-range travelers.
Uses LLM for missing data and outlier correction.
"""
import csv
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from src.scrapers.base import BaseScraper
from src.models import Country, City
from src.utils.cost_parser import parse_usd_value, parse_numbeo_index
from src.utils.country_mapping import (
    get_iso2_from_name,
    get_country_name,
    get_region,
    get_neighbors,
    COUNTRY_NAME_TO_ISO2
)
from src.utils.llm_estimator import (
    is_outlier,
    batch_estimate_budgets,
    MIN_REASONABLE_BUDGET,
    MAX_REASONABLE_BUDGET
)

logger = logging.getLogger(__name__)

# Budget weights for mid-range traveler
WEIGHTS = {
    'hotel': 0.40,
    'meals': 0.30,
    'transport': 0.15,
    'activities': 0.15,
}

# Range factor for creating min/max from single value
RANGE_FACTOR_LOW = 0.85   # min = value * 0.85
RANGE_FACTOR_HIGH = 1.15  # max = value * 1.15

# Numbeo fallback constants
NYC_REFERENCE_BUDGET = 200.0  # Typical mid-range daily budget in NYC
NYC_COST_INDEX = 100.0        # NYC's Numbeo cost of living index baseline

# Default CSV path
DEFAULT_CSV_PATH = Path(__file__).parent.parent.parent / "data" / "cost_of_living_2025.csv"


class BudgetCalculatorScraper(BaseScraper):
    """
    Scraper that calculates daily travel budget ranges from cost of living data.

    Uses BudgetYourTrip data as primary source, Numbeo as fallback,
    and LLM for missing data and outlier correction.

    All countries will have a budget - no None values.
    """

    def __init__(self, csv_path: Path = DEFAULT_CSV_PATH):
        """
        Initialize the budget calculator.

        Args:
            csv_path: Path to cost of living CSV file
        """
        self.csv_path = csv_path
        self.budget_data: Dict[str, Tuple[float, float]] = {}  # iso2 -> (min, max)
        self.raw_csv_data: Dict[str, Dict] = {}  # iso2 -> raw row data

    def fetch_countries(self) -> List[Country]:
        """Not used - this scraper only enriches existing countries."""
        return []

    def fetch_cities(self) -> List[City]:
        """Not applicable for this scraper."""
        return []

    def calculate_budgets(self) -> Dict[str, Tuple[float, float]]:
        """
        Parse CSV and calculate daily budget ranges for all countries.

        Returns:
            Dictionary mapping ISO2 codes to (min, max) budget tuples
        """
        logger.info(f"Reading cost of living data from: {self.csv_path}")

        if not self.csv_path.exists():
            logger.error(f"CSV file not found: {self.csv_path}")
            return {}

        # Phase 1: Parse CSV and calculate budgets from data
        self._parse_csv()

        # Phase 2: Run LLM for missing/outlier values
        asyncio.run(self._fill_missing_with_llm())

        logger.info(f"Final budget count: {len(self.budget_data)} countries")
        return self.budget_data

    def _parse_csv(self):
        """Parse CSV and calculate initial budgets."""
        skipped = []
        calculated = 0
        needs_llm = []

        with open(self.csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                country_name = row.get('country', '').strip()
                if not country_name:
                    continue

                # Get ISO2 code
                iso2 = get_iso2_from_name(country_name)
                if not iso2:
                    skipped.append(country_name)
                    continue

                # Store raw data for LLM context
                self.raw_csv_data[iso2] = row

                # Calculate budget
                budget_range = self._calculate_row_budget(row)

                if budget_range is not None:
                    min_budget, max_budget = budget_range

                    # Check for outliers
                    avg_budget = (min_budget + max_budget) / 2
                    if is_outlier(avg_budget):
                        logger.warning(f"{country_name} ({iso2}): outlier ${avg_budget:.0f}/day - will use LLM")
                        needs_llm.append({
                            "iso2": iso2,
                            "name": country_name,
                            "region": get_region(iso2),
                            "current_value": avg_budget,
                            "numbeo_index": parse_numbeo_index(row.get('numbeo_cost_of_living_index'))
                        })
                    else:
                        self.budget_data[iso2] = budget_range
                        calculated += 1
                        logger.debug(f"{country_name} ({iso2}): ${min_budget:.0f}-${max_budget:.0f}/day")
                else:
                    # No data at all - need LLM
                    needs_llm.append({
                        "iso2": iso2,
                        "name": country_name,
                        "region": get_region(iso2),
                        "current_value": None,
                        "numbeo_index": parse_numbeo_index(row.get('numbeo_cost_of_living_index'))
                    })

        if skipped:
            logger.warning(f"Skipped {len(skipped)} countries without ISO2 mapping")

        logger.info(f"Calculated {calculated} budgets from CSV data")
        logger.info(f"{len(needs_llm)} countries need LLM estimation")

        # Store for LLM phase
        self._countries_needing_llm = needs_llm

    async def _fill_missing_with_llm(self):
        """Use LLM to fill in missing budgets and correct outliers."""
        if not hasattr(self, '_countries_needing_llm') or not self._countries_needing_llm:
            return

        countries_to_estimate = self._countries_needing_llm

        logger.info(f"Starting LLM estimation for {len(countries_to_estimate)} countries...")

        try:
            llm_results = await batch_estimate_budgets(
                countries_to_estimate,
                self.budget_data  # Pass known budgets for neighbor context
            )

            # Merge results
            for iso2, budget_range in llm_results.items():
                self.budget_data[iso2] = budget_range

            logger.info(f"LLM estimated {len(llm_results)} budgets")

        except Exception as e:
            logger.error(f"LLM estimation failed: {e}")
            # Fallback: use regional averages for failed estimations
            self._fallback_regional_averages()

    def _fallback_regional_averages(self):
        """Fallback to regional averages if LLM fails."""
        # Group known budgets by region
        regional_budgets: Dict[str, List[Tuple[float, float]]] = {}

        for iso2, (min_b, max_b) in self.budget_data.items():
            region = get_region(iso2)
            if region not in regional_budgets:
                regional_budgets[region] = []
            regional_budgets[region].append((min_b, max_b))

        # Calculate regional averages
        regional_averages: Dict[str, Tuple[float, float]] = {}
        for region, budgets in regional_budgets.items():
            avg_min = sum(b[0] for b in budgets) / len(budgets)
            avg_max = sum(b[1] for b in budgets) / len(budgets)
            regional_averages[region] = (round(avg_min, 2), round(avg_max, 2))

        # Global average as ultimate fallback
        all_budgets = list(self.budget_data.values())
        global_avg = (
            sum(b[0] for b in all_budgets) / len(all_budgets),
            sum(b[1] for b in all_budgets) / len(all_budgets)
        ) if all_budgets else (50.0, 80.0)

        # Fill missing with regional averages
        for country_info in self._countries_needing_llm:
            iso2 = country_info["iso2"]
            if iso2 not in self.budget_data:
                region = country_info["region"]
                if region in regional_averages:
                    self.budget_data[iso2] = regional_averages[region]
                else:
                    self.budget_data[iso2] = (round(global_avg[0], 2), round(global_avg[1], 2))
                logger.info(f"Fallback for {iso2}: regional average")

    def _calculate_row_budget(self, row: Dict[str, str]) -> Optional[Tuple[float, float]]:
        """
        Calculate daily budget range for a single CSV row.

        Args:
            row: CSV row as dictionary

        Returns:
            Tuple (min_budget, max_budget) in USD or None if insufficient data
        """
        # Parse BudgetYourTrip costs
        costs = {
            'hotel': parse_usd_value(row.get('budgetyourtrip_hotel_cost')),
            'meals': parse_usd_value(row.get('budgetyourtrip_meals_cost')),
            'transport': parse_usd_value(row.get('budgetyourtrip_transport_cost')),
            'activities': parse_usd_value(row.get('budgetyourtrip_activities_cost')),
        }

        # Try weighted calculation with available data
        budget = self._calculate_weighted_budget(costs)
        if budget is not None:
            # Create range from calculated value
            min_budget = round(budget * RANGE_FACTOR_LOW, 2)
            max_budget = round(budget * RANGE_FACTOR_HIGH, 2)
            return (min_budget, max_budget)

        # Fallback to Numbeo estimation
        numbeo_budget = self._estimate_from_numbeo(row)
        if numbeo_budget is not None:
            min_budget = round(numbeo_budget * RANGE_FACTOR_LOW, 2)
            max_budget = round(numbeo_budget * RANGE_FACTOR_HIGH, 2)
            return (min_budget, max_budget)

        return None

    def _calculate_weighted_budget(self, costs: Dict[str, Optional[float]]) -> Optional[float]:
        """
        Calculate weighted budget from available cost components.

        Redistributes weight proportionally when some categories are missing.

        Args:
            costs: Dictionary of cost category -> USD value (or None)

        Returns:
            Weighted daily budget or None if no data
        """
        # Filter to available costs
        available = {k: v for k, v in costs.items() if v is not None}

        if not available:
            return None

        # Calculate sum of available weights
        available_weight_sum = sum(WEIGHTS[k] for k in available)

        if available_weight_sum == 0:
            return None

        # Calculate budget with normalized weights
        budget = 0.0
        for category, cost in available.items():
            normalized_weight = WEIGHTS[category] / available_weight_sum
            budget += cost * normalized_weight

        return round(budget, 2)

    def _estimate_from_numbeo(self, row: Dict[str, str]) -> Optional[float]:
        """
        Estimate daily budget using Numbeo cost of living index.

        Uses NYC as baseline (index 100 = $200/day mid-range).

        Args:
            row: CSV row dictionary

        Returns:
            Estimated daily budget or None
        """
        index = parse_numbeo_index(row.get('numbeo_cost_of_living_index'))

        if index is None:
            return None

        # Scale relative to NYC
        budget = (index / NYC_COST_INDEX) * NYC_REFERENCE_BUDGET
        return round(budget, 2)

    def get_budget_for_country(self, iso2: str) -> Optional[Tuple[float, float]]:
        """
        Get calculated budget range for a specific country.

        Args:
            iso2: ISO2 country code

        Returns:
            (min, max) budget tuple or None
        """
        return self.budget_data.get(iso2.upper())

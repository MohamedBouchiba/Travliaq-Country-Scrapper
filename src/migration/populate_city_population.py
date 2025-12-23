#!/usr/bin/env python3
"""
Population Enrichment Script for Cities Table

This script enriches the `cities` table by populating the `population` column using:
1. GeoNames dataset (primary source) - cities15000.zip
2. Wikidata SPARQL queries (fallback for unmatched cities)

The script performs fuzzy matching on city names and validates geographic proximity
to ensure accurate population data.

Usage:
    python populate_city_population.py

Environment Variables:
    SUPABASE_DB_URL: PostgreSQL connection string (required)
    GEONAMES_DATASET: Dataset to use (default: cities15000)
    MAX_RADIUS_KM: Maximum distance for matching (default: 30)
    WIKIDATA_MAX_QPS: Wikidata API rate limit (default: 2)
    BATCH_SIZE: Database batch size (default: 2000)
    ONLY_NULL: Only update NULL populations (default: 1)
"""

from __future__ import annotations

import asyncio
import io
import logging
import math
import os
import sys
import time
import zipfile
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple
from urllib.parse import quote

import httpx
import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from rapidfuzz import fuzz
from tenacity import retry, stop_after_attempt, wait_exponential
from unidecode import unidecode

# Try to import tqdm for progress bars, fallback gracefully
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    print("Warning: tqdm not installed. Install with 'pip install tqdm' for progress bars.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration - Build database URL
DB_URL = os.getenv("SUPABASE_DB_URL")

# If SUPABASE_DB_URL not provided, build from individual components
if not DB_URL:
    pg_host = os.getenv("PG_HOST")
    pg_user = os.getenv("PG_USER")
    pg_password = os.getenv("PG_PASSWORD")
    pg_database = os.getenv("PG_DATABASE", "postgres")
    pg_port = os.getenv("PG_PORT", "5432")
    pg_sslmode = os.getenv("PG_SSLMODE", "require")

    if pg_host and pg_user and pg_password:
        # Build PostgreSQL URL
        from urllib.parse import quote_plus
        DB_URL = f"postgresql://{pg_user}:{quote_plus(pg_password)}@{pg_host}:{pg_port}/{pg_database}?sslmode={pg_sslmode}"
        logger.info("Built database URL from individual PG_* environment variables")
    else:
        logger.error("Missing database configuration. Provide either:")
        logger.error("  - SUPABASE_DB_URL (complete connection string)")
        logger.error("  - Or PG_HOST, PG_USER, PG_PASSWORD (individual components)")
        sys.exit(1)

GEONAMES_DATASET = os.getenv("GEONAMES_DATASET", "cities15000").strip()
MAX_RADIUS_KM = float(os.getenv("MAX_RADIUS_KM", "30"))
WIKIDATA_MAX_QPS = float(os.getenv("WIKIDATA_MAX_QPS", "2"))
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "2000"))
ONLY_NULL = os.getenv("ONLY_NULL", "1").strip() != "0"

# Constants
GEONAMES_BASE_URL = "https://download.geonames.org/export/dump"
WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = os.getenv("WIKIDATA_USER_AGENT", "Travliaq/1.0 (population enrichment)")
EARTH_RADIUS_KM = 6371.0
EXACT_MATCH_THRESHOLD = 100  # Exact name match
FUZZY_MATCH_THRESHOLD = 94   # Fuzzy match minimum score
WIKIDATA_MATCH_THRESHOLD = 92


@dataclass
class CityRecord:
    """Represents a city record from the database."""
    id: str
    name: str
    country_code: str
    lat: float
    lon: float


@dataclass
class GeoNamesRecord:
    """Represents a city record from GeoNames dataset."""
    name_normalized: str
    ascii_normalized: str
    lat: float
    lon: float
    population: int


@dataclass
class MatchResult:
    """Result of a population match operation."""
    city_id: str
    population: int
    source: str  # 'geonames' or 'wikidata'


@dataclass
class Statistics:
    """Statistics for the population enrichment process."""
    total_cities: int = 0
    geonames_matches: int = 0
    wikidata_matches: int = 0
    no_match: int = 0
    errors: int = 0

    def print_summary(self) -> None:
        """Print a summary of the statistics."""
        logger.info("=" * 60)
        logger.info("POPULATION ENRICHMENT SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total cities processed:     {self.total_cities:,}")
        logger.info(f"GeoNames matches:           {self.geonames_matches:,} ({self._percent(self.geonames_matches)}%)")
        logger.info(f"Wikidata matches:           {self.wikidata_matches:,} ({self._percent(self.wikidata_matches)}%)")
        logger.info(f"No match found:             {self.no_match:,} ({self._percent(self.no_match)}%)")
        logger.info(f"Errors:                     {self.errors:,}")
        logger.info(f"Success rate:               {self._percent(self.geonames_matches + self.wikidata_matches)}%")
        logger.info("=" * 60)

    def _percent(self, value: int) -> str:
        """Calculate percentage with 1 decimal place."""
        if self.total_cities == 0:
            return "0.0"
        return f"{(value / self.total_cities * 100):.1f}"


def normalize_name(name: str) -> str:
    """
    Normalize a city name for comparison.

    Converts to lowercase, removes accents, keeps only alphanumeric,
    and normalizes whitespace.

    Args:
        name: Original city name

    Returns:
        Normalized name
    """
    if not name:
        return ""

    # Convert to lowercase and remove accents
    normalized = unidecode(name.strip().lower())

    # Keep only alphanumeric and spaces
    chars = []
    prev_space = False
    for ch in normalized:
        if ch.isalnum():
            chars.append(ch)
            prev_space = False
        elif not prev_space:
            chars.append(" ")
            prev_space = True

    return " ".join("".join(chars).split())


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on Earth.

    Args:
        lat1, lon1: First point coordinates
        lat2, lon2: Second point coordinates

    Returns:
        Distance in kilometers
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2)

    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


class GeoNamesProvider:
    """Provider for GeoNames dataset operations."""

    def __init__(self, dataset: str = GEONAMES_DATASET):
        """
        Initialize the GeoNames provider.

        Args:
            dataset: Dataset name (e.g., 'cities15000')
        """
        self.dataset = dataset
        self.url = f"{GEONAMES_BASE_URL}/{dataset}.zip"
        self.data_by_country: Dict[str, List[GeoNamesRecord]] = {}
        self.spatial_index: Dict[str, Dict[Tuple[int, int], List[GeoNamesRecord]]] = {}
        self.index_precision = 1  # Decimal places for spatial index

    def download_and_parse(self) -> None:
        """Download and parse the GeoNames dataset."""
        logger.info(f"Downloading GeoNames dataset: {self.dataset}")

        try:
            response = requests.get(self.url, timeout=180)
            response.raise_for_status()
            zip_bytes = response.content
            logger.info(f"Downloaded {len(zip_bytes) / 1024 / 1024:.1f} MB")
        except Exception as e:
            logger.error(f"Failed to download GeoNames dataset: {e}")
            raise

        self._parse_zip(zip_bytes)
        self._build_spatial_index()

        total_records = sum(len(records) for records in self.data_by_country.values())
        logger.info(f"Parsed {total_records:,} records from {len(self.data_by_country)} countries")

    def _parse_zip(self, zip_bytes: bytes) -> None:
        """Parse the GeoNames ZIP file."""
        try:
            with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
                txt_file = next((n for n in zf.namelist() if n.endswith(".txt")), None)
                if not txt_file:
                    raise RuntimeError("No .txt file found in GeoNames ZIP")

                with zf.open(txt_file) as f:
                    for line_bytes in f:
                        self._parse_line(line_bytes)
        except Exception as e:
            logger.error(f"Failed to parse GeoNames ZIP: {e}")
            raise

    def _parse_line(self, line_bytes: bytes) -> None:
        """Parse a single line from GeoNames file."""
        try:
            line = line_bytes.decode("utf-8", errors="ignore").rstrip("\n")
            parts = line.split("\t")

            if len(parts) < 15:
                return

            # Extract fields
            name = parts[1]
            ascii_name = parts[2]
            lat = float(parts[4])
            lon = float(parts[5])
            feature_class = parts[6]
            country_code = parts[8]
            population_str = parts[14]

            # Filter: only populated places (P class) with population > 0
            if feature_class != "P":
                return

            try:
                population = int(population_str)
            except (ValueError, TypeError):
                population = 0

            if population <= 0:
                return

            # Create record
            record = GeoNamesRecord(
                name_normalized=normalize_name(name),
                ascii_normalized=normalize_name(ascii_name),
                lat=lat,
                lon=lon,
                population=population
            )

            self.data_by_country.setdefault(country_code, []).append(record)

        except Exception as e:
            # Skip malformed lines silently
            pass

    def _build_spatial_index(self) -> None:
        """Build spatial index for faster lookups."""
        logger.info("Building spatial index...")

        multiplier = 10 ** self.index_precision

        for country_code, records in self.data_by_country.items():
            index: Dict[Tuple[int, int], List[GeoNamesRecord]] = {}

            for record in records:
                grid_key = (
                    int(round(record.lat * multiplier)),
                    int(round(record.lon * multiplier))
                )
                index.setdefault(grid_key, []).append(record)

            self.spatial_index[country_code] = index

    def _get_nearby_grid_keys(self, lat: float, lon: float) -> List[Tuple[int, int]]:
        """Get grid keys for nearby cells (3x3 grid)."""
        multiplier = 10 ** self.index_precision
        center_lat = int(round(lat * multiplier))
        center_lon = int(round(lon * multiplier))

        keys = []
        for delta_lat in (-1, 0, 1):
            for delta_lon in (-1, 0, 1):
                keys.append((center_lat + delta_lat, center_lon + delta_lon))

        return keys

    def match_city(self, city: CityRecord) -> Optional[int]:
        """
        Match a city to GeoNames and return population.

        Strategy:
        1. Try exact name match within spatial proximity
        2. Try fuzzy match (>94% similarity) within spatial proximity

        Args:
            city: City record to match

        Returns:
            Population if matched, None otherwise
        """
        records = self.data_by_country.get(city.country_code)
        if not records:
            return None

        # Get candidates from spatial index
        spatial_idx = self.spatial_index.get(city.country_code, {})
        candidates = []

        for grid_key in self._get_nearby_grid_keys(city.lat, city.lon):
            candidates.extend(spatial_idx.get(grid_key, []))

        # If no nearby candidates, use all records for the country
        if not candidates:
            candidates = records

        normalized_query = normalize_name(city.name)

        # Phase 1: Exact match
        best_exact_pop = None
        best_exact_dist = float('inf')

        for record in candidates:
            if record.name_normalized == normalized_query or record.ascii_normalized == normalized_query:
                distance = haversine_distance(city.lat, city.lon, record.lat, record.lon)
                if distance <= MAX_RADIUS_KM and distance < best_exact_dist:
                    best_exact_dist = distance
                    best_exact_pop = record.population

        if best_exact_pop is not None:
            return best_exact_pop

        # Phase 2: Fuzzy match
        best_fuzzy_pop = None
        best_fuzzy_score = 0
        best_fuzzy_dist = float('inf')

        for record in candidates:
            score = max(
                fuzz.ratio(normalized_query, record.name_normalized),
                fuzz.ratio(normalized_query, record.ascii_normalized)
            )

            if score < FUZZY_MATCH_THRESHOLD:
                continue

            distance = haversine_distance(city.lat, city.lon, record.lat, record.lon)

            if distance > MAX_RADIUS_KM:
                continue

            if score > best_fuzzy_score or (score == best_fuzzy_score and distance < best_fuzzy_dist):
                best_fuzzy_score = score
                best_fuzzy_dist = distance
                best_fuzzy_pop = record.population

        return best_fuzzy_pop


class WikidataProvider:
    """Provider for Wikidata SPARQL operations."""

    def __init__(self, max_qps: float = WIKIDATA_MAX_QPS):
        """
        Initialize the Wikidata provider.

        Args:
            max_qps: Maximum queries per second
        """
        self.max_qps = max_qps
        self.delay = 1.0 / max(max_qps, 0.1)
        self._last_request = 0.0

    async def _rate_limit(self) -> None:
        """Apply rate limiting."""
        now = time.time()
        elapsed = now - self._last_request

        if elapsed < self.delay:
            await asyncio.sleep(self.delay - elapsed)

        self._last_request = time.time()

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=10))
    async def _query(self, client: httpx.AsyncClient, sparql: str) -> Dict[str, Any]:
        """Execute a SPARQL query against Wikidata."""
        await self._rate_limit()

        response = await client.get(
            WIKIDATA_ENDPOINT,
            params={"format": "json", "query": sparql},
            headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/sparql-results+json"
            },
            timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _build_sparql(self, city: CityRecord, radius_km: float = MAX_RADIUS_KM) -> str:
        """Build SPARQL query for a city."""
        # Limit radius to reasonable value
        radius_km = min(radius_km, 50)

        return f"""
SELECT ?item ?itemLabel ?pop ?coord WHERE {{
  SERVICE wikibase:around {{
    ?item wdt:P625 ?coord .
    bd:serviceParam wikibase:center "Point({city.lon} {city.lat})"^^geo:wktLiteral .
    bd:serviceParam wikibase:radius "{radius_km}" .
  }}
  ?item wdt:P17 ?country .
  ?country wdt:P297 "{city.country_code}" .
  ?item wdt:P1082 ?pop .
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr". }}
}}
"""

    def _parse_result(self, city: CityRecord, bindings: List[Dict[str, Any]]) -> Optional[int]:
        """Parse Wikidata results and find best match."""
        normalized_query = normalize_name(city.name)

        best_pop = None
        best_score = 0
        best_dist = float('inf')

        for binding in bindings:
            # Extract label
            label = binding.get("itemLabel", {}).get("value", "")

            # Extract population
            pop_str = binding.get("pop", {}).get("value")
            if not pop_str:
                continue

            try:
                population = int(float(pop_str))
                if population <= 0:
                    continue
            except (ValueError, TypeError):
                continue

            # Extract coordinates
            coord_str = binding.get("coord", {}).get("value", "")
            if "Point(" not in coord_str:
                continue

            try:
                coords_part = coord_str.split("Point(")[1].split(")")[0].strip()
                lon_str, lat_str = coords_part.split()
                result_lat = float(lat_str)
                result_lon = float(lon_str)
            except (ValueError, IndexError):
                continue

            # Calculate match score and distance
            score = fuzz.ratio(normalized_query, normalize_name(label))
            distance = haversine_distance(city.lat, city.lon, result_lat, result_lon)

            # Keep best match
            if distance > MAX_RADIUS_KM:
                continue

            if score > best_score or (score == best_score and distance < best_dist):
                best_score = score
                best_dist = distance
                best_pop = population

        # Only return if match quality is sufficient
        if best_pop is not None and best_score >= WIKIDATA_MATCH_THRESHOLD:
            return best_pop

        return None

    async def match_cities(self, cities: List[CityRecord]) -> List[MatchResult]:
        """
        Match multiple cities against Wikidata.

        Args:
            cities: List of cities to match

        Returns:
            List of match results
        """
        results = []

        progress_iter = tqdm(cities, desc="Wikidata queries") if HAS_TQDM else cities

        async with httpx.AsyncClient() as client:
            for city in progress_iter:
                try:
                    sparql = self._build_sparql(city)
                    data = await self._query(client, sparql)
                    bindings = data.get("results", {}).get("bindings", [])

                    population = self._parse_result(city, bindings)

                    if population is not None:
                        results.append(MatchResult(
                            city_id=city.id,
                            population=population,
                            source='wikidata'
                        ))

                except Exception as e:
                    logger.warning(f"Wikidata query failed for {city.name}: {e}")

        return results


class DatabaseManager:
    """Manager for database operations."""

    def __init__(self, connection_string: str):
        """
        Initialize database manager.

        Args:
            connection_string: PostgreSQL connection string
        """
        self.connection_string = connection_string
        self.conn = None

    def connect(self) -> None:
        """Establish database connection."""
        logger.info("Connecting to database...")
        try:
            self.conn = psycopg2.connect(self.connection_string)
            self.conn.autocommit = False
            logger.info("Database connection established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")

    def fetch_cities(self) -> List[CityRecord]:
        """
        Fetch cities from database.

        Returns:
            List of city records
        """
        where_clause = "AND (population IS NULL OR population <= 0)" if ONLY_NULL else ""

        query = f"""
            SELECT
                id,
                name,
                country_code,
                ST_Y(location::geometry) AS lat,
                ST_X(location::geometry) AS lon
            FROM public.cities
            WHERE location IS NOT NULL
            {where_clause}
            ORDER BY country_code, name
        """

        try:
            with self.conn.cursor() as cursor:
                cursor.execute(query)
                rows = cursor.fetchall()

            cities = [
                CityRecord(
                    id=str(row[0]),
                    name=row[1],
                    country_code=row[2],
                    lat=float(row[3]),
                    lon=float(row[4])
                )
                for row in rows
            ]

            logger.info(f"Fetched {len(cities):,} cities from database")
            return cities

        except Exception as e:
            logger.error(f"Failed to fetch cities: {e}")
            raise

    def update_populations(self, matches: List[MatchResult]) -> int:
        """
        Update population values in database.

        Args:
            matches: List of population matches

        Returns:
            Number of rows updated
        """
        if not matches:
            return 0

        try:
            with self.conn.cursor() as cursor:
                # Create temporary table
                cursor.execute("""
                    CREATE TEMPORARY TABLE tmp_city_pop (
                        id UUID PRIMARY KEY,
                        population BIGINT
                    ) ON COMMIT DROP
                """)

                # Insert into temporary table
                values = [(match.city_id, match.population) for match in matches]
                execute_values(
                    cursor,
                    "INSERT INTO tmp_city_pop (id, population) VALUES %s",
                    values,
                    page_size=5000
                )

                # Update main table
                cursor.execute("""
                    UPDATE public.cities c
                    SET population = t.population
                    FROM tmp_city_pop t
                    WHERE c.id = t.id
                """)

                updated = cursor.rowcount
                self.conn.commit()

                return updated

        except Exception as e:
            self.conn.rollback()
            logger.error(f"Failed to update populations: {e}")
            raise


def main() -> None:
    """Main execution function."""
    logger.info("=" * 60)
    logger.info("CITY POPULATION ENRICHMENT SCRIPT")
    logger.info("=" * 60)
    logger.info(f"GeoNames dataset: {GEONAMES_DATASET}")
    logger.info(f"Max radius: {MAX_RADIUS_KM} km")
    logger.info(f"Batch size: {BATCH_SIZE}")
    logger.info(f"Only NULL populations: {ONLY_NULL}")
    logger.info("=" * 60)

    stats = Statistics()

    # Initialize database
    db = DatabaseManager(DB_URL)
    db.connect()

    try:
        # Fetch cities
        cities = db.fetch_cities()
        stats.total_cities = len(cities)

        if not cities:
            logger.info("No cities to process")
            return

        # Initialize GeoNames
        geonames = GeoNamesProvider(GEONAMES_DATASET)
        geonames.download_and_parse()

        # Match against GeoNames
        logger.info("Matching against GeoNames...")
        geonames_matches = []
        unmatched_cities = []

        progress_iter = tqdm(cities, desc="GeoNames matching") if HAS_TQDM else cities

        for city in progress_iter:
            try:
                population = geonames.match_city(city)

                if population is not None:
                    geonames_matches.append(MatchResult(
                        city_id=city.id,
                        population=population,
                        source='geonames'
                    ))
                    stats.geonames_matches += 1
                else:
                    unmatched_cities.append(city)

            except Exception as e:
                logger.error(f"Error matching {city.name}: {e}")
                stats.errors += 1
                unmatched_cities.append(city)

        # Update database with GeoNames matches in batches
        if geonames_matches:
            logger.info(f"Updating {len(geonames_matches):,} GeoNames matches...")

            for i in range(0, len(geonames_matches), BATCH_SIZE):
                batch = geonames_matches[i:i + BATCH_SIZE]
                updated = db.update_populations(batch)
                logger.info(f"Updated {updated:,} rows (batch {i // BATCH_SIZE + 1})")

        # Match unmatched cities against Wikidata
        if unmatched_cities:
            logger.info(f"Matching {len(unmatched_cities):,} unmatched cities against Wikidata...")

            wikidata = WikidataProvider(WIKIDATA_MAX_QPS)
            loop = asyncio.get_event_loop()
            wikidata_matches = loop.run_until_complete(wikidata.match_cities(unmatched_cities))

            stats.wikidata_matches = len(wikidata_matches)
            stats.no_match = len(unmatched_cities) - len(wikidata_matches)

            # Update database with Wikidata matches
            if wikidata_matches:
                logger.info(f"Updating {len(wikidata_matches):,} Wikidata matches...")

                for i in range(0, len(wikidata_matches), BATCH_SIZE):
                    batch = wikidata_matches[i:i + BATCH_SIZE]
                    updated = db.update_populations(batch)
                    logger.info(f"Updated {updated:,} rows (batch {i // BATCH_SIZE + 1})")
        else:
            stats.no_match = 0

        # Print summary
        stats.print_summary()

    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    finally:
        db.close()

    logger.info("Script completed successfully")


if __name__ == "__main__":
    main()

"""
Country Photo Enrichment Script - AUTO MODE with Rate Limit Handling

This script enriches existing country documents in MongoDB with 2 high-quality
representative photos from Unsplash for comparison. Automatically handles API
rate limits by sleeping for 1h10 when limit is reached.

Usage:
    python enrich_countries_photos_auto.py

Features:
    - Gets 2 photos per country for comparison
    - Auto-sleeps for 1h10 when rate limit hit
    - Continues automatically until all countries are processed
    - Perfect for overnight runs
"""

import sys
import logging
import time
from typing import Optional
from datetime import datetime

from src.database import Database
from src.scrapers.unsplash_photos import UnsplashPhotoScraper, get_country_photo_with_fallbacks
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CountryPhotoEnricherAuto:
    """Enriches country documents with 2 photos from Unsplash, with auto rate limit handling."""

    def __init__(self, db: Database, unsplash_scraper: UnsplashPhotoScraper):
        self.db = db
        self.scraper = unsplash_scraper
        self.rate_limit_sleep_seconds = 70 * 60  # 1h10 = 70 minutes

    def enrich_all_countries(self) -> dict:
        """
        Enrich all countries with 2 photos each, handling rate limits automatically.

        Returns:
            Statistics dictionary
        """
        stats = {
            "total": 0,
            "processed": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "already_has_photo": 0,
            "rate_limit_pauses": 0
        }

        try:
            # Fetch all countries from MongoDB
            countries_collection = self.db.db.countries
            query = {}

            # Count total
            stats["total"] = countries_collection.count_documents(query)
            logger.info(f"Found {stats['total']} countries in database")
            logger.info("=" * 70)
            logger.info("🌙 AUTO MODE: Will sleep 1h10 when rate limit is hit")
            logger.info("=" * 70)

            # Fetch countries
            cursor = countries_collection.find(query)
            consecutive_failures = 0
            max_consecutive_failures = 2  # After 2 consecutive 403s, we know we hit the limit

            for country_doc in cursor:
                stats["processed"] += 1
                country_name = country_doc.get("name", "Unknown")
                country_code = country_doc.get("code_iso2", "??")

                logger.info(f"[{stats['processed']}/{stats['total']}] Processing: {country_name} ({country_code})")

                # Skip if already has photos
                if country_doc.get("photo_url_1") and country_doc.get("photo_url_2"):
                    logger.info(f"  ↳ Already has 2 photos, skipping")
                    stats["already_has_photo"] += 1
                    stats["skipped"] += 1
                    consecutive_failures = 0  # Reset on success
                    continue

                # Fetch photos from Unsplash
                try:
                    photos_data = get_country_photo_with_fallbacks(self.scraper, country_name)

                    if photos_data and len(photos_data) > 0:
                        logger.info(f"  ✓ Found {len(photos_data)} photo(s) for {country_name}")

                        # Prepare update data for 2 photos
                        update_data = {}

                        for idx, photo in enumerate(photos_data[:2], 1):
                            logger.info(f"    Photo {idx}: {photo['photo_url'][:60]}...")
                            logger.info(f"    Credit {idx}: {photo['photo_credit']}")

                            update_data[f"photo_url_{idx}"] = photo["photo_url"]
                            update_data[f"photo_credit_{idx}"] = photo["photo_credit"]
                            update_data[f"photo_source_{idx}"] = photo["photo_source"]

                        # Update MongoDB document
                        countries_collection.update_one(
                            {"_id": country_doc["_id"]},
                            {"$set": update_data}
                        )
                        stats["updated"] += 1
                        consecutive_failures = 0  # Reset on success
                    else:
                        logger.warning(f"  ✗ No photo found for {country_name}")
                        stats["failed"] += 1
                        # Don't reset consecutive_failures here, keep counting

                except Exception as e:
                    error_message = str(e)

                    # Check if it's a rate limit error (403)
                    if "403" in error_message or "Forbidden" in error_message:
                        consecutive_failures += 1
                        logger.warning(f"  ✗ Rate limit hit for {country_name} (consecutive: {consecutive_failures})")

                        # If we've had multiple consecutive 403s, we're rate limited
                        if consecutive_failures >= max_consecutive_failures:
                            stats["rate_limit_pauses"] += 1
                            logger.warning("")
                            logger.warning("=" * 70)
                            logger.warning("⏰ RATE LIMIT REACHED!")
                            logger.warning(f"   Sleeping for 1h10 (70 minutes)...")
                            logger.warning(f"   Current time: {datetime.now().strftime('%H:%M:%S')}")
                            logger.warning(f"   Will resume at: {datetime.fromtimestamp(time.time() + self.rate_limit_sleep_seconds).strftime('%H:%M:%S')}")
                            logger.warning("=" * 70)
                            logger.warning("")

                            time.sleep(self.rate_limit_sleep_seconds)

                            logger.info("")
                            logger.info("=" * 70)
                            logger.info("✅ Sleep completed! Resuming enrichment...")
                            logger.info("=" * 70)
                            logger.info("")

                            consecutive_failures = 0  # Reset after sleep

                            # Retry the current country
                            try:
                                photos_data = get_country_photo_with_fallbacks(self.scraper, country_name)
                                if photos_data and len(photos_data) > 0:
                                    update_data = {}
                                    for idx, photo in enumerate(photos_data[:2], 1):
                                        update_data[f"photo_url_{idx}"] = photo["photo_url"]
                                        update_data[f"photo_credit_{idx}"] = photo["photo_credit"]
                                        update_data[f"photo_source_{idx}"] = photo["photo_source"]

                                    countries_collection.update_one(
                                        {"_id": country_doc["_id"]},
                                        {"$set": update_data}
                                    )
                                    stats["updated"] += 1
                                    logger.info(f"  ✓ Successfully updated {country_name} after rate limit pause")
                                else:
                                    stats["failed"] += 1
                            except Exception as retry_error:
                                logger.error(f"  ✗ Failed to update {country_name} even after pause: {retry_error}")
                                stats["failed"] += 1
                    else:
                        logger.error(f"  ✗ Error processing {country_name}: {e}")
                        stats["failed"] += 1

            # Print summary
            logger.info("\n" + "=" * 70)
            logger.info("ENRICHMENT SUMMARY")
            logger.info("=" * 70)
            logger.info(f"Total countries:          {stats['total']}")
            logger.info(f"Processed:                {stats['processed']}")
            logger.info(f"Successfully updated:     {stats['updated']}")
            logger.info(f"Already had photos:       {stats['already_has_photo']}")
            logger.info(f"Failed:                   {stats['failed']}")
            logger.info(f"Skipped:                  {stats['skipped']}")
            logger.info(f"Rate limit pauses (1h10): {stats['rate_limit_pauses']}")
            logger.info("=" * 70)

            return stats

        except Exception as e:
            logger.error(f"Fatal error during enrichment: {e}")
            raise


def main():
    """Main entry point for the auto-enrichment script."""

    # Check for Unsplash API key
    if not hasattr(settings, 'UNSPLASH_API_KEY') or not settings.UNSPLASH_API_KEY:
        logger.error("UNSPLASH_API_KEY not found in settings/environment")
        logger.error("Please add UNSPLASH_API_KEY to your .env file")
        logger.error("Get your API key at: https://unsplash.com/developers")
        sys.exit(1)

    try:
        # Initialize database and scraper
        db = Database()
        db.connect()  # Connect to MongoDB
        unsplash_scraper = UnsplashPhotoScraper()

        # Create enricher
        enricher = CountryPhotoEnricherAuto(db, unsplash_scraper)

        # Run enrichment
        logger.info("Starting AUTO country photo enrichment...")
        logger.info("🌙 This script will run overnight and handle rate limits automatically")
        logger.info("")

        stats = enricher.enrich_all_countries()

        logger.info("")
        logger.info("🎉 Enrichment completed successfully!")
        logger.info(f"✅ {stats['updated']} countries updated with 2 photos each")
        logger.info(f"⏰ Total rate limit pauses: {stats['rate_limit_pauses']} (1h10 each)")

        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\n⚠️  Enrichment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Enrichment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

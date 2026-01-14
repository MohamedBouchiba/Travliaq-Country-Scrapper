"""
Country Photo Enrichment Script

This script enriches existing country documents in MongoDB with high-quality
representative photos from Unsplash.

Usage:
    python enrich_countries_photos.py [--dry-run] [--limit N]

Options:
    --dry-run: Preview changes without updating the database
    --limit N: Process only first N countries (for testing)
"""

import sys
import logging
import argparse
from typing import Optional

from src.database import Database
from src.scrapers.unsplash_photos import UnsplashPhotoScraper, get_country_photo_with_fallbacks
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CountryPhotoEnricher:
    """Enriches country documents with photos from Unsplash."""

    def __init__(self, db: Database, unsplash_scraper: UnsplashPhotoScraper):
        self.db = db
        self.scraper = unsplash_scraper

    def enrich_all_countries(self, dry_run: bool = False, limit: Optional[int] = None) -> dict:
        """
        Enrich all countries with photos.

        Args:
            dry_run: If True, don't actually update the database
            limit: Maximum number of countries to process

        Returns:
            Statistics dictionary
        """
        stats = {
            "total": 0,
            "processed": 0,
            "updated": 0,
            "skipped": 0,
            "failed": 0,
            "already_has_photo": 0
        }

        try:
            # Fetch all countries from MongoDB
            countries_collection = self.db.db.countries
            query = {}

            # Count total
            stats["total"] = countries_collection.count_documents(query)
            logger.info(f"Found {stats['total']} countries in database")

            # Fetch countries
            cursor = countries_collection.find(query)
            if limit:
                cursor = cursor.limit(limit)
                logger.info(f"Processing limited to first {limit} countries")

            for country_doc in cursor:
                stats["processed"] += 1
                country_name = country_doc.get("name", "Unknown")
                country_code = country_doc.get("code_iso2", "??")

                logger.info(f"[{stats['processed']}/{stats['total']}] Processing: {country_name} ({country_code})")

                # Skip if already has a photo (unless we want to update)
                if country_doc.get("photo_url"):
                    logger.info(f"  ↳ Already has photo, skipping")
                    stats["already_has_photo"] += 1
                    stats["skipped"] += 1
                    continue

                # Fetch photo from Unsplash
                try:
                    photo_data = get_country_photo_with_fallbacks(self.scraper, country_name)

                    if photo_data:
                        logger.info(f"  ✓ Found photo for {country_name}")
                        logger.info(f"    URL: {photo_data['photo_url'][:60]}...")
                        logger.info(f"    Credit: {photo_data['photo_credit']}")

                        if not dry_run:
                            # Update MongoDB document
                            countries_collection.update_one(
                                {"_id": country_doc["_id"]},
                                {"$set": {
                                    "photo_url": photo_data["photo_url"],
                                    "photo_credit": photo_data["photo_credit"],
                                    "photo_source": photo_data["photo_source"]
                                }}
                            )
                            stats["updated"] += 1
                        else:
                            logger.info("  [DRY RUN] Would update database")
                            stats["updated"] += 1
                    else:
                        logger.warning(f"  ✗ No photo found for {country_name}")
                        stats["failed"] += 1

                except Exception as e:
                    logger.error(f"  ✗ Error processing {country_name}: {e}")
                    stats["failed"] += 1

            # Print summary
            logger.info("\n" + "=" * 60)
            logger.info("ENRICHMENT SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total countries:       {stats['total']}")
            logger.info(f"Processed:             {stats['processed']}")
            logger.info(f"Successfully updated:  {stats['updated']}")
            logger.info(f"Already had photos:    {stats['already_has_photo']}")
            logger.info(f"Failed:                {stats['failed']}")
            logger.info(f"Skipped:               {stats['skipped']}")
            logger.info("=" * 60)

            if dry_run:
                logger.info("\n** DRY RUN MODE - No changes were made to the database **\n")

            return stats

        except Exception as e:
            logger.error(f"Fatal error during enrichment: {e}")
            raise


def main():
    """Main entry point for the enrichment script."""
    parser = argparse.ArgumentParser(
        description="Enrich country documents with photos from Unsplash"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating the database"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Process only first N countries (for testing)"
    )
    parser.add_argument(
        "--force-update",
        action="store_true",
        help="Update photos even for countries that already have one"
    )

    args = parser.parse_args()

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
        enricher = CountryPhotoEnricher(db, unsplash_scraper)

        # Run enrichment
        logger.info("Starting country photo enrichment...")
        if args.dry_run:
            logger.info("Running in DRY RUN mode - no changes will be made")

        stats = enricher.enrich_all_countries(
            dry_run=args.dry_run,
            limit=args.limit
        )

        logger.info("Enrichment completed successfully!")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("\nEnrichment interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Enrichment failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Country Photo Enrichment Script - AUTO MODE v2

Simplified version that detects rate limit by checking HTTP 403 errors
and automatically sleeps for 1h10.
"""

import sys
import logging
import time
import requests
from typing import Optional
from datetime import datetime

from src.database import Database
from src.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_unsplash_photos(country_name: str, api_key: str) -> Optional[list]:
    """Get 2 photos from Unsplash for a country."""
    headers = {
        "Authorization": f"Client-ID {api_key}",
        "Accept-Version": "v1"
    }

    queries = [
        f"{country_name} landmark",
        f"{country_name} landscape",
    ]

    for query in queries:
        try:
            response = requests.get(
                "https://api.unsplash.com/search/photos",
                headers=headers,
                params={
                    "query": query,
                    "per_page": 2,
                    "orientation": "landscape",
                    "content_filter": "high",
                    "order_by": "relevant"
                },
                timeout=10
            )

            # Check for rate limit
            if response.status_code == 403:
                logger.warning(f"Rate limit hit on query: {query}")
                raise requests.exceptions.HTTPError("403 Rate Limit")

            response.raise_for_status()
            data = response.json()

            if data.get("total") > 0 and data.get("results"):
                photos = []
                for idx, photo in enumerate(data["results"][:2], 1):
                    photos.append({
                        "photo_url": photo["urls"]["regular"],
                        "photo_credit": f"Photo by {photo['user']['name']} on Unsplash",
                        "photo_source": f"https://unsplash.com/@{photo['user']['username']}",
                        "index": idx
                    })
                return photos if photos else None
        except requests.exceptions.HTTPError as e:
            if "403" in str(e):
                raise  # Re-raise 403 errors
            logger.error(f"HTTP error for {query}: {e}")
        except Exception as e:
            logger.error(f"Error for {query}: {e}")

    return None


def main():
    """Main enrichment loop with auto-sleep."""

    if not hasattr(settings, 'UNSPLASH_API_KEY') or not settings.UNSPLASH_API_KEY:
        logger.error("UNSPLASH_API_KEY not found")
        sys.exit(1)

    # Connect to MongoDB
    db = Database()
    db.connect()
    collection = db.db.countries

    total = collection.count_documents({})
    logger.info(f"Found {total} countries")
    logger.info("=" * 70)
    logger.info("🌙 AUTO MODE: Sleeping 1h10 when rate limit hit")
    logger.info("=" * 70)

    stats = {
        "processed": 0,
        "updated": 0,
        "failed": 0,
        "sleeps": 0
    }

    cursor = collection.find({})

    for country_doc in cursor:
        stats["processed"] += 1
        country_name = country_doc.get("name", "Unknown")
        country_code = country_doc.get("code_iso2", "??")

        logger.info(f"[{stats['processed']}/{total}] Processing: {country_name} ({country_code})")

        # Skip if already has 2 photos
        if country_doc.get("photo_url_1") and country_doc.get("photo_url_2"):
            logger.info(f"  ↳ Already has 2 photos, skipping")
            continue

        # Try to get photos
        while True:  # Loop to retry after sleep
            try:
                photos = get_unsplash_photos(country_name, settings.UNSPLASH_API_KEY)

                if photos and len(photos) > 0:
                    logger.info(f"  ✓ Found {len(photos)} photo(s)")

                    update_data = {}
                    for idx, photo in enumerate(photos[:2], 1):
                        logger.info(f"    Photo {idx}: {photo['photo_url'][:50]}...")
                        update_data[f"photo_url_{idx}"] = photo["photo_url"]
                        update_data[f"photo_credit_{idx}"] = photo["photo_credit"]
                        update_data[f"photo_source_{idx}"] = photo["photo_source"]

                    collection.update_one(
                        {"_id": country_doc["_id"]},
                        {"$set": update_data}
                    )
                    stats["updated"] += 1
                else:
                    logger.warning(f"  ✗ No photo found")
                    stats["failed"] += 1

                break  # Success, move to next country

            except requests.exceptions.HTTPError as e:
                if "403" in str(e):
                    # Rate limit hit!
                    stats["sleeps"] += 1
                    logger.warning("")
                    logger.warning("=" * 70)
                    logger.warning("⏰ RATE LIMIT REACHED!")
                    logger.warning(f"   Pause #{stats['sleeps']}")
                    logger.warning(f"   Sleeping for 1h10 (70 minutes)...")
                    logger.warning(f"   Current time: {datetime.now().strftime('%H:%M:%S')}")
                    resume_time = time.time() + (70 * 60)
                    logger.warning(f"   Will resume at: {datetime.fromtimestamp(resume_time).strftime('%H:%M:%S')}")
                    logger.warning("=" * 70)
                    logger.warning("")

                    time.sleep(70 * 60)  # Sleep 1h10

                    logger.info("")
                    logger.info("=" * 70)
                    logger.info("✅ Sleep completed! Resuming...")
                    logger.info("=" * 70)
                    logger.info("")
                    # Loop will retry the same country
                else:
                    logger.error(f"  ✗ HTTP error: {e}")
                    stats["failed"] += 1
                    break

    # Summary
    logger.info("\n" + "=" * 70)
    logger.info("ENRICHMENT SUMMARY")
    logger.info("=" * 70)
    logger.info(f"Total countries:     {total}")
    logger.info(f"Processed:           {stats['processed']}")
    logger.info(f"Successfully updated: {stats['updated']}")
    logger.info(f"Failed:              {stats['failed']}")
    logger.info(f"Sleep pauses (1h10): {stats['sleeps']}")
    logger.info("=" * 70)
    logger.info("🎉 Enrichment completed!")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.warning("\n⚠️  Interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1)
